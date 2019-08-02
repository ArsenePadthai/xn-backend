from XNBackend.task import celery
from .task import data_generate, network_relay_control, sensor_query
from XNBackend.models.models import db, IREventCount, AQIEventCount, LuxEventCount, SwitchFlag, Switches


default_value = 10000

def sensor_light(sensor_name):  
    for data, sensor in data_generate(sensor_name):
        model = {
            'IR':[IREventCount, ir_id, status],
            'Lux':[LuxEventCount, lux_id, value],
            'AQI':[AQIEventCount, aqi_id, status],
        }

        sensor_query.apply_async(args = [sensor_name, data, sensor], queue = sensor.ip_config.ip+':'+str(sensor.ip_config.port))
        event = model[sensor_name][0].query.filter_by(model[sensor_name][1] = sensor.id).first()
        if sensor.latest_record.model[sensor_name][2] == 0 or sensor.latest_record.model[sensor_name][2]>= default_value:
            event.count += 1
        else:
            event.count = 0
        db.session.commit()

        if event.count > 1:
            for switch in Switches.query.filter_by(model[sensor_name][1] = sensor.id).all():
                flag = SwitchFlag.query.filter_by(switch_id = switch.id).first
                if flag.manual == 0 and flag.touch != 1:
                    network_relay_control.apply_async(args = [switch.device_index_code, switch.channel, 0], queue = sensor.ip_config.ip+':'+str(sensor.ip_config.port))
                    flag.touch = 1
                    flag.latest_status = 0
    db.session.commit()


def switch_light():
    for data, sensor in data_generate('Switch'):
        flag = SwitchFlag.query.filter_by(switch_id = sensor.id).first()
        if flag.touch == 0:
            sensor_query.apply_async(args = ['Switch', data, sensor], queue = sensor.ip_config.ip+':'+str(sensor.ip_config.port))
            flag.manual = 1 if flag.latest_status ==  0 and sensor.latest_record.value == 1 else 0
            flag.latest_status = sensor.latest_record.value 
    db.session.commit()

 
@celery.task()
def night_control():
    switch_light()
    sensor_light('IR')


@celery.task()
def day_control():
    switch_light()
    sensor_light('Lux')
