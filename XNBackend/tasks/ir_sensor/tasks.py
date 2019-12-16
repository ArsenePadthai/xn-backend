from XNBackend.tasks import celery
from XNBackend.models import IRSensors
from XNBackend.tasks.sensor.tasks import ir_query


@celery.task()
def periodic_update_ir_status():
    irs = IRSensors.query
    for ir in irs:
        ir_query.apply_async(args=[ir.batch_no, ir.addr_no],
                             queue=ir.tcp_config.ip+':'+str(ir.tcp_config.port))
