import redis
import json
import logging
import time
from XNBackend.tasks import celery
from XNBackend.tasks.air_condition.tasks import send_cmd_to_air_condition
from XNBackend.models import Locators, SwitchPanel, AirConditioner
from XNBackend.utils import get_redis_value, get_socket_client, is_work_time
from XNBackend.api_client.light import sp_control_light

L = logging.getLogger(__name__)
R = redis.Redis(host=celery.flask_app.config['REDIS_HOST'],
                port=celery.flask_app.config['REDIS_PORT'])


def execute_eco(room_no: str):
    sp = SwitchPanel.query.filter(SwitchPanel.locator_id == room_no).first()
    if not sp:
        L.error(f'can not find sp for room {room_no}')
    tcp_conn = get_socket_client(sp.tcp_config.ip, sp.tcp_config.port, 5)
    if not tcp_conn:
        L.error(f'failed to get tcp connection, ip: {sp.tcp_config.ip}')
    time.sleep(0.5)
    if is_work_time():
        sp_control_light(tcp_conn, sp, 0)
    else:
        sp_control_light(tcp_conn, sp, 0, 0)
    try:
        tcp_conn.close()
    except Exception as e:
        pass

    acs = AirConditioner.query.filter(AirConditioner.locator_id).all()
    for ac in acs:
        send_cmd_to_air_condition.apply_async(args=[ac.device_index_code], kwargs={"StartStopStatus": 0}, queue="general")


@celery.task
def eco_check():
    eco_rooms = Locators.query.filter(Locators.eco_mode == 1).filter(Locators.internal_code == '501').all()
    for eco_room in eco_rooms:
        room_no_str = eco_room.internal_code
        value = get_redis_value(R, 'IR_' + room_no_str)
        prev_ir_count = get_redis_value(R, "IRCOUNT_" + room_no_str) or 0
        if value is None:
            continue
        else:
            occupied = 1 in value[0]
            if occupied:
                # reset IRCOUNT = 0
                ir_count = 0
            else:
                # empty case
                ir_count = prev_ir_count + 1
                if ir_count == celery.flask_app.config['ECO_COUNT']:
                    execute_eco(room_no_str)
            R.set("IRCOUNT_" + room_no_str, json.dumps(ir_count))


@celery.task
def eco_reset():
    for key in R.keys('IRCOUNT_*'):
        R.delete(key)

