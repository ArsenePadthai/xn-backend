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


def data_requests(body):
    r = request.post(auth_url, auth=MantunsciAuthBase(param['auth_url'], param['username'], param['password'], param['app_key'], param['app_secret'], param['project_code'], param['redirect_uri']), data=body)    
    message = json.load(r.text)
    return message['data']
    

def all_box():
    record = []
    body = json.dumps({'method':'GET_BOXES', 'projectCode':''})
    data = data_requests(body)
    for i in range(len(data)):
        box = CircuitBreakers(mac=data[i]['mac'], name=data[i]['name'], phone=data[i]['phone'])
        record.append(box)
    db.session.bulk_save_objects(record)
    db.session.commit()
    


@celery.task()
def power_month():
    record = []
    localtime = time.localtime(time.time())
    body = json.dumps({'method':'GET_BOX_MON_POWER', 'projectCode':'', 'mac':'', 'year':localtime[0]})
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
    body = json.dumps({'method':'GET_BOX_DAY_POWER', 'projectCode':'', 'mac':'', 'year':localtime[0], 'month':localtime[1]})
    data = data_requests(body)
    for i in range(len(data)):
        daily_record = EnergyConsumeDaily(addr=data[i]['addr'], electricity=data[i]['electricity'])
        record.append(daily_record)
    db.session.bulk_save_objects(record)
    db.session.commit()


@celery.task()
def circuit_current():
    localtime = time.localtime(time.time())
    body = json.dumps({'method':'GET_BOX_CHANNELS_REALTIME', 'projectCode':'', 'mac':'')
    data = data_requests(body)
    for i in range(len(data)):
        circuit_record = CircuitRecords(circuit_mac=data[i]['cricuit_mac'], validity=data[i]['validity'], 
                                        enable_netctr=data[i]['enableNetCtr'], oc=data[i]['oc'], 
                                        online=data[i]['online'], total_power=data[i]['power'], 
                                        mxgg=data[i]['mxgg'], mxgl=data[i]['mxgl'], 
                                        line_type=data[i]['lineType'], spec=data[i]['specification'], 
                                        control=data[i]['control'], visibility=data[i]['visibility'], 
                                        alarm=data[i]['alarm'], gLd=data[i]['gLd'], gA=data[i]['gA'], 
                                        gT=data[i]['gT'], gV=data[i]['gV'], gW=data[i]['gW'], 
                                        gPF=data[i]['gPF'], aA=data[i]['aA'], aT=data[i]['aT'], 
                                        aV=data[i]['aV'], aW=data[i]['aW'], aPF=data[i]['aPF'], 
                                        bA=data[i]['bA'], bT=data[i]['bT'], bV=data[i]['bV'], 
                                        bW=data[i]['bW'], bPF=data[i]['bPF'], cA=data[i]['cA'], 
                                        cT=data[i]['cT'], cV=data[i]['cV'], cW=data[i]['cW'], 
                                        cPF=data[i]['cPF'], nA=data[i]['nA'], nT=data[i]['nT'])
        record.append(circuit_record)
    db.session.bulk_save_objects(record)
    db.session.commit()






