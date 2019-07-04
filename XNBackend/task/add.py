from XNBackend.task import celery


@celery.task()
def add_together(a, b):
    return a + b


@celery.task()
def sub_together(a, b):
    return a - b


@celery.task()
def mul_together(a, b):
    return a * b


@celery.task()
def div_together(a, b):
    return a / b


