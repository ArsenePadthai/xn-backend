# -*- coding:utf-8 -*-
from .base import db
import logging

from sqlalchemy import ForeignKey, Unicode, BOOLEAN, TIMESTAMP, String, \
    SmallInteger, Integer, Float, Time
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from flask_bcrypt import generate_password_hash, check_password_hash
from XNBackend.api_client.air_conditioner import get_ac_data, set_ac_data

L = logging.getLogger(__name__)

SHORT_LEN = 30
MEDIUM_LEN = 50
LONG_LEN = 100


class TimeStampMixin:
    created_at = db.Column(TIMESTAMP, nullable=False,
                           server_default=func.current_timestamp())
    updated_at = db.Column(TIMESTAMP, onupdate=func.current_timestamp())


class CarbonMixin:
    carbon_mixin_factor = 0.33*0.68
    carbon_mixin_watt_attr_name = ''
    @property
    def carbon_emission(self):
        return getattr(self, self.carbo_mixin_watt_attr_name) \
            * self.carbon_mixin_factor


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
    password = db.Column(String(200))
    level = db.Column(SmallInteger)
    user_ref = relationship('Users', backref='user_logins')

    @property
    def level_repr(self):
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
    desc = db.Column(String(100))


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
    acs_record = relationship("AcsRecords",
                              foreign_keys=[latest_acs_record_id])


class AcsRecords(db.Model, TimeStampMixin):
    __tablename__ = "acs_records"
    id = db.Column(Integer, primary_key=True)
    acs_id = db.Column(Integer, ForeignKey(TrackingDevices.id,
                                           ondelete="CASCADE"))
    # status =1 means open status=0 means closing
    status = db.Column(SmallInteger)
    event_type = db.Column(Integer)
    event_id = db.Column(Unicode(length=LONG_LEN))
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


class MantunciBox(db.Model, TimeStampMixin):
    __tablename__ = 'mantunci_box'
    id = db.Column(Integer, primary_key=True)
    mac = db.Column(Unicode(length=MEDIUM_LEN), index=True)
    name = db.Column(String(SHORT_LEN))
    phone = db.Column(String(SHORT_LEN))
    latest_alarm_id = db.Column(Integer, ForeignKey('box_alarms.id',
                                                    ondelete='SET NULL'))
    latest_alarm = relationship('BoxAlarms', foreign_keys=[latest_alarm_id])
    locator_id = db.Column(Unicode(length=MEDIUM_LEN),
                           ForeignKey(Locators.internal_code,
                                      ondelete='SET NULL'))
    locator = relationship('Locators', foreign_keys=[locator_id])


class S3FC20(db.Model, TimeStampMixin):
    __tablename__ = 's3_fc20'
    id = db.Column(Integer, primary_key=True)
    addr = db.Column(Integer)
    desc = db.Column(Unicode(LONG_LEN))
    box_id = db.Column(Integer, ForeignKey(MantunciBox.id,
                                           ondelete="SET NULL"))
    box = relationship('MantunciBox')
    latest_record_id = db.Column(Integer, ForeignKey('s3_fc20_records.id',
                                                     ondelete='SET NULL'))
    latest_record = relationship(
        'S3FC20Records', foreign_keys=[latest_record_id])
    # 0 means light, 1 means ac, 2 means power socket
    measure_type = db.Column(SmallInteger)
    locator_id = db.Column(Unicode(length=MEDIUM_LEN),
                           ForeignKey(Locators.internal_code,
                                      ondelete='SET NULL'))
    locator = relationship('Locators', foreign_keys=[locator_id])


class S3FC20Records(db.Model, TimeStampMixin):
    __tablename__ = 's3_fc20_records'
    id = db.Column(Integer, primary_key=True)
    s3_fc20_id = db.Column(Integer, ForeignKey(S3FC20.id,
                                               ondelete='CASCADE'))
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
    s3_fc20 = relationship("S3FC20", foreign_keys=[s3_fc20_id])


class BoxAlarms(db.Model, TimeStampMixin):
    __tablename__ = 'box_alarms'
    id = db.Column(Integer, primary_key=True)
    box_id = db.Column(Integer, ForeignKey(MantunciBox.id,
                                           ondelete='CASCADE'),
                       nullable=False)
    addr = db.Column(Integer)
    node = db.Column(String(MEDIUM_LEN))
    alarm_or_type = db.Column(String(SHORT_LEN))
    info = db.Column(String(MEDIUM_LEN))
    type_number = db.Column(SmallInteger)
    time = db.Column(TIMESTAMP)
    box = relationship('MantunciBox', foreign_keys=[box_id])

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
            9: '漏电保护功能正常',
            10: '漏电保护自检未完成',
            11: '打火报警',
            12: '漏电预警',
            13: '电流预警',
            14: '过压预警',
            15: '欠压预警',
            16: '通讯报警'
        }
        return alarm_info_mapping[self.type_number]


