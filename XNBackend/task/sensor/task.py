import socket
import time
import pickle
from struct import pack
from XNBackend.task import celery, logger
from XNBackend.models.models import db, IRSensorStatus, IRSensors, AQIValues, AQISensors, LuxValues, LuxSensors, Switches, SwitchStatus
from XNBackend.parser.protocol import data_parse
from celery.signals import celeryd_init

L = logger.getChild(__name__)

client = None


def tcp_client(host, port):
    global client 
    client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    client.settimeout(5)
    client.connect((host, port))   
    L.info('Connected to %s: %s', host, port)
    

@celeryd_init.connect 
def configure_workers(sender=None, conf=None, **kwargs):
    if sender == 'worker@1':
        tcp_client('127.0.0.1', 51111)
    elif sender == 'worker@2':
        tcp_client('127.0.0.1', 51112)
    elif sender == 'worker@3':
        tcp_client('127.0.0.1', 51113)


def send_to_server(data, id):
    global client 
    try:
        client.send(data)
        data_byte = client.recv(1024)
        message = data_parse(data_byte)
        L.info('Received data: %s', message)
    except Exception:
        celery.control.broadcast('shutdown', destination=['worker@{}'.format(id)])
        celery.control.broadcast('shutdown', destination=['worker@{}'.format(id)])
        client = None
        L.error('Failed to connected, worker is restarted')

    return message


# def address_pack(address, n):
#     return pack('>Q', int(address) & 0xffffffffff)[n:]


def data_generate(model):
    models = {
        'Switch':[Switches, 'CC', 'FE EE'], 
        'IR':[IRSensors, 'DA', '86 86 86 EE'], 
        'AQI':[AQISensors, 'DC', '86 86 86 EE'], 
        'Lux':[LuxSensors, 'DE', '86 86 86 EE']
    }

    length = models[model][0].query.count()
    for items in range(length):
        sensor = models[model][0].query.filter_by(id = items+1).first()
        data = bytes.fromhex(models[model][1]) + pack('>H', int(sensor.device_index_code)) + bytes.fromhex(models[model][2])

        yield data, sensor


@celery.task(serializer='pickle')
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


@celery.task(serializer='pickle')
def network_relay_query(data, sensor):
    switch = send_to_server(data, sensor.id)
    L.info("Query the status of switch, send '%s' to the server", data)
    record = SwitchStatus(sensor_id=sensor.id, value=switch.status, load=switch.loadDetect)
    db.session.add(record)
    db.session.flush()
    sensor.latest_record_id = record.id
    db.session.add(sensor)
    db.session.commit()
    return record.id


@celery.task(serializer='pickle')
def IR_sensor_query(data, sensor):
    ir = send_to_server(data, sensor.id)
    L.info("Query the status of ir, send '%s' to the server", data)
    record = IRSensorStatus(sensor_id=sensor.id, value=ir.status)
    db.session.add(record)
    db.session.flush()
    sensor.latest_record_id = record.id
    db.session.add(sensor)
    db.session.commit()
    return record.id


@celery.task(serializer='pickle')
def AQI_sensor_query(data, sensor):
    aqi = send_to_server(data, sensor.id)
    L.info("Query the status of aqi, send '%s' to the server", data)
    record = AQIValues(sensor_id=sensor.id, temperature=aqi.temperature, humidity=aqi.humidity, pm25=aqi.pm, co2=aqi.co2, tvoc=aqi.tvoc, voc=aqi.voc)
    db.session.add(record)
    db.session.flush()
    sensor.latest_record_id = record.id
    db.session.add(sensor)
    db.session.commit()
    return record.id


@celery.task(serializer='pickle')
def Lux_sensor_query(data, sensor):
    luxdata = send_to_server(data, sensor.id)
    L.info("Query the status of lux, send '%s' to the server", data)
    record = LuxValues(sensor_id=sensor.id, value=luxdata.lux)
    db.session.add(record)
    db.session.flush()
    sensor.latest_record_id = record.id
    db.session.add(sensor)
    db.session.commit()
    return record.id


@celery.task()
def tasks_route(sensor_name: str):
    task = {
        'Switch':network_relay_query, 
        'IR':IR_sensor_query, 
        'AQI':AQI_sensor_query, 
        'Lux':Lux_sensor_query
    }

    for data, sensor in data_generate(sensor_name):
        task[sensor_name].apply_async(args=[data, sensor], queue=str(sensor.id))
        time.sleep(3)

    L.info('data stored')
    return ''
    
