# -*- encoding: utf-8 -*-

from celery import Celery
from kombu.utils import cached_property

current_flask_app = None


class FlaskCelery(Celery):
    def __init__(self, *args, **kwargs):
        global current_flask_app
        Celery.__init__(self, *args, **kwargs)
        flask_app = kwargs.pop('flask_app', current_flask_app)
        if flask_app:
            self.init_app(flask_app)
        else:
            self.flask_app = None

    @cached_property
    def Task(self):
        cls = self.create_task_cls()
        _celery = self
        o_call = cls.__call__

        # class ContextTask(TaskBase):
        def _task_call__(self, *_args, **_kwargs):
            if _celery.flask_app is None:
                from XNBackend.app.factory import create_app
                _celery.flask_app = create_app()
            with _celery.flask_app.app_context():
                return o_call(self, *_args, **_kwargs)

        cls.__call__ = _task_call__
        return cls

    def init_app(self, app):
        global current_flask_app
        self.main = app.import_name
        if app.config.get('CELERY_BROKER_URL'):
            self.conf['BROKER_URL'] = app.config['CELERY_BROKER_URL']
        self.conf.update(app.config)
        self.flask_app = app
        current_flask_app = app
        return self


celery = FlaskCelery()
