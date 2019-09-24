# -*- encoding: utf-8 -*-
import collections
import logging
import binascii
from struct import unpack
from marshmallow import fields, Schema

from XNBackend.parser.parser import Parsable, ParsableMeta, Marshallable, Unmarshallable
from XNBackend.models.models import AQISensors

L = logging.getLogger(__name__)


def data_parse(bs:bytes, sensor_type=None):
    header_info = {'22':NetworkRelayData, 'df':LuxSensorData}

    start_code_byte, body = bs[:1], bs[1:]
    start_code = str(binascii.b2a_hex(start_code_byte))[2:-1]

    if start_code == 'db':
        sensor = AQISensors.query.filter_by(tcp_config_id = sensor_type).first()
        if sensor is None:
            data = InfraredSensorData.parse(body)
        else:
            data = AQISensorData.parse(body)
    else:
        data = header_info[start_code].parse(body)
    return data[0]

'''
class AddressParseMixin:
    @property
    def _address(self):
        assert len(self.address) == 5
        return unpack('>Q', b'\x00\x00\x00' + self.address)[0] & 0xffffffffff
'''

class InfraredSensorData(Parsable, Marshallable):
    fields = '''
        H:address, B:detectValue, B:setValue, B:delay, B:status, B:endCode
    '''

    class MarshalSchema(Schema):
        Address = fields.String(attribute='address')
        Delay = fields.Integer(attribute='delay')
        Status = fields.Integer(attribute='status')


class NetworkRelayData(Parsable, Marshallable):
    fields = '''
        B:id, B:code, L:status, B:endCode
    '''

    class MarshalSchema(Schema):
        ID = fields.Integer(attribute='id')
        Channel = fields.Integer(attribute='channel')
        Status = fields.Integer(attribute='status')
        LoadDetect = fields.Integer(attribute='loadDetect')


class FloatAssembler:
    def __init__(self, integer, decimal, valueType):
        self.integer = integer
        self.decimal = decimal
        self.value = valueType 

    def __get__(self, instance, owner):
        i = getattr(instance, self.integer)
        d = getattr(instance, self.decimal)
        value = getattr(instance, self.value)
        ad = (i*256+d)
        if value == 'temp':
            return ad/10 
        elif value == 'pm25':
            return 0.17*ad*(5.0/1024)-0.1
        elif value == 'co2':
            return 44*ad/22.4
        else:
            return ad 
        

class AQISensorData(Parsable, Marshallable):
    fields = '''
        H:address, B:co2Integer,  B:co2Decimal, B:tvocInteger, B:tvocDecimal, 
        B:hchoInteger, B:hchoDecimal, B:pmInteger, B:pmDecimal,
        B:humidityInteger, B:humidityDecimal,
        B:temperatureInteger, B:temperatureDecimal, B:endCode
    '''
    
    temperature = FloatAssembler(integer='temperatureInteger', decimal='temperatureDecimal', valueType='temp')
    humidity = FloatAssembler(integer='humidityInteger', decimal='humidityDecimal', valueType='temp')
    co2 = FloatAssembler(integer='co2Integer', decimal='co2Decimal', valueType='co2')
    tvoc = FloatAssembler(integer='tvocInteger', decimal='tvocDecimal', valueType='tvoc')
    hcho = FloatAssembler(integer='hchoInteger', decimal='hchoDecimal', valueType='hcho')
    pm25 = FloatAssembler(integer='pmInteger', decimal='pmDecimal', valueType='pm25')


class LuxSensorData(Parsable, Marshallable):
    fields = '''
        H:address, B:lux, B:endCode
    '''
    '''
    @property
    def lux(self):
        return self.luxHigh << 32 | self.luxLow
    '''

    class MarshalSchema(Schema):
        Address = fields.String(attribute='address')
        LuxHigh = fields.Integer(attribute='luxHigh')
        LuxLow = fields.Integer(attribute='luxLow')


