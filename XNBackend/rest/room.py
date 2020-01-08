import redis
import json
from flask import current_app
from flask_restful import Resource, reqparse
from XNBackend.models import Switches, AirConditioner, Relay, Door, Locators
from XNBackend.rest.utils import ac_info_from_model


room_parser = reqparse.RequestParser()
room_parser.add_argument('room', required=True, type=int, help='require room number')


class Room(Resource):
    def get(self):
        room_number = room_parser.parse_args().get('room')
        errMsg = []
        ac_info = []
        room = Locators.query.filter(Locators.internal_code == str(room_number)).first()

        air_conditions = AirConditioner.query.filter(AirConditioner.locator_id == room_number).all()
        if not air_conditions:
            errMsg.append(f'{room_number} has no air condition')
        else:
            for ac in air_conditions:
                ac_info.append(ac_info_from_model(ac))

        ir_value = -1
        R1 = redis.Redis(host=current_app.config['REDIS_HOST'],
                         port=current_app.config['REDIS_PORT'])
        value = R1.get('IR_' + str(room_number))
        if not value:
            ir_value = -1
        else:
            value = json.loads(value)
            if 1 in value[0]:
                ir_value = 1
            elif 0 in value[0]:
                ir_value = 0
        door = Door.query.filter(Door.room_no_internal.like(str(room_number) + '%')).first()
        if door:
            acs_lock_value = True
        else:
            acs_lock_value = False

        room_switch = Switches.query.filter(Switches.switch_panel.has(locator_id=str(room_number)))
        main_switch = room_switch.filter(Switches.channel == 1).first()

        aux_switch = room_switch.filter(Switches.channel == 4).first()
        aux_light_value = -1
        if aux_switch:
            relay = Relay.query.filter(Relay.switch_id == aux_switch.id).first()
            if relay:
                aux_light_value = aux_switch.status
        main_light_value = main_switch.status if main_switch else -1
        return {
            "ac": ac_info,
            "main_light": main_light_value,
            "aux_light": aux_light_value,
            "acs_lock": acs_lock_value,
            "ir_sensor": ir_value,
            "errMsg": 'ok' if not errMsg else ','.join(errMsg),
            "eco": room.eco_mode
        }
