import requests
from celery import group
from hikvision_auth.auth import HIKVisionAuth
from XNBackend.task import celery
from XNBackend.models.models import db, Users, TrackingDevices, AppearRecords, HeatMapSnapshots


hostname = ''
port = ''
s = None


def req_session():
    global s
    if s is None:
        s = requests.Session()
        s.auth = HIKVisionAuth('app_key', 'app_secret', 'signature_headers')
    return s


def data_requests(url, body):
    s = req_session()
    r = s.post('https://{hostname}:{port}/artemis{url}'.format(hostname=hostname, port=port, url=url), data=body)    
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
    body = {'pageNo':num, 'pageSize':size}
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


@celery.task()
def device_store(num, size):
    devices = []
    url = '/api/resource/v1/cameras'
    body = {'pageNo':num, 'pageSize':size}
    data = data_requests(url, body)['list']
    for i in range(len(data)):
        device = TrackingDevices(device_index_code=data[i]['cameraIndexCode'], name=data[i]['cameraName'], device_type=0)
        devices.append(device)
    db.session.bulk_save_objects(devices)
    db.session.commit()    
    return len(data)


def user_store_group(size, n):
    count = 0
    while true:
        res = group(user_store.s(i+1+count*n, size) for i in range(n)).apply_async()
        if res.get()[n-1] == 0:
            return ''
        count += 1
