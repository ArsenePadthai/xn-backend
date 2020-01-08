from .entry import celery
celery.autodiscover_tasks(['XNBackend.tasks.mantunsci',
                           'XNBackend.tasks.ir_sensor',
                           'XNBackend.tasks.air_condition',
                           'XNBackend.tasks.aqi',
                           'XNBackend.tasks.sensor',
                           'XNBackend.tasks.eco_mode'])

