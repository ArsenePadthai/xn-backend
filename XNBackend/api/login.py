from ._blueprint import api_bp
from flask import request, jsonify, make_response
from flask_jwt_extended import create_access_token
from ..models import UserLogins


@api_bp.route('/api/login', methods=['POST'])
def login():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400
    username = request.json.get('username', None)
    password = request.json.get('password', None)

    if not username:
        return jsonify({"msg": "Missing username parameter"})
    if not password:
        return jsonify({"msg": "Missing password parameter"})
    
    user = UserLogins.query.filter_by(username=username).first()
    if user is None or not user.check_password(password):
        resp = make_response(jsonify({"msg": "User not exists or password is wrong."}))
        return resp
    else:
        resp = make_response(jsonify({"msg": "login success"}), 200)
        access_token = create_access_token(identity=username)
        resp.set_cookie('access_token_cookie', access_token)
        return resp

