import json
import random
from flask import current_app
from flask_restful import Resource, reqparse
from XNBackend.utils import get_redis_value, check_time_valid


floor_parser = reqparse.RequestParser()
floor_parser.add_argument('floor', required=True, type=int, help='require floor number')


class AQISensor(Resource):
    def get(self):
        import redis
        R = redis.Redis(host=current_app.config['REDIS_HOST'], port=current_app.config['REDIS_PORT'])
        outer_temperature = get_redis_value(R, 'OUTER_temperature')
        outer_humidity = get_redis_value(R, 'OUTER_humidity')
        outer_pm25 = get_redis_value(R, 'OUTER_pm25')

        args = floor_parser.parse_args()
        floor = args.get('floor')
        floor = 5
        aqi_collections = {
            3: [],
            4: [],
            5: ['504', '505', '516', '507', '515'],
            6: [],
            7: [],
            9: []
        }
        aqi_room = random.choice(aqi_collections[floor])
        aqi_values = get_redis_value(R, 'AQI_'+aqi_room)
        # TODO VALIDATE THE TIME HAS NOT EXPIRED
        if not aqi_values or not check_time_valid(aqi_values[1]):
            aqi_values = [None] * 6
        else:
            aqi_values = aqi_values[0]
        return {"tem": {"out": outer_temperature,
                        "in": aqi_values[-1]},
                "hum": {"out": outer_humidity,
                        "in": aqi_values[-2]},
                "pm25": {"out": outer_pm25,
                         "in": aqi_values[-3]},
                "co2": {"in": aqi_values[0]},
                "tvoc": {"out": None,
                         "in": aqi_values[1]}}
