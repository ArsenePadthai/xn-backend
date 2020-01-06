import redis
import json
import logging
import time
from XNBackend.tasks import celery
from XNBackend.models import Locators, SwitchPanel, AirConditioner
from XNBackend.utils import get_redis_value, get_socket_client
from XNBackend.api_client.light import sp_control_light
from XNBackend.api_client.air_conditioner import set_ac_data

L = logging.getLogger(__name__)
R = redis.Redis(host=celery.flask_app.config['REDIS_HOST'],
                port=celery.flask_app.config['REDIS_PORT'])


def execute_eco(room_no: str):
    sp = SwitchPanel.query.filter(SwitchPanel.locator_id == room_no).first()
    if not sp:
        L.error(f'can not find sp for room {room_no}')
    tcp_conn = get_socket_client(sp.tcp_config.ip, sp.tcp_config.port, 5)
    time.sleep(0.5)
    now = time.localtime()
    hour = now.tm_hour
    if 8 <= hour < 17:
        sp_control_light(tcp_conn, sp, 0)
    else:
        sp_control_light(tcp_conn, sp, 0, 0)
    try:
        tcp_conn.close()
    except Exception as e:
        pass

    acs = AirConditioner.query.filter(AirConditioner.locator_id).all()
    for ac in acs:
        set_ac_data(ac.device_index_code, ModeCmd=8)


@celery.task
def eco_check():
    eco_rooms = Locators.query.filter(Locators.eco_mode == 1).all()
    for eco_room in eco_rooms:
        room_no = eco_room.internal_code
        value = get_redis_value(R, 'IR_' + room_no)
        prev_ir_count = get_redis_value(R, "IRCOUNT_" + room_no) or 0
        if value is None:
            return
        else:
            occupied = value[0]
            if occupied and prev_ir_count==1:
                # reset IRCOUNT = 0
                ir_count = 0
            else:
                # empty case
                ir_count = prev_ir_count + 1
                if ir_count == 2:
                    execute_eco(room_no)
            R.set("IRCOUNT_" + room_no, json.dumps(ir_count))
