import json
import pytz
from datetime import datetime
from XNBackend.models import db, S3FC20, MantunciBox, EnergyConsumeByHour, EnergyConsumeDaily, BoxAlarms, \
UniAlarms
from XNBackend.tasks import logger

L = logger.getChild(__name__)
ALARM_MAPPING = {
    1: '未知报警',
    2: '短路报警',
    3: '漏电报警',
    4: '过载报警',
    5: '过压报警',
    6: '欠压报警',
    7: '温度报警',
    8: '浪涌报警',
    9: '漏电保护功能正常',
    10: '漏电保护自检未完成',
    11: '打火报警',
    12: '漏电预警',
    13: '电流预警',
    14: '过压预警',
    15: '欠压预警',
    16: '通讯报警'
}


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


def find_room(mac, addr, room_mapping):
    mac_mapping = room_mapping.get(mac)
    if not mac_mapping:
        return
    else:
        room = mac_mapping.get(addr)
        if not room:
            return
        return room[0]


def find_level(type_number: int) ->int:
    if type_number in [1, 2, 3, 4, 5, 6, 7, 8]:
        return 1
    elif type_number in [0, 11, 12, 13, 14, 15]:
        return 2
    elif type_number in [16, 10]:
        return 3
    else:
        return 4


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
        return self.room + '-----' + str(self.measure) + '--------'+ str(self.power) + '--------' + str(self.time)


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

    def compress_records(self):
        record_dict = {}
        for r in self.records:
            uni_key = self.get_uni_key(r)
            if uni_key not in record_dict:
                record_dict[uni_key] = r
            else:
                prev_value = self.get_value_from_key(record_dict[uni_key])
                now_value = self.get_value_from_key(r)
                total = prev_value + now_value
                self.set_value(record_dict[uni_key], total)
        self.records = list(record_dict.values())

    @staticmethod
    def get_uni_key(record):
        raise NotImplementedError

    @staticmethod
    def get_value_from_key(target):
        raise NotImplementedError

    @staticmethod
    def set_value(obj, value):
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

    @staticmethod
    def get_uni_key(record):
        key = '_'.join(['RTE', str(record.room), str(record.measure)])
        return key

    @staticmethod
    def get_value_from_key(target):
        return getattr(target, 'power')

    @staticmethod
    def set_value(obj, value):
        setattr(obj, 'power', value)


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

    @staticmethod
    def get_uni_key(record):
        return record.s3_fc20.desc

    @staticmethod
    def get_value_from_key(target):
        return getattr(target, 'electricity')

    @staticmethod
    def set_value(obj, value):
        setattr(obj, 'electricity', value)


class EnergyAlarm(ElectriConsumeHour):

    def load_data_from_response(self, req_body, mapping=None):
        resp = self.data_requests(req_body)
        if resp['code'] == '0':
            datas = resp['data']['datas']
            for entry in datas:
                if entry['typeNumber'] == 9:
                    continue
                room = find_room(self.mac, entry['addr'], mapping)
                external_id = entry['auto_id']
                ua = UniAlarms.query.filter(UniAlarms.external_id == external_id).first()
                if ua:
                    continue
                extra = json.dumps({"mac": self.mac, "addr": 1})

                box_alarm = UniAlarms(
                    external_id=entry['auto_id'],
                    alarm_group=0,
                    alarm_code=entry['typeNumber'],
                    alarm_content=ALARM_MAPPING.get(entry['typeNumber']),
                    room=room,
                    floor=int(room[0]) if room else None,
                    active=1,
                    level=find_level(entry['typeNumber']),
                    happen_time=datetime.strptime(entry['time'], '%Y-%m-%d %H:%M'),
                    extra=extra
                )
                self.records.append(box_alarm)
