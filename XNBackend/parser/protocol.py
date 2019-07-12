# -*- encoding: utf-8 -*-
import collections
import logging
import binascii
from struct import unpack
from marshmallow import fields, Schema

from XNBackend.parser.parser import Parsable, ParsableMeta, Marshallable, Unmarshallable

L = logging.getLogger(__name__)


def data_parse(bs:bytes):
    header_info = {'bb':NetworkRelayData, 'db':InfraredSensorData, 'dd':AQISensorData, 'df':LuxSensorData}
    start_code_byte, body = bs[:1], bs[1:-1]
    start_code = str(binascii.b2a_hex(start_code_byte))[2:-1]
    data = header_info[start_code].parse(body)
    return data[0]


class AddressParseMixin:
    @property
    def _address(self):
        assert len(self.address) == 5
        return unpack('>Q', b'\x00\x00\x00' + self.address)[0] & 0xffffffffff


class NetworkRelayData(Parsable, Marshallable):
    fields = '''
        H:id, B:channel, B:status, B:loadDetect
    '''

    class MarshalSchema(Schema):
        ID = fields.Integer(attribute='id')
        Channel = fields.Integer(attribute='channel')
        Status = fields.Integer(attribute='status')
        LoadDetect = fields.Integer(attribute='loadDetect')


class InfraredSensorData(Parsable, Marshallable, AddressParseMixin):
    fields = '''
        5s:address, B:delay, B:status
    '''

    class MarshalSchema(Schema):
        Address = fields.String(attribute='address')
        Delay = fields.Integer(attribute='delay')
        Status = fields.Integer(attribute='status')


class FloatAssembler:
    def __init__(self, integer, decimal):
        self.integer = integer
        self.decimal = decimal

    def __get__(self, instance, owner):
        i = getattr(instance, self.integer)
        d = getattr(instance, self.decimal)
        return float('%d.%d' % (i, d))

class AQISensorData(Parsable, Marshallable, AddressParseMixin):
    fields = '''
        5s:address, B:temperatureInteger, B:temperatureDecimal,
        B:humidityInteger, B:humidityDecimal,  B:pmInteger, B:pmDecimal,
        B:co2Integer, B:co2Decimal, B:tvocInteger, B:tvocDecimal,
        B:vocInteger, B:vocDecimal
    '''

    temperature = FloatAssembler(integer='temperatureInteger', decimal='temperatureDecimal')
    humidity = FloatAssembler(integer='humidityInteger', decimal='humidityDecimal')
    pm = FloatAssembler(integer='pmInteger', decimal='pmDecimal')
    co2 = FloatAssembler(integer='co2Integer', decimal='co2Decimal')
    tvoc = FloatAssembler(integer='tvocInteger', decimal='tvocDecimal')
    voc = FloatAssembler(integer='vocInteger', decimal='vocDecimal')

    class MarshalSchema(Schema):
        Address = fields.String(attribute='address')
        TemperatureInteger = fields.Integer(attribute='temperatureInteger')
        TemperatureDecimal = fields.Integer(attribute='temperatureDecimal')
        HumidityInteger = fields.Integer(attribute='humidityInteger')
        HumidityDecimal = fields.Integer(attribute='humidityDecimal')
        PmInteger = fields.Integer(attribute='pmInteger')
        PmDecimal = fields.Integer(attribute='pmDecimal')
        Co2Integer = fields.Integer(attribute='co2Integer')
        Co2Decimal = fields.Integer(attribute='co2Decimal')
        TvocInteger = fields.Integer(attribute='tvocInteger')
        TvocDecimal = fields.Integer(attribute='tvocDecimal')
        VocInteger = fields.Integer(attribute='vocInteger')
        VocDecimal = fields.Integer(attribute='vocDecimal')


class LuxSensorData(Parsable, Marshallable, AddressParseMixin):
    fields = '''
        5s:address, H:luxHigh, I:luxLow
    '''

    @property
    def lux(self):
        return self.luxHigh << 32 | self.luxLow

    class MarshalSchema(Schema):
        Address = fields.String(attribute='address')
        LuxHigh = fields.Integer(attribute='luxHigh')
        LuxLow = fields.Integer(attribute='luxLow')


