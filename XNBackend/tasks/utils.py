import json
import pytz
from datetime import datetime
from XNBackend.models import db, S3FC20, MantunciBox, EnergyConsumeByHour, EnergyConsumeDaily, BoxAlarms
from XNBackend.tasks import logger

L = logger.getChild(__name__)


def get_s3fc20_addr_mapping(mb_mac):
    addr2room = dict()
    for sf in S3FC20.query.filter(S3FC20.box.has(mac=mb_mac)):
        addr2room[sf.addr] = [sf.locator_id, sf.measure_type]
    return addr2room


def get_mantunsci_addr_mapping():
    mantunsci_dict = dict()
    for m in MantunciBox.query:
        mac = m.mac
        mantunsci_dict[mac] = get_s3fc20_addr_mapping(mac)
    return mantunsci_dict


class S3FC20RealTimePower:
    def __init__(self, content, room_mapping):
        self.power = content['aW']
        self.mac = content['mac']
        self.addr = content['addr']
        self.room, self.measure = room_mapping[self.mac][self.addr]
        self.time = datetime.strptime(content['updateTime'],
                                      '%Y-%m-%d %H:%M:%S')

    def save_to_rds(self, rds_client, sep):
        key = sep.join(['RTE', str(self.room), str(self.measure)])
        value = json.dumps([self.power, int(self.time.timestamp())])
        rds_client.set(key, value)

    def __str__(self):
        return self.room + ':' + str(self.power) + ':' + str(self.time)


class MantunsciBase:
    def __init__(self, mac, id, mantunsci_req_session, router_uri, project_code):
        self.mac = mac
        self.mb_id = id
        self.s = mantunsci_req_session
        self.router_uri = router_uri
        self.proj_code = project_code
        self.records = []

    def data_requests(self, req_body):
        r = self.s.post(self.router_uri, req_body)
        return r.json()

    def load_data_from_response(self, *args, **kwargs):
        raise NotImplementedError

    def save_data(self, *args):
        raise NotImplementedError


class MantunsciRealTimePower(MantunsciBase):
    def __init__(self, mac, id, mantunsci_req_session, router_uri, project_code, rds_client, req_body):
        super(MantunsciRealTimePower, self).__init__(mac,
                                                     id,
                                                     mantunsci_req_session,
                                                     router_uri,
                                                     project_code)
        self.rds_client = rds_client
        self.req_body = req_body

    def load_data_from_response(self, mapping=None):
        resp = self.data_requests(self.req_body)
        if resp['code'] == '0':
            for s in resp['data']:
                mac_info = s['mac']
                addr_info = s['addr']
                if mapping.get(mac_info).get(addr_info):
                    self.records.append(S3FC20RealTimePower(s, mapping))

    def save_data(self):
        for s in self.records:
            s.save_to_rds(self.rds_client, '_')


class ElectriConsumeHour(MantunsciBase):
    tz_info = pytz.timezone('Asia/Shanghai')

    def load_data_from_response(self, req_body, mapping=None):
        resp = self.data_requests(req_body)
        year = req_body.get('year')
        month = req_body.get('month')
        day = req_body.get('day')

        if resp['code'] == '0':
            for time_range in resp['data']:
                happen_time = datetime(year=year, month=month, day=day, hour=int(time_range),
                                       tzinfo=self.tz_info)
                for entry in resp['data'][time_range]:
                    addr = entry['addr']
                    s3fc20 = S3FC20.query.filter(S3FC20.addr == addr).filter(S3FC20.box.has(mac=self.mac)).first()
                    if s3fc20:
                        record = EnergyConsumeByHour(s3_fc20_id=s3fc20.id,
                                                     updated_at=happen_time,
                                                     electricity=entry['electricity'])
                        self.records.append(record)

    def save_data(self, db_session):
        db_session.bulk_save_objects(self.records)
        try:
            db_session.commit()
        except Exception as e:
            L.exception(e)
            db_session.rollback()


class EnergyConsumeDay(ElectriConsumeHour):

    def load_data_from_response(self, req_body, mapping=None):
        year = req_body.get('year')
        month = req_body.get('month')
        day = req_body.get('day')
        resp = self.data_requests(req_body)

        if resp['code'] == '0':
            happen_time = datetime(year=year, month=month, day=day, tzinfo=self.tz_info)
            for entry in resp['data']:
                addr = entry['addr']
                s3fc20 = S3FC20.query.filter(S3FC20.addr == addr).filter(S3FC20.box.has(mac=self.mac)).first()
                if s3fc20:
                    record = EnergyConsumeDaily(s3_fc20_id=s3fc20.id,
                                                updated_at=happen_time,
                                                electricity=entry['electricity'],
                                                s3_fc20=s3fc20)
                    self.records.append(record)

    def compress_records(self):
        record_dict = {}
        for r in self.records:
            if r.s3_fc20.desc not in record_dict:
                record_dict[r.s3_fc20.desc] = r
            else:
                elec_prev = record_dict[r.s3_fc20.desc].electricity
                elec_now = r.electricity
                total = elec_now + elec_prev
                record_dict[r.s3_fc20.desc].electricity = total
        self.records = list(record_dict.values())


class EnergyAlarm(ElectriConsumeHour):

    def load_data_from_response(self, req_body, mapping=None):
        resp = self.data_requests(req_body)
        if resp['code'] == '0':
            datas = resp['data']['datas']
            for entry in datas:
                b_a = BoxAlarms(id=int(entry['auto_id']),
                                addr=int(entry['addr']),
                                node=entry['node'],
                                alarm_or_type=entry['type'],
                                time=datetime.strptime(entry['time'], '%Y-%m-%d %H:%M'),
                                info=entry['info'],
                                type_number=entry.get('typeNumber'),
                                box_id=self.mb_id
                                )
                self.records.append(b_a)

