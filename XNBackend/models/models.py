# -*- coding:utf-8 -*-
from .base import db

from sqlalchemy import ForeignKey, Unicode, BOOLEAN, TIMESTAMP, String, \
    SmallInteger, Integer, Float
from sqlalchemy.orm import relationship

SHORT_LEN = 30
MEDIUM_LEN = 50
LONG_LEN = 100


class TimeObj:
    created_at = db.Column(TIMESTAMP)
    updated_at = db.Column(TIMESTAMP)


class Users(db.Model, TimeObj):
    __tablename__ = 'users'
    '''sync from hik'''
    id = db.Column(Integer, primary_key=True)
    person_id = db.Column(Unicode, index=True)
    job_no = db.Column(String(MEDIUM_LEN))
    gender = db.Column(SmallInteger)
    org_path = db.Column(String(MEDIUM_LEN))
    org_index_code = db.Column(String(MEDIUM_LEN))
    org_name = db.Column(String(MEDIUM_LEN))
    certificate_type = db.Column(Integer)
    certificate_no = db.Column(String(MEDIUM_LEN))
    phone_no = db.Column(String(SHORT_LEN))
    address = db.Column(String(LONG_LEN))
    email = db.Column(String(MEDIUM_LEN))
    education = db.Column(SmallInteger)
    nation = db.Column(SmallInteger)
    photo_url = db.Column(String(LONG_LEN))


class Locators(db.Model, TimeObj):
    __tablename__ = 'locators'
    internal_code = db.Column(Unicode, primary_key=True)
    description = db.Column(String(LONG_LEN))
    floor = db.Column(Integer)
    zone = db.Column(Integer)
    # coorX, coorY and coorZ may not necessary
    coorX = db.Column(Float, nullable=True)
    coorY = db.Column(Float, nullable=True)
    coorZ = db.Column(Float, nullable=True)


class TrackingDevices(db.Model, TimeObj):
    __tablename__ = 'tracking_devices'
    id = db.Column(Integer, primary_key=True)
    device_index_code = db.Column(Unicode, index=True)
    name = db.Column(String(MEDIUM_LEN))
    locator = db.Column(Unicode, ForeignKey(Locators.internal_code,
                                            ondelete='SET NULL'))
    status = db.Column(SmallInteger)
    # 0 means camera, 1 means acs
    device_type = db.Column(SmallInteger)


class AppearRecords(db.Model, TimeObj):
    __tablename__ = 'appear_records'
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey(Users.id,
                                            ondelete='CASCADE'))
    device_id = db.Column(Integer, ForeignKey(TrackingDevices.id,
                                              ondelete="CASCADE"))


class HeatMapSnapshots(db.Model, TimeObj):
    __tablename__ = 'heatmap_snapshots'
    id = db.Column(Integer, primary_key=True)
    device_id = db.Column(Integer, ForeignKey(TrackingDevices.id,
                                              ondelete="CASCADE"))
    count = db.Column(Integer)


class CircuitBreakers(db.Model, TimeObj):
    __tablename__ = 'circuit_breakers'
    id = db.Column(Integer, primary_key=True)
    mac = db.Column(Unicode, index=True)
    name = db.Column(String(SHORT_LEN))
    phone = db.Column(String(SHORT_LEN))
    locator = db.Column(Unicode, ForeignKey(Locators.internal_code,
                                            ondelete='SET NULL'))
    room = db.Column(String(SHORT_LEN))
    unit = db.Column(String(SHORT_LEN))


class CircuitRecords(db.Model, TimeObj):
    __tablename__ = 'circuit_records'
    id = db.Column(Integer, primary_key=True)
    circuit_mac = db.Column(Unicode, ForeignKey(CircuitBreakers.mac,
                                                ondelete='CASCADE'))
    addr = db.Column(Integer)
    title = db.Column(String)
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


class LatestCircuitRecord(db.Model):
    __tablename__ = 'latest_circuit_record'
    id = db.Column(Integer, primary_key=True)
    circuit_id = db.Column(Integer, ForeignKey(CircuitBreakers.id,
                                               ondelete='CASCADE'), index=True)
    circuit_record_id = db.Column(Integer, ForeignKey(CircuitRecords.id,
                                                      ondelete='SET NULL'))
    circuit_breaker = relationship('CircuitBreaker', backref='latest_record')
    circuit_record = relationship('CircuitRecord')


class CircuitAlarms(db.Model, TimeObj):
    __tablename__ = 'circuit_alarms'
    alarm_id = db.Column(Integer, primary_key=True)
    addr = db.Column(Integer)
    node = db.Column(String)
    alarm_type = db.Column(String(SHORT_LEN))
    info = db.Column(String)
    type_number = db.Column(SmallInteger)

    @property
    def alarm_type(self):
        alarm_info_mapping = {
            1: '未知',
            2: '短路报警',
            3: '漏电报警',
            4: '过载报警',
            5: '过压报警',
            6: '欠压报警',
            7: '温度报警',
            8: '浪涌报警',
            9: '漏电保护功能正常'
        }
        return alarm_info_mapping[self.type_number]


class LatestAlarm(db.Model, TimeObj):
    __tablename__ = 'latest_alarms'
    circuit_id = db.Column(Integer, ForeignKey(CircuitBreakers.id),
                           ondelete='CASCADE', index=True)
    circuit_alarm_id = db.Column(Integer, ForeignKey(CircuitAlarms.id),
                                 ondelete='SET NULL')
    circuit = relationship('CircuitBreaker')
    alarm = relationship('CircuitAlarms')


