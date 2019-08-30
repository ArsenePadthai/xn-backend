from flask_restful import Resource, reqparse
from XNBackend.task.hik.task import acs_control 
from XNBackend.models.models import db, TrackingDevices, Locators 

acs_parser = reqparse.RequestParser()
acs_parser.add_argument('room_no', type=str)


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
