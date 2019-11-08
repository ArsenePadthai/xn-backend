from flask_restful import Resource, reqparse
from XNBackend.task.sensor.task import tasks_route, send_data_to_panel
from XNBackend.models import SwitchPanel
from utils import query_panel_status

light_parser = reqparse.RequestParser()
light_parser.add_argument('room_no', required=True, type=str)
light_parser.add_argument('level', required=True, type=int)
light_parser.add_argument('action', required=True, type=int)


class LightControl(Resource):
    def patch(self):
        args = light_parser.parse_args()
        room_no = str(args.get('room_no'))
        light_type = args.get('level')
        is_open = args.get('action')
        if light_type == 0:
            channel = 1
        else:
            channel = 4

        sp = SwitchPanel.query.filter(SwitchPanel.locator_id == room_no).first()
        if not sp:
            return (f'no matching panel found for this room {room_no}', 200)

        ret = query_panel_status(sp.tcp_config.ip, sp.batch_no, sp.addr_no)
        s_1 = ret[-5]
        s_2 = ret[-4]
        s_3 = ret[-3]
        s_4 = ret[-2]

        light_action = '01' if is_open else '00'
        if light_type == 0:
            # main light
            data_to_send = bytes.fromhex(f'DA 06 {sp.addr_no} 02 {light_action}') \
                + bytes([s_2, s_3, s_4])
        else:
            # aux light
            if sp.panel_type == 0:
                # four switches
                data_to_send = bytes.fromhex(f'DA 06 {sp.addr_no} 02') \
                    + s_1 + s_2 + s_3 + bytes.fromhex(f'{light_action}')
            else:
                # two switches
                data_to_send = bytes.fromhex(f'DA 06 {sp.addr_no} 02') \
                    + s_1 + bytes.fromhex(f'{light_action}') + s_3 + s_4

        tasks_route.delay('LocatorControl', channel, is_open, zone=room_no)
        send_data_to_panel.apply_async(args=[data_to_send],
                                       queue=f'{sp.tcp_config.ip}:{sp.tcp_config.port}')

        return ('successful update status of light', 200)
