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
def configure_workers(sender=None, **kwargs):
    global client
    try:
        addr = sender.split('@')[1].split(':')
        tcp_client(addr[0], int(addr[1]))
    except Exception:
        client = None


def send_to_server(data, host, port):
    if client == None:
        tcp_client(host, port)
    client.send(data)
    data_byte = client.recv(1024)
    message = data_parse(data_byte)
    L.info('Received data: %s', message)

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

    for sensor in models[model][0].query.order_by():
        data = bytes.fromhex(models[model][1]) + pack('>B', sensor.batch_no) + pack('>B', sensor.addr_no)+ bytes.fromhex(models[model][2])
        yield data, sensor


@celery.task(bind=True, serializer='pickle')
def network_relay_control(self, id, channel, code):
    data = bytes.fromhex('AA') + pack('>H', id) + pack('>B', channel) + pack('>B', code) + bytes.fromhex('EE')

    L.info("Control switch, send '%s' to id: %d", data, id)
    try:
        recv_data = send_to_server(data)
        L.info('Received data from Switch at id of %s: %s', recv_data.id, recv_data)
    except Exception:
        celery.control.pool_restart(destination=[self.request.hostname])
        self.retry(countdown=3.0)

    switch = Switches.query.filter_by(device_index_code = recv_data.id).first()
    record = SwitchStatus(sensor_id=switch.id, value=recv_data.status, load=recv_data.loadDetect)
    db.session.add(record)
    db.session.flush()
    switch.latest_record_id = record.id
    db.session.add(switch)
    db.session.commit()
    L.info('Switch: control successfully')
    return ''


@celery.task(bind=True, serializer='pickle')
def sensor_query(self, sensor_name, query_data, sensor):
    task = {
        'Switch':[SwitchStatus, {
            'value': 'status',
            'load': 'loadDetect'
        }],
        'IR':[IRSensorStatus, {
            'value': 'status'
        }], 
        'AQI':[AQIValues, {
            'temperature': 'temperature',
            'humidity': 'humidity',
            'pm25': 'pm',
            'co2': 'co2',
            'tvoc': 'tvoc',
            'voc': 'voc'
        }], 
        'Lux':[LuxValues, {
            'value': 'lux'
        }]
    }

    L.info("Query the status of %s, send '%s' to the server", sensor_name, query_data)
    try:
        data = send_to_server(query_data, sensor.ip_config.ip, sensor.ip_config.port)
    except Exception:
        celery.control.pool_restart(destination=[self.request.hostname])
        self.retry(countdown=3.0)

    data_args = {
        k: getattr(data, v) for k,v in task[sensor_name][1].items()
    }
    record = task[sensor_name][0](sensor_id=sensor.id, **data_args)
    db.session.add(record)
    db.session.flush()
    sensor.latest_record_id = record.id
    db.session.add(sensor)
    db.session.commit()
    return ''


@celery.task()
def tasks_route(sensor_name: str, id=None, channel=None, code=None):
    if sensor_name == 'SwitchControl':
        sensor = Switches.query.filter_by(id = id).first()
        network_relay_control.apply_async(args = [id, channel, code], queue = sensor.ip_config.ip+':'+str(sensor.ip_config.port))

    for data, sensor in data_generate(sensor_name):
        sensor_query.apply_async(args = [sensor_name, data, sensor], queue = sensor.ip_config.ip+':'+str(sensor.ip_config.port))

    L.info('data stored')
    return ''
    
