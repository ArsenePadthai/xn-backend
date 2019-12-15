import json
import requests
import pytz
from datetime import datetime
from XNBackend.models import db, S3FC20, MantunciBox, EnergyConsumeByHour, EnergyConsumeDaily
from XNBackend.task import logger
from XNBackend.api_client.mantunsci import MantunsciAuthInMemory

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
    def __init__(self, mac, auth_params):
        self.mac = mac
        self.auth_params = auth_params
        self.s = requests.Session()
        self.s.auth = MantunsciAuthInMemory(
            auth_params['auth_url'],
            auth_params['username'],
            auth_params['password'],
            auth_params['app_key'],
            auth_params['app_secret'],
            auth_params['redirect_uri'],
        )

    def data_requests(self, req_body):
        r = self.s.post(self.auth_params['router_uri'], req_body)
        return r.json()

    def load_data_from_response(self, mapping=None):
        raise NotImplementedError

    def save_data(self):
        raise NotImplementedError


class MantunsciRealTimePower(MantunsciBase):
    def __init__(self, mac, auth_params, rds_client):
        super(MantunsciRealTimePower, self).__init__(mac, auth_params)
        self.rds_client = rds_client
        self.req_body = {
            "method": "GET_BOX_CHANNELS_REALTIME",
            "projectCode": self.auth_params['project_code'],
            'mac': self.mac
        }
        self.s3fc20s = []

    def load_data_from_response(self, mapping=None):
        resp = self.data_requests(self.req_body)
        if resp['code'] != '0':
            return
        else:
            for s in resp['data']:
                mac_info = s['mac']
                addr_info = s['addr']
                if mapping.get(mac_info).get(addr_info):
                    self.s3fc20s.append(S3FC20RealTimePower(s, mapping))

    def save_data(self):
        for s in self.s3fc20s:
            s.save_to_rds(self.rds_client, '_')


class ElectriConsumeHour(MantunsciBase):
    def __init__(self, mac, auth_params, year, month, day, db_session, req_body):
        super(ElectriConsumeHour, self).__init__(mac, auth_params)
        self.year = year
        self.month = month
        self.day = day
        self.req_body = req_body
        self.consumption_record = []
        self.db_session = db.session
        self.tz_info = pytz.timezone('Asia/Shanghai')

    def load_data_from_response(self, mapping=None):
        resp = self.data_requests(self.req_body)
        if resp['code'] != '0':
            return []
        else:
            for time_range in resp['data']:
                happen_time = datetime(year=self.year, month=self.month, day=self.day, hour=int(time_range),
                                       tzinfo=self.tz_info)
                for entry in resp['data'][time_range]:
                    addr = entry['addr']
                    s3fc20 = S3FC20.query.filter(S3FC20.addr == addr).filter(S3FC20.box.has(mac=self.mac)).first()
                    if s3fc20:
                        record = EnergyConsumeByHour(s3_fc20_id=s3fc20.id,
                                                     updated_at=happen_time,
                                                     electricity=entry['electricity'])
                        self.consumption_record.append(record)
            return self.consumption_record

    def save_data(self):
        self.db_session.bulk_save_objects(self.consumption_record)
        try:
            db.session.commit()
        except Exception as e:
            L.exception(e)
            db.session.rollback()


class EnergyConsumeDay(ElectriConsumeHour):

    def load_data_from_response(self, mapping=None):
        resp = self.data_requests(self.req_body)
        if resp['code'] != '0':
            return []
        else:
            happen_time = datetime(year=self.year, month=self.month, day=self.day, tzinfo=self.tz_info)
            for entry in resp['data']:
                addr = entry['addr']
                s3fc20 = S3FC20.query.filter(S3FC20.addr == addr).filter(S3FC20.box.has(mac=self.mac)).first()
                if s3fc20:
                    record = EnergyConsumeDaily(s3_fc20_id=s3fc20.id,
                                                updated_at=happen_time,
                                                electricity=entry['electricity'])
                    self.consumption_record.append(record)
            return self.consumption_record

