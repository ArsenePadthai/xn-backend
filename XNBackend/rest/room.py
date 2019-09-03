from flask_restful import Resource, reqparse
from XNBackend.models import IRSensors, TrackingDevices, Relay, S3FC20


room_parser = reqparse.RequestParser()
room_parser.add_argument('room', required=True, type=int, help='require room number')


class Room(Resource):
    def get(self):
        room_number = room_parser.parse_args().get('room')
        SWITCH_MAIN = 1
        SWITCH_AUX = 2
        SWITCH_FAN = 3
        SWITCH_AUTO = 4
        S3FC20_LIGHT = 0
        S3FC20_AC = 1
        S3FC20_SOCKET=2
        ir_sensor = IRSensors.query.filter(IRSensors.locator_body.has(zone=room_number))
        tracking_device = TrackingDevices.query.filter(TrackingDevices.locator_body.has(zone=room_number))
        relay = Relay.query.filter(Relay.locator.has(zone=room_number))

        # ac = S3FC20.query.filter(S3FC20.locator.has(zone=room_number)).filter(S3FC20.measure_type == S3FC20_AC)
        ac_value = False

        ir_value = False
        for i in ir_sensor.all():
            if i.latest_record and i.latest_record.value:
                ir_value = True

        acs_lock_value = True

        main_light_sensor = relay.filter(Relay.switch.has(channel=SWITCH_MAIN)).first()
        main_light_value = main_light_sensor.latest_record.value if (main_light_sensor and main_light_sensor.latest_record) else 0
        aux_light_sensor = relay.filter(Relay.switch.has(channel=SWITCH_AUX)).first()
        aux_light_value = aux_light_sensor.latest_record.value if (aux_light_sensor and aux_light_sensor.latest_record) else 0
        return {
            "ac_on": ac_value,
            "main_light": main_light_value,
            "aux_light": aux_light_value,
            "acs_lock": acs_lock_value,
            "ir_sensor": ir_value
        }