class EnergyConsumeByHour(db.Model, TimeStampMixin, CarbonMixin):
    __tablename__ = 'energy_consume_by_hour'
    carbon_mixin_watt_attr_name = 'electricity'
    consume_id = db.Column(Integer, primary_key=True)
    box_id = db.Column(Integer, ForeignKey(MantunciBox.id,
                                           ondelete='CASCADE'))
    s3_fc20_id = db.Column(Integer, ForeignKey(S3FC20.id,
                                               ondelete='SET NULL'))
    electricity = db.Column(Float)
    box = relationship('MantunciBox', foreign_keys=[
                       box_id], backref='hour_consume')
    s3_fc20 = relationship('S3FC20', foreign_keys=[s3_fc20_id])


class EnergyConsumeDaily(db.Model, TimeStampMixin, CarbonMixin):
    __tablename__ = 'energy_consume_daily'
    carbon_mixin_watt_attr_name = 'electricity'
    consume_id = db.Column(Integer, primary_key=True)
    box_id = db.Column(Integer, ForeignKey(MantunciBox.id,
                                           ondelete='CASCADE'))
    s3_fc20_id = db.Column(Integer, ForeignKey(S3FC20.id,
                                               ondelete='SET NULL'))
    electricity = db.Column(Float)
    box = relationship('MantunciBox', foreign_keys=[
                       box_id], backref='daily_consume')
    s3_fc20 = relationship('S3FC20', foreign_keys=[s3_fc20_id])


class EnegyConsumeMonthly(db.Model, TimeStampMixin):
    __tablename__ = 'energy_consume_monthly'
    consume_id = db.Column(Integer, primary_key=True)
    box_id = db.Column(Integer, ForeignKey(MantunciBox.id))
    s3_fc20_id = db.Column(Integer, ForeignKey(S3FC20.id,
                                               ondelete='SET NULL'))
    electricity = db.Column(Float)
    box = relationship('MantunciBox', foreign_keys=[
                       box_id], backref='monthly_consume')
    s3_fc20 = relationship('S3FC20', foreign_keys=[s3_fc20_id])


class IRSensorStatus(db.Model, TimeStampMixin):
    __tablename__ = 'ir_sensor_status'
    id = db.Column(Integer, primary_key=True)
    sensor_id = db.Column(Integer, ForeignKey("ir_sensors.id",
                                              ondelete="CASCADE"))
    value = db.Column(db.Integer)
    status = db.Column(db.BOOLEAN)
    sensor = relationship('IRSensors', foreign_keys=[sensor_id])


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
                                            ondelete='SET NULL'))
    threshold = db.Column(db.Integer)
    delay = db.Column(db.Integer)
    tcp_config_id = db.Column(Integer, ForeignKey(TcpConfig.id,
                                                 ondelete='SET NULL'))
    tcp_config = relationship('TcpConfig', foreign_keys=[tcp_config_id])
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
    pm25 = db.Column(db.DECIMAL(8, 3))
    co2 = db.Column(Float)
    tvoc = db.Column(Float)
    hcho = db.Column(Float)
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
    tcp_config_id = db.Column(Integer, ForeignKey(TcpConfig.id,
                                                  ondelete='set null'))
    tcp_config = relationship('TcpConfig', foreign_keys=[tcp_config_id])


class AQIEventCount(db.Model):
    __tablename__ = "aqi_event_count"
    id = db.Column(Integer, primary_key=True)
    aqi_id = db.Column(Integer, ForeignKey(AQISensors.id,
                                           ondelete="CASCADE"))
    count = db.Column(Integer)


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
    tcp_config_id = db.Column(Integer, ForeignKey(TcpConfig.id,
                                                  ondelete='set null'))
    tcp_config = relationship('TcpConfig', foreign_keys=[tcp_config_id])


class LuxEventCount(db.Model):
    __tablename__ = 'lux_event_count'
    id = db.Column(Integer, primary_key=True)
    lux_id = db.Column(Integer, ForeignKey(LuxSensors.id,
                                           ondelete="CASCADE"))
    count = db.Column(Integer)


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
    latest_record = relationship('FireAlarmStatus',
                                 foreign_keys=[latest_record_id])
    locator_body = relationship('Locators')


class SwitchPanel(db.Model, TimeStampMixin):
    __tablename__ = 'switch_panel'
    id = db.Column(Integer, primary_key=True)
    batch_no = db.Column(db.Integer)
    addr_no = db.Column(db.Integer)
    desc = db.Column(Unicode(length=LONG_LEN))
    # when panel_type is 0 means four control, when panel_type is 1 means double control
    panel_type = db.Column(SmallInteger)
    tcp_config_id = db.Column(Integer, ForeignKey(TcpConfig.id,
                                                  ondelete='set null'))
    tcp_config = relationship('TcpConfig', foreign_keys=[tcp_config_id])
    locator_id = db.Column(Unicode(length=MEDIUM_LEN),
                           ForeignKey(Locators.internal_code,
                                      ondelete='SET NULL'))
    locator = relationship('Locators')


