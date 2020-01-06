from flask_restful import Api
from .light import LightControl 
from .acs import AcsControl, Acs
from ._blueprint import dashboard_api_bp
from .mantunci_alarm import MantunciBoxAlarm
from .energy import Energy, EnergyShow
from .env import Env
from .device import Device
from .room import Room
from .sensor import FireDetector, IRSensor, Elevator, Light, FaceRecognition
from .callback import AcsCallback
from .air_condition import AirConditionControl, AirCondition
from .aqi import AQISensor
from .notification import NotificationApi
from .electric_consume import ElectricConsumeByDay, ElectricConsumeByMonth
from .appear_records import AppearRecordsApi
from .floor_control import FloorControl
from .door_event import DoorEvent

api = Api(dashboard_api_bp)

api.add_resource(LightControl, '/api/control/light')
api.add_resource(AcsControl, '/api/control/acs')
api.add_resource(AirConditionControl, '/api/control/air_condition')

api.add_resource(MantunciBoxAlarm, '/api/dashboard/alarm')
api.add_resource(Energy, '/api/dashboard/energy')
api.add_resource(Env, '/api/dashboard/env')
api.add_resource(Device, '/api/dashboard/device')
# mark as read
api.add_resource(Room, '/api/dashboard/room')
api.add_resource(AirCondition, '/api/dashboard/air_condition')
api.add_resource(FireDetector, '/api/dashboard/fire_detector')
api.add_resource(IRSensor, '/api/dashboard/ir_sensors')
api.add_resource(Elevator, '/api/dashboard/elevator')
api.add_resource(Light, '/api/dashboard/lights')
api.add_resource(FaceRecognition, '/api/dashboard/faceRecog')
api.add_resource(Acs, '/api/dashboard/acs')
api.add_resource(AcsCallback, '/api/callback/acs')

# new api
api.add_resource(EnergyShow, '/api/dashboard/energyshow')
api.add_resource(AQISensor, '/api/dashboard/aqi')
api.add_resource(NotificationApi, '/api/dashboard/notification')
# api.add_resource(ElectricConsumeByHour, '/api/dashboard/electric_consume_hour')
api.add_resource(ElectricConsumeByDay, '/api/dashboard/electric_consume_day')
api.add_resource(ElectricConsumeByMonth, '/api/dashboard/electric_consume_month')
api.add_resource(AppearRecordsApi, '/api/dashboard/appear_records')
api.add_resource(FloorControl, '/api/dashboard/floor_control')
api.add_resource(DoorEvent, '/api/dashboard/door_event')


