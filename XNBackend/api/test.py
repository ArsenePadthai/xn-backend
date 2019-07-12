from ._blueprint import api_bp
from flask import jsonify
from XNBackend.task.sensor.task import *


@api_bp.route('/test', methods=['GET'])
def test():
    Lux_sensor_query.delay()
    return jsonify({"hello":"world"})
