# -*- encoding: utf-8 -*-
import logging
import re
from collections import namedtuple
from struct import unpack, calcsize, pack
from typing import Any

L = logging.getLogger(__name__)

fields_splitter = re.compile(r',\s*')


def split_field_definition(fields):
    f = []
    n = []
    for field in fields_splitter.split(fields.strip()):
        fmt, name = field.split(':', 1)
        f.append(fmt)
        n.append(name)
    return ''.join(f), ','.join(n)


class ParsableMeta(type):
    def __new__(mcs, name, bases, namespace) -> Any:
        if 'fields' in namespace:
            fmt, field_names = split_field_definition(namespace.pop('fields'))
            bases = bases + (namedtuple(name, field_names),)
            namespace['format'] = fmt
        return super().__new__(mcs, name, bases, namespace)


class Parsable(object, metaclass=ParsableMeta):
    scalar = False
    endian = '>'

    @classmethod
    def parse(cls, bs: bytes) -> ('Parsable', bytes):
        struct_format = cls.endian + cls.format
        size = calcsize(struct_format)
        if size > len(bs):
            raise ValueError('expect %d bytes but only %d received' % (size, len(bs)))
        mine, rest = bs[:size], bs[size:]
        L.debug('%d bytes consumed, %d remain', len(mine), len(rest))
        obj = cls(*unpack(struct_format, mine))
        L.debug('get %s %s', obj.__class__.__name__, obj)
        return obj, rest

    def encode(self) -> bytes:
        struct_format = self.endian + self.format
        variables = (self,) if self.scalar else tuple(self)
        return pack(struct_format, *variables)


class Marshallable(object):
    def marshal(self):
        result = self.MarshalSchema().dump(self._asdict())
        if result.errors:
            raise ValueError(result.errors)
        return result.data


class Unmarshallable(object):
    @classmethod
    def unmarshal(cls, data, many=False):
        loaded = cls.MarshalSchema(many=many, strict=True).load(data)
        d = loaded.data
        if many:
            return [cls(**ele) for ele in d]
        else:
            return cls(**d)
