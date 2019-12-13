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
            {'2019-12-12': {"light": 233, "ac": 533, 'socket': 600, "detail": {
                "301": 333,
                "302": 254,
                "303": 254,
                "304": 666,
                "305": 666,
                "306": 666,
                "307": 666,
                "308": 666,
                "309": 666,
                "310": 653,
                "311": 653,
                "312": 653,
                "313": 653,
                "314": 653,
                "315": 653,
                "316": 653,
                "317": 653,
                "318": 653,
                "319": 653,
                "320": 653,
                "321": 653,
                "323": 653,
                "324": 653,
                "322": 23
            }}},
            {'2019-12-13': {"light": 233, "ac": 533, 'socket': 600, "detail": {
                "301": 333,
                "302": 254,
                "303": 254,
                "304": 666,
                "305": 666,
                "306": 666,
                "307": 666,
                "308": 666,
                "309": 666,
                "310": 653,
                "311": 653,
                "312": 653,
                "313": 653,
                "314": 653,
                "315": 653,
                "316": 653,
                "317": 653,
                "318": 653,
                "319": 653,
                "320": 653,
                "321": 653,
                "323": 653,
                "324": 653,
                "322": 23
            }}},
            {'2019-12-14': {"light": 233, "ac": 533, 'socket': 600, "detail": {
                "301": 333,
                "302": 254,
                "303": 254,
                "304": 666,
                "305": 666,
                "306": 666,
                "307": 666,
                "308": 666,
                "309": 666,
                "310": 653,
                "311": 653,
                "312": 653,
                "313": 653,
                "314": 653,
                "315": 653,
                "316": 653,
                "317": 653,
                "318": 653,
                "319": 653,
                "320": 653,
                "321": 653,
                "323": 653,
                "324": 653,
                "322": 23
            }}}
        ]


class ElectricConsumeByMonth(Resource):
    def get(self):
        pass
