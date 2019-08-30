from flask_restful import Resource, reqparse
from XNBackend.task.sensor.task import tasks_route

light_parser = reqparse.RequestParser()
light_parser.add_argument('room_no', type=str)
light_parser.add_argument('level', type=int)
light_parser.add_argument('action', type=int)


class LightControl(Resource):
    def patch(self):
        args = light_parser.parse_args()
        zone = int(args.get('room_no'))
        control_type = args.get('level') + 1
        is_open = args.get('action')

        tasks_route.delay('LocatorControl', zone=zone, control_type=control_type, is_open=is_open)

        return ('successful update status of light', 200)
