# -*- coding:utf-8 -*-
from .base import db

from sqlalchemy import ForeignKey, Unicode, BOOLEAN, TIMESTAMP, String, \
    SmallInteger, Integer, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from flask_bcrypt import generate_password_hash, check_password_hash

SHORT_LEN = 30
MEDIUM_LEN = 50
LONG_LEN = 100


class TimeStampMixin:
    created_at = db.Column(TIMESTAMP, nullable=False,
                           server_default=func.current_timestamp())
    updated_at = db.Column(TIMESTAMP, onupdate=func.current_timestamp())


class CarbonMixin:
    carbon_mixin_factor = 0.33
    carbon_mixin_watt_attr_name = ''
    @property
    def carbon_emission(self):
        return getattr(self, self.carbo_mixin_watt_attr_name) * self.carbon_mixin_factor


class Users(db.Model, TimeStampMixin):
    __tablename__ = 'users'
    '''sync from hik'''
    id = db.Column(Integer, primary_key=True)
    person_id = db.Column(Unicode(length=MEDIUM_LEN), index=True)
    person_name = db.Column(Unicode(length=SHORT_LEN))
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


class UserLogins(db.Model, TimeStampMixin):
    __tablename__ = 'user_logins'
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey(Users.id, ondelete='CASCADE'))
    username = db.Column(Unicode(length=MEDIUM_LEN))
    password = db.Column(String(LONG_LEN))
    level = db.Column(SmallInteger)
    user_ref = relationship('Users', backref='user_logins')

    @property
    def leverl_repr(self):
        if self.level == 0:
            return 'visitor'
        if self.level == 1:
            return 'employee'
        if self.level == 2:
            return 'sub_admin'
        if self.level == 3:
            return 'admin'

    def set_password(self, password):
        self.password = generate_password_hash(password, 10).decode('utf-8')

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Locators(db.Model, TimeStampMixin):
    __tablename__ = 'locators'
    internal_code = db.Column(Unicode(length=MEDIUM_LEN), primary_key=True)
    description = db.Column(String(LONG_LEN))
    floor = db.Column(Integer)
    zone = db.Column(Integer)
    # coorX, coorY and coorZ may not necessary
    coorX = db.Column(Float, nullable=True)
    coorY = db.Column(Float, nullable=True)
    coorZ = db.Column(Float, nullable=True)


class TcpConfig(db.Model, TimeStampMixin):
    __tablename__ = 'tcp_config'
    id = db.Column(Integer, primary_key=True)
    ip = db.Column(String(MEDIUM_LEN))
    port = db.Column(Integer)


class TrackingDevices(db.Model, TimeStampMixin):
    __tablename__ = 'tracking_devices'
    id = db.Column(Integer, primary_key=True)
    device_index_code = db.Column(Unicode(length=MEDIUM_LEN), index=True)
    name = db.Column(String(MEDIUM_LEN))
    locator = db.Column(Unicode(length=MEDIUM_LEN), 
                        ForeignKey(Locators.internal_code,
                                   ondelete='SET NULL'))
    # 0 means camera, 1 means acs
    device_type = db.Column(SmallInteger)
    locator_body = relationship('Locators', foreign_keys=[locator])
    latest_acs_record_id = db.Column(Integer,
                                     ForeignKey('acs_records.id',
                                                ondelete='SET NULL'))
    acs_record = relationship("AcsRecords", foreign_keys=[latest_acs_record_id])


class AcsRecords(db.Model, TimeStampMixin):
    __tablename__ = "acs_records"
    id = db.Column(Integer, primary_key=True)
    acs_id = db.Column(Integer, ForeignKey(TrackingDevices.id,
                                           ondelete="CASCADE"))
    status = db.Column(SmallInteger)
    event_type = db.Column(Integer)
    acs = relationship('TrackingDevices', foreign_keys=[acs_id])


class AppearRecords(db.Model, TimeStampMixin):
    __tablename__ = 'appear_records'
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey(Users.id,
                                            ondelete='CASCADE'))
    device_id = db.Column(Integer, ForeignKey(TrackingDevices.id,
                                              ondelete="CASCADE"))
    user = relationship('Users', backref='appear_record')
    device = relationship('TrackingDevices', backref='appear_record')


