from flask_jwt_extended import jwt_required
from flask_restful import Resource, reqparse
from XNBackend.api_client.hikvision import query_entry_room

door_event_arg_parse = reqparse.RequestParser()
door_event_arg_parse.add_argument('deviceIndexCode', type=str, required=True)
door_event_arg_parse.add_argument('startTime', type=str, required=True)
door_event_arg_parse.add_argument('endTime', type=str, required=True)
door_event_arg_parse.add_argument('pageNo', type=int, required=True)
door_event_arg_parse.add_argument('pageSize', type=int, required=True)


class DoorEvent(Resource):
    @jwt_required
    def get(self):
        args = door_event_arg_parse.parse_args()
        resp = query_entry_room(args.get('deviceIndexCode'),
                                args.get('startTime'),
                                args.get('endTime'),
                                args.get('pageNo'),
                                args.get('pageSize'))
        return resp
