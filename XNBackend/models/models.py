# -*- coding:utf-8 -*-
from .base import db

from sqlalchemy import ForeignKey, Unicode, BOOLEAN, TIMESTAMP, String, \
    SmallInteger, Integer, Float

SMALL_LEN = 30
MEDIUM_LEN = 50
LARGE_LEN = 100


class TimeObj:
    created_at = db.Column(TIMESTAMP)
    updated_at = db.Column(TIMESTAMP)


class Users(db.Model, TimeObj):
    '''sync from hik'''
    personId = db.Column(Unicode, primary_key=True)
    jobNo = db.Column(String(MEDIUM_LEN))
    gender = db.Column(SmallInteger)
    orgPath = db.Column(String(MEDIUM_LEN))
    orgIndexCode = db.Column(String(MEDIUM_LEN))
    orgName = db.Column(String(MEDIUM_LEN))
    certificateType = db.Column(Integer)
    certificateNo = db.Column(String(MEDIUM_LEN))
    phoneNo = db.Column(String(SMALL_LEN))
    address = db.Column(String(LARGE_LEN))
    email = db.Column(String(MEDIUM_LEN))
    education = db.Column(SmallInteger)
    nation = db.Column(SmallInteger)


class Locators(db.Model, TimeObj):
    internal_code = db.Column(Unicode, primary_key=True)
    description = db.Column(String(LARGE_LEN))
    floor = db.Column(Integer)
    # coorX, and coorY may not necessary
    coorX = db.Column(Float, nullable=True)
    coorY = db.Column(Float, nullable=True)


class Cameras(db.Model, TimeObj):
    device_index_code = db.Column(Unicode, primary_key=True)
    name = db.Column(String(MEDIUM_LEN))
    locator = db.Column(Unicode, ForeignKey(Locators.internal_code,
                                            ondelete='SET NULL'))
    status = db.Column(SmallInteger)


class Acs(db.Model, TimeObj):
    device_index_code = db.Column(Unicode, primary_key=True)
    name = db.Column(String(MEDIUM_LEN))
    locator = db.Column(Unicode, ForeignKey(Locators.internal_code,
                                            ondelete='SET NULL'))
    status = db.Column(SmallInteger)


class CircuitBreaker(db.Model, TimeObj):
    mac = db.Column(Unicode, primary_key=True)
    name = db.Column(String(SMALL_LEN))
    phone = db.Column(String(SMALL_LEN))
    locator = db.Column(Unicode, ForeignKey(Locators.internal_code,
                                            ondelete='SET NULL'))


class CircuitRecord(db.Model, TimeObj):
    id = db.Column(Integer, primary_key=True)
    circuit_mac = db.Column(Unicode, ForeignKey(CircuitBreaker.mac,
                                                ondelete='CASCADE'))
    validity = db.Column(BOOLEAN)
    enable_netctr = db.Column(BOOLEAN)
    oc = db.Column(BOOLEAN)
    online = db.Column(BOOLEAN)
    total_power = db.Column(Float)
    mxgg = db.Column(Float)
    mxgl = db.Column(Float)
    line_type = db.Column(SmallInteger)
    spec = db.Column(String)
    control = db.Column(BOOLEAN)
    visibility = db.Column(BOOLEAN)
    alarm = db.Column(Integer)
    gLd = db.Column(Float)
    gA = db.Column(Float)
    gT = db.Column(Float)
    gV = db.Column(Float)
    gW = db.Column(Float)
    gPF = db.Column(Float)
    aA = db.Column(Float)
    aT = db.Column(Float)
    aV = db.Column(Float)
    aW = db.Column(Float)
    aPF = db.Column(Float)
    bA = db.Column(Float)
    bT = db.Column(Float)
    bV = db.Column(Float)
    bW = db.Column(Float)
    bPF = db.Column(Float)
    cA = db.Column(Float)
    cT = db.Column(Float)
    cV = db.Column(Float)
    cW = db.Column(Float)
    cPF = db.Column(Float)
    nA = db.Column(Float)
    nT = db.Column(Float)
