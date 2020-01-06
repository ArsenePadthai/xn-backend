import socket
import json
import time


def get_panel_client(ip, port):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(15)
    client.connect((ip, port))
    return client


def query_panel_status(client, batch_no, addr_no):
    data = bytes.fromhex('DA {} {} 86 86 86 EE'.format(
        hex(int(batch_no))[2:].rjust(2, '0'),
        hex(int(addr_no))[2:].rjust(2, '0'))
                         )
    client.send(data)
    ret = client.recv(1024)
    return ret


def int2hex(number) -> str:
    return hex(number).lstrip('0x').rjust(2, '0')


def get_socket_client(ip, port, timeout=None):
    try:
        conn_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if timeout:
            conn_client.settimeout(timeout)
        conn_client.connect((ip, port))
        return conn_client
    except Exception as e:
        return


def get_redis_value(redis_conn, key):
    dumped = redis_conn.get(key)
    if dumped:
        return json.loads(dumped)
    else:
        return


def check_time_valid(ts, ts_gap=600):
    now_ts = int(time.time())
    return now_ts - ts_gap <= ts


def form_float(number):
    """limit float to 2 decimal"""
    return float('%.2f' % number)