class LatestPosition(db.Model, TimeStampMixin):
    __tablename__ = 'latest_position'
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey(Users.id,
                                            ondelete='CASCADE'))
    appear_record_id = db.Column(Integer, ForeignKey(AppearRecords.id,
                                                     ondelete='SET NULL'))
    user = relationship('Users', backref='latest_position_pointer')
    appear_record = relationship('AppearRecords')


class HeatMapSnapshots(db.Model, TimeStampMixin):
    __tablename__ = 'heatmap_snapshots'
    id = db.Column(Integer, primary_key=True)
    device_id = db.Column(Integer, ForeignKey(TrackingDevices.id,
                                              ondelete="CASCADE"))
    count = db.Column(Integer)
    device = relationship('TrackingDevices', backref="heatmap_snapshots")


class CircuitBreakers(db.Model, TimeStampMixin):
    __tablename__ = 'circuit_breakers'
    id = db.Column(Integer, primary_key=True)
    mac = db.Column(Unicode(length=MEDIUM_LEN), index=True)
    name = db.Column(String(SHORT_LEN))
    phone = db.Column(String(SHORT_LEN))
    locator = db.Column(Unicode(length=MEDIUM_LEN),
                        ForeignKey(Locators.internal_code,
                                   ondelete='SET NULL'))
    room = db.Column(String(SHORT_LEN))
    unit = db.Column(String(SHORT_LEN))
    locator_body = relationship('Locators')


class CircuitRecords(db.Model, TimeStampMixin):
    __tablename__ = 'circuit_records'
    id = db.Column(Integer, primary_key=True)
    circuit_breaker_id = db.Column(Integer, ForeignKey(CircuitBreakers.id,
                                                       ondelete='CASCADE'))
    addr = db.Column(Integer)
    title = db.Column(String(MEDIUM_LEN))
    validity = db.Column(BOOLEAN)
    enable_netctr = db.Column(BOOLEAN)
    oc = db.Column(BOOLEAN)
    online = db.Column(BOOLEAN)
    total_power = db.Column(Float)
    mxgg = db.Column(Float)
    mxgl = db.Column(Float)
    line_type = db.Column(SmallInteger)
    spec = db.Column(String(MEDIUM_LEN))
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
    circuit_breaker = relationship("CircuitBreakers")


class LatestCircuitRecord(db.Model):
    __tablename__ = 'latest_circuit_record'
    id = db.Column(Integer, primary_key=True)
    circuit_id = db.Column(Integer, ForeignKey(CircuitBreakers.id,
                                               ondelete='CASCADE'), index=True)
    circuit_record_id = db.Column(Integer, ForeignKey(CircuitRecords.id,
                                                      ondelete='SET NULL'))
    circuit_breaker = relationship('CircuitBreakers',
                                   backref='latest_record',
                                   foreign_keys=[circuit_id])
    circuit_record = relationship('CircuitRecords',
                                  foreign_keys=[circuit_record_id])


class CircuitAlarms(db.Model, TimeStampMixin):
    __tablename__ = 'circuit_alarms'
    id = db.Column(Integer, primary_key=True)
    circuit_breaker_id = db.Column(Integer, ForeignKey(CircuitBreakers.id, 
                                                       ondelete='CASCADE'),
                                   nullable=False)
    addr = db.Column(Integer)
    node = db.Column(String(MEDIUM_LEN))
    alarm_or_type = db.Column(String(SHORT_LEN))
    info = db.Column(String(MEDIUM_LEN))
    type_number = db.Column(SmallInteger)
    circuit_breaker = relationship('CircuitBreakers')

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


class LatestAlarm(db.Model, TimeStampMixin):
    __tablename__ = 'latest_alarms'
    id = db.Column(Integer, primary_key=True)
    circuit_id = db.Column(Integer, ForeignKey(CircuitBreakers.id,
                                               ondelete='CASCADE'), index=True)
    circuit_alarm_id = db.Column(Integer, ForeignKey(CircuitAlarms.id, 
                                                     ondelete='SET NULL'))
    circuit = relationship('CircuitBreakers', backref='latest_alarm')
    alarm = relationship('CircuitAlarms')


