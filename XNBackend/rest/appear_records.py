from datetime import datetime
from flask_restful import Resource, reqparse, fields, marshal_with
from flask_jwt_extended import jwt_required
from sqlalchemy import func, and_
from XNBackend.models import db, AppearRecords
from .utils import MyDateTime

time_parser = reqparse.RequestParser()
time_parser.add_argument('start',
                         required=True,
                         type=lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%S'),
                         help='need start time')
time_parser.add_argument('end',
                         required=True,
                         type=lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%S'),
                         help='need end time')
time_parser.add_argument('type',
                         required=False,
                         type=int)

time_parser.add_argument('active',
                         required=False,
                         type=int)

appear_record_patch_parser = reqparse.RequestParser()
appear_record_patch_parser.add_argument('id', type=int, required=True, help='please provide correct id')

appear_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'sex': fields.String,
    'certificateNum': fields.String,
    'happenTime': MyDateTime(attribute='happenTime'),
    'facePicture': fields.String,
    'type': fields.Integer,
    'deviceName': fields.String,
    'active': fields.Integer
}


class AppearRecordsApi(Resource):
    @jwt_required
    @marshal_with(appear_fields)
    def get(self):
        args = time_parser.parse_args()
        # TODO ADD COMPARE FOR START AND END
        start = args.get('start')
        end = args.get('end')
        target_type = args.get('type')
        active = args.get('active')

        subq = AppearRecords.query \
            .with_entities(AppearRecords.certificateNum, func.max(AppearRecords.happenTime).label('maxtime')) \
            .filter(AppearRecords.happenTime > start) \
            .filter(AppearRecords.happenTime < end) \
            .group_by(AppearRecords.certificateNum) \
            .subquery('t2')

        q = AppearRecords.query \
            .join(subq,
                  and_(AppearRecords.certificateNum == subq.c.certificateNum,
                       AppearRecords.happenTime == subq.c.maxtime))

        if target_type == 0 or target_type == 1:
            q = q.filter(AppearRecords.type == target_type)
        if active in (0, 1):
            q = q.filter(AppearRecords.active == active)

        a = q.order_by(AppearRecords.happenTime.desc()).all()
        return a

    @jwt_required
    def patch(self):
        args = appear_record_patch_parser.parse_args()
        the_id = args.get("id")
        ap = AppearRecords.query.filter(AppearRecords.id == the_id).first()
        if not ap:
            return {"code": -1,
                    "message": f"id {the_id} appear record does not exist"}
        elif ap.active == 0:
            return {"code": -1,
                    "message": f"id {the_id} appear record is already confirmed"}
        else:
            ap.active = 0
            db.session.add(ap)
            db.session.commit()
            return {"code": 0, "message": "ok"}
