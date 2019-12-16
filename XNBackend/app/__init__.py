from .entry import celery
celery.autodiscover_tasks(['XNBackend.tasks.mantunsci', 'XNBackend.tasks.ir_sensor', 'XNBackend.tasks.air_condition'])

