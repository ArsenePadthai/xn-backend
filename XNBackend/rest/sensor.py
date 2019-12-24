import time
import json
from flask_restful import Resource, reqparse, fields, marshal_with
from datetime import datetime, timedelta
from flask import current_app
from XNBackend.models import IRSensors, AppearRecords, Elevators, \
    Relay, Switches, SwitchPanel
from .utils import MyDateTime


floor_parser = reqparse.RequestParser()
floor_parser.add_argument('floor', required=True, type=int, help='require floor number')

query_appear_parser = reqparse.RequestParser()
query_appear_parser.add_argument('start',
                                 required=True,
                                 type=lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%S'))
query_appear_parser.add_argument('end',
                                 required=True,
                                 type=lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%S'))
query_appear_parser.add_argument('name',
                                 required=False,
                                 type=str)
query_appear_parser.add_argument('certificateNo',
                                 required=False,
                                 type=str)

appear_fields = {
    'id': fields.Integer,
    'faceId': fields.Integer,
    'name': fields.String,
    'sex': fields.String,
    'certificateType': fields.String,
    'certificateNum': fields.String,
    'facePicture': fields.String,
    'cameraIndexCode': fields.String,
    'deviceName': fields.String,
    'eventType': fields.String,
    'happenTime': MyDateTime(attribute='happenTime')
}


def if_time_expired(the_time, check_range=1200):
    now = int(time.time())
    return the_time > now - check_range


def check_occupied(ir_sensor_list):
    if not ir_sensor_list:
        return None
    if None in ir_sensor_list:
        return -1
    if 1 in ir_sensor_list:
        return 1
    return 0


def check_ir(floor):
    occupied = 0
    error = 0
    floor_map = current_app.config['FLOOR_ROOM_MAPPING']
    detail = {}
    room_range = floor_map[floor]
    import redis
    R = redis.Redis(host=current_app.config['REDIS_HOST'],
                    port=current_app.config['REDIS_PORT'])
    for room in room_range:
        value = R.get('IR_'+str(room))
        # exclude power room, networking room, restrooms
        if not value and room not in ['304',
                                      '313',
                                      '315',
                                      '317',
                                      '404',
                                      '418',
                                      '420',
                                      '422',
                                      '504',
                                      '511',
                                      '513',
                                      '515',
                                      '604',
                                      '618',
                                      '620',
                                      '622',
                                      '721']:
            detail[room] = -1
            error += 1
        else:
            value = json.loads(value)
            if 1 in value[0]:
                detail[room] = 1
                occupied += 1
            else:
                detail[room] = 0

    return len(detail), error, occupied, detail


def return_room_status(floor, status):
    room_status = dict()
    for index, stat in enumerate(status):
        room_status['%d%s' % (floor, str(index + 1).zfill(2))] = stat
    return room_status


class FireDetector(Resource):
    def get(self):
        floor = floor_parser.parse_args().get('floor')
        fire_sensor_count = 80
        fire_sensor_alarm = 0
        ROOM_COUNT = 24
        fire_status = [0] * ROOM_COUNT
        return {
            "total": fire_sensor_count,
            "alarm": fire_sensor_alarm,
            "detail": return_room_status(floor, fire_status)
        }


class IRSensor(Resource):
    def get(self):
        floor = floor_parser.parse_args().get('floor')
        floor_map = current_app.config['FLOOR_ROOM_MAPPING']
        if int(floor) not in floor_map:
            return {'code': -1, "errorMsg": "floor out of range"}
        total, error, occupied, detail = check_ir(floor)

        return {
            "total": total,
            "empty": total - error - occupied,
            "occupied": occupied,
            "error": error,
            "detail": detail
        }


class Elevator(Resource):
    def get(self):
        elevator1, elevator2 = Elevators.query.all()
        NO_DATA = -1

        if not elevator1.latest_record:
            e1_floor = NO_DATA
            e1_direction = NO_DATA
        else:
            e1_floor = elevator1.latest_record.floor
            e1_direction = elevator1.latest_record.direction

        if not elevator2.latest_record:
            e2_floor = NO_DATA
            e2_direction = NO_DATA
        else:
            e2_floor = elevator2.latest_record.floor
            e2_direction = elevator2.latest_record.direction

        return {
            "total": 2,
            "elevator1": {
                "floor": e1_floor,
                "direction": e1_direction,
            },
            "elevator2": {
                "floor": e2_floor,
                "direction": e2_direction,
            }
        }


class Light(Resource):
    def get(self):
        floor = floor_parser.parse_args().get('floor')
        floor_map = current_app.config['FLOOR_ROOM_MAPPING']

        status_dict = dict()
        main_count = 0
        main_count_on = 0
        aux_count = 0
        aux_count_on = 0

        for room in floor_map[floor]:
            panel = SwitchPanel.query.filter(SwitchPanel.locator_id == str(room)).first()
            if not panel:
                continue

            main_count += 1
            status_dict[str(room)] = [-1]
            switch = Switches.query.filter(Switches.switch_panel_id == panel.id)
            main_light = switch.filter(Switches.channel == 1).first()
            if main_light and getattr(main_light, 'status', None) in [0, 1]:
                status_dict[str(room)][0] = main_light.status
                if main_light.status:
                    main_count_on += 1

            aux_channel_no = 2 if panel.panel_type == 1 else 4
            aux_switch = switch.filter(Switches.channel == aux_channel_no).first()
            # 513/515 is restroom
            if aux_switch and panel.locator_id != "513" and panel.locator_id != "515":
                rel = Relay.query.filter(Relay.switch_id == aux_switch.id).first()
                if rel and getattr(aux_switch, 'status', None) in [0, 1]:
                    status_dict[str(room)].append(aux_switch.status)
                    aux_count += 1
                    if aux_switch.status:
                        aux_count_on += 1

        return {
            "total": main_count + aux_count,
            "on": main_count_on + aux_count_on,
            "detail": status_dict
        }


class FaceRecognition(Resource):
    @marshal_with(appear_fields)
    def get(self):
        args = query_appear_parser.parse_args()
        start = args.get('start')
        end = args.get('end')
        name = args.get('name')
        certificateNo = args.get('certificateNo')
        appear_records = AppearRecords.query.filter(AppearRecords.happenTime > start
                                                    ).filter(AppearRecords.happenTime < end)
        if name:
            appear_records = appear_records.filter(AppearRecords.name == name)
        if certificateNo:
            appear_records = appear_records.filter(AppearRecords.certificateNum == certificateNo)
        appear_records = appear_records.order_by(AppearRecords.happenTime.desc())
        return appear_records.all()
