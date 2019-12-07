# -*- coding: utf-8 -*-
import requests
import time
import json
from datetime import datetime
from flask import current_app
from datetime import datetime, timedelta
from XNBackend.api_client.mantunsci import MantunsciAuthInMemory
from XNBackend.task import celery, logger
from XNBackend.models.models import db, EnergyConsumeDaily, EnegyConsumeMonthly,\
    EnergyConsumeByHour, MantunciBox, S3FC20, S3FC20Records, BoxAlarms

L = logger.getChild(__name__)

param = {
    'auth_url': current_app.config['MANTUNSCI_AUTH_URL'],
    'username': current_app.config['MANTUNSCI_USERNAME'],
    'password': current_app.config['MANTUNSCI_PASSWORD'],
    'app_key': current_app.config['MANTUNSCI_APP_KEY'],
    'app_secret': current_app.config['MANTUNSCI_APP_SECRET'],
    'redirect_uri': current_app.config['MANTUNSCI_REDIRECT_URI']
}

localtime = time.localtime(time.time())
all_body = [
    {'method':'GET_BOX_MON_POWER', 'projectCode':'P00000000001', 'mac':'', 'year':localtime[0], 'month':localtime[1]},
    {'method':'GET_BOX_DAY_POWER', 'projectCode':'P00000000001', 'mac':'', 'year':localtime[0], 'month':localtime[1], 'day':localtime[2]},
    {'method':'GET_BOX_CHANNELS_REALTIME', 'projectCode':'P00000000001', 'mac':''},
    {'method':'GET_BOX_ALARM', 'projectCode':'P00000000001', 'mac':'', 'start':'', 'end':''},
    {'method':'GET_BOX_HOUR_POWER', 'projectCode':'P00000000001', 'mac':'', 'year':localtime[0], 'month':localtime[1], 'day':localtime[2], 'hour':localtime[3]}
    ]

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


def data_generator(n):
    global all_body
    for circuit in MantunciBox.query.order_by():
        all_body[n]['mac'] = circuit.mac
        data = data_requests(all_body[n])
        yield data, circuit.id


def data_generator_1(schema):
    for box in MantunciBox.query.order_by():
        schema['mac'] = box.mac
        data = data_requests(schema)
        yield data, box.id


@celery.task(bind=True)
def all_boxes(self):
    record = []
    body = {'method': 'GET_BOXES',
            'projectCode': 'P00000000001'}
    data = data_requests(body)['data']
    import pprint
    pprint.pprint(data)
    # # try:
    #     data = data_requests(body)['data']
    # except Exception:
    #     self.retry(countdown=3.0)
    #     return ''
    # for i in range(len(data)):
    #     breaker = MantunciBox.query.filter_by(mac=data[i]['mac']).first()
    #     if breaker is None:
    #         box = MantunciBox(mac=data[i]['mac'], name=data[i]['name'], phone=data[i]['phone'])
    #         record.append(box)
    #     else:
    #         breaker.name = data[i]['name']
    #         breaker.phone = data[i]['phone']
    # db.session.bulk_save_objects(record)
    # db.session.commit()


@celery.task()
def update_s3fc20_current():
    all_s3fc20 = S3FC20.query
    for i in all_s3fc20:
        body = {
            "method": "GET_BOX_CHANNELS_REALTIME",
            "projectCode": current_app.config["MANTUNSCI_PROJECT_CODE"],
        }
        data_requests()


@celery.task(bind=True)
def power_month(self):
    record = []
    for recv_data,id in data_generator(0):
        try:
            data = recv_data['data']
        except KeyError:
            #self.retry(countdown=3.0)
            continue
        for i in range(len(data)):
            c20 = S3FC20.query.filter_by(addr=data[i]['addr'], box_id=id).first()
            monthly_record = EnegyConsumeMonthly(box_id=id, s3_fc20_id=c20.id, electricity=data[i]['electricity'])
            record.append(monthly_record)
    db.session.bulk_save_objects(record)
    db.session.commit()


@celery.task(bind=True)
def power_day(self):
    record = []
    for recv_data,id in data_generator(1):
        try:
            data = recv_data['data']
        except KeyError:
            #self.retry(countdown=3.0)
            continue 
        for i in range(len(data)):
            c20 = S3FC20.query.filter_by(addr=data[i]['addr'], box_id=id).first()
            daily_record = EnergyConsumeDaily(box_id=id, s3_fc20_id=c20.id, electricity=data[i]['electricity'])
            record.append(daily_record)
    db.session.bulk_save_objects(record)
    db.session.commit()


