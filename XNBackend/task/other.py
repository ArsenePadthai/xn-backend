from XNBackend.task import celery


@celery.task()
def save_acs_event(device_id,
                   event_type,
                   event_id,
                   id_card_no,
                   time):
    pass