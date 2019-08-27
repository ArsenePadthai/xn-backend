import socket
import pickle
from threading import Thread
from struct import pack, unpack 
from XNBackend.task import celery, logger
from XNBackend.models.models import db, IRSensorStatus, IRSensors, AQIValues, AQISensors, LuxValues, LuxSensors, Switches, SwitchPanel, Relay, RelayStatus, TcpConfig
from XNBackend.parser.protocol import data_parse
from celery.signals import celeryd_init
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


L = logger.getChild(__name__)
engine = create_engine('mysql+pymysql://test:test@127.0.0.1:3306/xn?charset=utf8mb4', echo=True)
Session = sessionmaker(bind=engine)
session = Session()

client = None


def tcp_client(host, port):
    global client 
    client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    client.settimeout(5)
    client.connect((host, port))   
    L.info('Connected to %s: %s', host, port)
    

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
        'Switch':[Relay, '55', '10 00 00 00 00'], 
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


def network_relay_control(id, channel, is_open, sensor):
    code = '12' if is_open else '11'
    data = bytes.fromhex('55') + pack('>B', id) + bytes.fromhex(code + '00 00 00') + pack('>B', channel) + bytes.fromhex(hex(int(code, 16) + 85 + id + channel)[-2:])

    L.info("Control switch, send '%s' to id: %d", data, id)
    recv_data = send_to_server(data, sensor.tcp_config.ip, sensor.tcp_config.port)
    L.info('Received data from Switch at id of %s: %s', recv_data.id, recv_data)

    record = RelayStatus(relay_id = sensor.id, value = (recv_data.status & 1 << channel-1) != 0)
    db.session.add(record)
    db.session.flush()
    sensor.latest_record_id = record.id
    db.session.add(sensor)
    db.session.commit()
    L.info('Switch: control successfully')


@celery.task(bind=True, serializer='pickle')
def panel_relay_control(self, id, channel, is_open, sensor):
    try:
        network_relay_control(id, channel, is_open, sensor)
    except Exception:
        celery.control.pool_restart(destination=[self.request.hostname])
        self.retry(countdown=3.0)

    return ''


def client_recv():
    client.setblocking(1)
    while True:
        data = client.recv(1024)
        print(data)
        startcode, batch, addr, status = unpack('>B', data[:1])[0], unpack('>B', data[1:2])[0], unpack('>B', data[2:3])[0], data[3:-1]
        panel = session.query(SwitchPanel).filter_by(batch_no = batch, addr_no = addr).first()
        for i in range(len(status)):
            value = unpack('>B', status[i:i+1])[0] & 0x11 
            switch = session.query(Switches).filter_by(channel = i+1, switch_panel_id = panel.id).first()
            if switch == None:
                continue
            for relay in session.query(Relay).filter_by(switch_id = switch.id).order_by():
                is_open = 1 if value else 0 
                panel_relay_control.apply_async(args = [int(relay.device_index_code), i+1, is_open, relay], queue = relay.tcp_config.ip+':'+str(relay.tcp_config.port))
            switch.status = value 
            session.add(switch)
            session.commit()


@celeryd_init.connect 
def configure_workers(sender=None, **kwargs):
    global client 
    try:
        addr = sender.split('@')[1].split(':')
        tcp_client(addr[0], int(addr[1]))
        tcp = session.query(TcpConfig).filter_by(ip = addr[0], port = int(addr[1])).first()
        switch = session.query(SwitchPanel).filter_by(tcp_config_id = tcp.id).count()
        if switch != 0:
            thread = Thread(target = client_recv)
            thread.daemon=True
            thread.start()
    except Exception:
        client = None


@celery.task(bind=True)
def client_send(self, data):
    try:
        client.send(data)
    except Exception:
        celery.control.pool_restart(destination=[self.request.hostname])
        self.retry(countdown=3.0)


@celery.task(bind=True, serializer='pickle')
def relay_panel_control(self, id, channel, is_open, sensor):
    data_pre = ''
    try:
        network_relay_control(id, channel, is_open, sensor)
    except Exception:
        celery.control.pool_restart(destination=[self.request.hostname])
        self.retry(countdown=3.0)

    data = pack('>B', is_open)
    for panel in Switches.query.filter_by(switch_panel_id = sensor.switch.switch_panel_id).order_by():
        if panel.channel < sensor.channel:
            data_pre += pack('>B', panel.status)
        elif panel.channel > sensor.channel:
            data += pack('>B', panel.status)

    all_data = (data_pre+data).ljust(4, pack('>B', 0))
    data_bytes = bytes.fromhex('DA')+pack('>B', sensor.switch.switch_panel.batch_no)+pack('>B', sensor.switch.switch_panel.addr_no)+pack('>B', 2)+all_data+bytes.fromhex('EE')
    client_send.apply_async(args = [data_bytes], queue = panel.switch_panel.tcp_config.ip+':'+str(panel.switch_panel.tcp_config.port))



@celery.task(bind=True, serializer='pickle')
def sensor_query(self, sensor_name, query_data, sensor):
    task = {
        'Switch':[RelayStatus, {
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
def tasks_route(sensor_name: str, id=None, channel=None, is_open=None):
    if sensor_name == 'SwitchControl':
        sensor = Relay.query.filter_by(device_index_code = id, channel = channel).first()
        relay_panel_control.apply_async(args = [id, channel, is_open, sensor], queue = sensor.tcp_config.ip+':'+str(sensor.tcp_config.port))
    else:
        for data, sensor in data_generate(sensor_name):
            sensor_query.apply_async(args = [sensor_name, data, sensor], queue = sensor.tcp_config.ip+':'+str(sensor.tcp_config.port))

    L.info('data stored')
    return ''
 

