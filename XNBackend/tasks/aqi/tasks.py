# -*- coding:utf-8 -*-
import socket
import redis
import json
import time
import logging
import concurrent.futures
from datetime import datetime
from XNBackend.tasks import celery
from XNBackend.api_client.aqi_client import query_aqi_value
from XNBackend.api_client.ir_client import query_ir_status
from XNBackend.api_client.public_aqi import request_weather_info
from XNBackend.api_client.light import sp_control_light
from XNBackend.models import AQISensors, IRSensors, SwitchPanel, Switches
from XNBackend.utils import get_socket_client, close_conn


L = logging.getLogger(__name__)


def is_work_begin_time():
    now = datetime.now()
    start = now.replace(hour=8, minute=0, second=0)
    end = now.replace(hour=9, minute=30, second=0)
    return start <= now <= end


# TODO optimize
@celery.task()
def turn_on_room_light(room_str):
    sp = SwitchPanel.query.filter(SwitchPanel.locator_id == room_str).first()
    if not sp:
        L.error(f'room {room_str} has no sp.')
        return
    sw = Switches.query.filter(Switches.switch_panel_id == sp.id).filter(Switches.channel == 1).first()
    if sw and sw.status == 1:
        L.debug('already on==========')
        return
    ip = sp.tcp_config.ip
    port = 4196
    tcp_conn = get_socket_client(ip, port, timeout=5)
    if not tcp_conn:
        L.error(f'can not build connection to zlan ip {ip}')
        return
    sp_control_light(tcp_conn, sp, main=1)
    close_conn(tcp_conn)


# def update_aqi_ir_task(tcp_obj, sensor_list: list, redis_conn):
def update_aqi_ir_task(args):
    tcp_obj = args[0]
    sensor_list = args[1]
    redis_conn = args[2]

    timestamp = int(time.time())
    conn_client = get_socket_client(tcp_obj.ip,
                                    celery.flask_app.config['ZLAN_PORT'],
                                    timeout=5)
    if not conn_client:
        L.error('AQI and IR updating failed, reason: failed to create the connection.')
        return

    for s in sensor_list:
        if s.__tablename__ == 'aqi_sensors':
            query_func = query_aqi_value
            prefix = "AQI"
            addr_int = s.addr_int
        else:
            query_func = query_ir_status
            prefix = "IR"
            addr_int = s.addr_no

        resp = query_func(addr_int, conn_client)
        if resp is not None:
            if s.__tablename__ == 'aqi_sensors':
                redis_conn.set(f'{prefix}_{s.locator}', json.dumps((resp, timestamp)))
            else:
                value = redis_conn.get(f'{prefix}_{s.locator}')
                if not value:
                    redis_conn.set(f'{prefix}_{s.locator}', json.dumps(([resp], timestamp)))
                else:
                    if resp == 1 and is_work_begin_time():
                        turn_on_room_light.apply_async(args=[s.locator], queue='general')
                    load_value = json.loads(value)
                    if len(load_value) != 2:
                        return
                    prev_timestamp = load_value[1]
                    prev_status = load_value[0]
                    if prev_timestamp == timestamp:
                        prev_status.append(resp)
                        redis_conn.set(f'{prefix}_{s.locator}',
                                       json.dumps((prev_status, timestamp)))
                    else:
                        redis_conn.set(f'{prefix}_{s.locator}',
                                       json.dumps(([resp], timestamp)))
    conn_client.close()


@celery.task()
def periodic_update_aqi_ir_value():
    sensor_collection = {}
    f5_aqi_sensors = AQISensors.query.filter(AQISensors.locator_body.has(floor=5)).all()
    # f3_aqi_sensors = AQISensors.query.filter(AQISensors.locator_body.has(floor=3)).all()
    ir_sensors = IRSensors.query.filter(IRSensors.locator_body.has(floor=5)).all()
    R = redis.Redis(host=celery.flask_app.config['REDIS_HOST'],
                    port=celery.flask_app.config['REDIS_PORT'])
    # for sensor in f5_aqi_sensors + f3_aqi_sensors + ir_sensors:
    for sensor in f5_aqi_sensors + ir_sensors:
        if sensor.tcp_config not in sensor_collection:
            sensor_collection[sensor.tcp_config] = [sensor]
        else:
            sensor_collection[sensor.tcp_config].append(sensor)

    args_group = [(k, v, R) for k, v in sensor_collection.items()]
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(update_aqi_ir_task, args_group)
    return {"code": 0, "message": "light cmd sent"}


@celery.task()
def no_exist_count():
    ir = IRSensors.query.filter(IRSensors.id == 18).first()
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.settimeout(5)
    conn.connect(('10.100.102.83', 4196))
    time.sleep(1)
    ret = query_ir_status(ir.addr_no, conn)
    conn.close()
    if ret == 0:
        R1 = redis.Redis(host=celery.flask_app.config['REDIS_HOST'],
                         port=celery.flask_app.config['REDIS_PORT'])
        count = R1.get('NO_EXIST_COUNT')
        if count:
            count = json.loads(count)
            count += 1
            R1.set('NO_EXIST_COUNT', json.dumps(count))
        else:
            R1.set('NO_EXIST_COUNT', json.dumps(0))


@celery.task()
def periodic_update_outer_aqi():
    weather_info = request_weather_info('weather', 'wuxi')
    aqi_info = request_weather_info('aqi', 'wuxi')
    if weather_info is None or aqi_info is None:
        return
    R_aqi = redis.Redis(host=celery.flask_app.config['REDIS_HOST'],
                        port=celery.flask_app.config['REDIS_PORT'])
    R_aqi.set('OUTER_temperature',
              json.dumps(weather_info['temperature']))
    R_aqi.set('OUTER_humidity',
              json.dumps(weather_info['humidity']))
    R_aqi.set('OUTER_pm25',
              json.dumps(int(aqi_info['pm25'])))
