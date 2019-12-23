import threading
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from XNBackend.models import IRSensors, AQISensors
from XNBackend.utils import get_socket_client
from XNBackend.api_client.ir_client import query_ir_status
from XNBackend.api_client.aqi_client import query_aqi_value

ENGINE = create_engine('mysql+pymysql://xn:Pass1234@10.100.101.199:3306/xn?charset=utf8mb4')
Session = sessionmaker(bind=ENGINE)
session = Session()


def check_ir_aqi(tcp_obj, sensors: list):
    conn = get_socket_client(tcp_obj.ip, 4196, timeout=5)
    time.sleep(0.5)
    if not conn:
        print('AQI and IR updating failed, reason: failed to create the connection.')
        return

    for s in sensors:
        if s.__tablename__ == 'aqi_sensors':
            query_func = query_aqi_value
            addr_int = s.addr_int
        else:
            query_func = query_ir_status
            addr_int = s.addr_no

        resp = query_func(addr_int, conn)
        if resp or resp == 0:
            print(resp)
        elif resp is None:
            print(f'WRONG sensor: {s.id}, addr: {addr_int} for sensor type {s.__tablename__}')
        time.sleep(0.5)
    conn.close()


def check_all(floor):
    threads = []
    sensor_collection = {}
    aqi_sensors = AQISensors.query.filter(AQISensors.locator.like(str(floor)+'%')).all()
    ir_sensors = IRSensors.query.filter(IRSensors.locator.like(str(floor)+'%')).all()

    for sensor in aqi_sensors + ir_sensors:
        if sensor.tcp_config not in sensor_collection:
            sensor_collection[sensor.tcp_config] = [sensor]
        else:
            sensor_collection[sensor.tcp_config].append(sensor)

    for k, v in sensor_collection.items():
        t = threading.Thread(target=check_ir_aqi, args=(k, v))
        threads.append(t)

    for th in threads:
        th.start()
        th.join()


if __name__ == "__main__":
    check_all(5)