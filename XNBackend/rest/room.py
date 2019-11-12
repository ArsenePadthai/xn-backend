from flask_restful import Resource, reqparse
from XNBackend.models import IRSensors, TrackingDevices, Relay, S3FC20, Switches, AirConditioner


room_parser = reqparse.RequestParser()
room_parser.add_argument('room', required=True, type=int, help='require room number')


class Room(Resource):
    def get(self):
        room_number = room_parser.parse_args().get('room')
        errMsg = []
        SWITCH_FAN = 3
        SWITCH_AUTO = 4
        S3FC20_LIGHT = 0
        S3FC20_AC = 1
        S3FC20_SOCKET=2
        ir_sensor = IRSensors.query.filter(IRSensors.locator_body.has(zone=room_number))
        tracking_device = TrackingDevices.query.filter(TrackingDevices.locator_body.has(zone=room_number))

        ac_info = []
        air_conditions = AirConditioner.query.filter(AirConditioner.locator_id == room_number).all()
        if not air_conditions:
            errMsg.append(f'{room_number} has no air condition')
        else:
            for a in air_conditions:
                ac_info.append({"device_index_code": a.device_index_code,
                                "ac_on": True if a.ac_on else False,
                                "temperature": a.temperature,
                                "if_online": a.if_online,
                                "set_mode": a.desired_mode,
                                "set_speed": a.desired_speed})

        ir_value = False
        for i in ir_sensor.all():
            if i.latest_record and i.latest_record.value:
                ir_value = True

        acs_lock_value = True

        room_switch = Switches.query.filter(Switches.switch_panel.has(locator_id=str(room_number)))
        main_switch = room_switch.filter(Switches.channel == 1).first()
        aux_switch = room_switch.filter(Switches.channel == 4).first()
        main_light_value = main_switch.status if main_switch else 0
        aux_light_value = aux_switch.status if aux_switch else 0
        return {
            "ac": ac_info,
            "main_light": main_light_value,
            "aux_light": aux_light_value,
            "acs_lock": acs_lock_value,
            "ir_sensor": ir_value,
            "errMsg": 'ok' if not errMsg else ','.join(errMsg)
        }
