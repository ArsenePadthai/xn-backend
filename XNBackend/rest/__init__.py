from flask_restful import Api
from flask_restful import Api
from .light import LightControl 
from .acs import AcsControl
from ._blueprint import dashboard_api_bp
from .mantunci_alarm import MantunciBoxAlarm

api = Api(dashboard_api_bp)

api.add_resource(LightControl, '/api/control/light')
api.add_resource(AcsControl, '/api/control/acs')
api.add_resource(MantunciBoxAlarm, '/api/dashboard/alarm')
