import socket
import random
from XNBackend.task import celery
from XNBackend.models.models import db, IRSensorStatus, IRSensors, AQIValues, AQISensors, LuxValues, LuxSensors 
from sqlalchemy.dialects.mysql import insert


target_host = "127.0.0.1" 
target_port = 51113 
hik_client = None


def tcp_hik():
    global hik_client 
    if hik_client is None:   
        hik_client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        hik_client.settimeout(5)
        hik_client.connect((target_host,target_port))   
    return hik_client
    

def send_to_hik(data):
    global hik_client 
    try:
        client = tcp_hik()
        client.send(str(data).encode()[:-1])
        client.send(str(data).encode()[-1:])
        data_byte = client.recv(1024)
        '''
        Prevent connections from closing too fast and the RESET package sent by TCP will not be received.
        '''
    except Exception:
        celery.control.broadcast('shutdown', destination=['worker1@xn-hik.service'])
        hik_client = None
    return data_byte

    
@celery.task()
def network_relay_query():
    id_bytes = bytes.fromhex(hex(random.randint(1, 65535))[2:].rjust(4, '0'))
    data = bytes.fromhex('CC') + id_bytes + bytes.fromhex('FE EE')
    message = send_to_hik(data)
    network_data = data_parse(message)
    # network_record = 
    return str(network_data)

 
@celery.task()
def IR_sensor_query():
    data = bytes.fromhex('DA') + '000AAD2A33'.encode() + bytes.fromhex('86 86 86 EE')
    message = send_to_hik(data)
    ir_data = data_parse(message)
    # ir_record = IRSensorStatus()
    return str(ir_data)


@celery.task()
def AQI_sensor_query():
    data = bytes.fromhex('DC') + '000AAD2A33'.encode() + bytes.fromhex('86 86 86 EE')
    message = send_to_hik(data)
    aqi_data = data_parse(message)
    aqi_record = AQIValues()
    return str(aqi_data)


@celery.task()
def Lux_sensor_query():
    data = bytes.fromhex('DF') + '000AAD2A33'.encode() + bytes.fromhex('86 86 86 EE')
    message = send_to_hik(data)
    lux_data = data_parse(message)
    lux_record = LuxValues()
    return str(lux_data)


