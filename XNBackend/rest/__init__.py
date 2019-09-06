from flask_restful import Api
from .light import LightControl 
from .acs import AcsControl, Acs
from ._blueprint import dashboard_api_bp
from .mantunci_alarm import MantunciBoxAlarm
from .energy import Energy
from .env import Env
from .device import Device
from .room import Room
from .sensor import AirCondition, FireDetector, IRSensor, Elevator, Camera, Light, FaceRecognition
from .callback import AcsCallback

api = Api(dashboard_api_bp)

api.add_resource(LightControl, '/api/control/light')
api.add_resource(AcsControl, '/api/control/acs')
api.add_resource(MantunciBoxAlarm, '/api/dashboard/alarm')
api.add_resource(Energy, '/api/dashboard/energy')
api.add_resource(Env, '/api/dashboard/env')
api.add_resource(Device, '/api/dashboard/device')
api.add_resource(Room, '/api/dashboard/room')
api.add_resource(AirCondition, '/api/dashboard/air_condition')
api.add_resource(FireDetector, '/api/dashboard/fire_detector')
api.add_resource(IRSensor, '/api/dashboard/ir_sensors')
api.add_resource(Elevator, '/api/dashboard/elevator')
api.add_resource(Camera, '/api/dashboard/cameres')
api.add_resource(Light, '/api/dashboard/lights')
api.add_resource(FaceRecognition, '/api/dashboard/faceRecog')
api.add_resource(Acs, '/api/dashboard/acs')
api.add_resource(AcsCallback, '/api/callback/acs')

