from ._blueprint import api_bp
from flask import jsonify

@api_bp.route('/test', methods=['GET'])
def test():
    return jsonify({"hello":"world"})

