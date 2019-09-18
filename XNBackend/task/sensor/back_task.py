import socket
import pickle
import sys
import time
from datetime import datetime
from threading import Thread, local as threading_local
from struct import pack, unpack
from celery.signals import worker_process_init
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker

from XNBackend.parser.protocol import data_parse
from XNBackend.task import celery, logger
from XNBackend.models.models import db, Locators, IRSensorStatus, IRSensors, \
AQIValues, AQISensors, LuxValues, LuxSensors, Switches, SwitchPanel, Relay, \
    RelayStatus, TcpConfig, AutoControllers


L = logger.getChild(__name__)
engine = create_engine('mysql+pymysql://test:test@127.0.0.1:3306/xn?charset=utf8mb4', echo=True)
Session = sessionmaker(bind=engine)
session = Session()

client = None


def tcp_client(host, port):
    global client
    try:
        client.close()
    except:
        pass
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(15)
        # client.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        # if hasattr(socket, "TCP_KEEPIDLE") and hasattr(socket, "TCP_KEEPINTVL") and hasattr(socket, "TCP_KEEPCNT"):
        #    client.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 10)
        #    client.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 5)
        #    client.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)
        client.connect((host, port))
        L.info('success Connected to %s: %s' % (host, port))
    except Exception:
        L.exception('failed to create tcp connetion')


def send_to_server(data, host, port):
    assert client is not None, 'TCP client not initialized'
    client.send(data)
    data_byte = client.recv(1024)
    tcp = TcpConfig.query.filter_by(ip=host, port=port).first()
    message = data_parse(data_byte, tcp.id)
    L.info('Received data: %s', message)
    return message


def keep_alive(ip, port, local_data):
    Session = sessionmaker(bind=engine)
    local_data.session = Session()
    while 1:
        try:
            client
        except NameError:
            time.sleep(3)
            continue

        # reprequisite: CAN receive response after sending query data
        panel = local_data.session.query(SwitchPanel).filter(SwitchPanel.tcp_config.has(ip = ip)).first()
        data = bytes.fromhex('DA {} {} 86 86 86 EE'.format(hex(panel.batch_no)[2:].rjust(2, '0'), hex(panel.addr_no)[2:].rjust(2,'0')))
        try:
            client.send(data)
        except Exception:
            L.exception(f'failed to send query data to panel {panel.id}')
        time.sleep(10)


def data_generate(model):
    models = {
        'Relay': [Relay, '55', '10 00 00 00 00'],
        'IR': [IRSensors, 'DA', '86 86 86 EE'],
        'AQI': [AQISensors, 'DA', '86 86 86 EE'],
        'Lux': [LuxSensors, 'DE', '86 86 86 EE']
    }

    if model == 'Relay':
        for sensor in models[model][0].query.order_by():
            data = bytes.fromhex(models[model][1]) + pack('>B', int(sensor.addr)) + bytes.fromhex(models[model][2]) + bytes.fromhex(hex(101+int(sensor.addr))[-2:])
            yield data, sensor
    else:
        for sensor in models[model][0].query.order_by():
            data = bytes.fromhex(models[model][1]) + pack('>B', sensor.batch_no) + pack('>B', sensor.addr_no) + bytes.fromhex(models[model][2])
            yield data, sensor


def day_control(control): 
    for switch in Switches.query.filter_by(switch_panel_id=control.switch_panel_id, channel=1).order_by():
        for relay in Relay.query.filter_by(switch_id=switch.id).order_by():
            network_relay_control.apply_async(args = [relay.id, relay.channel, 0], queue = relay.tcp_config.ip+':'+str(relay.tcp_config.port))
 


def night_control(control):
    panel = SwitchPanel.query.filter_by(id=control.switch_panel_id).first()
    if panel.panel_type == 0:
        for switch in Switches.query.filter_by(or_(channel==1, channel==2), switch_panel_id=control.switch_panel_id).order_by():
            for relay in Relay.query.filter_by(switch_id=switch.id).order_by():
                network_relay_control.apply_async(args = [relay.id, relay.channel, 0], queue = relay.tcp_config.ip+':'+str(relay.tcp_config.port))
    else:
        for switch in Switches.query.filter_by(switch_panel_id=control.switch_panel_id, channel=1).order_by():
            for relay in Relay.query.filter_by(switch_id=switch.id).order_by():
                network_relay_control.apply_async(args = [relay.id, relay.channel, 0], queue = relay.tcp_config.ip+':'+str(relay.tcp_config.port))


 
