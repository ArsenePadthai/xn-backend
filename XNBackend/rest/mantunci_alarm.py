from flask_restful import Resource, reqparse
from datetime import datetime, timedelta
from XNBackend.models import BoxAlarms, MantunciBox

parser = reqparse.RequestParser()
parser.add_argument('startTime',
                    type=str,
                    required=False,
                    help='please provide correct start time, example: 20190830T100000')

parser.add_argument('endTime',
                    type=str,
                    required=False,
                    help='please provide correct end time, example: 20190830T100000')


def count_alarm(enties):
    short_circuit = len(list(
        filter(lambda x: x.type_number == 2, enties)
    ))
    leak = len(list(
        filter(lambda x: x.type_number == 3, enties)
    ))
    over_heat = len(list(
        filter(lambda x: x.type_number == 7, enties)
    ))
    surge = len(list(
        filter(lambda x: x.type_number == 8, enties)
    ))
    more_less_vol = len(list(
        filter(lambda x: (x.type_number == 5 or x.type_number == 6), enties)
    ))
    over_load = len(list(
        filter(lambda x: x.type_number == 4, enties)
    ))
    circuit_fire = len(list(
        filter(lambda x: x.type_number == 11, enties)
    ))
    return {
        'short_circuit': short_circuit,
        'leak': leak,
        'over_heat': over_heat,
        'surge': surge,
        'more_less_vol': more_less_vol,
        'over_load': over_load,
        'circuit_fire': circuit_fire
    }


class MantunciBoxAlarm(Resource):
    def get(self):
        # TODO allow customized startTime and endTime in request parameter
        args = parser.parse_args()
        #
        end_time = datetime.utcnow()
        start_time = datetime.utcnow() - timedelta(days=7)
        # TODO ADD COMPARE
        # if start_time > end_time:
        #     abort(400)
        query_all = BoxAlarms.query.filter(
            BoxAlarms.time > start_time
        ).filter(
            BoxAlarms.time < end_time
        )

        box_ids = MantunciBox.query.filter(MantunciBox.locator.has(floor=3)).all()
        box_ids = [i.id for i in box_ids]
        query_3f = BoxAlarms.query.filter(BoxAlarms.box_id.in_(box_ids))
        ret_all = query_all.all()
        ret_3f = query_3f.all()
        return {
            'total': count_alarm(ret_all),
            '3f': count_alarm(ret_3f),
            '7f': {
                'short_circuit': 0,
                'leak': 0,
                'over_heat': 0,
                'surge': 0,
                'more_less_vol': 0,
                'over_load': 0,
                'circuit_fire': 0
            }
        }
