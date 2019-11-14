import socket
import sys
import time
from threading import Thread
from struct import pack, unpack
from celery.signals import worker_process_init
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from enum import Enum

from XNBackend.parser.protocol import data_parse
from XNBackend.task import celery, logger
from XNBackend.models.models import db, Locators, IRSensorStatus, IRSensors, \
    AQIValues, AQISensors, LuxValues, LuxSensors, Switches, SwitchPanel, \
    Relay, TcpConfig, AutoControllers


L = logger.getChild(__name__)
ENGINE = create_engine('mysql+pymysql://xn:Pass1234@127.0.0.1:3306/xn?charset=utf8mb4', echo=True)

client = None


def tcp_client(host, port):
    global client
    try:
        client.close()
    except Exception:
        pass
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(15)
    client.connect((host, port))
    L.info('success Connected to %s: %s' % (host, port))


def send_to_server(data, host, port):
    assert client is not None, 'TCP client not initialized'

    try:
        client.send(data)
        data_byte = client.recv(1024)
        tcp = TcpConfig.query.filter_by(ip=host, port=port).first()
        message = data_parse(data_byte, tcp.id)
        L.info('Received data: %s', message)
    except Exception as e:
        L.error(e)
        L.info('after 5s later, restart processes pool')
        time.sleep(5)
        L.exception('try to restart child processes pool...')
        celery.control.pool_restart(reload=True, destination=['worker@'+host+':'+str(port)])

    return message


def data_generate(model):
    models = {
        'Relay': [Relay, '55', '10 00 00 00 00'],
        'IR': [IRSensors, 'DA', '86 86 86 EE'],
        'AQI': [AQISensors, 'DA', '86 86 86 EE'],
        'Lux': [LuxSensors, 'DE', '86 86 86 EE']
    }

    if model == 'Relay':
        for sensor in models[model][0].query.order_by():
            data = bytes.fromhex(models[model][1])
            + pack('>B', int(sensor.addr))
            + bytes.fromhex(models[model][2])
            + bytes.fromhex(hex(101+int(sensor.addr))[-2:])
            yield data, sensor
    else:
        for sensor in models[model][0].query.order_by():
            data = bytes.fromhex(models[model][1])
            + pack('>B', sensor.batch_no)
            + pack('>B', sensor.addr_no)
            + bytes.fromhex(models[model][2])
            yield data, sensor 


def keep_alive(ip, port):
    Session = sessionmaker(bind=ENGINE)
    session = Session()
    while 1:
        try:
            client
        except NameError:
            time.sleep(3)
            continue

        # require: CAN receive response after sending query data
        panel = session.query(SwitchPanel).filter(
            SwitchPanel.tcp_config.has(ip=ip)
            ).first()
        data = bytes.fromhex('DA {} {} 86 86 86 EE'
                             .format(hex(panel.batch_no)[2:].rjust(2, '0'),
                                     hex(panel.addr_no)[2:].rjust(2, '0')))
        try:
            client.send(data)
        except Exception:
            L.exception(f'failed to send query data to panel {panel.id}')
        time.sleep(10)


def day_control(control_id): 
    control = AutoControllers.query.filter_by(id=control_id).first()
    for switch in Switches.query.filter_by(switch_panel_id=control.switch_panel_id,
                                           channel=1).order_by():
        for relay in Relay.query.filter_by(switch_id=switch.id).order_by():
            relay_panel_control.apply_async(args=[relay.id, 0], queue='relay')


def night_control(control_id):
    control = AutoControllers.query.filter_by(id=control_id).first()
    panel = SwitchPanel.query.filter_by(id=control.switch_panel_id).first()
    if panel.panel_type == 0:
        for switch in Switches.query.filter(or_(Switches.channel == 1, Switches.channel == 2),
                                            switch_panel_id=control.switch_panel_id).order_by():
            for relay in Relay.query.filter_by(switch_id=switch.id).order_by():
                relay_panel_control.apply_async(args=[relay.id, 0], queue='relay')
    else:
        for switch in Switches.query.filter_by(switch_panel_id=control.switch_panel_id,
                                               channel=1).order_by():
            for relay in Relay.query.filter_by(switch_id=switch.id).order_by():
                relay_panel_control.apply_async(args=[relay.id, 0], queue='relay')