class EnergyConsumeDaily(db.Model, TimeStampMixin, CarbonMixin):
    __tablename__ = 'energy_consume_daily'
    carbon_mixin_watt_attr_name = 'electricity'
    consume_id = db.Column(Integer, primary_key=True)
    circuit_breaker = db.Column(Integer, ForeignKey(CircuitBreakers.id,
                                                    ondelete='CASCADE'))
    addr = db.Column(Integer)
    electricity = db.Column(Float)
    circuit_break_body = relationship('CircuitBreakers',
                                      backref='daily_consume')
    # 统计时刻电量, 单位 KWH
    # total_electricity = db.Column(Float)


class EnegyConsumeMonthly(db.Model, TimeStampMixin):
    __tablename__ = 'energy_consume_monthly'
    consume_id = db.Column(Integer, primary_key=True)
    circuit_breaker = db.Column(Integer, ForeignKey(CircuitBreakers.id))
    addr = db.Column(Integer)
    electricity = db.Column(Float)
    circuit_break_body = relationship('CircuitBreakers',
                                      backref='monthly_consume')
    # 统计时刻电量, 单位 KWH
    # total_electricity = db.Column(Float)


class IRSensorStatus(db.Model, TimeStampMixin):
    __tablename__ = 'ir_sensor_status'
    id = db.Column(Integer, primary_key=True)
    sensor_id = db.Column(Integer, ForeignKey("ir_sensors.id",
                                              ondelete="CASCADE"))
    value = db.Column(db.Integer)
    status = db.Column(db.BOOLEAN)
    sensor = relationship('IRSensors', foreign_keys=[sensor_id])


# TODO 是查询还是推送
class IRSensors(db.Model, TimeStampMixin):
    __tablename__ = 'ir_sensors'
    id = db.Column(Integer, primary_key=True)
    batch_no = db.Column(db.Integer)
    addr_no = db.Column(db.Integer)
    locator = db.Column(Unicode(length=MEDIUM_LEN),
                        ForeignKey(Locators.internal_code,
                                   ondelete='SET NULL'))
    latest_record_id = db.Column(Integer,
                                 ForeignKey(IRSensorStatus.id,
                                            ondelete="SET NULL"))
    threshold = db.Column(db.Integer)
    delay = db.Column(db.Integer)
    ip_config_id = db.Column(Integer, ForeignKey(TcpConfig.id,
                                                 ondelete='SET NULL'))
    ip_config = relationship('TcpConfig', foreign_keys=[ip_config_id])
    latest_record = relationship('IRSensorStatus',
                                 foreign_keys=[latest_record_id])
    locator_body = relationship('Locators', foreign_keys=[locator])


class AQIValues(db.Model, TimeStampMixin):
    __tablename__ = 'aqi_values'
    # 只有主动查询
    id = db.Column(Integer, primary_key=True)
    sensor_id = db.Column(Integer, ForeignKey("aqi_sensors.id",
                                              ondelete="CASCADE"))
    temperature = db.Column(Float)
    humidity = db.Column(Float)
    pm25 = db.Column(Float)
    co2 = db.Column(Float)
    tvoc = db.Column(Float)
    voc = db.Column(Float)
    sensor = relationship('AQISensors', foreign_keys=[sensor_id])


class AQISensors(db.Model, TimeStampMixin):
    __tablename__ = 'aqi_sensors'
    id = db.Column(Integer, primary_key=True)
    device_index_code = db.Column(Unicode(length=MEDIUM_LEN), index=True)
    locator = db.Column(Unicode(length=MEDIUM_LEN), 
                        ForeignKey(Locators.internal_code,
                                   ondelete='SET NULL'))
    latest_record_id = db.Column(Integer, ForeignKey(AQIValues.id,
                                                     ondelete="SET NULL"))
    latest_record = relationship('AQIValues', foreign_keys=[latest_record_id])
    locator_body = relationship('Locators')


class LuxValues(db.Model, TimeStampMixin):
    __tablename__ = 'lux_values'
    # 只有主动查询
    id = db.Column(Integer, primary_key=True)
    sensor_id = db.Column(Integer, ForeignKey("lux_sensors.id",
                                              ondelete='CASCADE'))
    value = db.Column(Integer)
    sensor = relationship('LuxSensors', foreign_keys=[sensor_id])


