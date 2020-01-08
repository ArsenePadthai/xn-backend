from datetime import datetime
from flask_restful import Resource, reqparse, fields
from flask_jwt_extended import jwt_required
from XNBackend.models import db, UniAlarms
from XNBackend.rest.utils import MyDateTime, marshal_with_extra, ExtraInfo

alarm_req_parse = reqparse.RequestParser()
alarm_req_parse.add_argument('start', required=False, type=str)
alarm_req_parse.add_argument('end', required=False, type=str)
alarm_req_parse.add_argument('pageNo', required=True, type=int)
alarm_req_parse.add_argument('pageSize', required=True, type=int)
alarm_req_parse.add_argument('room', required=False, type=int)
alarm_req_parse.add_argument('group', required=False, type=int)
alarm_req_parse.add_argument('active', required=False, type=int)

alarm_confirm_parse = reqparse.RequestParser()
alarm_confirm_parse.add_argument('id', required=True, type=int)


class InternalId(fields.Raw):
    def output(self, key, obj):
        return obj.internal_id


ua_fields = {
    'id': InternalId,
    'happen_time': MyDateTime,
    'alarm_group': fields.Integer,
    'alarm_code': fields.Integer,
    'alarm_content': fields.String,
    'room': fields.String,
    'floor': fields.Integer,
    'active': fields.Integer,
    'level': fields.Integer,
    'extra': ExtraInfo,
    'cancel_time': MyDateTime
}


class AlarmApi(Resource):
    @marshal_with_extra(ua_fields, envelope='data')
    def get(self):
        args = alarm_req_parse.parse_args()
        start_str = args.get('start')
        end_str = args.get('end')
        page_no = args.get('pageNo')
        page_size = args.get('pageSize')
        room = args.get('room')
        group = args.get('group')
        active = args.get('active')
        ua = UniAlarms.query

        if start_str:
            start = datetime.strptime(start_str, '%Y-%m-%dT%H:%M:%S')
            ua = ua.filter(UniAlarms.happen_time >= start)

        if end_str:
            end = datetime.strptime(end_str, '%Y-%m-%dT%H:%M:%S')
            ua = ua.filter(UniAlarms.happen_time <= end)

        if room is not None:
            ua = ua.filter(UniAlarms.room == room)
        if group is not None:
            ua = ua.filter(UniAlarms.alarm_group == group)
        if active is not None:
            ua = ua.filter(UniAlarms.active == active)

        ua = ua.order_by(UniAlarms.happen_time.desc())
        paged = ua.paginate(page_no, page_size, error_out=True)

        return paged.items, {"code": 0,
                             "message": "ok",
                             "pageNo": page_no,
                             "pageSize": page_size,
                             "total": paged.total,
                             "hasPrev": paged.has_prev,
                             "hasNext": paged.has_next}

    @jwt_required
    def patch(self):
        args = alarm_confirm_parse.parse_args()
        alarm_id = args.get('id')
        ua = UniAlarms.query.filter(UniAlarms.internal_id == alarm_id).first()
        if not ua:
            return {"code": -1, "message": "Failed to find the alarm record"}
        else:
            if ua.active == 0:
                return {"code": -1, "message": "already in confirm status"}
            ua.active = 0
            ua.cancel_time = datetime.now()
            db.session.commit()
            return {"code": 0, "message": "ok"}
