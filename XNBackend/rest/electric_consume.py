from flask_restful import Resource, reqparse

time_range_parse = reqparse.RequestParser()
time_range_parse.add_argument('start', required=True, type=str, help='need start time')
time_range_parse.add_argument('end', required=True, type=str, help='need end time')


class ElectricConsumeByHour(Resource):
    def get(self):
        pass


class ElectricConsumeByDay(Resource):
    def get(self):
        args = time_range_parse.parse_args()
        start = args.get('start')
        end = args.get('end')
        return [
            {'2019-12-12': {"light": 233, "ac": 533, 'socket': 600}},
            {'2019-12-13': {"light": 233, "ac": 533, 'socket': 600}},
            {'2019-12-14': {"light": 233, "ac": 533, 'socket': 600}}
        ]


class ElectricConsumeByMonth(Resource):
    def get(self):
        pass
