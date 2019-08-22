from ._blueprint import api_bp
from flask import request, jsonify, make_response
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from ..models import UserLogins, Users


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
        resp = make_response(jsonify({"msg": "login success", "user_id": user.id}), 200)
        access_token = create_access_token(identity=username)
        resp.set_cookie('access_token_cookie', access_token)
        return resp


@api_bp.route('/api/current_user', methods=['GET'])
@jwt_required
def get_user():
    username = get_jwt_identity()
    this_user = UserLogins.query.filter_by(username=username).first()
    level = this_user.level
    if this_user is None:
        resp = make_response(jsonify({"code":404, "msg":"User not exists"}))
    else:
        this_user = this_user.user_ref
        resp = make_response(jsonify({
            "code": 200,
            "msg": 'success',
            "data": {
                "id": this_user.id,
                "person_id": this_user.person_id,
                "person_name": this_user.person_name,
                "job_no": this_user.job_no,
                "gender": this_user.gender,
                "certificate_type": this_user.certificate_type,
                "certificate_no": this_user.certificate_no,
                "phone_no": this_user.phone_no,
                "address": this_user.address,
                "email": this_user.email,
                "education": this_user.education,
                "nation": this_user.nation,
                "photo_url": this_user.photo_url,
                "username": username,
                "level": level
            }
        }))
    return resp
