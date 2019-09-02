from flask_restful import Resource
from XNBackend.models import FireAlarmSensors, IRSensors, Elevators, TrackingDevices, Relay, Switches


FLOOR3 = 0
FLOOR4 = 1
FLOOR5 = 2
FLOOR6 = 3
FLOOR7 = 4


class Device(Resource):
    def get(self):
        fire_alarm_sensor_count = [0, 30, 30, 30, 30]
        fire_alarm_count = [0, 0, 0, 0, 0]
        fire_alarm_sensor_count[FLOOR3] = FireAlarmSensors.query.filter(FireAlarmSensors.locator_body.has(floor=3))
        return {
            "total": {
                "fire_alarm": {
                    "detectors": 200,
                    "alarms": 60,
                    "running": 140
                },
                "ir_sensors": {
                    "rooms": 200,
                    "occupied": 80,
                    "error": 2
                },
                "central_ac": {
                    "running": 40,
                    "running_on_empty": 13,
                    "full_running": 20
                },
                "elevator": {
                    "total": 2,
                    "running": 2,
                    "error": 0
                },
                "acs": {
                    "total": 60,
                    "count": 44,
                    "open": 22
                },
                "camera": {
                    "total": 100,
                    "general": 50,
                    "ai": 50
                },
                "light": {
                    "total": 100,
                    "online": 80,
                    "light_on": 50
                }
            },
            "3f": {
                "fire_alarm": {
                    "detectors": 200,
                    "alarms": 60,
                    "running": 140
                },
                "ir_sensors": {
                    "rooms": 200,
                    "occupied": 80,
                    "error": 2
                },
                "central_ac": {
                    "running": 40,
                    "running_on_empty": 13,
                    "full_running": 20
                },
                "elevator": {
                    "total": 2,
                    "running": 2,
                    "error": 0
                },
                "acs": {
                    "total": 60,
                    "count": 44,
                    "open": 22
                },
                "camera": {
                    "total": 100,
                    "general": 50,
                    "ai": 50
                },
                "light": {
                    "total": 100,
                    "online": 80,
                    "light_on": 50
                }
            },
            "7f": {
                "fire_alarm": {
                    "detectors": 200,
                    "alarms": 60,
                    "running": 140
                },
                "ir_sensors": {
                    "rooms": 200,
                    "occupied": 80,
                    "error": 2
                },
                "central_ac": {
                    "running": 40,
                    "running_on_empty": 13,
                    "full_running": 20
                },
                "elevator": {
                    "total": 2,
                    "running": 2,
                    "error": 0
                },
                "acs": {
                    "total": 60,
                    "count": 44,
                    "open": 22
                },
                "camera": {
                    "total": 100,
                    "general": 50,
                    "ai": 50
                },
                "light": {
                    "total": 100,
                    "online": 80,
                    "light_on": 50
                }
            }
        }
