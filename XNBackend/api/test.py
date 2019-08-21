from ._blueprint import api_bp
from flask import jsonify
from celery import group
from XNBackend.task.sensor.task import *
from XNBackend.task.mantunsci.task import *


@api_bp.route('/test', methods=['GET'])
def test():
    #tasks_route.delay('SwitchControl', 1, 1, False)
    #tasks_route.delay('Switch')
    circuit_current.delay()
    return jsonify({"hello": "world"})
