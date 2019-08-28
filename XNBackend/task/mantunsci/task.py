import requests
import time
from mantunsci_auth.auth import MantunsciAuthInMemory
from XNBackend.task import celery, logger
from XNBackend.models.models import db, EnergyConsumeDaily, EnegyConsumeMonthly, EnergyConsumeByHour, MantunciBox, S3FC20, S3FC20Records, BoxAlarms

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
        s.auth = MantunsciAuthInMemory(param['auth_url'], param['username'], param['password'], param['app_key'], param['app_secret'], param['redirect_uri'])
    return s


def data_requests(body):
    s = req_session()
    r = s.post('http://192.168.50.117/ebx-rook/invoke/router.as', data=body)    
    message = r.json()
    return message


def data_generator(n):
    global all_body
    for circuit in MantunciBox.query.order_by():
        all_body[n]['mac'] = circuit.mac
        data = data_requests(all_body[n])
        yield data, circuit.id

    
@celery.task(bind=True)
def all_boxes(self):
    record = []
    body = {'method':'GET_BOXES', 'projectCode':'P00000000001'}
    try:
        data = data_requests(body)['data']
    except Exception:
        self.retry(countdown=3.0)
        return ''
    for i in range(len(data)):
        breaker = MantunciBox.query.filter_by(mac=data[i]['mac']).first()
        if breaker is None:
            box = MantunciBox(mac=data[i]['mac'], name=data[i]['name'], phone=data[i]['phone'])
            record.append(box)
        else:
            breaker.name = data[i]['name']
            breaker.phone = data[i]['phone']
    db.session.bulk_save_objects(record)
    db.session.commit()    


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
            db.session.add(c20)
            db.session.commit()

   
@celery.task(bind=True)
def circuit_alarm(self, start_time, end_time):
    global all_body
    all_body[3]['start'] = start_time
    all_body[3]['end'] = end_time
    for recv_data,num in data_generator(3):
        try:
            data = recv_data['data']
        except KeyError:
            #self.retry(countdown=3.0)
            continue 
        for i in range(len(data)):
            alarm_record = BoxAlarms(id= data[i]['auto_id'], box_id=num, addr=data[i]['addr'], node=data[i]['node'], alarm_or_type=data[i]['type'], info=data[i]['info'], type_number=data[i]['typeNumber'])
            db.session.add(alarm_record)
            db.session.flush()
            box = MantunciBox.query.filter_by(id = num).first()
            box.latest_alarm_id = alarm_record.id
            db.session.add(box)
            db.session.commit()



