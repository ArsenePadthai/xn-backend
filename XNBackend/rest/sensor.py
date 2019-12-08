from flask_restful import Resource, reqparse, fields, marshal_with
from datetime import datetime
from XNBackend.models import IRSensors, TrackingDevices, AppearRecords, \
    LuxSensors, FireAlarmSensors, Elevators, Relay, AirConditioner, Switches, SwitchPanel


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


class MyDateTime(fields.Raw):
    def format(self, value):
        return value.strftime("%Y-%m-%d %H:%M:%S")


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


def check_ir(floor):
    floor_map = {
        3: range(301, 325),
        4: range(401, 428),
        5: range(501, 523),
        6: range(601, 630),
        7: range(701, 730),
        9: range(901, 905),
    }
    sensors = IRSensors.query.filter(IRSensors.locator_body.has(floor=floor)).all()
    room_range = floor_map[floor]
    status_dict = dict()
    for room in room_range:
        status_dict[room] = -1

    occupied = 0
    empty = 0
    error = 0
    for i in sensors:
        if i.status == 1:
            occupied += 1
            status_dict[i.locator_body.zone] = 1
        elif i.status == 0:
            empty += 1
            status_dict[i.locator_body.zone] = 0
        elif i.status is None:
            error += 1
    return occupied, empty, error, status_dict


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
        occupied, empty, error, status = check_ir(floor)

        return {
            "total": occupied + empty,
            "empty": empty,
            "occupied": occupied,
            "detail": status
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
        floor = floor_parser.parse_args().get('floor')
        floor_map = {
            3: range(301, 325),
            4: range(401, 428),
            5: range(501, 523),
            6: range(601, 630),
            7: range(701, 730),
            9: range(901, 905),
        }

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
            if aux_switch:
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
