# -*- encoding: utf-8 -*-
import logging
from csv import DictReader
from datetime import datetime
from typing import Optional, Iterable

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from XNBackend.modal.module import Module, ModuleType
from XNBackend.modal.user import User

L = logging.getLogger(__name__)


def add_module(session: Session, sn, imei, added_by: User, created_at: Optional[datetime]=None):
    m = Module(
        created_at=created_at or datetime.utcnow(),
        added_by=added_by,
        sn=sn,
        imei=imei,
        type=ModuleType.BC95,
    )
    session.add(m)
    try:
        session.flush()
    except IntegrityError as ex:
        L.warning('cannot add module %s/%s due to integrity error %s', sn, imei, ex)
        session.rollback()
    return m


def import_modules(session: Session, reader: Iterable[dict], added_by: User, created_at: Optional[datetime]=None):
    try:
        for m in reader:
            add_module(session, m['sn'], m['imei'], added_by, created_at)
        session.commit()
    except:
        L.exception('import module failed due to unhandled exception, rollback')
        session.rollback()
        raise


def import_modules_from_csv(session: Session, f: bytes, added_by: User, created_at: Optional[datetime]=None):
    reader = DictReader(f)
    import_modules(session, reader, added_by, created_at)
