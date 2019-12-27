import logging
from flask_jwt_extended import jwt_required
from flask_restful import Resource, reqparse
from XNBackend.models import db, SwitchPanel, AirConditioner
from XNBackend.tasks.sensor.tasks import network_relay_control_sync
from XNBackend.tasks.air_condition.tasks import send_cmd_to_air_condition, periodic_query_air_condition

L = logging.getLogger(__name__)

floor_control_parser = reqparse.RequestParser()
floor_control_parser.add_argument('floor',
                                  required=True,
                                  type=int,
                                  help='please provide floor parameter')
floor_control_parser.add_argument('action',
                                  required=True,
                                  type=int,
                                  help='please provide control action, 1 means turn on, 0 means turn off.')
floor_control_parser.add_argument('resource_type',
                                  required=True,
                                  type=int,
                                  help='please provide control resource type 0 means light, 1 means air condition')


class FloorControl(Resource):
    @jwt_required
    def patch(self):
        args = floor_control_parser.parse_args()
        floor = args.get('floor')
        action = args.get('action')
        resource_type = args.get('resource_type')

        # light control
        if resource_type == 0:
            switch_panel = SwitchPanel.query(SwitchPanel.locator_id.like(str(floor)+'%'))
            switch_panel_4_buttons = switch_panel.query(SwitchPanel.panel_type == 0)
            switch_panel_2_buttons = switch_panel.query(SwitchPanel.panel_type == 1)

            for sw in switch_panel_4_buttons.belong_switches + switch_panel_2_buttons.belong_switches:
                for r in sw.belong_relays:
                    network_relay_control_sync.apply_async(args=[r.id, action], queue='relay')
                sw.status = action
                db.session.flush()
            try:
                db.session.commit()
                return {"code": 0, "message": "ok"}
            except Exception as e:
                db.session.rollback()
                L.exception(e)
                return {"code": -1, "message": "failed to control floor light"}

        # air condition control
        elif resource_type == 1:
            air_conditions = AirConditioner.query.filter(AirConditioner.locator_id.like(str(floor) + '%'))
            device_index_codes = [ac.device_index_code for ac in air_conditions]
            send_cmd_to_air_condition.apply_async(args=device_index_codes,
                                                  kwargs={"StartStopStatus": action},
                                                  queue="general")
            periodic_query_air_condition.apply_async(countdown=15)
            return {"code": 0, "message": "air condition cmd sent"}



