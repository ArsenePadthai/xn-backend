from flask_restful import Resource, reqparse
from XNBackend.task.sensor.task import tasks_route, send_data_to_panel
from XNBackend.models import SwitchPanel, Switches, db
from ..utils import query_panel_status

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

        sp = SwitchPanel.query.filter(SwitchPanel.locator_id == room_no).first()
        if not sp:
            return (f'no matching panel found for this room {room_no}', 200)
        room_switches = Switches.query.filter(Switches.switch_panel_id == sp.id)
        
        if light_type == 0: # main switch
            channel = 1
        else:               # aux switch
            channel = 4 if sp.panel_type == 0 else 2
        
        sw = room_switches.filter(Switches.channel == channel).first()
        sw.status = is_open
        tasks_route.delay('LocatorControl', channel, is_open, zone=room_no)
        db.session.add(sw)
        db.session.commit()
        return ('successful update status of light', 200)
        
        # ================================================================
        # ret = query_panel_status(sp.tcp_config.ip, sp.batch_no, sp.addr_no)
        # s_1 = ret[-5]
        # s_2 = ret[-4]
        # s_3 = ret[-3]
        # s_4 = ret[-2]

        # if light_type == 0:
        #     channel = 1
        #     # main light
        #     four_bits = [is_open, s_2, s_3, s_4]
        # else:
        #     channel = 4
        #     # aux light
        #     if sp.panel_type == 0:
        #         four_bits = [s_1, s_2, s_3, is_open]
        #     else:
        #         # two switches
        #         four_bits = [s_1, is_open, s_3, s_4]
        #the_q = f'{sp.tcp_config.ip}:{sp.tcp_config.port}'
        # =================================================================

        #send_data_to_panel.apply_async(args=[sp.addr_no, four_bits],
        #                               queue=the_q)

