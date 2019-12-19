# -*- coding: utf-8 -*-
from flask_restful import Resource, reqparse
from datetime import datetime
from XNBackend.models import BoxAlarms

alarm_query_parser = reqparse.RequestParser()
alarm_query_parser.add_argument('start',
                                type=lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%S'),
                                required=False,
                                help='please provide correct start time, example: 2019-08-30T10:00:00')
alarm_query_parser.add_argument('end',
                                type=lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%S'),
                                required=False,
                                help='please provide correct end time, example: 2019-08-30T10:00:00')
alarm_query_parser.add_argument("pageNo",
                                type=int,
                                required=False,
                                help="please provide correct page no")
alarm_query_parser.add_argument('perPage',
                                type=int,
                                required=False,
                                help="please provide correct perPage")


class MantunciBoxAlarm(Resource):
    def get_alarm_summary(self, items):
        alarm_count = [0] * 17
        ret = {}

        for alarm in items:
            type_number = alarm.type_number
            alarm_count[type_number] += 1

        alarm_type = ["unknown",
                      "short_circuit",
                      "leak",
                      "over_load",
                      "over_flow",
                      "over_voltage",
                      "lack_voltage",
                      "temp_alarm",
                      "surge",
                      "leak_protection_ok",
                      "leak_protection_undo",
                      "circuit_fire",
                      "leak_warn",
                      "circuit_warn",
                      "over_vol_warn",
                      "lack_vol_warn",
                      "connect_warn"]
        for a in range(len(alarm_type)):
            ret[alarm_type[a]] = alarm_count[a]
        return ret

    def get(self):
        args = alarm_query_parser.parse_args()
        start = args.get('start')
        end = args.get('end')
        page_no = args.get('pageNo')
        perPage = args.get('perPage')
        if start and end and start >= end:
            return {"code": -1, "message": "start time should be earlier than end time"}

        query = BoxAlarms.query
        if start:
            query = query.filter(BoxAlarms.time > start)
        if end:
            query = query.filter(BoxAlarms.time < end)
        query = query.paginate(page_no, perPage, error_out=True).items
        return self.get_alarm_summary(query)

