from flask_restful import fields


class MyDateTime(fields.Raw):
    def format(self, value):
        return value.strftime("%Y-%m-%d %H:%M:%S")