@celery.task(serializer='pickle')
def ir_query(control_id, auto, is_day=None):
    try:
        control = AutoControllers.query.filter_by(id=control_id).first()
        sensor = IRSensors.query.filter_by(batch_no=control.ir_sensor.batch_no,
                                       addr_no=control.ir_sensor.addr_no).first()
        data = bytes.fromhex('DA') + pack('>B', sensor.batch_no) + pack('>B', sensor.addr_no)
        + bytes.fromhex('86 86 86 EE')
    except Exception as e:
        L.error(e)
        pass 

    try:
        msg = send_to_server(data, sensor.tcp_config.ip, sensor.tcp_config.port)
        record = IRSensorStatus(sensor_id=control.ir_sensor_id,
                                value=msg.detectValue,
                                status=msg.status)
        db.session.add(record)
        db.session.flush()
        sensor.latest_record_id = record.id
        if msg.status == 0 and auto:
            control.ir_count += 1
        elif auto is False:
            control.ir_count = 0 if msg.status else 1
        db.session.commit()
    except Exception as e:
        L.error(e)
        L.exception('Records update failure')
        db.session.rollback()

    if control.ir_count > 1:
        if is_day == 1:
            day_control(control.id)
        elif is_day == 0:
            night_control(control.id)


class panel(Enum):
    fourType = 0
    doubleType = 1 
    mainLight = 1
    acs = 2
    auto = 3
    auxLight = 4
    doubleAuto = 2


@celery.task(serializer='pickle')
def auto_change(relay_id, is_open):
    pass
    # try:
    #     sensor = Relay.query.filter_by(id=relay_id).first()
    #     if sensor.switch.channel == panel.mainLight or sensor.switch.channel == panel.auxLight and sensor.switch.switch_panel.panel_type == panel.fourType:
    #         control = AutoControllers.query.filter_by(switch_panel_id=sensor.switch.switch_panel_id).first()
    #         control.if_auto = 0
    #     elif sensor.switch.channel == panel.auto or sensor.switch.channel == panel.doubleAuto and sensor.switch.switch_panel.panel_type == panel.doubleType:
    #         control = AutoControllers.query.filter_by(switch_panel_id=sensor.switch.switch_panel_id).first()
    #         if is_open:
    #             L.info('Start auto control')
    #             ir_query.apply_async(args = [control.id, False], queue = control.ir_sensor.tcp_config.ip+':'+str(control.ir_sensor.tcp_config.port))
    #         control.if_auto = is_open
    # except Exception as e:
    #     L.error(e)
    #     pass
    # else:
    #     try:
    #         record = RelayStatus(relay_id=sensor.id, value=is_open)
    #         db.session.add(record)
    #         db.session.flush()
    #         sensor.latest_record_id = record.id
    #         db.session.commit()
    #         L.info('Record relay status successfully')
    #     except:
    #         L.exception('db commit failure')
    #         db.session.rollback()


@celery.task(serializer='pickle')
def network_relay_control_sync(relay_id, is_open):
    sensor = Relay.query.filter_by(id=relay_id).first()
    code = '32' if is_open else '31'
    data = bytes.fromhex('55') + pack('>B', sensor.addr) + bytes.fromhex(code + '00 00 00') + pack('>B',sensor.channel) + bytes.fromhex(hex(int(code, 16) + 85 + sensor.addr + sensor.channel)[-2:])

    client_temp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_temp.connect((sensor.tcp_config.ip, sensor.tcp_config.port))
    try:
        client_temp.send(data)
    except Exception as e:
        L.error(e)
    try:
        client_temp.close()
    except Exception:
        pass


@celery.task(serializer='pickle')
def handle_switch_signal(data, ip):
    addr, status = unpack('>B', data[2:3])[0], data[3:-1]
    panel = SwitchPanel.query.filter_by(addr_no=addr).filter(SwitchPanel.tcp_config.has(ip=ip)).first()
    if panel:
        for i in range(len(status)):
            value = unpack('>B', status[i:i+1])[0] & 0x11 
            if panel.panel_type == 0:
                switch = Switches.query.filter_by(channel=i+1, switch_panel_id=panel.id).first()
            else:
                if i == 2 or i == 3:
                    continue
                else:
                    switch = Switches.query.filter_by(channel=i+1, switch_panel_id=panel.id).first()
            if switch is None or switch.status == value:
                continue
            for relay in Relay.query.filter_by(switch_id=switch.id).order_by():
                network_relay_control_sync.apply_async(args=[relay.id, value], queue='relay')
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
                raise Exception(f'{len(recv_data)} bytes received, too long')
        except Exception:
            L.info('after 10s later, restart processes pool')
            time.sleep(10)
            L.exception('try to restart child processes pool...')
            celery.control.pool_restart(reload=True, destination=['worker@'+ip+':'+str(port)])

        while int(len(recv_data)/8):
            data, recv_data = recv_data[0:8], recv_data[8:]
            if data[0] != 219 or data[-1] != 238:
                recv_data = bytearray()
                continue
            handle_switch_signal.apply_async(args=[data, ip], queue=ip+':'+str(port))