@celery.task(bind=True)
def power_hour(self):
    record = []
    for recv_data,id in data_generator(4):
        try:
            data = recv_data['data']
        except KeyError:
            #self.retry(countdown=3.0)
            continue 
        for i in range(len(data)):
            c20 = S3FC20.query.filter_by(addr=data[i]['addr'], box_id=id).first()
            daily_record = EnergyConsumeByHour(box_id=id, s3_fc20_id=c20.id, electricity=data[i]['electricity'])
            record.append(daily_record)
    db.session.bulk_save_objects(record)
    db.session.commit()


column_mappings = {
    'title': 'title', 
    'validity': 'validity', 
    'enable_netctr': 'enableNetCtrl',
    'oc': 'oc', 
    'online': 'online', 
    'total_power': 'power', 
    'mxgg': 'mxgg', 
    'mxgl': 'mxgl', 
    'line_type': 'lineType', 
    'spec': 'specification', 
    'control': 'control', 
    'visibility': 'visibility',
    'alarm': 'alarm', 
    'gLd': 'gLd', 
    'gA': 'gA', 
    'gT': 'gT', 
    'gV': 'gV', 
    'gW': 'gW', 
    'gPF': 'gPF',
    'aA': 'aA', 
    'aT': 'aT', 
    'aV': 'aV', 
    'aW': 'aW', 
    'aPF': 'aPF', 
    'bA': 'bA', 
    'bT': 'bT', 
    'bV': 'bV',
    'bW': 'bW', 
    'bPF': 'bPF', 
    'cA': 'cA', 
    'cT': 'cT', 
    'cV': 'cV', 
    'cW': 'cW', 
    'cPF': 'cPF',
    'nA': 'nA', 
    'nT': 'nT'
}

@celery.task(bind=True)
def circuit_current(self):
    for recv_data,id in data_generator(2):
        try:
            data = recv_data['data']
        except KeyError:
            #self.retry(countdown=3.0)
            continue 
        for i in range(len(data)):
            data_args = {
                k: data[i].get(v) for k,v in column_mappings.items()
            }
            c20 = S3FC20.query.filter_by(addr=data[i]['addr'], box_id=id).first()
            circuit_record = S3FC20Records(s3_fc20_id=c20.id, **data_args)
            db.session.add(circuit_record)
            db.session.flush()
            c20.latest_record_id = circuit_record.id
            db.session.commit()


@celery.task(bind=True)
# todo need testing
def circuit_alarm(self, minute_range=-5.5):
    global all_body
    query_dict = {
        'method': 'GET_BOX_ALARM',
        'projectCode': 'P00000000001',
        'mac': '',
    }
    end = datetime.now()
    start = end + timedelta(minutes=minute_range)
    query_dict['end'] = end.strftime('%Y-%m-%d %H:%M')
    query_dict['start'] = start.strftime('%Y-%m-%d %H:%M')
    alarms = []

    for recv_data, num in data_generator_1(query_dict):
        try:
            data = recv_data['data']
        except KeyError:
            #self.retry(countdown=3.0)
            continue 
        for i in range(len(data)):
            alarm_record = BoxAlarms(
                id=data[i]['auto_id'],
                box_id=num,
                addr=data[i]['addr'],
                node=data[i]['node'],
                alarm_or_type=data[i]['type'],
                info=data[i]['info'],
                time=data[i]['time'],
                type_number=data[i]['typeNumber']
            )
            alarms.append(alarm_record)
        db.session.bulk_save_objects(alarms)
            # may not need to store latest alarm in MantunciBox model
            # db.session.flush()
            # box = MantunciBox.query.filter_by(id=num).first()
            # box.latest_alarm_id = alarm_record.id
            # db.session.commit()


@celery.task(bind=True)
# todo need testing
def control_airfan(self, cmd):
    # 大楼的新风系统，目前暂定由某个曼顿的盒子控制
    # cmd='open' 为开； cmd='close' 为关
    post_dict = {
        'method': 'PUT_BOX_CONTROL',
        'projectCode': 'P00000000001',
        'mac': '',
        'cmd': 'OCSWITCH',
        'value1': cmd,
        'value2': ''
    }
    try:
        resp = data_requests(post_dict)
        return
    except Exception as e:
        L.error(e)


class RedisReporterBase():
    def __init__(self, redis_client, rd_key_prefix: str, targets: list,
                 rd_key_tail=None):
        self.rd = redis_client
        self.prefix = rd_key_prefix
        self.targets = targets
        if rd_key_tail:
            self.tail = rd_key_tail


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
        rt_power = content.get('gW')
        updated_time = content.get('updateTime')
        updated_time = datetime.strptime(updated_time, '%Y-%m-%d %H:%M:%S')
        return rt_power, room, measure_type, int(updated_time.timestamp())

    def get_rd_key(self, room, measure):
        return self.prefix + str(room) + str(measure)

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
                print(rt_power, room, measure_type, update_time)
                key = self.get_rd_key(room, measure_type)
                self.set_value(key, (rt_power, update_time))