class Switches(db.Model, TimeStampMixin):
    __tablename__ = 'switches'
    id = db.Column(Integer, primary_key=True)
    channel = db.Column(Integer)
    switch_panel_id = db.Column(Integer,
                                ForeignKey('switch_panel.id',
                                           ondelete='SET NULL'))
    status = db.Column(SmallInteger)
    switch_panel = relationship('SwitchPanel', foreign_keys=[switch_panel_id])
    desc = db.Column(String(100))

    @property
    def four_control_type_readable(self):
        if self.channel == 1:
            return u'main light'
        elif self.channel == 2:
            return u'acs'
        elif self.channel == 3:
            return u'auto'
        elif self.channel == 4:
            return u'aux light'

    @property
    def double_control_type_readable(self):
        if self.channel == 1:
            return u'main light'
        elif self.channel == 2:
            return u'auto'


class Relay(db.Model, TimeStampMixin):
    __tablename__ = 'relay'
    id = db.Column(Integer, primary_key=True)
    device_index_code = db.Column(Unicode(length=MEDIUM_LEN), index=True)
    addr = db.Column(Integer)
    channel = db.Column(Integer)
    switch_id = db.Column(Integer, ForeignKey('switches.id',
                                              ondelete='SET NULL'))
    switch = relationship('Switches', foreign_keys=[switch_id])
    locator_id = db.Column(Unicode(length=MEDIUM_LEN),
                           ForeignKey(Locators.internal_code,
                                      ondelete='SET NULL'))
    locator = relationship('Locators')
    tcp_config_id = db.Column(Integer, ForeignKey(TcpConfig.id,
                                                  ondelete='set null'))
    tcp_config = relationship('TcpConfig', foreign_keys=[tcp_config_id])
    IPAddr = db.Column(String(100))


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
        return mapping[self.direction]


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


class AutoControllers(db.Model, TimeStampMixin):
    __tablename__ = 'auto_controllers'
    id = db.Column(Integer, primary_key=True)
    # 0 means manual 1 means auto
    if_auto = db.Column(SmallInteger)
    ir_count = db.Column(SmallInteger)
    start_time = db.Column(Time)
    end_time = db.Column(Time)
    switch_panel_id = db.Column(Integer,
                                ForeignKey('switch_panel.id',
                                           ondelete='SET NULL'))
    switch_panel = relationship('SwitchPanel', foreign_keys=[switch_panel_id])
    ir_sensor_id = db.Column(Integer,
                                ForeignKey('ir_sensors.id',
                                           ondelete='SET NULL'))
    ir_sensor = relationship('IRSensors', foreign_keys=[ir_sensor_id])
    lux_sensor_id = db.Column(Integer,
                              ForeignKey('lux_sensors.id',
                                         ondelete='SET NULL'))
    lux_sensor = relationship('LuxSensors', foreign_keys=[lux_sensor_id])


class AirConditioner(db.Model, TimeStampMixin):
    __tablename__ = 'air_conditioner'
    device_index_code = db.Column(Unicode(length=MEDIUM_LEN), primary_key=True)
    desired_speed = db.Column(Integer)
    if_online = db.Column(SmallInteger)
    desired_mode = db.Column(SmallInteger)
    temperature = db.Column(Integer)
    ac_on = db.Column(SmallInteger)
    desired_temperature = db.Column(SmallInteger)
    locator_id = db.Column(Unicode(length=MEDIUM_LEN), ForeignKey(Locators.internal_code,
                                                                  ondelete='SET NULL'))
    locator = relationship('Locators')

    def apply_values(self, data):
        assert self.device_index_code == data.get('deviceCode')
        if data.get('errCode', 0) != 0:
            reason = data.get('errMsg')
            L.info(f'Failed to get values of ac reason: {reason}')
            return

        online = data.get('online')
        if not online:
            self.if_online = 0
            return
        else:
            self.if_online = 1

        for d in data.get('variantDatas'):
            if d['code'] == 'FanSpeedSet':
                self.desired_speed = int(d['value'])
                continue
            if d['code'] == 'ModeCmd':
                self.desired_mode = int(d['value'])
                continue
            if d['code'] == 'RoomTemp':
                self.temperature = int(d['value'])
                continue
            if d['code'] == 'StartStopStatus':
                self.ac_on = int(d['value'])
                continue
            if d['code'] == 'TempSet':
                self.desired_temperature = int(d['value'])

    def update_values(self):
        ret = get_ac_data([self.device_index_code])
        self.apply_values(ret['data'][0])
