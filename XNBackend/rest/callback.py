import logging
from datetime import datetime
from flask_restful import Resource
from flask import request
from XNBackend.models import AppearRecords, Door, db

L = logging.getLogger()


class AcsCallback(Resource):
    def post(self):
        json_body = request.get_json()
        if json_body['params']['events'][0]['srcIndex'] == '96ee43fccdf8442f995030b4f60ebdf1':
            return
        ability = json_body['params']['ability']
        if ability == 'event_face_recognition':
            events = json_body['params']['events']
            for e in events:
                if e['eventType'] != 1644175361:
                    L.info({f'not recongnize events'})
                    return
                else:
                    happenTime = datetime.strptime(e['happenTime'][:19], '%Y-%m-%dT%H:%M:%S')
                    resInfo = e['data']['resInfo'][0]
                    deviceName = resInfo['cn']
                    cameraIndexCode = resInfo['indexCode']

                    snap = e['data']['faceRecognitionResult']['snap']
                    facePicture = snap['faceUrl']

                    faces = e['data']['faceRecognitionResult']['faceMatch']
                    for f in faces:
                        name = f['faceInfoName']
                        sex = f['faceInfoSex']
                        certificateNum = f['certificate']

                        ap_record = AppearRecords(
                            name=name,
                            sex=sex,
                            certificateNum=certificateNum,
                            facePicture=facePicture,
                            cameraIndexCode=cameraIndexCode,
                            deviceName=deviceName.lstrip('AI-'),
                            eventType=e['eventType'],
                            happenTime=happenTime
                        )
                        db.session.add(ap_record)
                        db.session.commit()

        elif ability == 'event_acs':
            events = json_body['params']['events']
            for e in events:
                event_type = e['eventType']
                happenTime = datetime.strptime(e['happenTime'][:19], '%Y-%m-%dT%H:%M:%S')
                if event_type == 198913:
                    door_new_status = 1
                elif event_type == 199169:
                    door_new_status = 0
                else:
                    return
                door_index_code = e['srcIndex']
                door = Door.query.filter(Door.door_index_code == door_index_code).first()
                if door:
                    door.status = door_new_status
                    door.updated_at = happenTime
                    db.session.commit()
                else:
                    continue
            return {"ret": 'ok'}
