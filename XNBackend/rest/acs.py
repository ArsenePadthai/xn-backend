from flask_restful import Resource, reqparse
from XNBackend.task.hik.acs import *
from XNBackend.task.hik.task import acs_control 
from XNBackend.models.models import db, TrackingDevices, Locators

acs_parser = reqparse.RequestParser()
acs_parser.add_argument('room_no', type=str)

acs_get_parser = reqparse.RequestParser()
acs_get_parser.add_argument('floor',
                            required=True,
                            type=int,
                            help='wrong floor parameter')


class AcsControl(Resource):
    def patch(self):
        args = acs_parser.parse_args()
        room_no = int(args.get('room_no'))

        try:
            locator = Locators.query.filter_by(zone = room_no).first()
            device = TrackingDevices.query.filter_by(locator=locator.internal_code).first()
            acs = [device.device_index_code]
        except AttributeError:
            return ('wrong request', 400)

        acs_control.delay(acs, 2)

        return ('successful open the door', 200)


class Acs(Resource):
    def get(self):
        def calc_acs(entries):
            count_open = 0
            count_infra = 0
            for e in entries:
                if e.acs_record:
                    if e.acs_record.status == 1:
                        count_open += 1
                    if e.acs_record.event_type == 198657:
                        count_infra += 1
            return {
                'open': count_open,
                'infra': count_infra
            }

        args = acs_get_parser.parse_args()
        floor = args['floor']
        acs = TrackingDevices.query.filter(
            TrackingDevices.device_type == 1
        ).filter(
            TrackingDevices.locator_body.has(floor=floor)
        ).all()
        ret = {'total': len(acs)}
        detail = dict()
        for a in acs:
            if not detail.get(a.locator_body.internal_code):
                if a.acs_record:
                    detail[a.locator_body.internal_code] = a.acs_record.status == 1

        ret.update({"detail": detail})
        ret.update(calc_acs(acs))
        return ret


class AcsEvent(Resource):
    def post(self):
        args = acs_post_parser.parse_args()
        method = args.get('method')
        params = args.get('params')['events'][0]
        print(params)
        '''
        if params.get('eventTypes') == '196893':
            face_recognition.delay(params['data']['ExtEventCardNo'], params['srcName'])
        elif params.get('eventTypes') == '198919':
            door_control.delay()
        elif params.get('eventTypes') == '198657':
            door_destroy.delay()
        '''





