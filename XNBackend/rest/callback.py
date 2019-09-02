from flask_restful import Resource
from flask import request


class AcsCallback(Resource):
    def post(self):
        # TODO have not finished
        json_body = request.get_json()
        event = json_body['params']["events"]
        event_type = event['eventType']
        data = event['data']
        return {"hello": "world"}
