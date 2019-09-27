from flask_restful import Resource, reqparse
from XNBackend.task.sensor.task import tasks_route

light_parser = reqparse.RequestParser()
light_parser.add_argument('room_no', required=True, type=str)
light_parser.add_argument('level', required=True, type=int)
light_parser.add_argument('action', required=True, type=int)


class LightControl(Resource):
    def patch(self):
        args = light_parser.parse_args()
        zone = int(args.get('room_no'))
        light_type = args.get('level')
        is_open = args.get('action')
        if light_type == 0:
            channel = 1
        else:
            channel = 4

        tasks_route.delay('LocatorControl', channel, is_open, zone=zone)
        return ('successful update status of light', 200)
