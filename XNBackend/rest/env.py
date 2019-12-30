import redis
import logging
import random
from flask_restful import Resource
from flask import current_app
from XNBackend.utils import get_redis_value, check_time_valid, form_float

L = logging.getLogger(__name__)


def get_floor_env(floor, redis_cli):
    aqi_rooms = current_app.config['AQI_ROOMS']
    floor_rooms = aqi_rooms[floor]
    room = random.choice(floor_rooms)
    aqi_value = get_redis_value(redis_cli, 'AQI_' + str(room))
    if not aqi_value:
        L.error(f'Failed to get aqi value from redis cache for room {room}')
        return
    aqi_value_tuple, aqi_ts = aqi_value
    ret = check_time_valid(aqi_ts, 600)
    if not ret:
        L.error(f'expired timestamp for aqi value')
        return
    return {
        'temperature': aqi_value_tuple[-1],
        'humidity': aqi_value_tuple[-2],
        'co2': aqi_value_tuple[1],
        'pm25': aqi_value_tuple[-3]
    }


def get_other():
    return {"lux": 103, "fan": True, 'fire_alarm': True}


class Env(Resource):
    def get(self):
        tem = hum = co2 = pm25 = 0
        tem_count = hum_count = co2_count = pm25_count = 0
        ret = {}
        R = redis.Redis(host=current_app.config['REDIS_HOST'],
                        port=current_app.config['REDIS_PORT'])
        floors = [3, 4, 5, 6, 7, 9]
        for f in floors:
            aqi_value = get_floor_env(f, R)
            if aqi_value is None:
                aqi_value = {
                    'temperature': None,
                    'humidity': None,
                    'co2': None,
                    'pm25': None,
                }
            other_index = get_other()
            aqi_value.update(other_index)
            if aqi_value['temperature'] is not None:
                tem += aqi_value['temperature']
                tem_count += 1

            if aqi_value['humidity'] is not None:
                hum += aqi_value['humidity']
                hum_count += 1

            if aqi_value['co2'] is not None:
                co2 += aqi_value['co2']
                co2_count += 1

            if aqi_value['pm25'] is not None:
                pm25 += aqi_value['pm25']
                pm25_count += 1

            ret[f'{f}f'] = aqi_value

        if tem_count:
            avg_tem = form_float(tem/tem_count)
        else:
            avg_tem = None
        if hum_count:
            avg_hum = form_float(hum/hum_count)
        else:
            avg_hum = None
        if co2_count:
            avg_co2 = form_float(co2/co2_count)
        else:
            avg_co2 = None
        if pm25_count:
            avg_pm25 = form_float(pm25/pm25_count)
        else:
            avg_pm25 = None

        avg_env = {
            'temperature': avg_tem,
            'humidity': avg_hum,
            'co2': avg_co2,
            'pm25': avg_pm25
        }

        avg_env.update(get_other())
        ret['total'] = avg_env
        return ret
