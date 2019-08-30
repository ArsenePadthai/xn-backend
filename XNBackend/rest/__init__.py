from ._blueprint import rest_api_bp
from flask_restful import Api
from .light import LightControl 
from .acs import AcsControl 

api = Api(rest_api_bp)

api.add_resource(LightControl, '/api/control/light')
api.add_resource(AcsControl, '/api/control/acs')