@celery.task(serializer='pickle')
def ir_query(control_id, auto, is_day=None):
    control = AutoControllers.query.filter_by(id=control_id).first()
    sensor = IRSensors.query.filter_by(batch_no=control.ir_sensor.batch_no, addr_no=control.ir_sensor.addr_no).first()
    data = bytes.fromhex('DA') + pack('>B', sensor.batch_no) + pack('>B', sensor.addr_no) + bytes.fromhex('86 86 86 EE')
    msg = send_to_server(data, sensor.tcp_config.ip, sensor.tcp_config.port)

    record = IRSensorStatus(sensor_id=control.ir_sensor_id, value=msg.detectValue, status=msg.status)
    db.session.add(record)
    db.session.flush()
    sensor.latest_record_id = record.id
    if msg.status == 1 and auto:
        control.ir_count += 1
    elif auto == False:
        control.ir_count = msg.status 
    db.session.commit()

    if control.ir_count > 1:
        if is_day == 1:
            day_control(control)
        elif is_day == 0:
            night_control(control)
        control.if_auto = 0
        db.session.commit()



@celery.task(bind=True, serializer='pickle')
def network_relay_control_sync(self, relay_id, channel, is_open):
    sensor = Relay.query.filter_by(id=relay_id).first()
    code = '32' if is_open else '31'
    data = bytes.fromhex('55') + pack('>B', sensor.addr) + bytes.fromhex(code + '00 00 00') + pack('>B', channel) + bytes.fromhex(hex(int(code, 16) + 85 + sensor.addr + channel)[-2:])

    client_temp = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    client_temp.connect((sensor.tcp_config.ip, sensor.tcp_config.port))
    try:
        client_temp.send(data)
    except Exception as e:
        L.error(e)
    try:
        client_temp.close()
    except:
        pass

'''    
@celery.task(bind=True, serializer='pickle')
def network_relay_control(self, id, channel, is_open):
    global client
    sensor = Relay.query.filter_by(id=id).first()
    code = '32' if is_open else '31'
    data = bytes.fromhex('55') + pack('>B', sensor.addr) + bytes.fromhex(code + '00 00 00') + pack('>B', channel) + bytes.fromhex(hex(int(code, 16) + 85 + sensor.addr + channel)[-2:])

    L.error(client.getpeername())
    L.error("Control relay, send '%s' to id: %d", data, sensor.id)
    try:
        L.error('try to send data to server')
        L.error(data)
        send_to_server(data, sensor.tcp_config.ip, sensor.tcp_config.port)
        recv_data = send_to_server(data, sensor.tcp_config.ip, sensor.tcp_config.port)
        L.info('Received data from relay at id of %s: %s', recv_data.id, recv_data)
    except Exception:
        L.exception('send to server part')
        client = None
        self.retry(countdown=3.0)
    
    if sensor.switch.channel == 1 or sensor.switch.channel == 4 and sensor.switch.switch_panel.panel_type == 0:
        control = AutoControllers.query.filter_by(switch_panel_id=sensor.switch.switch_panel_id).first()
        control.if_auto = 0
    elif sensor.switch.channel == 3 or sensor.switch.channel == 2 and sensor.switch.switch_panel.panel_type == 1:
        control = AutoControllers.query.filter_by(switch_panel_id=sensor.switch.switch_panel_id).first()
        if is_open:
            ir_query.apply_async(args = [control.id, False], queue = control.ir_sensor.tcp_config.ip+':'+str(control.ir_sensor.tcp_config.port))
        control.if_auto = is_open 
    record = RelayStatus(relay_id = sensor.id, value = (recv_data.status & (1 << channel-1)) != 0)
    db.session.add(record)
    db.session.flush()

    sensor.latest_record_id = record.id
    db.session.commit()
    L.info('Relay: control successfully')
'''    


