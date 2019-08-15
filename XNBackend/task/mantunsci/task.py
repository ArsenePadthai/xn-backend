import requests
import time
from mantunsci_auth.auth import MantunsciAuthInMemory
from XNBackend.task import celery, logger
from XNBackend.models.models import db, EnergyConsumeDaily, EnegyConsumeMonthly, CircuitRecords, CircuitBreakers, LatestCircuitRecord, CircuitAlarms, LatestAlarm

L = logger.getChild(__name__)

param = {
    'auth_url':'http://192.168.50.117/ebx-rook/',
    'username':'demo',
    'password':'1QAZxsw2)(',
    'app_key':'O000000063',
    'app_secret':'3EB15ED2C0B6DFDDFAE4CC7BDDB58F0C',
    'redirect_uri':'http://192.168.50.117:8000/callback'
}

localtime = time.localtime(time.time())
all_body = [
    {'method':'GET_BOX_MON_POWER', 'projectCode':'', 'mac':'', 'year':localtime[0]},
    {'method':'GET_BOX_DAY_POWER', 'projectCode':'', 'mac':'', 'year':localtime[0], 'month':localtime[1]},
    {'method':'GET_BOX_CHANNELS_REALTIME', 'projectCode':'', 'mac':''},
    {'method':'GET_BOX_ALARM', 'projectCode':'', 'mac':'', 'start':'', 'end':''}
]

s = None


def req_session():
    global s
    if s is None:
        s = requests.Session()
        s.auth = MantunsciAuthInMemory(param['auth_url'], param['username'], param['password'], param['app_key'], param['app_secret'], param['redirect_uri'])
    return s


def data_requests(body):
    s = req_session()
    r = s.post('http://192.168.50.117/ebx-rook/invoke/router.as', data=body)    
    message = r.json()
    return message


def data_generator(n):
    global all_body
    for circuit in CircuitBreakers.query.order_by():
        all_body[n]['mac'] = circuit.mac
        data = data_requests(all_body[n])
        yield data, circuit.id

    
@celery.task(bind=True)
def all_boxes(self):
    record = []
    body = {'method':'GET_BOXES', 'projectCode':''}
    try:
        recv_data = data_requests(body)['data']
    except Exception:
        self.retry(countdown=3.0)
    for i in range(len(data)):
        box = CircuitBreakers(mac=data[i]['mac'], name=data[i]['name'], phone=data[i]['phone'])
        record.append(box)
    db.session.bulk_save_objects(record)
    db.session.commit()    


@celery.task(bind=True)
def power_month(self):
    record = []
    for recv_data,id in data_generator(0):
        try:
            data = recv_data['data']
        except KeyError:
            self.retry(countdown=3.0)
        for i in range(len(data)):
            monthly_record = EnergyConsumeMonthly(circuit_breaker=id, addr=data[i]['addr'], electricity=data[i]['electricity'])
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
            self.retry(countdown=3.0)
        for i in range(len(data)):
            daily_record = EnergyConsumeDaily(circuit_breaker=id, addr=data[i]['addr'], electricity=data[i]['electricity'])
            record.append(daily_record)
    db.session.bulk_save_objects(record)
    db.session.commit()


column_mappings = {
    'addr': 'addr', 
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
        record = []
        try:
            data = recv_data['data']
        except KeyError:
            self.retry(countdown=3.0)
        for i in range(len(data)):
            data_args = {
                k: data[i].get(v) for k,v in column_mappings.items()
            }
            circuit_record = CircuitRecords(circuit_breaker_id=id, **data_args)
            record.append(circuit_record)
        db.session.bulk_save_objects(record)
        db.session.commit()

        last_record = CircuitRecord.query.order_by(CircuitRecord.id.desc()).first()
        try:
            latest_record = LatestCircuitRecord.query.filter_by(circuit_id=id).first()
            latest_record.circuit_record_id = last_record.id
        except Exception:
            latest_record = LatestCircuitRecord(circuit_id=id, circuit_record_id=last_record.id)
            db.session.add(latest_record)
        db.session.commit()
            
    
@celery.task(bind=True)
def circuit_alarm(self, start_time, end_time):
    global all_body
    all_body[3]['start'] = start_time
    all_body[3]['end'] = end_time
    for recv_data,id in data_generator(3):
        try:
            data = recv_data['data']
        except KeyError:
            self.retry(countdown=3.0)
        for i in range(len(data)):
            alarm_record = CircuitAlarms(id= data[i]['auto_id'], circuit_breaker_id=id, addr=data[i]['addr'], node=data[i]['node'], alarm_or_type=data[i]['type'], info=data[i]['info'], type_number=data[i]['typeNumber'])
            try:
                db.session.add(alarm_record)
                db.session.commit()
            except Exception:
                continue

        last_alarm = CircuitAlarms.query.order_by(CircuitAlarms.id.desc()).first()
        try:
            latest_alarm = LatestAlarm.query.filter_by(circuit_id=id).first()
            latest_alarm.circuit_record_id = last_alarm.id
        except Exception:
            latest_alarm = LatestCircuitRecord(circuit_id=id, circuit_alarm_id=last_alarm.id)
            db.session.add(latest_alarm)
        db.session.commit()
    

@celery.task()
def get_token_test():
    data = {'method':'GET_PROJECTS'}
    message = data_requests(data)
    return message

