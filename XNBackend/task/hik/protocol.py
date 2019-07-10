# -*- encoding: utf-8 -*-
import collections
import logging
import binascii
from marshmallow import fields, Schema

from XNBackend.task.hik.parser import Parsable, ParsableMeta, Marshallable, Unmarshallable

L = logging.getLogger(__name__)


def data_parse(bs:bytes):
    header_info = {'bb':NetworkRelayData, 'db':InfraredSensorData, 'dd':AQISensorData, 'df':IlluminationSensorData}
    start_code_byte, body = bs[:1], bs[1:-1]
    start_code = str(binascii.b2a_hex(start_code_byte))[2:-1]
    data = header_info[start_code].parse(body)
    return data


class NetworkRelayData(Parsable, Marshallable):
    fields = '''
        H:id, B:channel, B:status, B:loadDetect
    '''

    class MarshalSchema(Schema):
        ID = fields.Integer(attribute='id')
        Channel = fields.Integer(attribute='channel')
        Status = fields.Integer(attribute='status')
        LoadDetect = fields.Integer(attribute='loadDetect')


class InfraredSensorData(Parsable, Marshallable):
    fields = '''
        10s:address, B:delay, B:status
    '''

    class MarshalSchema(Schema):
        Address = fields.String(attribute='address')
        Delay = fields.Integer(attribute='delay')
        Status = fields.Integer(attribute='status')


class AQISensorData(Parsable, Marshallable):
    fields = '''
        10s:address, B:tempHigh, B:tempLow,
        B:humidityHigh, B:humidityLow,  B:pmHigh, B:pmLow,
        B:co2High, B:co2Low, B:tvocHigh, B:tvocLow,
        B:vocHigh, B:vocLow
    '''

    class MarshalSchema(Schema):
        Address = fields.String(attribute='address')
        TempHigh = fields.Integer(attribute='tempHigh')
        TempLow = fields.Integer(attribute='tempLow')
        HumidityHigh = fields.Integer(attribute='humidityHigh')
        HumidityLow = fields.Integer(attribute='humidityLow')
        PmHigh = fields.Integer(attribute='pmHigh')
        PmLow = fields.Integer(attribute='pmLow')
        Co2High = fields.Integer(attribute='co2High')
        Co2Low = fields.Integer(attribute='co2Low')
        TvocHigh = fields.Integer(attribute='tvocHigh')
        TvocLow = fields.Integer(attribute='tvocLow')
        VocHigh = fields.Integer(attribute='vocHigh')
        VocLow = fields.Integer(attribute='vocLow')


class IlluminationSensorData(Parsable, Marshallable):
    fields = '''
        10s:address, H:illumHigh, I:illumLow
    '''

    class MarshalSchema(Schema):
        Address = fields.String(attribute='address')
        IllumHigh = fields.Integer(attribute='illumHigh')
        IllumLow = fields.Integer(attribute='illumLow')


