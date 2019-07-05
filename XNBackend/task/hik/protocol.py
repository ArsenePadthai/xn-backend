# -*- encoding: utf-8 -*-
import collections
import logging
from binascii import b2a_hex
from enum import Enum

from marshmallow import fields, Schema

from XNBackend.task.hik.parser import Parsable, ParsableMeta, Marshallable, Unmarshallable

L = logging.getLogger(__name__)


class DeviceType(Enum):
    NBIOT_TELECOM = 10
    NBIOT_UDP = 20
    ETHERNET_UDP = 30


class PacketRevision(Enum):
    NBIOT = 0x00
    ETHERNET = 0x08


class DeviceReportDataMeta(ParsableMeta):
    registered_report_types = {}

    def __init__(cls, t, obj, o, **kwargs):
        super().__init__(t, obj, o)
        if hasattr(cls, 'target_revision'):
            message_type_map = collections.defaultdict(dict)
            message_type_map['__header'] = cls
            DeviceReportDataMeta.registered_report_types[cls.target_revision] = message_type_map
            L.debug('register report revision %r as %r', cls.target_revision, cls)
        elif hasattr(cls, 'header_revision') and hasattr(cls, 'message_type'):
            if cls.header_revision not in DeviceReportDataMeta.registered_report_types:
                raise TypeError('unregistered revision class %r' % (cls.header_revision,))
            elif cls.message_type in DeviceReportDataMeta.registered_report_types[cls.header_revision]:
                raise TypeError('message type %r has been registered by %r' % (
                    cls.message_type,
                    DeviceReportDataMeta.registered_report_types[cls.header_revision][cls.message_type]
                ))
            else:
                DeviceReportDataMeta.registered_report_types[cls.header_revision][cls.message_type] = cls
                L.debug('register message type %s of revision %r as %r', cls.message_type, cls.header_revision, cls)


class DeviceInfoHeader(Parsable, metaclass=DeviceReportDataMeta):
    @property
    def revision(self):
        return PacketRevision(self.revision_)

    @property
    def message_type_map(self):
        return DeviceReportDataMeta.registered_report_types[self.revision]

    @classmethod
    def get_header_cls_by_revision(cls, revision):
        if isinstance(revision, PacketRevision):
            try:
                revision = PacketRevision(revision)
            except ValueError:
                raise ValueError('revision should be either PacketRevision instance or valid value of PacketRevision')
        return DeviceReportDataMeta.registered_report_types[revision]['__header']


class NBIOTDeviceInfoHeader(DeviceInfoHeader):
    target_revision = PacketRevision.NBIOT
    fields = 'B:revision_, 16s:imei, H:seq'


class EthernetDeviceInfoHeader(DeviceInfoHeader):
    target_revision = PacketRevision.ETHERNET
    fields = 'B:revision_, 12s:hwid, 4s:reserved, H:seq'


class MessageType(Parsable, int):
    scalar = True
    format = 'B'


class ReportData(Parsable, metaclass=DeviceReportDataMeta):
    @staticmethod
    def parse_message(bs: bytes) -> (DeviceInfoHeader, MessageType, Parsable):
        revision = PacketRevision(int(bs[0]))
        header_cls = DeviceInfoHeader.get_header_cls_by_revision(revision)
        header, bs = header_cls.parse(bs)
        msg_type, bs = MessageType.parse(bs)
        message_cls = header.message_type_map[msg_type]
        L.debug('msg_type %d mapping to %s', msg_type, message_cls.__name__)
        answer, bs = message_cls.parse(bs)
        if len(bs) > 0:
            L.warning('remaining %d bytes after parsing: %s', len(bs), b2a_hex(bs))
        return header, msg_type, answer


class NBIoTSensorData(ReportData, Marshallable):
    header_revision = PacketRevision.NBIOT
    service = 'BasicStatus'
    message_type = 0
    fields = '''
        B:flags, h:v220ma, h:v24ma, h:v12ma,
        h:temperatureBy10, H:humidityBy10,
        H:pm25, H:pm10,
        I:lux1, I:lux2, I:lux3,
        H:voicePeak, H:voiceAverage
    '''

    class MarshalSchema(Schema):
        TemperatureBy10 = fields.Integer(attribute='temperatureBy10')
        HumidityBy10 = fields.Integer(attribute='humidityBy10')
        Flags = fields.Integer(attribute='flags')
        V220mA = fields.Integer(attribute='v220ma')
        V24mA = fields.Integer(attribute='v24ma')
        V12mA = fields.Integer(attribute='v12ma')
        Lux1 = fields.Integer(attribute='lux1')
        Lux2 = fields.Integer(attribute='lux2')
        Lux3 = fields.Integer(attribute='lux3')
        VoicePeak = fields.Integer(attribute='voicePeak')
        VoiceAverage = fields.Integer(attribute='voiceAverage')
        PM25 = fields.Integer(attribute='pm25')
        PM10 = fields.Integer(attribute='pm10')


