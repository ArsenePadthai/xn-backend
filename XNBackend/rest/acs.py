from flask_jwt_extended import jwt_required
from flask_restful import Resource, reqparse
from XNBackend.tasks.hik.tasks import acs_control
from XNBackend.models.models import TrackingDevices, Door
from XNBackend.api_client.hikvision import open_door

acs_parser = reqparse.RequestParser()
acs_parser.add_argument('room_no', required=False, type=str)
acs_parser.add_argument('device_index_code', required=False, type=str)

acs_get_parser = reqparse.RequestParser()
acs_get_parser.add_argument('floor',
                            required=True,
                            type=str,
                            help='wrong floor parameter')


class AcsControl(Resource):
    @jwt_required
    def patch(self):
        args = acs_parser.parse_args()
        device_index_code = args.get("device_index_code")
        room_no = args.get("room_no")
        if device_index_code:
            return open_door(args.get("device_index_code"))
        if room_no:
            success = []
            failed = []
            doors = Door.query.filter(Door.room_no_external.like(args.get("room_no"))).all()
            for d in doors:
                ret = open_door(d.door_index_code)
                if ret['code'] == 0:
                    success.append(d.door_index_code)
                else:
                    failed.append(d.door_index_code)
            if failed:
                return {
                    "code": -1,
                    "message": ','.join(failed) + 'failed'
                }
            else:
                return {
                    "code": 0,
                    "message": "ok"
                }
        else:
            return {
                "code": -1,
                "message": "need room_no or device_index_code"
            }


class Acs(Resource):
    def get(self):
        args = acs_get_parser.parse_args()
        floor = args.get('floor')
        doors = Door.query.filter(Door.room_no_internal.like(floor+'%'))
        total_count = doors.count()
        total_open = doors.filter(Door.status == 1)
        total_open_count = total_open.count()
        status_dict = dict()
        for d in doors:
            status_dict[d.room_no_internal] = d.status
        return {
            'total': total_count,
            'open': total_open_count,
            'detail': status_dict
        }
