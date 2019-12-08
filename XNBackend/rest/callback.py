import logging
from flask_restful import Resource
from flask import request
from XNBackend.task.hik.acs import * 
import pprint

L = logging.getLogger()



class AcsCallback(Resource):
    def post(self):
        json_body = request.get_json()
        print('============================')
        print(json_body)
        L.error(json_body)
        return {}
        # event = json_body['params']["events"][0]
        # event_type = event['eventType']

        # if event_type == '196893':
        #     face_recognition.delay(event['data']['ExtEventCardNo'], event['srcName'], event['eventId'])
        # elif event_type == '198919':
        #     door_control.delay(event['srcName'], event['eventId'])
        # elif event_type == '198657':
        #     door_destory.delay(event['srcName'], event['eventId'])
