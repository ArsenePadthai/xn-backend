# -*- coding: utf-8 -*-
import logging
import json
from datetime import datetime
from flask_restful import Resource
from flask import request
from XNBackend.models import db, AppearRecords, UniAlarms

L = logging.getLogger()

# 重点人员识别事件ID
IMP_REG_ID = 1644175361
STR_REG_ID = 1644171265
BREAK_CARD = 200453
BREAK_DEVICE = 199708
FORCE_OPEN_DOOR = 198657

# 告警分级， 告警分为3级， 1级告警为严重， 2级告警为一般告警， 3级告警为轻微


class AcsCallback(Resource):
    def post(self):
        json_body = request.get_json()
        ability = json_body['params']['ability']
        if ability == 'event_face_recognition':
            events = json_body['params']['events']
            for e in events:
                resInfo = e['data']['resInfo'][0]
                snap = e['data']['faceRecognitionResult']['snap']
                deviceName = resInfo['cn']
                cameraIndexCode = resInfo['indexCode']
                facePicture = snap['faceUrl']
                happenTime = datetime.strptime(e['happenTime'][:19], '%Y-%m-%dT%H:%M:%S')
                if e['eventType'] == 1644171265:
                    L.info("callback event: stranger identified!!")
                    extra = {"device_index_code": e["srcIndex"],
                             "link": e["data"]["faceRecognitionResult"]["snap"]["faceUrl"]}
                    extra = json.dumps(extra)
                    ua = UniAlarms(
                        external_id=e['eventId'],
                        happen_time=happenTime,
                        alarm_group=1,
                        alarm_code=1644171265,
                        alarm_content='陌生人告警',
                        extra=extra,
                        active=1,
                        level=2
                    )
                    ap_record = AppearRecords(
                        facePicture=facePicture,
                        certificateNum='stranger',
                        cameraIndexCode=cameraIndexCode,
                        deviceName=deviceName,
                        eventType=e['eventType'],
                        happenTime=happenTime,
                        type=1,
                        active=1
                    )
                    db.session.add(ua)
                    db.session.add(ap_record)
                    db.session.commit()

                elif e['eventType'] == 1644175361:
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
                            happenTime=happenTime,
                            type=0,
                            active=0
                        )
                        db.session.add(ap_record)
                    db.session.commit()
        elif ability == 'event_acs':
            events = json_body['params']['events']
            for e in events:
                if e['srcIndex'] == '96ee43fccdf8442f995030b4f60ebdf1':
                    return {"ret": "ok"}
                event_type = e['eventType']
                happenTime = datetime.strptime(e['happenTime'][:19], '%Y-%m-%dT%H:%M:%S')
                if event_type not in (FORCE_OPEN_DOOR, BREAK_DEVICE, BREAK_CARD):
                    return {"code": -1, "message": "event not in scope"}
                if event_type == FORCE_OPEN_DOOR:
                    alarm_content = '门被外力开启'
                if event_type == BREAK_CARD:
                    alarm_content = '读卡器被拆!'
                if event_type == BREAK_DEVICE:
                    alarm_content = "门禁设备被拆!"

                extra = json.dumps({
                    "device_index_code": e['srcIndex']
                })
                ua = UniAlarms(
                    external_id=e['eventId'],
                    happen_time=happenTime,
                    alarm_group=1,
                    alarm_code=event_type,
                    alarm_content=alarm_content,
                    extra=extra,
                    active=1,
                    level=1
                )
                db.session.add(ua)
                db.session.commit()
        return {"ret": 'ok'}
