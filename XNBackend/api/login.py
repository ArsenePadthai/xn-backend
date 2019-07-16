from ._blueprint import api_bp
from flask import request, jsonify
from flask_jwt_extended import create_access_token
from ..models import UserLogins


@api_bp.route('/login', methods=['POST'])
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
        return jsonify({"msg": "User not exists or password is wrong."})
    else:
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token), 200

