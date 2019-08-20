from XNBackend.task import celery
from .task import data_generate, network_relay_control, sensor_query
from XNBackend.models.models import db, IREventCount, AQIEventCount, LuxEventCount, SwitchFlag, Switches


default_lux_value = 10000
default_aqi_value = 10000

def sensor_light(sensor_name):  
    model = {
        'IR':[IREventCount, ir_id],
        'Lux':[LuxEventCount, lux_id],
        'AQI':[AQIEventCount, aqi_id]
    }

    for data, sensor in data_generate(sensor_name):
        sensor_query.apply_async(args = [sensor_name, data, sensor], queue = sensor.ip_config.ip+':'+str(sensor.ip_config.port))
        event = model[sensor_name][0].query.filter_by(model[sensor_name][1] = sensor.id).first()
        branch = lambda name:sensor.latest_record.status==0 if name=='IR' else sensor.latest_record.value>=default_lux_value if name=='Lux' else sensor.latest_record.pm25>=default_aqi_value 
        if branch(sensor_name):
            event.count += 1
        else:
            event.count = 0
        db.session.commit()

        if event.count > 1:
            for switch in Switches.query.filter_by(model[sensor_name][1] = sensor.id).all():
                flag = SwitchFlag.query.filter_by(switch_id = switch.id).first
                if flag.manual == 0 and flag.touch != 1:
                    network_relay_control.apply_async(args = [switch.device_index_code, switch.channel, False], queue = sensor.ip_config.ip+':'+str(sensor.ip_config.port))
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
def auto_control(sensor_name):
    switch_light()
    sensor_light(sensor_name)


@celery.task()
def init_control():
    sensor_name = ['IR', 'Lux', 'AQI']
    model = {
        'IR':[IREventCount, ir_id, status],
        'Lux':[LuxEventCount, lux_id, value],
        'AQI':[AQIEventCount, aqi_id, pm25],
    }

    for data, sensor in data_generate('Switch'):
        flag = SwitchFlag.query.filter_by(switch_id = sensor.id).first()
        flag.latest_status = sensor.latest_record.value
        flag.manual = 0
        flag.touch = 0
    db.session.commit()

    for i in range(3):
        for data, sensor in data_generate(sensor_name[i]):
            sensor_query.apply_async(args = [sensor_name[i], data, sensor], queue = sensor.ip_config.ip+':'+str(sensor.ip_config.port))
            event = model[sensor_name[i]][0].query.filter_by(model[sensor_name[i]][1] = sensor.id).first()
            if sensor.latest_record.model[sensor_name[i]][2] == 0 or sensor.latest_record.model[sensor_name[i]][2] >= default_value:
                event.count = 1
            else:
                event.count = 0
    db.session.commit()
    

