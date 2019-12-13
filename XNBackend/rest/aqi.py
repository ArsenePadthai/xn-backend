from flask_restful import Resource, reqparse


floor_parser = reqparse.RequestParser()
floor_parser.add_argument('floor', required=True, type=int, help='require floor number')


class AQISensor(Resource):
    def get(self):
        args = floor_parser.parse_args()
        floor = args.get('floor')
        return {"tem": {"in": 11, "out": 12},
                "hum": {"in": 0.6, "out": 13},
                "pm25": {"in": 43, "out": 33},
                "co2": {"in": 66},
                "tvoc": {"in": 45, "out": 66}}