class LuxSensors(db.Model, TimeStampMixin):
    __tablename__ = 'lux_sensors'
    id = db.Column(Integer, primary_key=True)
    batch_no = db.Column(db.Integer)
    addr_no = db.Column(db.Integer)
    locator = db.Column(Unicode(length=MEDIUM_LEN),
                        ForeignKey(Locators.internal_code,
                                   ondelete='SET NULL'))
    latest_record_id = db.Column(Integer, ForeignKey(LuxValues.id,
                                                     ondelete="SET NULL"))
    latest_record = relationship('LuxValues', foreign_keys=[latest_record_id])
    locator_body = relationship('Locators')
    ip_config_id = db.Column(Integer, ForeignKey(TcpConfig.id,
                                                 ondelete='SET NULL'))
    ip_config = relationship('TcpConfig', foreign_keys=[ip_config_id])


class FireAlarmStatus(db.Model, TimeStampMixin):
    __tablename__ = 'fire_alarm_status'
    id = db.Column(Integer, primary_key=True)
    sensor_id = db.Column(Integer, ForeignKey('fire_alarm_sensors.id',
                                              ondelete='CASCADE'))
    value = db.Column(SmallInteger)
    sensor = relationship('FireAlarmSensors', foreign_keys=[sensor_id])


class FireAlarmSensors(db.Model, TimeStampMixin):
    __tablename__ = 'fire_alarm_sensors'
    id = db.Column(Integer, primary_key=True)
    device_index_code = db.Column(Unicode(length=MEDIUM_LEN), index=True)
    locator = db.Column(Unicode(length=MEDIUM_LEN),
                        ForeignKey(Locators.internal_code,
                                   ondelete='SET NULL'))
    latest_record_id = db.Column(Integer, 
                                 ForeignKey('fire_alarm_status.id',
                                            ondelete='SET NULL'))
    latest_record = relationship('FireAlarmStatus', foreign_keys=[latest_record_id])
    locator_body = relationship('Locators')


class SwitchStatus(db.Model, TimeStampMixin):
    __tablename__ = 'switch_status'
    id = db.Column(Integer, primary_key=True)
    sensor_id = db.Column(Integer, ForeignKey('switches.id',
                                              ondelete='CASCADE'))
    value = db.Column(SmallInteger)
    load = db.Column(Integer)
    sensor = relationship('Switches', foreign_keys=[sensor_id])


class Switches(db.Model, TimeStampMixin):
    __tablename__ = 'switches'
    id = db.Column(Integer, primary_key=True)
    device_index_code = db.Column(Unicode(length=MEDIUM_LEN), index=True)
    channel = db.Column(Integer)
    locator = db.Column(Unicode(length=MEDIUM_LEN), 
                        ForeignKey(Locators.internal_code,
                                   ondelete='SET NULL'))
    latest_record_id = db.Column(Integer,
                                 ForeignKey('switch_status.id',
                                            ondelete='SET NULL'))
    latest_record = relationship('SwitchStatus', 
                                 foreign_keys=[latest_record_id])
    locator_body = relationship('Locators')
    status = relationship("SwitchStatus", foreign_keys=[latest_record_id])


class ElevatorStatus(db.Model, TimeStampMixin):
    __tablename__ = 'elevator_status'
    id = db.Column(Integer, primary_key=True)
    elevator_id = db.Column(Integer, ForeignKey('elevators.id',
                                                ondelete='CASCADE'))
    floor = db.Column(Integer)
    direction = db.Column(SmallInteger)
    elevator = relationship('Elevators', foreign_keys=[elevator_id])

    @property
    def readable_direction(self):
        mapping = {1: "up",
                   2: "down",
                   0: "stop"}
        return mapping(self.direction)


class Elevators(db.Model, TimeStampMixin):
    __tablename__ = 'elevators'
    id = db.Column(Integer, primary_key=True)
    device_index_code = db.Column(Unicode(length=MEDIUM_LEN), index=True)
    locator = db.Column(Unicode(length=MEDIUM_LEN), 
                        ForeignKey(Locators.internal_code,
                                   ondelete='SET NULL'))
    latest_record_id = db.Column(Integer, ForeignKey('elevator_status.id',
                                                     ondelete='SET NULL'))
    latest_record = relationship('ElevatorStatus',
                                 foreign_keys=[latest_record_id])
