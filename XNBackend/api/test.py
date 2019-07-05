from ._blueprint import api_bp
from flask import jsonify
from XNBackend.task.hik.task_hik import *


@api_bp.route('/test', methods=['GET'])
def test():
    add_together.delay(12, 13)
        
    return jsonify({"hello":"world"})

