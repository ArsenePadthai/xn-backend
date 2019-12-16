import time
from XNBackend.tasks import celery
from .tasks import ir_query
from XNBackend.models.models import db, AutoControllers


default_lux_value = 10000
default_aqi_value = 10000


@celery.task()
def auto_control():
    is_day = 1 if time.strftime('%H%M%S')>='070000' and time.strftime('%H%M%S')<'220000' else 0
    for control in AutoControllers.query.filter_by(if_auto=1).order_by():
        ir_query.apply_async(args = [control.id, True, is_day], queue = control.ir_sensor.tcp_config.ip+':'+str(control.ir_sensor.tcp_config.port))



@celery.task()
def init_control():
    for control in AutoControllers.query.order_by():
        ir_query.apply_async(args = [control.id, False], queue = control.ir_sensor.tcp_config.ip+':'+str(control.ir_sensor.tcp_config.port))
        control.if_auto = 1
        db.session.commit()



