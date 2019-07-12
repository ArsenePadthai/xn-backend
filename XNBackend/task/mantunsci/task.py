import json
import requests
import time
from mantunsci_auth.auth import MantunsciAuthBase
from XNBackend.task import celery
from XNBackend.models.models import db, EnergyConsumeDaily, EnergyConsumeMonthly, CircuitRecords, CircuitBreakers


param = {
    'auth_url':'',
    'username':'',
    'password':'',
    'app_key':'',
    'app_secret':'',
    'project_code':'',
    'redirect_uri':''
}
s = None

def req_session():
    global s
    if s is None:
        s = requests.Session()
        s.auth = MantunsciAuthInMemory(param['auth_url'], param['username'], param['password'], param['app_key'], param['app_secret'], param['project_code'], param['redirect_uri'])
    return s


def data_requests(body):
    s = req_session()
    r = s.post(param['auth_url'], data=body)    
    message = r.json
    return message['data']

    
'''
def all_box():
    record = []
    body = {'method':'GET_BOXES', 'projectCode':''}
    data = data_requests(body)
    for i in range(len(data)):
        box = CircuitBreakers(mac=data[i]['mac'], name=data[i]['name'], phone=data[i]['phone'])
        record.append(box)
    db.session.bulk_save_objects(record)
    db.session.commit()
'''    


@celery.task()
def power_month():
    record = []
    localtime = time.localtime(time.time())
    body = {'method':'GET_BOX_MON_POWER', 'projectCode':'', 'mac':'', 'year':localtime[0]}
    data = data_requests(body)
    for i in range(len(data)):
        monthly_record = EnergyConsumeMonthly(addr=data[i]['addr'], electricity=data[i]['electricity'])
        record.append(monthly_record)
    db.session.bulk_save_objects(record)
    db.session.commit()


@celery.task()
def power_day():
    record = []
    localtime = time.localtime(time.time())
    body = {'method':'GET_BOX_DAY_POWER', 'projectCode':'', 'mac':'', 'year':localtime[0], 'month':localtime[1]}
    data = data_requests(body)
    for i in range(len(data)):
        daily_record = EnergyConsumeDaily(addr=data[i]['addr'], electricity=data[i]['electricity'])
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
@celery.task()
def circuit_current():
    localtime = time.localtime(time.time())
    body = {'method':'GET_BOX_CHANNELS_REALTIME', 'projectCode':'', 'mac':''}
    data = data_requests(body)
    for i in range(len(data)):
        data_args = {
            k: data[i].get(v) for k,v in column_mappings.items()
        }
        circuit_record = CircuitRecords(**data_args)
        record.append(circuit_record)
    db.session.bulk_save_objects(record)
    db.session.commit()






