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
                "301": {"light": 333, "ac": 222, "socket": 111},
                "302": {"light": 333, "ac": 222, "socket": 111},
                "303": {"light": 333, "ac": 222, "socket": 111},
                "304": {"light": 333, "ac": 222, "socket": 111},
                "305": {"light": 333, "ac": 222, "socket": 111},
                "306": {"light": 333, "ac": 222, "socket": 111},
                "307": {"light": 333, "ac": 222, "socket": 111},
                "308": {"light": 333, "ac": 222, "socket": 111},
                "309": {"light": 333, "ac": 222, "socket": 111},
                "310": {"light": 333, "ac": 222, "socket": 111},
                "311": {"light": 333, "ac": 222, "socket": 111},
                "312": {"light": 333, "ac": 222, "socket": 111},
                "313": {"light": 333, "ac": 222, "socket": 111},
                "314": {"light": 333, "ac": 222, "socket": 111},
                "315": {"light": 333, "ac": 222, "socket": 111},
                "316": {"light": 333, "ac": 222, "socket": 111},
                "317": {"light": 333, "ac": 222, "socket": 111},
                "318": {"light": 333, "ac": 222, "socket": 111},
                "319": {"light": 333, "ac": 222, "socket": 111},
                "320": {"light": 333, "ac": 222, "socket": 111},
                "321": {"light": 333, "ac": 222, "socket": 111},
                "322": {"light": 333, "ac": 222, "socket": 111},
                "323": {"light": 333, "ac": 222, "socket": 111},
                "324": {"light": 333, "ac": 222, "socket": 111},
            }}}
        ]


class ElectricConsumeByMonth(Resource):
    def get(self):
        pass
