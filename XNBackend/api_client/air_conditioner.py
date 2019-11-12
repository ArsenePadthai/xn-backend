import time
import requests
import hashlib
import json
import logging
from flask import current_app

L = logging.getLogger(__name__)


def _request_main_string(interface):
    time_info = str(int(time.time()))
    app_code = current_app.config['AC_APPCODE']
    app_key = current_app.config['AC_SECRET_KEY']

    group = [time_info, app_code, app_key]
    group.sort()
    sign = hashlib.md5(''.join(group).encode('utf-8')).hexdigest()

    return f'http://{current_app.config["AC_SERVER_IP"]}:{current_app.config["AC_SERVER_PORT"]}' \
        f'/app/{current_app.config["AC_APPCODE"]}/api/protected/{interface}' + f'?time={time_info}' + f'&sign={sign}'


def get_ac_data(device_codes: list,
                target=["FanSpeedSet",
                        "IsOnline",
                        "ModeCmd",
                        "RoomTemp",
                        "StartStopStatus",
                        "TempSet"]
                ):
    url = _request_main_string('getDeviceVariantData')
    data = [{"deviceCode": dc,
             "variants": target} for dc in device_codes]
    try:
        ret = requests.get(url, json=data)
        return json.loads(ret.content)
    except Exception as e:
        L.exception(e)
        return {"errMsg": 'failed'}


def set_ac_data(device_code: str, **kwargs):
    full_writable = ['FanSpeedSet', 'ModeCmd', 'StartStopStatus', 'TempSet']
    assert set(kwargs.keys()).issubset(set(full_writable))
    url = _request_main_string('writeDeviceVariantData')
    data = {
        "deviceCode": device_code,
        "writeData": kwargs
    }
    try:
        ret = requests.post(url, json=data)
        content = json.loads(ret.content)
        errMsg = content.get('errMsg')
        if errMsg != 'ok':
            errCode = content.get('errCode')
            L.error(f'Failed to set parameters. Reason: {errMsg}, Code: {errCode}')
            return {"errMsg": errMsg,
                    "errCode": errCode}
        else:
            return {"errMsg": 'ok',
                    "writeResult": content.get('writeResult')}
    except Exception as e:
        L.exception(e)
        return {"errMsg": e}
