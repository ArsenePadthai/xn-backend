from flask_restful import Resource
from XNBackend.models import FireAlarmSensors, IRSensors, Elevators, TrackingDevices, Relay
from .sensor import check_ir
from functools import partial

FLOOR3 = 0
FLOOR4 = 1
FLOOR5 = 2
FLOOR6 = 3
FLOOR7 = 4


def floor_detail(floor, main=None, aux=None, tracking=None, e1='', e2='', room=0):
    def calc_acs(entries):
        count_open = 0
        count_infra = 0
        for e in entries:
            if e.acs_record:
                if e.acs_record.status == 1:
                    count_open += 1
                if e.acs_record.event_type == 198657:
                    count_infra += 1
        return {
            'open': count_open,
            'infra': count_infra
        }

    acs = tracking.filter(
        TrackingDevices.locator_body.has(floor=floor)
    ).all()
    ret = {'total': len(acs)}
    ret.update(calc_acs(acs))

    FIRE_DETECTORS = 40
    ALARM = 0

    ROOM_NUMBER = room
    ir_occupied, ir_empty, ir_status = check_ir(floor)

    main_light = main.filter(Relay.locator.has(floor=floor))
    aux_light = aux.filter(Relay.locator.has(floor=floor))

    total_main = main_light.count()
    total_aux = aux_light.count()

    main_on_count = 0
    for i in main_light.all():
        if i.latest_record.value:
            main_on_count += 1

    aux_on_count = 0
    for i in aux_light.all():
        if i.latest_record.value:
            aux_on_count += 1
    return_data = {
        "fire_alarm": {
            "detectors": FIRE_DETECTORS,
            "alarms": ALARM,
            "running": FIRE_DETECTORS - ALARM
        },
        "ir_sensors": {
            "rooms": ROOM_NUMBER,
            "empty": ir_empty,
            "offices": int(ROOM_NUMBER / 2),
            "offices_empty": int(ir_empty / 2),
            "meeting_room": ROOM_NUMBER - int(ROOM_NUMBER / 2),
            "meeting_empty": ir_empty - int(ir_empty / 2)
        },
        "central_ac": {
            "outter": 50,
            "outter_run": 30,
            "inner": 34,
            "inner_run": 23,
            "run_on_empty": 0
        },
        "elevator": {
            "total": 2,
            "location1": e1,
            "location2": e2
        },
        "camera": {
            "total": 100,
            "general": 50,
            "ai": 50
        },
        "light": {
            "total": str(total_main + total_aux),
            "total_main": str(total_main),
            "main_run": str(main_on_count),
            "total_aux": str(total_aux),
            "aux_run": str(aux_on_count)
        }
    }
    return_data.update({'acs': ret})

    return {'%df' % floor: return_data}


def cal_total(floor_list, property_name, sub_property_name):
    sum = 0
    for i in floor_list:
        data = list(i.values())[0]
        sum += int(data[property_name][sub_property_name])
    return sum


class Device(Resource):
    def get(self):
        elevator1, elevator2 = Elevators.query.all()
        elevator1_loc = str(elevator1.latest_record.floor) if not elevator1.latest_record.direction else "运行中"
        elevator2_loc = str(elevator2.latest_record.floor) if not elevator2.latest_record.direction else "运行中"

        relay_main_light = Relay.query.filter(Relay.switch.has(channel=1))
        relay_aux_light = Relay.query.filter(Relay.switch.has(channel=2))
        tracking = TrackingDevices.query.filter(TrackingDevices.device_type == 1)

        get_floor_data = partial(floor_detail, main=relay_main_light, aux=relay_aux_light, e1=elevator1_loc,
                                 e2=elevator2_loc, room=24, tracking=tracking)
        floor3 = get_floor_data(3)
        floor4 = get_floor_data(4)
        floor5 = get_floor_data(5)
        floor6 = get_floor_data(6)
        floor7 = get_floor_data(7)

        total_floor = [floor3, floor4, floor5, floor6, floor7]

        total_fire_detectors = cal_total(total_floor, 'fire_alarm', 'detectors')
        total_fire_alarm = cal_total(total_floor, 'fire_alarm', 'alarms')

        return_data = {
            "total": {
                "fire_alarm": {
                    "detectors": total_fire_detectors,
                    "alarms": total_fire_alarm,
                    "running": total_fire_detectors - total_fire_alarm
                },
                "ir_sensors": {
                    "rooms": cal_total(total_floor, 'ir_sensors', 'rooms'),
                    "empty": cal_total(total_floor, 'ir_sensors', 'empty'),
                    "offices": cal_total(total_floor, 'ir_sensors', 'offices'),
                    "offices_empty": cal_total(total_floor, 'ir_sensors', 'offices_empty'),
                    "meeting_room": cal_total(total_floor, 'ir_sensors', 'meeting_room'),
                    "meeting_empty": cal_total(total_floor, 'ir_sensors', 'meeting_empty')
                },
                "central_ac": {
                    "outter": cal_total(total_floor, 'central_ac', 'outter'),
                    "outter_run": cal_total(total_floor, 'central_ac', 'outter_run'),
                    "inner": cal_total(total_floor, 'central_ac', 'inner'),
                    "inner_run": cal_total(total_floor, 'central_ac', 'inner_run'),
                    "run_on_empty": cal_total(total_floor, 'central_ac', 'run_on_empty')
                },
                "elevator": {
                    "total": 2,
                    "location1": elevator1_loc,
                    "location2": elevator2_loc
                },
                "acs": {
                    "total": cal_total(total_floor, 'acs', 'total'),
                    "infra": cal_total(total_floor, 'acs', 'infra'),
                    "open": cal_total(total_floor, 'acs', 'open')
                },
                "camera": {
                    "total": cal_total(total_floor, 'camera', 'total'),
                    "general": cal_total(total_floor, 'camera', 'general'),
                    "ai": cal_total(total_floor, 'camera', 'ai')
                },
                "light": {
                    "total": cal_total(total_floor, 'light', 'total'),
                    "total_main": cal_total(total_floor, 'light', 'total_main'),
                    "main_run": cal_total(total_floor, 'light', 'main_run'),
                    "total_aux": cal_total(total_floor, 'light', 'total_aux'),
                    "aux_run": cal_total(total_floor, 'light', 'aux_run')
                }
            }
        }

        return_data.update(floor3)
        return_data.update(floor4)
        return_data.update(floor5)
        return_data.update(floor6)
        return_data.update(floor7)

        return return_data
