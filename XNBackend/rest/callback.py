import logging
from datetime import datetime
from flask_restful import Resource
from flask import request
from XNBackend.models import AppearRecords, db

L = logging.getLogger()


class AcsCallback(Resource):
    def post(self):
        json_body = request.get_json()
        print(json_body)
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
                            deviceName=deviceName,
                            eventType=e['eventType'],
                            happenTime=happenTime
                        )
                        db.session.add(ap_record)
                        db.session.commit()
        return {"ret": 'ok'}
