from flask_restful import Resource, reqparse
from flask import current_app
from XNBackend.models import AirConditioner
from XNBackend.tasks.air_condition.tasks import send_cmd_to_air_condition, update_specific_air_condition

ac_patch_parser = reqparse.RequestParser()
ac_patch_parser.add_argument('device_index_code', required=True, type=str, 
                             help='require device_index_code')
ac_patch_parser.add_argument('ac_on', required=False, type=bool)
ac_patch_parser.add_argument('set_mode', required=False, type=int)
ac_patch_parser.add_argument('temperature', required=False, type=int)
ac_patch_parser.add_argument('set_speed', required=False, type=int)

floor_parser = reqparse.RequestParser()
floor_parser.add_argument('floor', required=True, type=int, help='require floor number')


def return_room_status(floor, status):
    room_status = dict()
    for index, stat in enumerate(status):
        room_status['%d%s' % (floor, str(index + 1).zfill(2))] = stat
    return room_status


class AirConditionControl(Resource):
    def patch(self):
        args = ac_patch_parser.parse_args()
        device_index_code = args.get('device_index_code')
        run = args.get('ac_on')
        mode = args.get('set_mode')
        temperature = args.get('temperature')
        fan_speed = args.get('set_speed')
        kwarg_control = {}

        if run is not None:
            kwarg_control['StartStopStatus'] = 1 if run else 0
        if mode:
            kwarg_control['ModeCmd'] = mode
        if temperature:
            kwarg_control['TempSet'] = temperature
        if fan_speed:
            kwarg_control['FanSpeedSet'] = fan_speed

        if not kwarg_control:
            return {"errMsg": f'no parameter is found for set air condition'}

        send_cmd_to_air_condition.apply_async(args=[device_index_code],
                                              kwargs=kwarg_control,
                                              queue="general")
        update_specific_air_condition.apply_async(args=[device_index_code],
                                                  queue='general',
                                                  countdown=10)
        return {'errMsg': 'ok'}


class AirCondition(Resource):
    def get(self):
        floor = floor_parser.parse_args().get('floor')
        ac_query = AirConditioner.query.filter(AirConditioner.locator.has(floor=floor))
        total = ac_query.count()
        on_count = ac_query.filter(AirConditioner.ac_on == 1).count()
        floor_map = current_app.config['FLOOR_ROOM_MAPPING']
        if int(floor) not in floor_map:
            return {'code': -1, "errorMsg": "floor out of range"}

        room_range = floor_map[int(floor)]
        status_dict = dict()

        for room in room_range:
            room_air_conditions = AirConditioner.query\
                .filter(AirConditioner.locator.has(zone=int(room))).all()
            if room_air_conditions:
                status_dict[str(room)] = dict()
            for room_ac in room_air_conditions:
                if room_ac.ac_on is None:
                    status = -1
                else:
                    status = room_ac.ac_on
                status_dict[str(room)].update({room_ac.device_index_code: status})
                
        return {
            "total": total,
            "run": on_count,
            "detail": status_dict
        }
