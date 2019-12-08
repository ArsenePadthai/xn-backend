import json
import requests
from flask import current_app
from datetime import datetime
from XNBackend.models import S3FC20
from XNBackend.task import logger
from XNBackend.api_client.mantunsci import MantunsciAuthInMemory

L = logger.getChild(__name__)
param = {
    # 'auth_url': current_app.config['MANTUNSCI_AUTH_URL'],
    # 'username': current_app.config['MANTUNSCI_USERNAME'],
    # 'password': current_app.config['MANTUNSCI_PASSWORD'],
    # 'app_key': current_app.config['MANTUNSCI_APP_KEY'],
    # 'app_secret': current_app.config['MANTUNSCI_APP_SECRET'],
    # 'redirect_uri': current_app.config['MANTUNSCI_REDIRECT_URI'],
    'auth_url': 'http://10.100.101.198:8088/ebx-rook/',
    'username': 'prod',
    'password': 'abc123++',
    'app_key': 'O000000063',
    'app_secret': '590752705B63B2DADD84050303C09ECF',
    'redirect_uri': 'http://10.100.101.198:8088/ebx-rook/demo.jsp'
}

s = None


def req_session():
    global s
    if s is None:
        s = requests.Session()
        s.auth = MantunsciAuthInMemory(param['auth_url'],
                                       param['username'],
                                       param['password'],
                                       param['app_key'],
                                       param['app_secret'],
                                       param['redirect_uri'])
    return s


def data_requests(body):
    # assume it is correct
    s = req_session()
    r = s.post(current_app.config['MANTUNSCI_ROUTER_URI'], data=body)
    message = r.json()
    return message


class RedisReporterBase():
    def __init__(self, redis_client, rd_key_prefix: str, targets: list, sep='_'):
        self.rd = redis_client
        self.prefix = rd_key_prefix
        self.targets = targets
        self.sep = sep


class MantunsciBoxReporter(RedisReporterBase):
    @staticmethod
    def get_addr_mapping(mb_mac):
        addr2room = dict()
        for sf in S3FC20.query.filter(S3FC20.box.has(mac=mb_mac)):
            addr2room[sf.addr] = [sf.box.locator_id, sf.measure_type]
        return addr2room

    @staticmethod
    def parse_sf_content(content: dict, mapping):
        addr = content.get('addr')
        if addr not in mapping:
            return
        room = mapping[addr][0]
        measure_type = mapping[addr][1]
        rt_power = content.get('aW')
        updated_time = content.get('updateTime')
        updated_time = datetime.strptime(updated_time, '%Y-%m-%d %H:%M:%S')
        return rt_power, room, measure_type, int(updated_time.timestamp())

    def get_rd_key(self, room, measure):
        return self.sep.join([self.prefix, str(room), str(measure)])

    def set_value(self, key, value):
        value_serialized = json.dumps(value)
        self.rd.set(key, value_serialized)

    def report(self):
        for mb in self.targets:
            body = {'method': 'GET_BOX_CHANNELS_REALTIME',
                    'projectCode': 'P00000000001',
                    'mac': mb.mac}
            try:
                m_data = data_requests(body)
                assert m_data['code'] == '0'
            except Exception as e:
                L.exception(e)
                L.error('failed to get mantunscibox realtime data')
                return

            mapping = self.get_addr_mapping(mb.mac)
            for paragraph in m_data['data']:
                addr = paragraph.get('addr')
                parse_ret = self.parse_sf_content(paragraph, mapping)
                if not parse_ret:
                    L.info(f'failed to parse addr {addr} for mantunscibox {mb.mac}')
                    continue
                rt_power, room, measure_type, update_time = self.parse_sf_content(paragraph,
                                                                                  mapping)
                key = self.get_rd_key(room, measure_type)
                self.set_value(key, (rt_power, update_time))