@celery.task(serializer='pickle')
def handle_switch_signal(data):
    batch, addr, status = unpack('>B', data[1:2])[0], unpack('>B', data[2:3])[0], data[3:-1]
    panel = SwitchPanel.query.filter_by(batch_no = batch, addr_no = addr).first()
    if panel:
        for i in range(len(status)):
            value = unpack('>B', status[i:i+1])[0] & 0x11 
            if panel.panel_type == 0:
                switch = Switches.query.filter_by(channel = i+1, switch_panel_id = panel.id).first()
            else:
                if i == 2 or i == 3:
                    continue 
                else:
                    switch = Switches.query.filter_by(channel = i+1, switch_panel_id = panel.id).first()
            if switch == None or switch.status == value:
                continue
            for relay in Relay.query.filter_by(switch_id = switch.id).order_by():
                network_relay_control_sync.apply_async(args = [relay.id, relay.channel, value], queue = relay.tcp_config.ip+':'+str(relay.tcp_config.port))
            switch.status = value 

            try:
                db.session.commit()
            except:
                L.exception('db commit failure')
                db.session.rollback()
    else:
        L.error('No cooresponding panel found')



def client_recv(ip, port):
    recv_data = bytearray()
    while True:
        try:
            delta_data = client.recv(1024)
            if not delta_data:
                raise Exception('Zero Data Received, need to restart child processes pool')
            recv_data += delta_data
            if len(recv_data) > 255:
                raise Exception('%d bytes received, too long' % len(recv_data))
        except Exception:
            L.info('after 10s later, restart processes pool')
            time.sleep(10)
            L.exception('try to restart child processes pool...')
            celery.control.pool_restart(reload = True, destination=['worker@'+ip+':'+str(port)])

        while int(len(recv_data)/8):
            data, recv_data = recv_data[0:8], recv_data[8:]
            if data[0]!=219 or data[-1]!=238:
                recv_data = bytearray()
                continue
            handle_switch_signal.apply_async(args = [data], queue = ip+':'+str(port))
            

@worker_process_init.connect 
def configure_workers(sender=None, **kwargs):
    global client 
    try:
        assert '-n' in sys.argv, 'worker name must be assigned by -n'
        hostname = sys.argv[sys.argv.index('-n') + 1]
        addr = hostname.split('@')[1].split(':')
        if len(addr) < 2:
            return
        # for now, only consider light
        # for now, only consider light
        # for now, only consider light
        # TODO add compatibility to tcp servers of other sensor
        # tcp = session.query(TcpConfig).filter_by(ip = addr[0], port = int(addr[1])).first()
        # switch = session.query(SwitchPanel).filter_by(tcp_config_id = tcp.id).count()
        if addr[0] in ['10.100.102.1', '10.100.102.2', '10.100.102.4']:
            tcp_client(addr[0], int(addr[1]))
            d = threading_local()
            thread = Thread(target = client_recv, args=(addr[0], int(addr[1])))
            thread_ka = Thread(target = keep_alive, args=(addr[0], int(addr[1]), d))
            thread.daemon = True
            thread_ka.daemon = True
            thread.start()
            time.sleep(2)
            thread_ka.start()
    except Exception:
        L.exception('configure works failed')


@celery.task(bind=True, serializer='pickle')
def client_send(self, data):
    global client
    try:
        client.send(data)
    except Exception:
        L.exception('client_send error')
        client = None
        celery.control.pool_restart(destination=[self.request.hostname])
        self.retry(countdown=3.0)



@celery.task(bind=True, serializer='pickle')
def relay_panel_control(self, id, channel, is_open):
    data_pre = ''
    
    sensor = Relay.query.filter_by(id=id, channel=channel).first()
    panel = SwitchPanel.query.filter_by(id = sensor.switch.switch_panel_id).first()
    if panel.panel_type == 0:
        data = '0'+str(is_open)
        for switch in Switches.query.filter_by(switch_panel_id = panel.id).order_by():
            if switch.channel < sensor.switch.channel:
                data_pre += ('0'+str(switch.status))
            elif switch.channel > sensor.switch.channel:
                data += ('0'+str(switch.status))
    else: 
        for switch in Switches.query.filter_by(switch_panel_id = panel.id).order_by():
            if switch.channel < sensor.switch.channel:
                data = ('0'+str(switch.status))+('0'+str(is_open))+'0000'
            elif switch.channel > sensor.switch.channel:
                data = ('0'+str(is_open))+('0'+str(switch.status))+'0000'
 
    all_data = data_pre+data
    data_bytes = bytes.fromhex('DA')+pack('>B', panel.batch_no)+pack('>B', panel.addr_no)+pack('>B', 2)+bytes.fromhex(all_data)+bytes.fromhex('EE')
    client_send.apply_async(args = [data_bytes], queue = panel.tcp_config.ip+':'+str(panel.tcp_config.port))



