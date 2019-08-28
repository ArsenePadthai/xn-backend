from XNBackend.task import celery
from .task import ir_query 
from XNBackend.models.models import db, AutoControllers 


default_lux_value = 10000
default_aqi_value = 10000


def day_control(controller): 
    for swicth in Switches.query.filter_by(switch_panel_id=controller.switch_panel_id, level=0).order_by():
        for relay in Relay.query.filter_by(switch_id=switch.id).order_by():
            panel_relay_control.apply_async(args = [int(relay.device_index_code), relay.channel, 0, relay], queue = relay.tcp_config.ip+':'+str(relay.tcp_config.port))



def night_control(controller):
    for swicth in Switches.query.filter_by(switch_panel_id=controller.switch_panel_id).order_by():
        for relay in Relay.query.filter_by(switch_id=switch.id).order_by():
            panel_relay_control.apply_async(args = [int(relay.device_index_code), relay.channel, 0, relay], queue = relay.tcp_config.ip+':'+str(relay.tcp_config.port))


 
@celery.task()
def auto_control():
    is_day = 1 if time.strftime('%H%M%S')>='070000' and time.strftime('%H%M%S')<'220000' else 0
    for control in AutoControllers.query.filter_by(if_auto=1).order_by():
        ir_query.apply_async(args = [control, is_day], queue = control.ir_sensor.tcp_config.ip+':'+str(control.ir_sensor.tcp_config.port))
        if control.ir_count > 1
            control.if_auto = 0
        db.session.add(control)
        db.session.commit()



@celery.task()
def init_control():
    for control in AutoControllers.query.filter_by(if_auto=1).order_by():
        ir_query.apply_async(args = [control], queue = control.ir_sensor.tcp_config.ip+':'+str(control.ir_sensor.tcp_config.port))
        control.if_auto = 1
        db.session.add(control)
        db.session.commit()



