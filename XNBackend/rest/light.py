import logging
from flask_restful import Resource, reqparse
from XNBackend.task.sensor.task import tasks_route
from XNBackend.models import SwitchPanel, Switches, db
from ..utils import query_panel_status, get_panel_client

light_parser = reqparse.RequestParser()
light_parser.add_argument('room_no', required=True, type=str)
light_parser.add_argument('level', required=True, type=int)
light_parser.add_argument('action', required=True, type=int)

L = logging.getLogger(__name__)


class LightControl(Resource):
    def patch(self):
        args = light_parser.parse_args()
        room_no = args.get('room_no')
        light_type = args.get('level')
        is_open = args.get('action')

        sp = SwitchPanel.query.filter(SwitchPanel.locator_id == room_no).first()
        if not sp:
            return {"errMsg": f'no matching panel found for this room {room_no}'}

        try:
            client = get_panel_client(sp.tcp_config.ip, 4196)
            ret = query_panel_status(client, sp.tcp_config.ip, sp.batch_no, sp.addr_no)
            s_1 = ret[-5]
            s_2 = ret[-4]
            s_3 = ret[-3]
            s_4 = ret[-2]
        except Exception as e:
            client.close()
            L.exception(e)
            return {"errMsg": 'failed to get panel information'}

        if light_type == 0:
            # main light
            channel = 1
            four_bits = [is_open, s_2, s_3, s_4]
        else:
            # aux light
            if sp.panel_type == 0:
                channel = 4
                four_bits = [s_1, s_2, s_3, is_open]
            else:
                # two switches
                channel = 2
                four_bits = [s_1, is_open, s_3, s_4]

        cmd = bytes.fromhex(f'DA 06 {int(sp.addr_no)} 02') + bytes(four_bits) + bytes.fromhex('EE')
        L.debug(cmd)
        try:
            client.send(cmd)
            sw = Switches.query.filter(Switches.switch_panel_id == sp.id
                                       ).filter(Switches.channel == channel).first()
            sw.status = is_open
            db.session.add(sw)
            db.session.commit()
            client.close()
        except Exception as e:
            L.exception(e)
            client.close()
            return {'errMsg': 'failed to send cmd to panel'}

        tasks_route.delay('LocatorControl', channel, is_open, zone=room_no)
        tasks_route.apply_async(args=['LocatorControl', channel, is_open],
                                kwargs={'zone': room_no})
        return {'errMsg': 'ok'}
