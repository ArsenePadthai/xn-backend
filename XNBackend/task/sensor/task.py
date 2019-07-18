import socket
import random
import time
from struct import pack
from XNBackend.task import celery, logger
from XNBackend.models.models import db, IRSensorStatus, IRSensors, AQIValues, AQISensors, LuxValues, LuxSensors, Switches, SwitchStatus
from XNBackend.parser.protocol import *

L = logger.getChild(__name__)

target_host = "127.0.0.1" 
target_port = 51113 
client = None


def tcp_client():
    global client 
    if client is None:   
        client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        client.settimeout(5)
        client.connect((target_host,target_port))   
        L.info('Connected to %s: %s', target_host, target_port)
    return client
    

def send_to_server(data):
    global client 
    try:
        client = tcp_client()
        client.send(data[:-1])
        client.send(data[-1:])
        data_byte = client.recv(1024)
        '''
        Prevent connections from closing too fast and the RESET package sent by TCP will not be received.
        '''
    except Exception:
        celery.control.broadcast('shutdown', destination=['worker1@xn-hik.service'])
        client = None
        L.error('Failed to connected to %s: %s, worker is restarted', target_host, target_port)

    message = data_parse(data_byte)
    return message


def address_pack(address, n):
    return pack('>Q', int(address) & 0xffffffffff)[n:]


def data_generator(model):
    models = {
        'Switch':[Switches, 'CC', 6, 'FE EE'], 
        'IR':[IRSensors, 'DA', 3, '86 86 86 EE'], 
        'AQI':[AQISensors, 'DC', 3, '86 86 86 EE'], 
        'Lux':[LuxSensors, 'DF', 3, '86 86 86 EE']
    }

    length = models[model][0].query.count()
    for items in range(length):
        time.sleep(2)
        sensor = models[model][0].query.filter_by(id = items+1).first()
        data = bytes.fromhex(models[model][1]) + address_pack(sensor.device_index_code, models[model][2]) + bytes.fromhex(models[model][3])

        L.info("Query the status of %s, send '%s' to the server", model, data)
        recv_data = send_to_server(data)

        if model == 'Switch':
            L.info('Received data from %s at id of %s: %s', model, recv_data.id, recv_data)
        else:
            L.info('Received data from %s at address of %s: %s', model, recv_data._address, recv_data)

        yield recv_data, sensor.id


@celery.task()
def network_relay_control(id, channel, code):
    data = bytes.fromhex('AA') + bytes.fromhex(id) + bytes.fromhex(channel) + bytes.fromhex(code) + bytes.fromhex('EE')

    L.info("Control switch, send '%s' to id: %d", data, id)
    recv_data = send_to_server(data)
    L.info('Received data from Switch at id of %s: %s', recv_data.id, recv_data)

    switch = Switches.query.filter_by(device_index_code = recv_data.id).first()
    record = SwitchStatus(sensor_id=switch.id, value=recv_data.status, load=recv_data.loadDetect)
    db.session.add(record)
    db.session.commit()
    L.info('Switch: control successfully')
    return switch.id


@celery.task()
def network_relay_query():
    records = []

    for switch, id in data_generator('Switch'):
        record = SwitchStatus(sensor_id=id, value=switch.status, load=switch.loadDetect)
        records.append(record)

    db.session.bulk_save_objects(records)
    db.session.commit()
    L.info('Switch: data stored')
    return id


@celery.task()
def IR_sensor_query():
    records = []

    for ir, id in data_generator('IR'):
        record = IRSensorStatus(sensor_id=id, value=ir.status)
        records.append(record)

    db.session.bulk_save_objects(records)
    db.session.commit()
    L.info('IR: data stored')
    return id


@celery.task()
def AQI_sensor_query():
    records = []

    for aqi, id in data_generator('AQI'):
        record = AQIValues(sensor_id=id, temperature=aqi.temperature, humidity=aqi.humidity, pm25=aqi.pm, co2=aqi.co2, tvoc=aqi.tvoc, voc=aqi.voc)
        records.append(record)

    db.session.bulk_save_objects(records)
    db.session.commit()
    L.info('AQI: data stored')
    return id


@celery.task()
def Lux_sensor_query():
    records = []

    for luxdata, id in data_generator('Lux'):
        record = LuxValues(sensor_id=id, value=luxdata.lux)
        records.append(record)

    db.session.bulk_save_objects(records)
    db.session.commit()
    L.info('Lux: data stored')
    return id


