from flask_restful import Resource, reqparse


floor_parser = reqparse.RequestParser()
floor_parser.add_argument('floor', required=True, type=int, help='require floor number')


class AQISensor(Resource):
    def get(self):
        args = floor_parser.parse_args()
        floor = args.get('floor')
        return {"tem": {"in": 20, "out": 16},
                "hum": {"in": 80, "out": 80},
                "pm25": {"in": 43, "out": 54},
                "co2": {"in": 243},
                "tvoc": {"in": 0.2, "out": 0.1}}
