import redis
import socket
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from XNBackend.task import celery, logger
from XNBackend.models import db, AirConditioner, IRSensors, MantunciBox
from XNBackend.api_client.air_conditioner import get_ac_data, set_ac_data
from XNBackend.task.utils import MantunsciBoxReporter

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
        addr = hex(ir.addr_no).strip('0x').rjust(2, '0')
        ip = ir.tcp_config.ip
        data = bytes.fromhex(f'DA 00 {addr} 86 86 86 EE')

        if client is None or client.getpeername()[0] != ip:
            try:
                client.close()
            except Exception:
                pass

            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(10)
            client.connect((ip, 4196))

        client.send(data)
        try:
            m = client.recv(1024)
            assert m[1] == 0
            ir.status = m[-2]
            session.flush()
        except AssertionError as e:
            wrong_list.append((ir.id, addr, int('0x'+addr, 0), ip))
        except Exception as e:
            wrong_list.append((ir.id, addr, int('0x'+addr, 0), ip))
    try:
        session.commit()
    except Exception as e:
        L.exception(e)
        L.error('failed to save status to ir')
        session.rollback()
    L.error(wrong_list)


# TODO MOVE TO OTHER PLACES
@celery.task()
def periodic_get_realtime_power():
    mbs = MantunciBox.query.all()
    R = redis.Redis(host='127.0.0.1', port=6379)
    reporter = MantunsciBoxReporter(R, 'RTE', mbs)
    reporter.report()
