# -*- encoding: utf-8 -*-
from XNBackend.app.factory import create_app
from XNBackend.tasks import celery
assert celery

app = create_app()
