from flask_restful import Resource
from XNBackend.models import LuxSensors, AQISensors


TEM = 0
HUM = 1
LUX = 2
CO2 = 3
PM = 4
FAN = 5
FIRE = 6


def form_float(number):
    return float('%.2f' % number)


def floor_sensors(lux_query=None, pm_co2_query=None):
    temperature = 22
    humidity = 66
    lux = 0
    co2 = 0
    pm25 = 0
    fan = False
    fire_alarm = False

    sensor_no_data_count = 0
    if lux_query.all():
        for i in lux_query.all():
            if i.locator_body.latest_record:
                lux += i.locator_body.latest_record.value
            else:
                sensor_no_data_count += 1
        lux /= (lux_query.count() - sensor_no_data_count)
    else:
        lux = 0

    sensor_no_data_count = 0
    if pm_co2_query.all():
        for i in pm_co2_query.all():
            if i.locator_body.latest_record:
                pm25 += i.locator_body.latest_record.pm25
                co2 += i.locator_body.latest_record.co2
            else:
                sensor_no_data_count += 1
        pm25 /= (pm_co2_query.count() - sensor_no_data_count)
        co2 /= (pm_co2_query.count() - sensor_no_data_count)
    else:
        pm25 = 0
        co2 = 0

    return [temperature, humidity, form_float(lux), form_float(co2), form_float(pm25), fan, fire_alarm]


def return_floor_detail(floor, floor_data):
    return {
        floor: {
            "temperature": floor_data[TEM],
            "humidity": floor_data[HUM],
            "lux": floor_data[LUX],
            "co2": floor_data[CO2],
            "pm25": floor_data[PM],
            "fan": floor_data[FAN],
            "fire_alarm": floor_data[FIRE]
        }
    }


class Env(Resource):

    def get(self):

        lux_sensor = LuxSensors.query
        pm25_co2_sensor = AQISensors.query

        floor3 = floor_sensors(lux_query=lux_sensor.filter(LuxSensors.locator_body.has(floor=3)),
                               pm_co2_query=pm25_co2_sensor.filter(AQISensors.locator_body.has(floor=3)))
        floor4 = floor_sensors(lux_query=lux_sensor.filter(LuxSensors.locator_body.has(floor=4)),
                               pm_co2_query=pm25_co2_sensor.filter(AQISensors.locator_body.has(floor=4)))
        floor5 = floor_sensors(lux_query=lux_sensor.filter(LuxSensors.locator_body.has(floor=5)),
                               pm_co2_query=pm25_co2_sensor.filter(AQISensors.locator_body.has(floor=5)))
        floor6 = floor_sensors(lux_query=lux_sensor.filter(LuxSensors.locator_body.has(floor=6)),
                               pm_co2_query=pm25_co2_sensor.filter(AQISensors.locator_body.has(floor=6)))
        floor7 = floor_sensors(lux_query=lux_sensor.filter(LuxSensors.locator_body.has(floor=7)),
                               pm_co2_query=pm25_co2_sensor.filter(AQISensors.locator_body.has(floor=7)))

        alarm_if_exist = False
        for alarm in [floor3[FIRE], floor4[FIRE], floor5[FIRE], floor6[FIRE], floor7[FIRE]]:
            if alarm:
                alarm_if_exist = True

        total_tem = (floor3[TEM] + floor4[TEM] + floor5[TEM] + floor6[TEM] + floor7[TEM]) / 5
        total_hum = (floor3[HUM] + floor4[HUM] + floor5[HUM] + floor6[HUM] + floor7[HUM]) / 5

        sensor_no_data_count = 0
        if lux_sensor.all():
            total_lux = 0
            for i in lux_sensor.all():
                if i.locator_body.latest_record:
                    total_lux += i.locator_body.latest_record.value
                else:
                    sensor_no_data_count += 1
            total_lux_avg = total_lux / (lux_sensor.count() - sensor_no_data_count)
        else:
            total_lux_avg = 0

        sensor_no_data_count = 0
        if pm25_co2_sensor.all():
            total_pm25 = 0
            total_co2 = 0
            for i in pm25_co2_sensor.all():
                if i.locator_body.latest_record:
                    total_pm25 += i.locator_body.latest_record.pm25
                    total_co2 += i.locator_body.latest_record.co2
                else:
                    sensor_no_data_count += 1
            total_pm25_avg = total_pm25 / (pm25_co2_sensor.count() - sensor_no_data_count)
            total_co2_avg = total_co2 / (pm25_co2_sensor.count() - sensor_no_data_count)
        else:
            total_pm25_avg = total_co2_avg = 0

        return_data = {
            "total": {
                "temperature": total_tem,
                "humidity": total_hum,
                "lux": form_float(total_lux_avg),
                "co2": form_float(total_co2_avg),
                "pm25": form_float(total_pm25_avg),
                "fan": floor3[FAN],
                "fire_alarm": alarm_if_exist
            }
        }
        return_data.update(return_floor_detail('3f', floor3))
        return_data.update(return_floor_detail('4f', floor4))
        return_data.update(return_floor_detail('5f', floor5))
        return_data.update(return_floor_detail('6f', floor6))
        return_data.update(return_floor_detail('7f', floor7))

        return return_data