class EnergyConsumeDaily(db.Model, TimeObj):
    __tablename__ = 'energy_consume_daily'
    consume_id = db.Column(Integer, primary_key=True)
    circuit_breaker = db.Column(Integer, ForeignKey(CircuitBreakers.id,
                                                    ondelete='CASCADE'))
    addr = db.Column(Integer)
    electricity = db.Column(Float)
    # 统计时刻电量, 单位 KWH
    # total_electricity = db.Column(Float)


class EnegyConsumeMonthly(db.Model, TimeObj):
    __tablename__ = 'energy_consume_monthly'
    consume_id = db.Column(Integer, primary_key=True)
    circuit_breaker = db.Column(Integer, ForeignKey(CircuitBreakers.id))
    addr = db.Column(Integer)
    electricity = db.Column(Float)
    # 统计时刻电量, 单位 KWH
    # total_electricity = db.Column(Float)


class IRSensorStatus(db.Model, TimeObj):
    __tablename__ = 'ir_sensor_status'
    id = db.Column(Integer, primary_key=True)
    sensor_id = db.Column(Integer, ForeignKey("IRSensors.id",
                                              ondelete="CASCADE"))
    value = db.Column(BOOLEAN)
    sensor = relationship('IRSensors')


# TODO 是查询还是推送
class IRSensors(db.Model, TimeObj):
    __tablename__ = 'ir_sensors'
    id = db.Column(Integer, primary_key=True)
    device_index_code = db.Column(Unicode, index=True)
    locator = db.Column(Unicode, ForeignKey(Locators.internal_code,
                                            ondelete='SET NULL'))
    latest_record_id = db.Column(Integer, ForeignKey(IRSensorStatus.id,
                                                     ondelete="SET NULL"))
    latest_record = relationship('IRSensorStatus')


class AQIValues(db.Model, TimeObj):
    __tablename__ = 'aqi_values'
    # 只有主动查询
    id = db.Column(Integer, primary_key=True)
    sensor_id = db.Column(Integer, ForeignKey("AQISensors.id",
                                              ondelete="CASCADE"))
    temperature = db.Column(Float)
    humidity = db.Column(Float)
    pm25 = db.Column(Float)
    co2 = db.Column(Float)
    tvoc = db.Column(Float)
    voc = db.Column(Float)
    sensor = relationship('AQISensors')


class AQISensors(db.Model, TimeObj):
    __tablename__ = 'aqi_sensors'
    id = db.Column(Integer, primary_key=True)
    device_index_code = db.Column(Unicode, Index=True)
    locator = db.Column(Unicode, ForeignKey(Locators.internal_code,
                                            ondelete='SET NULL'))
    latest_record_id = db.Column(Integer, ForeignKey(AQIValues.id,
                                                     ondelete="SET NULL"))
    latest_record = relationship('AQIValues')


class LuxValues(db.Model, TimeObj):
    __tablename__ = 'lux_values'
    # 只有主动查询
    id = db.Column(Integer, primary_key=True)
    sensor_id = db.Column(Integer, ForeignKey("LuxSensors.id",
                                              ondelete='CASCADE'))
    value = db.Column(Float)
    sensor = relationship('LuxSensors')


class LuxSensors(db.Model, TimeObj):
    __tablename__ = 'lux_sensors'
    id = db.Column(Integer, primary_key=True)
    device_index_code = db.Column(Unicode, Index=True)
    locator = db.Column(Unicode, ForeignKey(Locators.internal_code,
                                            ondelete='SET NULL'))
    latest_record_id = db.Column(Integer, ForeignKey(LuxValues.id,
                                                     ondelete="SET NULL"))
    latest_record = relationship('LuxValues')


class FireAlarmStatus(db.Model, TimeObj):
    __tablename__ = 'fire_alarm_status'
    id = db.Column(Integer, primary_key=True)
    sensor_id = db.Column(Integer, ForeignKey('FireAlarmSensors.id',
                                              ondelete='CASCADE'))
    value = db.Column(SmallInteger)
    sensor = relationship('FireAlarmSensors')


class FireAlarmSensors(db.Model, TimeObj):
    __tablename__ = 'fire_alarm_sensors'
    id = db.Column(Integer, primary_key=True)
    device_index_code = db.Column(Unicode, Index=True)
    locator = db.Column(Unicode, ForeignKey(Locators.internal_code,
                                            ondelete='SET NULL'))


class SwitchStatus(db.Model, TimeObj):
    __tablename__ = 'switch_status'
    id = db.Column(Integer, primary_key=True)
    sensor_id = db.Column(Integer, ForeignKey('Switches.id',
                                              ondelete='CASCADE'))
    value = db.Column(SmallInteger)
    sensor = relationship('Switch')


class Switches(db.Model, TimeObj):
    __tablename__ = 'switch_status'
    id = db.Column(Integer, primary_key=True)
    device_index_code = db.Column(Unicode, Index=True)
    locator = db.Column(Unicode, ForeignKey(Locators.internal_code,
                                            ondelete='SET NULL'))


class ElevatorStatus(db.Model, TimeObj):
    __tablename__ = 'elevator_status'
    id = db.Column(Integer, primary_key=True)
    elevator_id = db.Column(Integer, ForeignKey('Elevators.id',
                                                ondelete='CASCADE'))
    floor = db.Column(Integer)
    direction = db.Column(SmallInteger)
    elevator = relationship('Elevators')

    @property
    def direction(self):
        mapping = {1:"up",
                   2:"down",
                   0:"stop"}
        return mapping(self.direction)

    
class Elevators(db.Model, TimeObj):
    __tablename__ = 'elevators'
    id = db.Column(Integer, primary_key=True)
    device_index_code = db.Column(Unicode, Index=True)
    locator = db.Column(Unicode, ForeignKey(Locators.internal_code,
                                            ondelete='SET NULL'))
