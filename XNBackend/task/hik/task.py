import json
import time
import requests
from celery import group
from hikvision_auth.auth import HIKVisionAuth
from XNBackend.task import celery
from XNBackend.models.models import db, Users, TrackingDevices, AppearRecords, HeatMapSnapshots


hostname = ''
port = ''
app_key = ''
app_secret = ''
signature_headers = ''
s = None


def req_session():
    global s
    if s is None:
        s = requests.Session()
        s.auth = HIKVisionAuth(app_key, app_secret, signature_headers)
    return s


def data_requests(url, body):
    s = req_session()
    r = s.post('https://{hostname}:{port}/artemis{url}'.format(hostname=hostname, port=port, url=url), json=body)    
    message = r.json
    return message['data']


column_mappings = {
    'person_id': 'personId',
    'person_name': 'personName',
    'job_no': 'jobNo',
    'gender': 'gender',
    'org_path': 'orgPath',
    'org_index_code': 'orgIndexCode',
    'org_name': 'orgName',
    'certificate_type': 'certificateType',
    'certificate_no': 'certificateNo',
    'phone_no': 'phoneNo',
    'address': 'address',
    'email': 'email',
    'education': 'education',
    'nation': 'nation',
}

@celery.task()
def user_store(num, size):
    users = []
    url = '/api/resource/v1/person/personList'
    body = json.dumps({'pageNo':num, 'pageSize':size})
    data = data_requests(url, body)['list']
    for i in range(len(data)):
        data_args = {
            k: data[i].get(v) for k,v in column_mappings.items()
        }
        user = Users(**data_args, photo_url=data[i]['personPhoto']['picUri'])
        users.append(user)
    db.session.bulk_save_objects(users)
    db.session.commit()    
    return len(data)


def user_store_group(size, n):
    count = 0
    while True:
        res = group(user_store.s(i+1+count*n, size) for i in range(n)).apply_async()
        if res.get()[n-1] == 0:
            return ''
        count += 1


device_column_mappings = [
    {
        'device_index_code': 'cameraIndexCode',
        'name': 'cameraName'
    },
    {
        'device_index_code': 'acsDevIndexCode',
        'name': 'acsDevName'
    }
]

@celery.task()
def device_store(num, size, is_acs: int):
    devices = []
    url_camera = '/api/resource/v1/cameras'
    url_acs = '/api/resource/v1/acsDevice/acsDeviceList'
    body = json.dumps({'pageNo':num, 'pageSize':size})
    data = data_requests(url=url_acs if is_acs else url_camera, body)['list']
    for i in range(len(data)):
        data_args = {
            k: data[i].get(v) for k,v in device_column_mappings[is_acs].items()
        }
        device = TrackingDevices(**data_args, device_type=is_acs)
        devices.append(device)
    db.session.bulk_save_objects(devices)
    db.session.commit()    
    return len(data)


def device_store_group(size, n):
    count = 0
    is_acs = 0
    while True:
        res = group(device_store.s(i+1+count*n, size, is_acs) for i in range(n)).apply_async()
        count += 1
        if res.get()[n-1] == 0:
            if is_acs == 1:
                break
            count = 0
            is_acs = 1


@celery.task()
def people_count():
    snapshots = []
    length = TrackingDevices.query.count()
    t = time.strftime('%Y-%m-%d ', time.localtime())
    for i in range(1, length+1):
        num = AppearRecords.query.filter(and_(AppearRecords.device_id == i, AppearRecords.created_at >= t)).count()
        try:
            snapshot = HeatMapSnapshots.query.filter_by(device_id = i).first()
            snapshot.count = num
        except:
            snapshot = HeatMapSnapshots(device_id=i, count=num)
        snapshots.append(snapshot)
    db.session.bulk_save_objects(snapshots)
    db.session.commit()    
