from flask_restful import Resource
from flask import request
from XNBackend.task.other import save_acs_event


class AcsCallback(Resource):
    def post(self):
        # TODO have not finished
        json_body = request.get_json()
        event = json_body['params']["events"]
        event_type = event['eventType']
        event_id = event['eventId']
        data = event['data']
        device_id = data['ExtEventMainDevID']
        id_card_no = data['ExtEventCardNo']
        time = event['happenTime']

        save_acs_event.delay(device_id,
                             event_type,
                             event_id,
                             id_card_no,
                             time)
        return {"msg": "ok"}
