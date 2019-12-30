import logging
import requests
import base64
import time
from hashlib import sha1
import hmac
from flask import current_app


L = logging.getLogger(__name__)


def parse_weather_resp(resp):
    weather_data = {'temperature': int(resp['results'][0]['now']['temperature']),
                    'humidity': int(resp['results'][0]['now']['humidity'])}
    return weather_data


def parse_aqi_resp(resp):
    return resp['results'][0]['air']['city']


def sign_my_string(ts, uid):
    my_string = f'ts={ts}&uid={uid}'
    hashed = hmac.new(bytes(current_app.config['WEATHER_PRIVATE_KEY'], encoding='utf-8'),
                      bytes(my_string, encoding='utf-8'), sha1)
    return base64.b64encode(hashed.digest()).decode('utf-8')


def request_weather_info(req_type, location):
    """ This is low level api for xinzhi weather api function.
    Args:
        req_type: str, options are 'weather' and 'aqi'
        location: str, str name of the city
    """
    ts = int(time.time())
    uid = current_app.config['WEATHER_PUB_KEY']
    if req_type == 'weather':
        url = current_app.config['PUB_WEATHER_URL']
        parse_func = parse_weather_resp
    elif req_type == 'aqi':
        url = current_app.config['PUB_AQI_URL']
        parse_func = parse_aqi_resp
    else:
        return
    full_url = url + '?' + f'ts={ts}&uid={uid}&location={location}&sig=' + sign_my_string(ts, uid)
    try:
        resp = requests.get(full_url)
    except Exception as e:
        L.exception('failed to get weather information')
        return
    return parse_func(resp.json())




