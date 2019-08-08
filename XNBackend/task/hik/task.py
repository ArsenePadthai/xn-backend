import json
import time
import requests
from celery import group
from hikvision_auth.auth import HIKVisionAuth
from XNBackend.task import celery
from XNBackend.models.models import db, Users, TrackingDevices, AcsRecords, AppearRecords, HeatMapSnapshots


hostname = ''
port = ''
app_key = ''
app_secret = ''
s = None


def req_session():
    global s
    if s is None:
        s = requests.Session()
        s.auth = HIKVisionAuth(app_key, app_secret)
    return s


def data_requests(url, body):
    s = req_session()
    date = time.strftime('%a %b %d %H:%M:%S %Z %Y', time.localtime())
    r = s.post('https://{hostname}:{port}/artemis{url}'.format(hostname=hostname, port=port, url=url), json=body, headers={'Date':date})    
    message = r.json
    return message 


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

@celery.task(bind=True)
def user_store(self, num, size):
    users = []
    url = '/api/resource/v1/person/personList'
    body = json.dumps({'pageNo':num, 'pageSize':size})
    try:
        data = data_requests(url, body)['data']['list']
    except Exception:
        self.retry(countdown=3.0)
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
        if res.get()[-1] == 0:
            return ''
        count += 1


device_column_mappings = [
    {
        'device_index_code': 'cameraIndexCode',
        'name': 'cameraName'
    },
    {
        'device_index_code': 'doorIndexCode',
        'name': 'acsDevName'
    }
]

@celery.task(bind=True)
def device_store(self, num, size, is_acs: int):
    devices = []
    url_camera = '/api/resource/v1/cameras'
    url_acs = '/api/resource/v1/acsDoor/advance/acsDoorList'
    body = json.dumps({'pageNo':num, 'pageSize':size})
    try:
        data = data_requests(url=url_acs if is_acs else url_camera, body)['data']['list']
    except Exception:
        self.retry(countdown=3.0)

    for i in range(len(data)):
        data_args = {
            k: data[i].get(v) for k,v in device_column_mappings[is_acs].items()
        }
        device = TrackingDevices.query.filter_by(device_index_code = data_args['device_index_code']).first()

        if device != None and device.device_type == is_acs:
            device.name = data_args['name']
        else:
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
        if res.get()[-1] == 0:
            if is_acs == 1:
                break
            count = 0
            is_acs = 1


@celery.task()
def people_count():
    snapshots = []
    for device in TrackingDevices.query.order_by():
        if device.device_type == 1:
            continue 
        num = AppearRecords.query.filter_by(device_id == device.id).count()
        try:
            snapshot = HeatMapSnapshots.query.filter_by(device_id = device.id).first()
            snapshot.count = num
        except:
            snapshot = HeatMapSnapshots(device_id=device.id, count=num)
        snapshots.append(snapshot)
    db.session.bulk_save_objects(snapshots)
    db.session.commit()    


@celery.task(bind=True)
def acs_record(self, num, size, start, end):
    url = '/api/acs/v1/door/events'
    body = json.dumps({'startTime':start, 'endTime':end, 'pageNo':num, 'pageSize':size})
    try:
        data = data_requests(url, body)['data']['list']
    except KeyError:
        self.retry(countdown=3.0)

    for i in range(len(data)):
        device = TrackingDevices.query.filter_by(device_index_code=data[i]['doorIndexCode']).first()
        record = AcsRecords(acs_id=device.id, event_type=data[i]['eventType'])
        db.session.add(record)
        db.session.flush()
        device.latest_acs_record_id = record.id
    db.session.commit()    
    return len(data)


def acs_store_group(start, end, size, n):
    count = 0
    while True:
        res = group(acs_record.s(i+1+count*n, size, start, end) for i in range(n)).apply_async()
        count += 1
        if res.get()[-1] == 0:
            break


@celry.task()
def acs_control(doorIndex: list, controlType):
    result = []
    url = '/api/acs/v1/door/doControl'
    body = json.dumps({'doorIndexCodes':doorIndex, 'controlType':controlType})
    data = data_requests(url, body)['data']

    for i in range(len(data)):
        result.append({data[i]['doorIndexCode']:data[i]['controlResultCode']})
        if data[i]['controlResultCode'] == 0:
            device = TrackingDevices.query.filter_by(device_index_code=data[i]['doorIndexCode']).first()
            try:
                device.acs_record.status = controlType
            except Exception:
                record = AcsRecords(acs_id=device_id, status=controlType)
                db.session.add(record)
                db.sesson.flush()
                device.latest_acs_record_id = record.id 
    db.session.commit()    

    return result


