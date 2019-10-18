from ._blueprint import api_bp
from flask import jsonify
from celery import group
from XNBackend.task.sensor.task import *
from XNBackend.task.sensor.autoctrl import *
from XNBackend.task.mantunsci.task import *


@api_bp.route('/test', methods=['GET'])
def test():
    tasks_route.delay('RelayControl', 3, 1, relay_id = 7)
    #tasks_route.delay('LocatorControl', 2, 1, zone = 1)
    #circuit_current.delay()
    #init_control.delay()
    #tasks_route.delay('IR', None, None)
    return jsonify({"hello": "world"})
