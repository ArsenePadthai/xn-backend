import socket
import random
from struct import pack
from XNBackend.task import celery
from XNBackend.models.models import db, IRSensorStatus, IRSensors, AQIValues, AQISensors, LuxValues, LuxSensors 
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


def address_pack(address):
    return pack('>Q' address & 0xffffffffff)[3:]


def generator_id(length):
    for i in range(length):
        yield i

    
@celery.task()
def network_relay_query():
    id_bytes = bytes.fromhex(hex(random.randint(1, 65535))[2:].rjust(4, '0'))
    data = bytes.fromhex('CC') + id_bytes + bytes.fromhex('FE EE')
    network_data = send_to_server(data)
    #network_record = 
    return str(network_data)

 
@celery.task()
def IR_sensor_query():
    records = []
    for items in generator_id(IRSensors.query.count):
        ir_sensor = IRSensors.query.filter_by(id = items).first()
        data = bytes.fromhex('DA') + address_pack(ir_sensor.address) + bytes.fromhex('86 86 86 EE')
        ir_data = send_to_server(data)
        ir_record = IRSensorStatus(sensor_id=ir_record._address, value=ir_data.status)
        records.append(ir_record)
    db.session.bulk_save_objects(records)
    db.session.commit()
    return str(ir_data)


@celery.task()
def AQI_sensor_query():
    data = bytes.fromhex('DC') + address_pack(3131413) + bytes.fromhex('86 86 86 EE')
    aqi_data = send_to_server(data)
    #aqi_record = AQIValues()
    return str(aqi_data.voc)


@celery.task()
def Lux_sensor_query():
    data = bytes.fromhex('DF') + address_pack(78568) + bytes.fromhex('86 86 86 EE')
    lux_data = send_to_server(data)
    #lux_record = LuxValues()
    return str(lux_data.lux)


