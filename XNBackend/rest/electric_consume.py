from flask_restful import Resource, reqparse
from datetime import datetime, timedelta
from flask import current_app
from XNBackend.models import EnergyConsumeDaily, S3FC20

time_range_parse = reqparse.RequestParser()
time_range_parse.add_argument('start',
                              required=True,
                              type=lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%S')-timedelta(hours=1),
                              help='need start time')
time_range_parse.add_argument('end',
                              required=True,
                              type=lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%S')-timedelta(hours=1),
                              help='need end time')
time_range_parse.add_argument('floor',
                              type=int,
                              required=True,
                              help='wrong floor parameter')


class ElectricConsumeByDay(Resource):

    @staticmethod
    def get_one_day_ret(time_marker, floor):
        light = ac = socket = 0
        detail = dict()
        floor_map = current_app.config['FLOOR_ROOM_MAPPING'][floor]
        for room in floor_map:
            detail[str(room)] = {"light": 0, "ac": 0, "socket": 0}
        detail['999'] = {"light": 0, "ac": 0, "socket": 0}

        subq = S3FC20.query.filter(S3FC20.locator_id.like(str(floor)+'%')).subquery('t2')
        enery_consume_floor = EnergyConsumeDaily.query\
            .join(subq, EnergyConsumeDaily.s3_fc20_id == subq.c.id)\
            .filter(EnergyConsumeDaily.updated_at == time_marker)

        for enery_consume in enery_consume_floor:
            this_room = enery_consume.s3_fc20.locator_id
            measure = enery_consume.s3_fc20.measure_type
            if measure == 0:
                measure_name = 'light'
                light += enery_consume.electricity
            elif measure == 1:
                measure_name = 'ac'
                ac += enery_consume.electricity
            else:
                measure_name = 'socket'
                socket += enery_consume.electricity
            detail[this_room][measure_name] = int(enery_consume.electricity)

        time_key = time_marker.strftime('%Y-%m-%d')
        return {time_key: {"light": int(light),
                           "ac": int(ac),
                           "socket": int(socket),
                           "detail": detail}
                }

    def get(self):
        ret = []
        args = time_range_parse.parse_args()
        start = args.get('start')
        end = args.get('end')
        floor = args.get('floor')

        time_list = EnergyConsumeDaily.query.\
            with_entities(EnergyConsumeDaily.updated_at).\
            filter(EnergyConsumeDaily.updated_at > start).\
            filter(EnergyConsumeDaily.updated_at < end)\
            .distinct()

        for t in time_list:
            ret.append(self.get_one_day_ret(t.updated_at, floor))

        return ret


class ElectricConsumeByMonth(Resource):
    def get(self):
        pass