@celery.task(bind=True, serializer='pickle')
def relay_query(self, query_data, id):
    global client
    sensor = Relay.query.filter_by(id=id).first()
    L.info("Query the status of relay, send '%s' to the server", query_data)
    try:
        data = send_to_server(query_data, sensor.tcp_config.ip, sensor.tcp_config.port)
    except Exception:
        L.exception('relay_query')
        client = None
        celery.control.pool_restart(destination=[self.request.hostname])
        self.retry(countdown=3.0)

    status = ((data.status & 1 << sensor.channel-1) != 0)
    relay_panel_control.apply_async(args = [sensor.addr, sensor.channel, status], queue = sensor.tcp_config.ip+':'+str(sensor.tcp_config.port))
    record = RelayStatus(relay_id=sensor.id, value=status) 
    db.session.add(record)
    db.session.flush()
    sensor.latest_record_id = record.id
    db.session.commit()
    return '' 



@celery.task(bind=True, serializer='pickle')
def sensor_query(self, sensor_name, query_data, id):
    global client
    task = {
        'IR':[IRSensorStatus, {
            'value': 'detectValue',
            'status': 'status'
        }, IRSensors], 
        'AQI':[AQIValues, {
            'temperature': 'temperature',
            'humidity': 'humidity',
            'pm25': 'pm25',
            'co2': 'co2',
            'tvoc': 'tvoc',
            'hcho': 'hcho'
        }, AQISensors], 
        'Lux':[LuxValues, {
            'value': 'lux'
        }, LuxSensors]
    }

    sensor = task[sensor_name][2].query.filter_by(id=id).first()
    L.info("Query the status of %s, send '%s' to the server", sensor_name, query_data)
    try:
        data = send_to_server(query_data, sensor.tcp_config.ip, sensor.tcp_config.port)
    except Exception:
        L.exception('sensor_query')
        client = None
        celery.control.pool_restart(destination=[self.request.hostname])
        self.retry(countdown=3.0)

    data_args = {
        k: getattr(data, v) for k,v in task[sensor_name][1].items()
    }
    record = task[sensor_name][0](sensor_id=sensor.id, **data_args)
    db.session.add(record)
    db.session.flush()
    sensor.latest_record_id = record.id
    db.session.commit()
    return '' 



@celery.task()
def tasks_route(sensor_name: str, channel, is_open, id=None, zone=None):
    if sensor_name == 'RelayControl':
        sensor = Relay.query.filter_by(addr=id, channel=channel).first()
        relay_panel_control.apply_async(args = [id, channel, is_open], queue = sensor.tcp_config.ip+':'+str(sensor.tcp_config.port))
    elif sensor_name == 'LocatorControl':
        locator = Locators.query.filter_by(zone = zone).first()
        panel = SwitchPanel.query.filter_by(locator_id = locator.internal_code).first()
        switch = Switches.query.filter_by(switch_panel_id = panel.id, channel = channel).first()
        for relay in Relay.query.filter_by(switch_id = switch.id).order_by():
            relay_panel_control.apply_async(args = [int(relay.addr), relay.channel, is_open], queue = relay.tcp_config.ip+':'+str(relay.tcp_config.port))
    else:
        for data, sensor in data_generate(sensor_name):
            if sensor_name == 'Relay':
                relay_query.apply_async(args = [data, sensor.id], queue = sensor.tcp_config.ip+':'+str(sensor.tcp_config.port))
            else:
                sensor_query.apply_async(args = [sensor_name, data, sensor.id], queue = sensor.tcp_config.ip+':'+str(sensor.tcp_config.port))

    L.info('data stored')
    return ''
 