class BC95ConnectivityInfo(ReportData):
    header_revision = PacketRevision.NBIOT
    message_type = 1
    fields = '''
        I:valid_fields,
        b:rssi, B:ecl, b:sinr,
        B:rsrq, h:rsrp,
        H:daily_active_time,
        I:cell_id, I:earfcn, 3s:pci
    '''


class EthernetSensorData(ReportData, Marshallable):
    header_revision = PacketRevision.ETHERNET
    service = 'BasicStatus'
    message_type = 0
    fields = '''
        B:flags,
        h:v24v1, h:v24v2, h:v24v3,
        h:v12v1, h:v12v2, h:v12v3, h:v220v1,
        h:v24ma1, h:v24ma2, h:v24ma3,
        h:v12ma1, h:v12ma2, h:v12ma3, h:v220ma1,
        h:temperatureBy10, H:humidityBy10
    '''

    class MarshalSchema(Schema):
        TemperatureBy10 = fields.Integer(attribute='temperatureBy10')
        HumidityBy10 = fields.Integer(attribute='humidityBy10')
        Flags = fields.Integer(attribute='flags')
        Amp1 = fields.Integer(attribute='v220ma1')
        Amp2 = fields.Integer(attribute='v24ma1')
        Amp3 = fields.Integer(attribute='v12ma1')
        Amp4 = fields.Integer(attribute='v24ma2')
        Amp5 = fields.Integer(attribute='v24ma3')
        Amp6 = fields.Integer(attribute='v12ma2')
        Amp7 = fields.Integer(attribute='v12ma3')
        ACVoltage1 = fields.Integer(attribute='v220v1')
        ACVoltage2 = fields.Integer(attribute='v24v1')
        ACVoltage3 = fields.Integer(attribute='v24v2')
        ACVoltage4 = fields.Integer(attribute='v24v3')
        DCVoltage1 = fields.Integer(attribute='v12v1')
        DCVoltage2 = fields.Integer(attribute='v12v2')
        DCVoltage3 = fields.Integer(attribute='v12v3')


class CommandHead(Parsable):
    HEAD_OF_COMMAND = 0x55
    fields = '''
        B:head, B:command_id, H:command_seq,
        B:checksum, B:length
    '''

    # noinspection PyArgumentList
    @classmethod
    def new_header(cls, command_id, seq, body):
        length = len(body)
        if length > 0xff:
            raise ValueError('body exceeds 255 bytes: ' + str(length))
        unchecked = CommandHead(
            cls.HEAD_OF_COMMAND, command_id, seq,
            0x00, length
        )
        unchecked_bs = (~(0xff & sum(unchecked.encode() + body)) + 1) & 0xff
        return CommandHead(
            cls.HEAD_OF_COMMAND, command_id, seq,
            unchecked_bs, length
        )


class CommandMeta(ParsableMeta):
    registered_commands = collections.defaultdict(
        lambda: collections.defaultdict(dict)
    )

    # noinspection PyUnresolvedReferences
    def __init__(cls, t, obj, o, **kwargs):
        super().__init__(t, obj, o)
        if hasattr(cls, 'service') and hasattr(cls, 'method') and hasattr(cls, 'device_type'):
            CommandMeta.registered_commands[cls.device_type][cls.service][cls.method] = cls


class Command(Parsable, metaclass=CommandMeta):
    command_id = None

    def wrap(self, seq):
        body = self.encode() if getattr(self, 'format', None) else b''
        header = CommandHead.new_header(self.command_id, seq, body)
        return header.encode() + body

    @classmethod
    def load_one_command(cls, d):
        device_type = DeviceType(d['device']['deviceType'])
        cmd_cls = cls.registered_commands[device_type][d['service']].get(d['method'], None)
        if not cmd_cls:
            raise ValueError('cannot find command %s/%s for device_type %s' % (d['service'], d['method'], device_type))
        elif not issubclass(cmd_cls, Unmarshallable):
            raise ValueError(
                'concrete command class %r must be subclass of parser.Unmarshallable' % (cmd_cls,)
            )
        return cmd_cls.unmarshal(
            # not .get('params', {}) because server may return None in params
            # which doesn't trigger marshmallow validator
            d.get('params') or {}
        )

    @classmethod
    def load_commands(cls, d):
        return [cls.load_one_command(cmd) for cmd in d]


class CommandAck(Command):
    command_id = 0x80
    device_type = DeviceType.ETHERNET_UDP


class CommandRelayCycle(Command, Unmarshallable):
    command_id = 0x81
    device_type = DeviceType.ETHERNET_UDP
    service = 'BasicStatus'
    method = 'RelayCycle'

    fields = '''
        B:relay_id, B:relay_state
    '''

    class MarshalSchema(Schema):
        relay_id = fields.Integer(required=True)
        relay_state = fields.Integer(required=True)
