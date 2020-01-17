import logging
import redis
from XNBackend.tasks import celery
from XNBackend.models import db, AirConditioner
from XNBackend.api_client.air_conditioner import get_ac_data, set_ac_data
from XNBackend.utils import get_redis_value

L = logging.getLogger(__name__)


def check_skip(device_index_code):
    R_conn = redis.Redis(host=celery.flask_app.config['REDIS_HOST'],
                         port=celery.flask_app.config['REDIS_PORT'])
    value = get_redis_value(R_conn, 'SKIP_' + device_index_code)
    if value:
        return False
    else:
        return True


@celery.task()
def periodic_query_air_condition():
    devices_with_keys = {}
    for a in AirConditioner.query:
        devices_with_keys[a.device_index_code] = a

    device_codes = list(devices_with_keys.keys())
    tmp_device_codes = list(filter(check_skip, device_codes))
    device_codes = tmp_device_codes

    all_data = get_ac_data(device_codes)
    if all_data.get('errMsg') == 'ok':
        for each_data in all_data['data']:
            the_device = devices_with_keys[each_data.get('deviceCode')]
            the_device.apply_values(each_data)
            db.session.flush()
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        L.exception(e)


@celery.task()
def send_cmd_to_air_condition(device_index_code: str, **kwarg):
    ret = set_ac_data(device_index_code, **kwarg)
    if ret.get('errMsg') == 'ok':
        ac = AirConditioner.query.filter(AirConditioner.device_index_code == device_index_code).first()
        if ac:
            if "StartStopStatus" in kwarg:
                ac.ac_on = kwarg['StartStopStatus']
            if "TempSet" in kwarg:
                ac.desired_temperature = kwarg['TempSet']
            if "FanSpeedSet" in kwarg:
                ac.desired_speed = kwarg['FanSpeedSet']
            db.session.commit()
        return 0
    return 1


@celery.task()
def update_specific_air_condition(device_index_code):
    resp = get_ac_data([device_index_code])
    if resp['errCode'] == 0:
        device_data = resp['data'][0]
        ac = AirConditioner.query.filter(AirConditioner.device_index_code == device_index_code).first()
        ac.apply_values(device_data)
        db.session.commit()
        return {"code": 0, "message": "ok"}
    else:
        L.error(f'failed to get ac data for device index code {device_index_code}')
