from XNBackend.task import celery, logger
from XNBackend.models import db, AirConditioner
from XNBackend.api_client.air_conditioner import get_ac_data, set_ac_data

L = logger.getChild(__name__)


@celery.task()
def periodic_query_air_condition():
    devices_with_keys = {}
    for a in AirConditioner.query:
        devices_with_keys[a.device_index_code] = a

    device_codes = list(devices_with_keys.keys())
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

    else:
        L.error(f'Fail to get ac data reason{all_data["errMsg"]}')


@celery.task()
def send_cmd_to_air_condition(device_index_code: str, **kwarg):
    ret = set_ac_data(device_index_code, **kwarg)
    return 0 if ret.get('errMsg') == 'ok' else 1
