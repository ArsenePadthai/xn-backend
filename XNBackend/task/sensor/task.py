import socket
import random
from struct import pack
from XNBackend.task import celery
from XNBackend.models.models import db, IRSensorStatus, IRSensors, AQIValues, AQISensors, LuxValues, LuxSensors, Switches, SwitchStatus
from XNBackend.parser.protocol import data_parse


target_host = "127.0.0.1" 
target_port = 51113 
client = None


def tcp_client():
    global client 
    if client is None:   
        client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        client.settimeout(5)
        client.connect((target_host,target_port))   
    return client
    

def send_to_server(data):
    global client 
    try:
        client = tcp_client()
        client.send(str(data).encode()[:-1])
        client.send(str(data).encode()[-1:])
        data_byte = client.recv(1024)
        '''
        Prevent connections from closing too fast and the RESET package sent by TCP will not be received.
        '''
    except Exception:
        celery.control.broadcast('shutdown', destination=['worker1@xn-hik.service'])
        client = None
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
        sensor = models[model][0].query.filter_by(id = items+1).first()
        data = bytes.fromhex(models[model][1]) + address_pack(sensor.device_index_code, models[model][2]) + bytes.fromhex(models[model][3])
        recv_data = send_to_server(data)
        yield recv_data, sensor.id


@celery.task()
def network_relay_control(id, channel, code):
    data = bytes.fromhex('AA') + bytes.fromhex(id) + bytes.fromhex(channel) + bytes.fromhex(code) + bytes.fromhex('EE')
    recv_data = send_to_server(data)
    switch = Switches.query.filter_by(device_index_code = recv_data.id).first()
    record = SwitchStatus(sensor_id=switch.id, value=recv_data.status, load=recv_data.loadDetect)
    db.session.add(record)
    db.session.commit()
    return switch.id


@celery.task()
def network_relay_query():
    records = []
    for object, id in data_generator('Switch'):
        record = SwitchStatus(sensor_id=id, value=object.status, load=object.loadDetect)
        records.append(record)
    db.session.bulk_save_objects(records)
    db.session.commit()
    return id


@celery.task()
def IR_sensor_query():
    records = []
    for object, id in data_generator('IR'):
        record = IRSensorStatus(sensor_id=id, value=object.status)
        records.append(record)
    db.session.bulk_save_objects(records)
    db.session.commit()
    return id


@celery.task()
def AQI_sensor_query():
    records = []
    for object, id in data_generator('AQI'):
        record = AQIValues(sensor_id=id, temperature=object.temperature, humidity=object.humidity, pm25=object.pm, co2=object.co2, tvoc=object.tvoc, voc=object.voc)
        records.append(record)
    db.session.bulk_save_objects(records)
    db.session.commit()
    return id


@celery.task()
def Lux_sensor_query():
    records = []
    for object, id in data_generator('Lux'):
        record = LuxValues(sensor_id=id, value=object.lux)
        records.append(record)
    db.session.bulk_save_objects(records)
    db.session.commit()
    return id


