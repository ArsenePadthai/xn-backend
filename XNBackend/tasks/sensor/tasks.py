import socket
import sys
import time
from threading import Thread
from struct import pack, unpack
from celery.signals import worker_process_init
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from enum import Enum
from XNBackend.tasks import celery, logger
from XNBackend.models.models import db, Switches, SwitchPanel, Relay, Locators


L = logger.getChild(__name__)
ENGINE = create_engine('mysql+pymysql://xn:Pass1234@127.0.0.1:3306/xn?charset=utf8mb4', echo=True)

client = None


def tcp_client(host, port, block=True):
    global client
    try:
        client.close()
    except Exception:
        pass
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if not block:
        client.settimeout(15)
    client.connect((host, port))
    L.info('success Connected to %s: %s' % (host, port))


def keep_alive(ip):
    Session = sessionmaker(bind=ENGINE)
    session = Session()
    count = 0
    while 1:
        count += 1
        try:
            client
        except NameError:
            time.sleep(3)
            continue

        # require: CAN receive response after sending query data
        obj = session.query(SwitchPanel).filter(SwitchPanel.tcp_config.has(ip=ip)).first()
        data = bytes.fromhex('DA {} {} 86 86 86 EE'.format(hex(obj.batch_no)[2:].rjust(2, '0'),
                                                           hex(obj.addr_no)[2:].rjust(2, '0')))
        try:
            client.send(data)
            if count < 3:
                L.info('keep alive has sent data to client')
            if count == 1000:
                count = 0
        except Exception:
            L.exception(f'failed to send query data to panel {panel.id}')
        time.sleep(10)


class panel(Enum):
    fourType = 0
    doubleType = 1
    mainLight = 1
    acs = 2
    auto = 3
    auxLight = 4
    doubleAuto = 2


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
    try:
        assert data[0] == 219
        assert data[1] == 6
    except:
        L.error(f'corrupt data received, data: {data.hex()}, ignored')
        return
    the_panel = SwitchPanel.query.filter_by(addr_no=addr)\
        .filter(SwitchPanel.tcp_config.has(ip=ip)).first()
    if not the_panel:
        L.error(f'can not find the panel for ip {ip}')
        return
    
    for i in range(len(status)):
        value = unpack('>B', status[i:i+1])[0] & 0x11
        if i == 0:
            switch = Switches.query.filter_by(channel=i+1, switch_panel_id=the_panel.id).first()
        elif (i == 1 and the_panel.panel_type == 1) or (i == 2 and the_panel.panel_type == 0):
            room = Locators.query.filter(Locators.internal_code == the_panel.locator_id).first()
            prev_eco = room.eco_mode
            if prev_eco != value:
                room.eco_mode = value
                db.session.add(room)
            continue
        elif i == 3 and the_panel.panel_type == 0:
            switch = Switches.query.filter_by(channel=i + 1, switch_panel_id=the_panel.id).first()
        else:
            continue

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


def client_recv(ip, port):
    L.info(f'ip {ip} start to recv data......')
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
            L.exception('try to restart child processes pool...')
            L.info('after 10s later, restart processes pool')
            time.sleep(10)
            celery.control.pool_restart(reload=True, destination=['worker@'+ip+':'+str(port)])

        while int(len(recv_data)/8):
            data, recv_data = recv_data[0:8], recv_data[8:]
            if data[0] != 219 or data[-1] != 238:
                recv_data = bytearray()
                continue
            handle_switch_signal.apply_async(args=[data, ip], queue=ip+':'+str(port))


@worker_process_init.connect(retry=True)
def configure_workers(sender=None, **kwargs):
    try:
        assert '-n' in sys.argv, 'worker name must be assigned by -n'
        hostname = sys.argv[sys.argv.index('-n') + 1]
        if hostname == 'general':
            # do nothing
            return
        addr = hostname.split('@')[1].split(':')
        if len(addr) < 2:
            return
        L.info('==========================')
        L.info(f'start to configure worker: {hostname}, {addr}')
        L.info('==========================')
        # ir = session.query(IRSensors).filter(IRSensors.tcp_config.has(ip=addr[0])).first()
        tcp_client(addr[0], int(addr[1]), block=False)
        # use_for = 'ir' if ir else 'panel'
        thread = Thread(target=client_recv, args=(addr[0], int(addr[1])))
        thread_ka = Thread(target=keep_alive, args=(addr[0],))
        thread.daemon = True
        thread_ka.daemon = True
        thread.start()
        L.info('recv recv recv recv recv recv recv recv recv recv recv recv ')
        time.sleep(2)
        thread_ka.start()
        L.info('ka ka ka ka ka ka ka ka ka ka ka ka ka ka ka ka ka ka ka ')
    except Exception:
        L.exception('configure works failed')
        time.sleep(300)
        raise Exception('x')
