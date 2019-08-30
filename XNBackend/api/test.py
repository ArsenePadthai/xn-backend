from ._blueprint import api_bp
from flask import jsonify
from celery import group
from XNBackend.task.sensor.task import *
from XNBackend.task.sensor.autoctrl import *
from XNBackend.task.mantunsci.task import *


@api_bp.route('/test', methods=['GET'])
def test():
    #tasks_route.delay('RelayControl', 1, 1, 1)
    #tasks_route.delay('Relay')
    #circuit_current.delay()
    init_control.apply_async(queue='sensor')
    return jsonify({"hello": "world"})
