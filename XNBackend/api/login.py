from ._blueprint import api_bp
from flask import request, jsonify, make_response
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, \
    create_refresh_token, jwt_refresh_token_required
from ..models import UserLogins


@api_bp.route('/api/login', methods=['POST'])
def login():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400
    username = request.json.get('username', None)
    password = request.json.get('password', None)

    if not username:
        return jsonify({"message": "Missing username parameter", "code": -1})
    if not password:
        return jsonify({"message": "Missing password parameter", "code": -1})
    
    user = UserLogins.query.filter_by(username=username).first()
    if user is None or not user.check_password(password):
        resp = make_response(jsonify({"message": "User not exists or password is wrong.", "code": -1}))
        return resp
    else:
        access_token = create_access_token(identity=username)
        refresh_token = create_refresh_token(identity=username)
        resp = make_response(jsonify({"message": "ok",
                                      "user_id": user.id,
                                      "access_token": access_token,
                                      "refresh_token": refresh_token}), 200)
        return resp


@api_bp.route('/api/refresh', methods=['POST'])
@jwt_refresh_token_required
def refresh():
    current_user = get_jwt_identity()
    ret = {
        'access_token': create_access_token(identity=current_user),
        'refresh_token': create_refresh_token(identity=current_user)
    }
    return jsonify(ret), 200


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
