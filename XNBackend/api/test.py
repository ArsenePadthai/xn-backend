from ._blueprint import api_bp
from flask import jsonify
from celery import group
from XNBackend.task.sensor.task import *
from XNBackend.task.mantunsci.task import *


@api_bp.route('/test', methods=['GET'])
def test():
    #tasks_route.delay('SwitchControl', 10, 1, 0)
    get_token_test.delay()
    return jsonify({"hello": "world"})
