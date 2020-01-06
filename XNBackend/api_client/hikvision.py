import requests
import hmac
import json
import base64
import hashlib
from datetime import datetime
from flask import current_app


def get_date_string():
    now = datetime.now()
    return now.strftime('%a %b %d %H:%M:%S' + " CST " + "%Y")


def open_door(door_index_code, control_type=2):
    """
    Control the door to open. Closing is not supported.

    Args:
        door_index_code (str): device_index_code of the door in database
        control_type: 2, without question
    """
    if control_type == 3:
        return {"code": -1,
                "message": "control type 3 is not allowed"}
    req_body = {
        "doorIndexCodes": [door_index_code],
        "controlType": control_type
    }

    method = "POST"
    accept = "*/*"
    content_md5 = base64.b64encode(hashlib.md5(json.dumps(req_body).encode("utf-8")).digest()).decode()
    date_string = get_date_string()
    content_type = "application/json"
    x_ca_signature_headers = "x-ca-key"
    x_ca_key = current_app.config['HIK_APP_KEY']
    path = "/artemis/api/acs/v1/door/doControl"

    http_headers = method +"\n" + accept + "\n" + content_md5 +"\n" + content_type + "\n" + date_string + "\n"
    custom_headers = x_ca_signature_headers + ":" + x_ca_key + "\n"
    url = path
    pre_sign = http_headers + custom_headers + url

    signed_str = base64.b64encode(hmac.new(bytes(current_app.config['HIK_APP_SECRET'], encoding='utf-8'),
                                           bytes(pre_sign, encoding='utf-8'),
                                           hashlib.sha256).digest()).decode('utf-8')

    headers = {
        "Accept": "*/*",
        "Content-MD5": content_md5,
        "Content-Type": "application/json",
        "Date": get_date_string(),
        "X-Ca-Key": current_app.config['HIK_APP_KEY'],
        "X-Ca-Signature": signed_str,
        "X-Ca-Signature-Headers": 'x-ca-key',
    }

    resp = requests.post('http://10.100.103.1/' + path, headers=headers, json=req_body)
    j_resp = resp.json()
    return {
        "code": j_resp['code'],
        "message": j_resp['msg']
    }


# TODO refactor
def query_entry_room(door_index_code,
                     start_time,
                     end_time,
                     page_no=1,
                     page_size=100,
                     event_type=196893,
                     sort='eventTime',
                     order="desc"):
    path = "/artemis/api/acs/v1/door/events"
    start_time = start_time + '.000+08:00'
    end_time = end_time + '.000+08:00'
    req_body = {
        "startTime": start_time,
        "endTime": end_time,
        "eventType": event_type,
        "doorIndexCodes": [door_index_code],
        "sort": sort,
        "order": order,
        "pageNo": page_no,
        "pageSize": page_size
    }

    method = "POST"
    accept = "*/*"
    content_md5 = base64.b64encode(hashlib.md5(json.dumps(req_body).encode("utf-8")).digest()).decode()
    date_string = get_date_string()
    content_type = "application/json"
    x_ca_signature_headers = "x-ca-key"
    x_ca_key = current_app.config['HIK_APP_KEY']


    http_headers = method + "\n" + accept + "\n" + content_md5 + "\n" + content_type + "\n" + date_string + "\n"
    custom_headers = x_ca_signature_headers + ":" + x_ca_key + "\n"
    url = path
    pre_sign = http_headers + custom_headers + url
    signed_str = base64.b64encode(hmac.new(bytes(current_app.config['HIK_APP_SECRET'], encoding='utf-8'),
                                           bytes(pre_sign, encoding='utf-8'),
                                           hashlib.sha256).digest()).decode('utf-8')

    headers = {
        "Accept": "*/*",
        "Content-MD5": content_md5,
        "Content-Type": "application/json",
        "Date": get_date_string(),
        "X-Ca-Key": current_app.config['HIK_APP_KEY'],
        "X-Ca-Signature": signed_str,
        "X-Ca-Signature-Headers": 'x-ca-key',
    }

    resp = requests.post('http://10.100.103.1/' + path, headers=headers, json=req_body)
    j_resp = resp.json()
    return {
        "code": j_resp['code'],
        "message": j_resp['msg'],
        "data": j_resp['data']
    }
