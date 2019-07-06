from ._blueprint import api_bp
from flask import jsonify
from XNBackend.task.hik.task_hik import *
from XNBackend.task.hik.protocol import *


@api_bp.route('/test', methods=['GET'])
def test():
    data = network_relay_query.delay().get()
    data_byte = eval(data)
    message = header(data_byte)
    return jsonify({"hello":"world", 'data':str(message)})

