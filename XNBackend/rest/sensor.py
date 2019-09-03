from flask_restful import Resource, reqparse
from XNBackend.models import IRSensors, TrackingDevices, LuxSensors, FireAlarmSensors, Elevators, Relay


floor_parser = reqparse.RequestParser()
floor_parser.add_argument('floor', required=True, type=int, help='require floor number')


def check_ir(floor):
    sensors = IRSensors.query.filter(IRSensors.locator_body.has(floor=floor)).all()
    ROOM_NUMBER = [24, 24, 24, 24, 24, 24, 24, 24]
    status = [False] * ROOM_NUMBER[floor]  # floor - 1
    occupied = 0
    empty = 0
    for i in sensors:
        if i.latest_record and i.latest_record.status:
            occupied += 1
            status[i.locator_body.zone - floor * 100 - 1] = True
        else:
            empty += 1
    return occupied, empty, status


def return_room_status(floor, status):
    room_status = dict()
    for index, stat in enumerate(status):
        room_status['%d%s' % (floor, str(index + 1).zfill(2))] = stat
    return room_status


class AirCondition(Resource):
    def get(self):
        floor = floor_parser.parse_args().get('floor')
        ac_count = 24
        # occupied, empty, status = check_ir(floor)
        ac_status = [True, True, False] * 8

        return {
            "total": ac_count,
            "empty_run": 8,
            "full_running": 16,
            "detail": return_room_status(floor, ac_status)
        }


class FireDetector(Resource):
    def get(self):
        floor = floor_parser.parse_args().get('floor')
        fire_sensor_count = 80
        fire_sensor_alarm = 0
        ROOM_COUNT = 24
        fire_status = [False] * ROOM_COUNT
        return {
            "total": fire_sensor_count,
            "alarm": fire_sensor_alarm,
            "normal": fire_sensor_count - fire_sensor_alarm,
            "detail": return_room_status(floor, fire_status)
        }


class IRSensor(Resource):
    def get(self):
        floor = floor_parser.parse_args().get('floor')
        occupied, empty, status = check_ir(floor)

        return {
            "total": occupied + empty,
            "empty": empty,
            "occupied": occupied,
            "detail": return_room_status(floor, status)
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


class Camera(Resource):
    def get(self):
        TRACKING_CAM = 0
        TRACKING_ACS = 1
        floor = floor_parser.parse_args().get('floor')
        # cam_count = TrackingDevices.query.filter(TrackingDevices.locator_body.has(floor=floor)).filter(TrackingDevices.device_type == TRACKING_CAM)
        cam_count = 100
        ai_cam_count = 40
        details = dict()
        for i in range(24):
            details['%d%s' % (floor, str(i + 1).zfill(2))] = "192.168.%d.%d/trsp" % (floor, i + 1)
        return {
            "total": cam_count,
            "normal": cam_count - ai_cam_count,
            "ai": ai_cam_count,
            "detail": details
        }


class Light(Resource):
    def get(self):
        BOTH_OFF = 0
        AUX_ON = 1
        MAIN_ON = 2
        BOTH_ON = 3
        floor = floor_parser.parse_args().get('floor')
        main_light = Relay.query.filter(Relay.locator.has(floor=floor)).filter(Relay.switch.has(channel=1))
        aux_light = Relay.query.filter(Relay.locator.has(floor=floor)).filter(Relay.switch.has(channel=2))
        on_count = 0

        details = dict()
        for i in main_light.all():
            if i.latest_record and i.latest_record.value:
                on_count += 1
                details.setdefault(str(i.locator.zone), 0)
                details[str(i.locator.zone)] += 1 << 1

        for i in aux_light.all():
            if i.latest_record and i.latest_record.value:
                on_count += 1
                details.setdefault(str(i.locator.zone), 0)
                details[str(i.locator.zone)] += 1

        return {
            "total": main_light.count() + aux_light.count(),
            "online": main_light.count() + aux_light.count(),
            "on": on_count,
            "detail": details
        }


class FaceRecognition(Resource):
    def get(self):
        floor = floor_parser.parse_args().get('floor')
        return [
            {
                "name": "mayun",
                "time": "20190827T120000",
                "device_code": "xxxx"
            },
            {
                "name": "zhangsan",
                "time": "20190827T130000",
                "device_code": "xxxx"
            },
            {
                "name": "lisi",
                "time": "20190828T093000",
                "device_code": "xxxx"
            },
            {
                "name": "wangwu",
                "time": "20190827T120000",
                "device_code": "xxxx"
            },
            {
                "name": "liuliu",
                "time": "20190820T142013",
                "device_code": "xxxx"
            },
            {
                "name": "heqi",
                "time": "20190827T130142",
                "device_code": "xxxx"
            },
            {
                "name": "sunba",
                "time": "20190827T095120",
                "device_code": "xxxx"
            },
            {
                "name": "linjiu",
                "time": "20190827T165607",
                "device_code": "xxxx"
            },
            {
                "name": "chenshi",
                "time": "20190827T141145",
                "device_code": "xxxx"
            },
            {
                "name": "liuqiangdong",
                "time": "20190827T112019",
                "device_code": "xxxx"
            },
        ]