@worker_process_init.connect(retry=True)
def configure_workers(sender=None, **kwargs):
    Session = sessionmaker(bind=ENGINE)
    session = Session()
    try:
        assert '-n' in sys.argv, 'worker name must be assigned by -n'
        hostname = sys.argv[sys.argv.index('-n') + 1]
        if hostname == 'general':
            return
        addr = hostname.split('@')[1].split(':')
        if len(addr) < 2:
            return
        L.error('==========================')
        L.error(f'start to configure worker: {hostname}, {addr}')
        L.error('==========================')
        tcp_client(addr[0], int(addr[1]))
        sensor = session.query(IRSensors).filter(
            IRSensors.tcp_config.has(ip=addr[0])
            ).first()
        if sensor is None:
            thread = Thread(target=client_recv, args=(addr[0], int(addr[1])))
            thread_ka = Thread(target=keep_alive, args=(addr[0], int(addr[1])))
            thread.daemon = True
            thread_ka.daemon = True
            thread.start()
            time.sleep(2)
            thread_ka.start()
    except Exception:
        L.exception('configure works failed')
        time.sleep(300)
        raise Exception('x')



@celery.task(bind=True, serializer='pickle')
def client_send(self, data):
    global client
    try:
        client.send(data)
    except Exception as e:
        L.exception('client_send error')
        L.error(e)
        celery.control.pool_restart(reload=True, destination=[self.request.hostname])


@celery.task(serializer='pickle')
def relay_panel_control(relay_id, is_open):
    data_pre = ''

    try:
        sensor = Relay.query.filter_by(id=relay_id).first()
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
    except Exception as e:
        L.error(e)
        pass 
 
    all_data = data_pre+data
    data_bytes = bytes.fromhex('DA')+pack('>B', panel.batch_no)+pack('>B', panel.addr_no)+pack('>B', 2)+bytes.fromhex(all_data)+bytes.fromhex('EE')
    client_send.apply_async(args = [data_bytes], queue = panel.tcp_config.ip+':'+str(panel.tcp_config.port))



# @celery.task(bind=True, serializer='pickle')
# def relay_query(self, query_data, id):
#     sensor = Relay.query.filter_by(id=id).first()
#     L.info("Query the status of relay, send '%s' to the server", query_data)
#     try:
#         client_temp = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
#         client_temp.connect((sensor.tcp_config.ip, sensor.tcp_config.port))
#         client_temp.send(query_data)
#         data_byte = client_temp.recv(1024)
#     except Exception as e:
#         L.exception('relay_query error')
#         L.error(e)
#     try:
#         client_temp.close()
#     except Exception:
#         pass

#     if len(data_byte) == 8 and data_byte[0] == 34: 
#         data = data_parse(data_byte)
#     else:
#         pass 
#     status = ((data.status & 1 << sensor.channel-1) != 0)
#     relay_panel_control.apply_async(args=[sensor.id, status], queue='relay')
#     record = RelayStatus(relay_id=sensor.id, value=status) 
#     db.session.add(record)
#     db.session.flush()
#     sensor.latest_record_id = record.id
#     try:
#         db.session.commit()
#     except:
#         L.exception('db commit failure')
#         db.session.rollback()



@celery.task(bind=True, serializer='pickle')
def sensor_query(self, sensor_name, query_data, id):
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
    except Exception as e:
        L.error('sensor_query')
        L.error(e)
        celery.control.pool_restart(reload=True, destination=[self.request.hostname])

    data_args = {
        k: getattr(data, v) for k,v in task[sensor_name][1].items()
    }
    record = task[sensor_name][0](sensor_id=sensor.id, **data_args)
    db.session.add(record)
    db.session.flush()
    sensor.latest_record_id = record.id
    db.session.commit()


@celery.task()
def tasks_route(sensor_name: str, channel, is_open, relay_id=None, zone=None):
    if sensor_name == 'RelayControl':
        network_relay_control_sync.apply_async(args=[relay_id, is_open], queue='relay')
    elif sensor_name == 'LocatorControl':
        panel = SwitchPanel.query.filter(SwitchPanel.locator_id == zone).first()
        if not panel:
            L.error(f'for zone {zone}, no panel can be found!')
            return
        switch = Switches.query.filter_by(switch_panel_id=panel.id, channel=channel).first()
        for relay in Relay.query.filter_by(switch_id=switch.id).order_by():
            network_relay_control_sync.apply_async(args=[relay.id, is_open], queue='relay')
            L.info(f'remote control light-delay {relay.id}')
    # else:
    #     for data, sensor in data_generate(sensor_name):
    #         if sensor_name == 'Relay':
    #             relay_query.apply_async(args=[data, sensor.id], queue='relay')
    #         else:
    #             sensor_query.apply_async(args=[sensor_name, data, sensor.id], queue=sensor.tcp_config.ip+':'+str(sensor.tcp_config.port))

    # L.info('data stored')
