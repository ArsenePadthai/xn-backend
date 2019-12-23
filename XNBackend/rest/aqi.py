import json
import random
from flask import current_app
from flask_restful import Resource, reqparse


floor_parser = reqparse.RequestParser()
floor_parser.add_argument('floor', required=True, type=int, help='require floor number')


class AQISensor(Resource):
    def get(self):
        import redis
        R = redis.Redis(host=current_app.config['REDIS_HOST'], port=current_app.config['REDIS_PORT'])
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
        aqi_values = R.get('AQI_'+aqi_room)
        # TODO VALIDATE THE TIME HAS NOT EXPIRED
        if not aqi_values:
            # mock value
            ret = (681, 49, 0.02, 0, 46.2, 17.8)
        else:
            ret = json.loads(aqi_values)[0]
        return {"tem": {"out": 20, "in": ret[-1]},
                "hum": {"out": 80, "in": ret[-2]},
                "pm25": {"out": 43, "in": ret[-3]},
                "co2": {"in": ret[0]},
                "tvoc": {"out": 0.2, "in": ret[1]}}
