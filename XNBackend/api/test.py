from ._blueprint import api_bp
from flask import jsonify
from XNBackend.task.add import *

@api_bp.route('/test', methods=['GET'])
def test():
    a = str(add_together.delay(12,3).get())
    b = str(sub_together.delay(34,17).get())
    c = str(mul_together.delay(8,2).get())
    d = str(div_together.delay(36,2).get())
    return jsonify({"hello":"world", a:b, c:d})

