# -*- encoding: utf-8 -*-
from datetime import datetime

from WFDashboard.modal.module import Module
from WFDashboard.task import celery


@celery.task()
def add_together(a, b):
    print(datetime.now(), 'enter add')
    print(datetime.now(), 'start query')
    x = Module.query.count()
    print(datetime.now(), 'end query')
    ans = a + b + x
    print(datetime.now(), 'leave add')
    return ans
