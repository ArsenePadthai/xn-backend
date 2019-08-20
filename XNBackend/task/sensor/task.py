import socket
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


def data_generate(model):
    models = {
        'Switch':[Switches, '55', '10 00 00 00 00'], 
        'IR':[IRSensors, 'DA', '86 86 86 EE'], 
        'AQI':[AQISensors, 'DC', '86 86 86 EE'], 
        'Lux':[LuxSensors, 'DE', '86 86 86 EE']
    }

    if model == 'Switch':
        for sensor in models[model][0].query.order_by():
            data = bytes.fromhex(models[model][1]) + pack('>B', int(sensor.device_index_code)) + bytes.fromhex(models[model][2]) + bytes.fromhex(hex(101+int(sensor.device_index_code))[-2:])
            yield data, sensor
    else:
        for sensor in models[model][0].query.order_by():
            data = bytes.fromhex(models[model][1]) + pack('>B', sensor.batch_no) + pack('>B', sensor.addr_no) + bytes.fromhex(models[model][2])
            yield data, sensor


@celery.task(bind=True, serializer='pickle')
def network_relay_control(self, id, channel, is_open, sensor):
    code = '12' if is_open else '11'
    data = bytes.fromhex('55') + pack('>B', id) + bytes.fromhex(code + '00 00 00') + pack('>B', channel) + bytes.fromhex(hex(int(code, 16) + 85 + id + channel)[-2:])

    L.info("Control switch, send '%s' to id: %d", data, id)
    try:
        recv_data = send_to_server(data, sensor.tcp_config.ip, sensor.tcp_config.port)
        L.info('Received data from Switch at id of %s: %s', recv_data.id, recv_data)
    except Exception:
        celery.control.pool_restart(destination=[self.request.hostname])
        self.retry(countdown=3.0)

    record = SwitchStatus(sensor_id = sensor.id, value = (recv_data.status & 1 << channel-1) != 0)
    db.session.add(record)
    db.session.flush()
    sensor.latest_record_id = record.id
    db.session.add(sensor)
    db.session.commit()
    L.info('Switch: control successfully')
    return ''


@celery.task(bind=True, serializer='pickle')
def sensor_query(self, sensor_name, query_data, sensor):
    task = {
        'Switch':[SwitchStatus, {
            'value': 'status',
        }],
        'IR':[IRSensorStatus, {
            'value': 'detectValue',
            'status': 'status'
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
        data = send_to_server(query_data, sensor.tcp_config.ip, sensor.tcp_config.port)
    except Exception:
        celery.control.pool_restart(destination=[self.request.hostname])
        self.retry(countdown=3.0)

    if sensor_name == 'Switch':
        data_args = {'value': (data.status & 1 << sensor.channel-1) != 0}
    else:
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
def tasks_route(sensor_name: str, id=None, channel=None, is_open=True):
    if sensor_name == 'SwitchControl':
        sensor = Switches.query.filter_by(device_index_code = id, channel = channel).first()
        network_relay_control.apply_async(args = [id, channel, is_open, sensor], queue = sensor.tcp_config.ip+':'+str(sensor.tcp_config.port))
    else:
        for data, sensor in data_generate(sensor_name):
            sensor_query.apply_async(args = [sensor_name, data, sensor], queue = sensor.tcp_config.ip+':'+str(sensor.tcp_config.port))

    L.info('data stored')
    return ''
    
