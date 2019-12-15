from datetime import datetime
from flask_restful import Resource, reqparse
from XNBackend.models import db, Notification


notification_post_parse = reqparse.RequestParser()
notification_post_parse.add_argument('title', required=False, type=str)
notification_post_parse.add_argument('content', required=True, type=str)
notification_post_parse.add_argument('color', )


class NotificationApi(Resource):
    def get(self):
        n = Notification.query.order_by(Notification.created_at.desc()).first()
        return {
            "title": n.title,
            "content": n.content,
            "color": n.color,
            "time": n.updated_at
        }

    def post(self):
        args = notification_post_parse.parse_args()
        content = args.get('content')
        color = args.get('color')
        title = args.get('title')
        the_time = datetime.now()
        n = Notification(content=content)
        if title:
            n.title = title
        if color:
            n.color = color
        n.created_at = the_time
        db.session.add(n)
        db.session.commit()
        return {"msg": 'ok'}



