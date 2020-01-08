from flask_restful import Resource, reqparse
from XNBackend.models import db, Locators

ecoapi_patch_parser = reqparse.RequestParser()
ecoapi_patch_parser.add_argument('room', type=str, required=True)
ecoapi_patch_parser.add_argument('eco_mode', type=int, required=True)


class EcoApi(Resource):
    def get(self):
        args = ecoapi_patch_parser.parse_args()
        room_str = args.get("room")
        eco_mode = args.get("eco_mode")
        room = Locators.query.filter(Locators.internal_code == room_str).first()
        if not room:
            return {"code": -1, "message": f"can not find room {room_str}"}
        elif eco_mode == room.eco_mode:
            return {"code": -1, "message": f"room {room_str} is already in eco mode."}
        else:
            room.eco_mode = eco_mode
            db.session.commit()
            return {"code": 0, "message": "ok"}
