import socket
import redis
import json
import time
import logging
import threading
from XNBackend.tasks import celery
from XNBackend.api_client.aqi_client import query_aqi_value
from XNBackend.api_client.ir_client import query_ir_status
from XNBackend.models import AQISensors, IRSensors
from XNBackend.utils import get_socket_client


L = logging.getLogger(__name__)


def update_aqi_ir_task(tcp_obj, sensor_list: list, redis_conn):
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
            if s.__tablename__ == 'aqi_sensor':
                redis_conn.set(f'{prefix}_{s.locator}', json.dumps((resp, timestamp)))
            else:
                value = redis_conn.get(f'{prefix}_{s.locator}')
                if not value:
                    redis_conn.set(f'{prefix}_{s.locator}', json.dumps(([resp], timestamp)))
                else:
                    load_value = json.loads(value)
                    if len(load_value) != 2:
                        print('xxxxxxx')
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
    threads = []
    sensor_collection = {}
    f5_aqi_sensors = AQISensors.query.filter(AQISensors.locator_body.has(floor=5)).all()
    # f3_aqi_sensors = AQISensors.query.filter(AQISensors.locator_body.has(floor=3)).all()
    ir_sensors = IRSensors.query.filter(IRSensors.locator_body.has(floor=5)).all()
    R = redis.Redis(host=celery.flask_app.config['REDIS_HOST'],
                    port=celery.flask_app.config['REDIS_PORT'])

    #for sensor in f5_aqi_sensors + f3_aqi_sensors + ir_sensors:
    for sensor in f5_aqi_sensors + ir_sensors:
        if sensor.tcp_config not in sensor_collection:
            sensor_collection[sensor.tcp_config] = [sensor]
        else:
            sensor_collection[sensor.tcp_config].append(sensor)

    for k, v in sensor_collection.items():
        t = threading.Thread(target=update_aqi_ir_task, args=(k, v, R))
        threads.append(t)

    for th in threads:
        th.start()
    for th in threads:
        th.join()


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
