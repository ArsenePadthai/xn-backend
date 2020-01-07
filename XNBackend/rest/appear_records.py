from datetime import datetime
from flask_restful import Resource, reqparse, fields, marshal_with
from flask_jwt_extended import jwt_required
from sqlalchemy import func, and_
from XNBackend.models import AppearRecords
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

appear_fields = {
    'name': fields.String,
    'sex': fields.String,
    'certificateNum': fields.String,
    'happenTime': MyDateTime(attribute='happenTime'),
    'facePicture': fields.String,
    'type': fields.Integer,
    'deviceName': fields.String
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

        if target_type:
            a = q.filter(AppearRecords.type == target_type) \
                .order_by(AppearRecords.happenTime.desc()) \
                .all()
        else:
            a = q.order_by(AppearRecords.happenTime.desc()).all()
        return a
