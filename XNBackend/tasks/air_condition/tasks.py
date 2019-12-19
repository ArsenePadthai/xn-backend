import socket
import time
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from XNBackend.tasks import celery, logger
from XNBackend.models import db, AirConditioner, IRSensors, MantunciBox
from XNBackend.api_client.air_conditioner import get_ac_data, set_ac_data

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


@celery.task()
def update_specific_air_condition(device_index_code):
    resp = get_ac_data([device_index_code])
    if resp['errCode'] == 0:
        device_data = resp['data'][0]
        ac = AirConditioner.query.filter(AirConditioner.device_index_code == device_index_code).first()
        ac.apply_values(device_data)
        db.session.commit()
        return {"code": 0, "message": "ok"}
    else:
        L.error(f'failed to get ac data for device index code {device_index_code}')


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


