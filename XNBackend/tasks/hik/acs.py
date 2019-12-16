from XNBackend.tasks import celery
from .tasks import data_requests
from XNBackend.models.models import db, Users, TrackingDevices, AcsRecords, AppearRecords, HeatMapSnapshots, LatestPosition


@celery.task()
def face_recognition(cardNo, acsName, eventId):
    personId = data_requests('/api/irds/v1/card/cardInfo', json={'cardNo':cardNo})['data']['personId']
    user = Users.query.filter_by(person_id=personId).first()
    device = TrackingDevices.query.filter_by(name=acsName, device_type=1).first()
    acs_record = AcsRecords(acs_id=device.id, event_type='196893', event_id=eventId)
    appear_record = AppearRecords(user_id=user.id, device_id=device.id)
    db.session.add(acs_record)
    db.session.add(appear_record)
    db.session.flush()

    position = LatestPosition(user_id=user.id, appear_record_id=appear_record.id)
    device.latest_acs_record_id = acs_record.id
    db.session.add(position)
    db.session.commit()


@celery.task()
def door_control(acsName, eventId):
    device = TrackingDevices.query.filter_by(name=acsName, device_type=1).first()
    acs_record = AcsRecords(acs_id=device.id, event_type='198919', event_id=eventId)
    db.session.add(acs_record)
    db.session.flush()
    device.latest_acs_record_id = acs_record.id
    db.session.commit()
    


@celery.task()
def door_destroy(acsName, eventId):
    device = TrackingDevices.query.filter_by(name=acsName, device_type=1).first()
    acs_record = AcsRecords(acs_id=device.id, event_type='198657', event_id=eventId)
    db.session.add(acs_record)
    db.session.flush()
    device.latest_acs_record_id = acs_record.id
    db.session.commit()
    
