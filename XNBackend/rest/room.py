from flask_restful import Resource, reqparse
from XNBackend.models import IRSensors, TrackingDevices, Switches, AirConditioner
from XNBackend.api_client.air_conditioner import get_ac_data


room_parser = reqparse.RequestParser()
room_parser.add_argument('room', required=True, type=int, help='require room number')


class Room(Resource):
    def get(self):
        room_number = room_parser.parse_args().get('room')
        errMsg = []
        ir_sensor = IRSensors.query.filter(IRSensors.locator_body.has(zone=room_number))
        tracking_device = TrackingDevices.query.filter(TrackingDevices.locator_body.has(zone=room_number))

        ac_info = []
        air_conditions = AirConditioner.query.filter(AirConditioner.locator_id == room_number).all()
        if not air_conditions:
            errMsg.append(f'{room_number} has no air condition')
        else:
            ac_index_codes = [a.device_index_code for a in air_conditions]
            ret = get_ac_data(ac_index_codes)
            if ret.get('errMsg') == 'ok':
                ac_datas = ret.get('data')
                for each_ac in ac_datas:
                    each_ac_dict = AirConditioner.extract_data(each_ac)
                    ac_info.append(each_ac_dict)

        ir_value = -1
        for i in ir_sensor:
            if i.status == 0:
                ir_value = 0
            elif i.status == 1:
                ir_value = 1

        acs_lock_value = True

        room_switch = Switches.query.filter(Switches.switch_panel.has(locator_id=str(room_number)))
        main_switch = room_switch.filter(Switches.channel == 1).first()
        aux_switch = room_switch.filter(Switches.channel == 4).first()
        main_light_value = main_switch.status if main_switch else -1
        aux_light_value = aux_switch.status if aux_switch else -1
        return {
            "ac": ac_info,
            "main_light": main_light_value,
            "aux_light": aux_light_value,
            "acs_lock": acs_lock_value,
            "ir_sensor": ir_value,
            "errMsg": 'ok' if not errMsg else ','.join(errMsg)
        }
