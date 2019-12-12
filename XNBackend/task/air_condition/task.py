import redis
import socket
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask import current_app
from XNBackend.task import celery, logger
from XNBackend.models import db, AirConditioner, IRSensors, MantunciBox
from XNBackend.api_client.air_conditioner import get_ac_data, set_ac_data
from XNBackend.task.utils import MantunsciRealTimePower, \
    ElectriConsumeHour, EnergyConsumeDay, get_mantunsci_addr_mapping

L = logger.getChild(__name__)


@celery.task()
def periodic_query_air_condition():
    devices_with_keys = {}
    for a in AirConditioner.query:
        devices_with_keys[a.device_index_code] = a

    device_codes = list(devices_with_keys.keys())
    all_data = get_ac_data(device_codes)
    if all_data.get('errMsg') == 'ok':
        for each_data in all_data['data']:
            the_device = devices_with_keys[each_data.get('deviceCode')]
            the_device.apply_values(each_data)
            db.session.flush()
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        L.exception(e)

    else:
        L.error(f'Fail to get ac data reason{all_data["errMsg"]}')


@celery.task()
def send_cmd_to_air_condition(device_index_code: str, **kwarg):
    ret = set_ac_data(device_index_code, **kwarg)
    return 0 if ret.get('errMsg') == 'ok' else 1


# TODO MOVE TO IR section
@celery.task()
def periodic_update_ir_status():
    ENGINE = create_engine('mysql+pymysql://xn:Pass1234@10.100.101.199:3306/xn?charset=utf8mb4',
                           echo=False)
    Session = sessionmaker(bind=ENGINE)
    session = Session()
    all_ir = session.query(IRSensors).order_by(IRSensors.tcp_config_id)
    client = None

    wrong_list = []
    for ir in all_ir:
        addr = hex(ir.addr_no).lstrip('0x').ljust(2, '0')
        ip = ir.tcp_config.ip
        data = bytes.fromhex(f'DA 00 {addr} 86 86 86 EE')

        if client is None or client.getpeername()[0] != ip:
            try:
                client.close()
            except Exception:
                pass

            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(5)
            client.connect((ip, 4196))

        print(f'addr {addr}, ip {ip}, data {data}')
        client.send(data)
        try:
            m = client.recv(1024)
            assert m[1] == 0
            ir.status = m[-2]
            ir.updated_at = datetime.now()
            session.commit()
        except AssertionError as e:
            print(e)
            wrong_list.append((ir.id, addr, int('0x'+addr, 0), ip))
        except Exception as e:
            print(e)
            wrong_list.append((ir.id, addr, int('0x'+addr, 0), ip))
    L.error(wrong_list)


# TODO MOVE TO OTHER PLACES
@celery.task()
def periodic_realtime_power():
    auth_param = {
        'auth_url': current_app.config['MANTUNSCI_AUTH_URL'],
        'username': current_app.config['MANTUNSCI_USERNAME'],
        'password': current_app.config['MANTUNSCI_PASSWORD'],
        'app_key': current_app.config['MANTUNSCI_APP_KEY'],
        'app_secret': current_app.config['MANTUNSCI_APP_SECRET'],
        'redirect_uri': current_app.config['MANTUNSCI_REDIRECT_URI'],
        'router_uri': current_app.config['MANTUNSCI_ROUTER_URI'],
        'project_code': current_app.config['MANTUNSCI_PROJECT_CODE']
    }
    mapping = get_mantunsci_addr_mapping()

    mbs = MantunciBox.query
    R = redis.Redis(host=current_app.config['REDIS_HOST'], port=current_app.config['REDIS_PORT'])
    for mb in mbs:
        realtime_mb_power = MantunsciRealTimePower(mb.mac, auth_param, R)
        realtime_mb_power.load_data_from_response(mapping)
        realtime_mb_power.save_data()


@celery.task()
def periodic_electricity_usage_hour():
    """每天凌晨1点同步昨天的每小时耗电量"""
    auth_param = {
        'auth_url': current_app.config['MANTUNSCI_AUTH_URL'],
        'username': current_app.config['MANTUNSCI_USERNAME'],
        'password': current_app.config['MANTUNSCI_PASSWORD'],
        'app_key': current_app.config['MANTUNSCI_APP_KEY'],
        'app_secret': current_app.config['MANTUNSCI_APP_SECRET'],
        'redirect_uri': current_app.config['MANTUNSCI_REDIRECT_URI'],
        'router_uri': current_app.config['MANTUNSCI_ROUTER_URI'],
        'project_code': current_app.config['MANTUNSCI_PROJECT_CODE']
    }
    mbs = MantunciBox.query
    session = db.session
    current_time = datetime.now()
    for mb in mbs:
        req_body = {
            "method": "GET_BOX_HOUR_POWER",
            "projectCode": auth_param['project_code'],
            'mac': mb.mac,
            'year': current_time.year,
            'month': current_time.month,
            'day': current_time.day
        }
        elec_hour = ElectriConsumeHour(mb.mac, auth_param, current_time.year,
                                       current_time.month, current_time.day, session, req_body)
        elec_hour.load_data_from_response()
        elec_hour.save_data()

