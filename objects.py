# TODO:
#   what is "DYNPROPS: True"?
#   where do descriptions come from?
#   how to determine start of TOC in class instance?
# BUGs:
#   class instance: "root\\CIMV2" Microsoft_BDD_Info NS_68577372C66A7B20658487FBD959AA154EF54B5F935DCC5663E9228B44322805/CI_6FCB95E1CB11D0950DA7AE40A94D774F02DCD34701D9645E00AB9444DBCF640B/IL_EEC4121F2A07B61ABA16414812AA9AFC39AB0A136360A5ACE2240DC19B0464EB.1606.116085.3740

import logging
import functools
from datetime import datetime
from collections import namedtuple

from funcy.objects import cached_property

from common import h
from common import one
from common import LoggingObject
from cim import Key
from cim import Index
from cim import CIM_TYPE_XP
from cim import CIM_TYPE_WIN7
import vstruct
from vstruct.primitives import *

logging.basicConfig(level=logging.DEBUG)
g_logger = logging.getLogger("cim.objects")


ROOT_NAMESPACE_NAME = "root"
SYSTEM_NAMESPACE_NAME = "__SystemClass"
NAMESPACE_CLASS_NAME = "__namespace"


class FILETIME(vstruct.primitives.v_prim):
    _vs_builder = True
    def __init__(self):
        vstruct.primitives.v_prim.__init__(self)
        self._vs_length = 8
        self._vs_value = "\x00" * 8
        self._vs_fmt = "<Q"
        self._ts = datetime.min

    def vsParse(self, fbytes, offset=0):
        offend = offset + self._vs_length
        q = struct.unpack("<Q", fbytes[offset:offend])[0]
        try:
            self._ts = datetime.utcfromtimestamp(float(q) * 1e-7 - 11644473600 )
        except ValueError:
            self._ts = datetime.min
        return offend

    def vsEmit(self):
        raise NotImplementedError()

    def vsSetValue(self, guidstr):
        raise NotImplementedError()

    def vsGetValue(self):
        return self._ts

    def __repr__(self):
        return self._ts.isoformat("T") + "Z"


class WMIString(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.zero = v_uint8()
        self.s = v_zstr()

    def __repr__(self):
        return repr(self.s)

    def vsGetValue(self):
        return self.s.vsGetValue()


class ClassDefinitionHeader(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.super_class_unicode_length = v_uint32()
        self.super_class_unicode = v_wstr(size=0)  # not present if no superclass
        self.timestamp = FILETIME()
        self.unk0 = v_uint8()
        self.unk1 = v_uint32()
        self.offset_class_name = v_uint32()
        self.junk_length = v_uint32()

        # junk type:
        #   0x19 - has 0xC5000000 at after about 0x10 bytes of 0xFF
        #     into `junk`
        self.unk3 = v_uint32()
        self.super_class_ascii = WMIString()  # not present if no superclass

        # has to do with junk
        # if junk type:
        #   0x19 - then 0x11
        #   0x18 - then 0x10
        #   0x17 - then 0x0F
        self.unk4 = v_uint32()  # not present if no superclass

    def pcb_super_class_unicode_length(self):
        self["super_class_unicode"].vsSetLength(self.super_class_unicode_length * 2)
        if self.super_class_unicode_length == 0:
            self.vsSetField("super_class_ascii", v_str(size=0))
            self.vsSetField("unk4", v_str(size=0))


CIM_TYPES = v_enum()
CIM_TYPES.CIM_TYPE_LANGID = 0x3
CIM_TYPES.CIM_TYPE_REAL32 = 0x4
CIM_TYPES.CIM_TYPE_STRING = 0x8
CIM_TYPES.CIM_TYPE_BOOLEAN = 0xB
CIM_TYPES.CIM_TYPE_UINT8 = 0x11
CIM_TYPES.CIM_TYPE_UINT16 = 0x12
CIM_TYPES.CIM_TYPE_UINT32= 0x13
CIM_TYPES.CIM_TYPE_UINT64 = 0x15
CIM_TYPES.CIM_TYPE_DATETIME = 0x65

CIM_TYPE_SIZES = {
    CIM_TYPES.CIM_TYPE_LANGID: 4,
    CIM_TYPES.CIM_TYPE_REAL32: 4,
    CIM_TYPES.CIM_TYPE_STRING: 4,
    CIM_TYPES.CIM_TYPE_BOOLEAN: 2,
    CIM_TYPES.CIM_TYPE_UINT8: 1,
    CIM_TYPES.CIM_TYPE_UINT16: 2,
    CIM_TYPES.CIM_TYPE_UINT32: 4,
    CIM_TYPES.CIM_TYPE_UINT64: 8,
    # looks like: stringref to "\x00 00000000000030.000000:000"
    CIM_TYPES.CIM_TYPE_DATETIME: 4
}


class BaseType(object):
    """
    this acts like a CimType, but its not backed by some bytes,
      and is used to represent a type.
    probably not often used. good example is an array CimType
      that needs to pass along info on the type of each item.
      each item is not an array, but has the type of the array.
    needs to adhere to CimType interface.
    """
    def __init__(self, type_, value_parser):
        self._type = type_
        self._value_parser = value_parser

    @property
    def type(self):
        return self._type

    @property
    def is_array(self):
        return False

    @property
    def value_parser(self):
        return self._value_parser

    def __repr__(self):
        return CIM_TYPES.vsReverseMapping(self._type)

    @property
    def base_type_clone(self):
        return self


ARRAY_STATES = v_enum()
ARRAY_STATES.NOT_ARRAY = 0x0
ARRAY_STATES.ARRAY = 0x20


BOOLEAN_STATES = v_enum()
BOOLEAN_STATES.FALSE = 0x0
BOOLEAN_STATES.TRUE = 0xFFFF


class CimType(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.type = enum_uint8(CIM_TYPES)
        self.array_state = enum_uint8(ARRAY_STATES)
        self.unk0 = v_uint8()
        self.unk2 = v_uint8()

    @property
    def is_array(self):
        # TODO: this is probably a bit-flag
        return self.array_state == ARRAY_STATES.ARRAY

    @property
    def value_parser(self):
        if self.is_array:
            return v_uint32
        elif self.type == CIM_TYPES.CIM_TYPE_LANGID:
            return v_uint32
        elif self.type == CIM_TYPES.CIM_TYPE_REAL32:
            return v_float
        elif self.type == CIM_TYPES.CIM_TYPE_STRING:
            return v_uint32
        elif self.type == CIM_TYPES.CIM_TYPE_BOOLEAN:
            return functools.partial(enum_uint16, BOOLEAN_STATES)
        elif self.type == CIM_TYPES.CIM_TYPE_UINT8:
            return v_uint8
        elif self.type == CIM_TYPES.CIM_TYPE_UINT16:
            return v_uint16
        elif self.type == CIM_TYPES.CIM_TYPE_UINT32:
            return v_uint32
        elif self.type == CIM_TYPES.CIM_TYPE_UINT64:
            return v_uint64
        elif self.type == CIM_TYPES.CIM_TYPE_DATETIME:
            return v_uint32
        else:
            raise RuntimeError("unknown qualifier type: %s", h(self.type))

    def __repr__(self):
        r = ""
        if self.is_array:
            r += "arrayref to "
        r += CIM_TYPES.vsReverseMapping(self.type)
        return r

    @property
    def base_type_clone(self):
        return BaseType(self.type, self.value_parser)


BUILTIN_QUALIFIERS = v_enum()
BUILTIN_QUALIFIERS.PROP_KEY = 0x1
BUILTIN_QUALIFIERS.PROP_READ_ACCESS = 0x3
BUILTIN_QUALIFIERS.CLASS_NAMESPACE = 0x6
BUILTIN_QUALIFIERS.CLASS_UNK = 0x7
BUILTIN_QUALIFIERS.PROP_TYPE = 0xA


class QualifierReference(vstruct.VStruct):
    # ref:4 + unk0:1 + valueType:4 = 9
    MIN_SIZE = 9

    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.key_reference = v_uint32()
        self.unk0 = v_uint8()
        self.value_type = CimType()
        self.value = v_bytes(size=0)

    def pcb_value_type(self):
        P = self.value_type.value_parser
        self.vsSetField("value", P())

    @property
    def is_builtin_key(self):
        return self.key_reference & 0x80000000 > 0

    @property
    def key(self):
        return self.key_reference & 0x7FFFFFFF

    def __repr__(self):
        return "QualifierReference(type: {:s}, isBuiltinKey: {:b}, keyref: {:s})".format(
                self.value_type,
                self.is_builtin_key,
                h(self.key)
            )


class QualifiersList(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.count = 0
        self.size = v_uint32()
        self.qualifiers = vstruct.VArray()

    def vsParse(self, bytez, offset=0, fast=False):
        soffset = offset
        offset = self["size"].vsParse(bytez, offset=offset)
        eoffset = soffset + self.size

        self.count = 0
        while offset + QualifierReference.MIN_SIZE <= eoffset:
            q = QualifierReference()
            offset = q.vsParse(bytez, offset=offset)
            self.qualifiers.vsAddElement(q)
            self.count += 1
        return offset

    def vsParseFd(self, fd):
        # TODO
        raise NotImplementedError()


class _Property(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.type = CimType()  # the on-disk type for this property's value
        self.entry_number = v_uint16()  # the on-disk order for this property
        self.unk1 = v_uint32()
        self.unk2 = v_uint32()
        self.qualifiers = QualifiersList()


class Property(LoggingObject):
    def __init__(self, class_def, propref):
        super(Property, self).__init__()
        self._class_definition = class_def
        self._propref = propref

        # this is the raw struct, without references/strings resolved
        self._prop = _Property()
        property_offset = self._propref.offset_property_struct
        self._prop.vsParse(self._class_definition.data, offset=property_offset)

    def __repr__(self):
        return "Property(name: {:s}, type: {:s}, qualifiers: {:s})".format(
            self.name,
            CIM_TYPES.vsReverseMapping(self.type.type),
            ",".join("%s=%s" % (k, str(v)) for k, v in self.qualifiers.items()))

    @property
    def name(self):
        # TODO: don't reach
        return self._class_definition._fields.get_string(self._propref.offset_property_name)

    @property
    def type(self):
        return self._prop.type

    @property
    def qualifiers(self):
        """ get dict of str to str """
        # TODO: remove duplication
        ret = {}
        for i in range(self._prop.qualifiers.count):
            q = self._prop.qualifiers.qualifiers[i]
            # TODO: don't reach
            qk = self._class_definition._fields.get_qualifier_key(q)
            qv = self._class_definition._fields.get_qualifier_value(q)
            ret[str(qk)] = qv
        return ret

    @property
    def entry_number(self):
        return self._prop.entry_number


class PropertyReference(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.offset_property_name = v_uint32()
        self.offset_property_struct = v_uint32()


class PropertyReferenceList(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.count = v_uint32()
        self.refs = vstruct.VArray()

    def pcb_count(self):
        self.refs.vsAddElements(self.count, PropertyReference)


class ClassFieldGetter(LoggingObject):
    """ fetches values from ClassDefinition, ClassInstance """
    def __init__(self, buf):
        """ :type buf: v_bytes """
        super(ClassFieldGetter, self).__init__()
        self._buf = buf

    def get_string(self, ref):
        s = WMIString()
        s.vsParse(self._buf, offset=int(ref))
        return str(s.s)

    def get_array(self, ref, item_type):
        Parser = item_type.value_parser
        data = self._buf

        arraySize = v_uint32()
        arraySize.vsParse(data, offset=int(ref))

        items = []
        offset = ref + 4  # sizeof(array_size:uint32_t)
        for i in range(arraySize):
            p = Parser()
            p.vsParse(data, offset=offset)
            items.append(self.get_value(p, item_type))
            offset += len(p)
        return items

    def get_value(self, value, value_type):
        """
        value: is a parsed value, might need dereferencing
        value_type: is a CimType
        """
        if value_type.is_array:
            return self.get_array(value, value_type.base_type_clone)

        t = value_type.type
        if t == CIM_TYPES.CIM_TYPE_STRING:
            return self.get_string(value)
        elif t == CIM_TYPES.CIM_TYPE_BOOLEAN:
            return value != 0
        elif t == CIM_TYPES.CIM_TYPE_DATETIME:
            return self.get_string(value)
        elif CIM_TYPES.vsReverseMapping(t):
            return value
        else:
            raise RuntimeError("unknown qualifier type: %s", str(value_type))

    def get_qualifier_value(self, qualifier):
        return self.get_value(qualifier.value, qualifier.value_type)

    def get_qualifier_key(self, qualifier):
        if qualifier.is_builtin_key:
            return BUILTIN_QUALIFIERS.vsReverseMapping(qualifier.key)
        return self.get_string(qualifier.key)


class ClassDefinition(vstruct.VStruct, LoggingObject):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        LoggingObject.__init__(self)

        self.header = ClassDefinitionHeader()
        self.qualifiers_list = QualifiersList()
        self.property_references = PropertyReferenceList()
        self.junk = v_bytes(size=0)
        self._data_length = v_uint32()
        self.data = v_bytes(size=0)

        self._fields = ClassFieldGetter(self.data)

    def pcb_header(self):
        self["junk"].vsSetLength(self.header.junk_length)

    @property
    def data_length(self):
        return self._data_length & 0x7FFFFFFF

    def pcb__data_length(self):
        self["data"].vsSetLength(self.data_length)

    def pcb_data(self):
        self._fields = ClassFieldGetter(self.data)

    def __repr__(self):
        return "ClassDefinition(name: {:s})".format(self.class_name)

    @property
    def keys(self):
        """
        get names of Key properties for instances

        :rtype: str
        """
        ret = []
        for propname, prop in self.properties.items():
            for k, v in prop.qualifiers.items():
                # TODO: don't hardcode BUILTIN_QUALIFIERS.PROP_KEY symbol name
                if k == "PROP_KEY" and v == True:
                    ret.append(propname)
        return ret

    @property
    def class_name(self):
        """ :rtype: str """
        return self._fields.get_string(self.header.offset_class_name)

    @property
    def super_class_name(self):
        """ :rtype: str """
        return str(self.header.super_class_unicode)

    @property
    def timestamp(self):
        """ :rtype: datetime.datetime """
        return self.header.timestamp

    @cached_property
    def qualifiers(self):
        """ :rtype: Mapping[str, Variant]"""
        ret = {}
        qualrefs = self.qualifiers_list
        for i in range(qualrefs.count):
            q = qualrefs.qualifiers[i]
            qk = self._fields.get_qualifier_key(q)
            qv = self._fields.get_qualifier_value(q)
            ret[str(qk)] = qv
        return ret

    @cached_property
    def properties(self):
        """ :rtype: Mapping[str, Property] """
        ret = {}
        proprefs = self.property_references
        for i in range(proprefs.count):
            propref = proprefs.refs[i]
            prop = Property(self, propref)
            ret[prop.name] = prop
        return ret



class InstanceKey(object):
    """ the key that uniquely identifies an instance """
    def __init__(self):
        object.__setattr__(self, '_d', {})

    def __setattr__(self, key, value):
        self._d[key] = value

    def __getattr__(self, item):
        return self._d[item]

    def __setitem__(self, key, item):
        self._d[key] = item

    def __getitem__(self, item):
        return self._d[item]

    def __repr__(self):
        return "InstanceKey({:s})".format(str(self._d))

    def __str__(self):
        return ",".join(["{:s}={:s}".format(str(k), str(self[k])) for k in sorted(self._d.keys())])



class ClassInstance(vstruct.VStruct, LoggingObject):
    def __init__(self, cim_type, class_layout):
        vstruct.VStruct.__init__(self)
        LoggingObject.__init__(self)

        self._cim_type = cim_type
        self.class_layout = class_layout
        self._buf = None

        if self._cim_type == CIM_TYPE_XP:
            self.name_hash = v_wstr(size=0x20)
        elif self._cim_type == CIM_TYPE_WIN7:
            self.name_hash = v_wstr(size=0x40)
        else:
            raise RuntimeError("Unexpected CIM type: " + str(self._cim_type))

        self.ts1 = FILETIME()
        self.ts2 = FILETIME()
        self.data_length2 = v_uint32()  # length of entire instance data
        self.extra_padding = v_bytes(size=0)

        self.toc = vstruct.VArray()
        for prop in self.class_layout.properties:
            P = prop.type.value_parser
            self.toc.vsAddElement(P())

        self.qualifiers_list = QualifiersList()
        self.unk1 = v_uint8()
        self.data_length = v_uint32()  # high bit always set, length of variable data
        self.data = v_bytes(size=0)

        self._property_index_map = {prop.name: i for i, prop in enumerate(self.class_layout.properties)}
        self._property_type_map = {prop.name: prop.type for prop in self.class_layout.properties}

        self._fields = ClassFieldGetter(self.data)

    def set_buffer(self, buf):
        """
        This is a hack until we can correctly compute extra_padding_length without trial and error.
        Must be called before vsParse.
        """
        self._buf = buf

    def pcb_data(self):
        self._fields = ClassFieldGetter(self.data)

    def pcb_data_length2(self):
        # hack: at this point, we know set_buffer must have been called
        l = self.extra_padding_length()
        self["extra_padding"].vsSetLength(l)

    def pcb_data_length(self):
        self["data"].vsSetLength(self.data_length & 0x7FFFFFFF)

    def pcb_unk1(self):
        if self.unk1 != 0x1:
            # seems that when this field is 0x0, then there is additional property data
            # maybe this is DYNPROPS: True???
            raise NotImplementedError("ClassInstance.unk1 != 0x1: %s" % h(self.unk1))

    def __repr__(self):
        # TODO: make this nice
        return "ClassInstance(classhash: {:s}, key: {:s})".format(self.name_hash, self.key)

    def extra_padding_length(self):
        class_definition = self.class_layout.class_definition
        if class_definition.header.unk3 == 0x18:
            return class_definition.header.unk1 + 0x6

        # these are all the same, split up to be explicit
        elif class_definition.header.unk3 == 0x19:
            return class_definition.header.unk1 + 0x5
        elif class_definition.header.unk3 == 0x17:
            # this is an extreme hack: we attempt a few commonly seen values and sanity check them
            # empirically, it seems CD.header.unk0 is usually 0x5 or 0x6 less than then extra length
            # so we try each of those, matching up the instance length against the computed field
            #   lengths and this magical value

            # a temp variable
            s = v_uint32()

            # the length of all toc entries, totally based on the CL
            toc_length = 0
            for prop in self.class_layout.properties:
                if prop.type.is_array:
                    toc_length += 0x4
                else:
                    toc_length += CIM_TYPE_SIZES[prop.type.type]

            u1 = class_definition.header.unk1

            # start right after the hash & timestamps
            # times 0x2 due to WCHAR (.name_hash is the string, not bytes object)
            header_length = (len(self.name_hash) * 2) + 0x10
            o = 0x0
            o += header_length

            # parse total instance size field
            s.vsParse(self._buf, o)
            total_size = s.vsGetValue()
            # seek past total size field
            o += 0x4

            # this is where the extra padding is
            start_extra_padding = o

            # here are the two offsets we'll attemp
            for i in (5, 6):
                o = start_extra_padding
                o += u1 + i

                # seek past toc
                o += toc_length

                # read qualifiers list size
                try:
                    s.vsParse(self._buf, o)
                except struct.error:
                    continue
                # seek past qualifiers list
                o += s.vsGetValue()

                # theres an extra byte, unk1
                o += 1

                # we should be at the variable data length field
                try:
                    s.vsParse(self._buf, o)
                except struct.error:
                    continue

                # match the variable size field against the instance data size field
                variable_size = s.vsGetValue() & 0x7FFFFFFF
                if (o - header_length + 0x4) + variable_size == total_size:
                    return u1 + i
            raise RuntimeError("Unable to determine extraPadding len")
        else:
            return class_definition.header.unk1 + 0x5

    @property
    def class_name(self):
        return self._fields.get_string(0x0)

    @cached_property
    def qualifiers(self):
        """ get dict of str to str """
        # TODO: remove duplication
        ret = {}
        for i in range(self.qualifiers_list.count):
            q = self.qualifiers_list.qualifiers[i]
            qk = self._fields.get_qualifier_key(q)
            qv = self._fields.get_qualifier_value(q)
            ret[str(qk)] = qv
        return ret

    @cached_property
    def properties(self):
        """ get dict of str to Property instances """
        ret = []
        for prop in self.class_layout.properties:
            n = prop.name
            i = self._property_index_map[n]
            t = self._property_type_map[n]
            v = self.toc[i]
            ret.append(self._fields.get_value(v, t))
        return ret

    def get_property_value(self, name):
        i = self._property_index_map[name]
        t = self._property_type_map[name]
        v = self.toc[i]
        return self._fields.get_value(v, t)

    @property
    def key(self):
        ret = InstanceKey()
        for prop_name in self.class_layout.class_definition.keys:
            ret[prop_name] = self.get_property_value(prop_name)
        return ret


class CoreClassInstance(vstruct.VStruct, LoggingObject):
    """
    begins with DWORD:0x0 and has no hash field
    seen at least for __NAMESPACE on an XP repo
    """
    def __init__(self, class_layout):
        vstruct.VStruct.__init__(self)
        LoggingObject.__init__(self)

        self.class_layout = class_layout
        self._buf = None

        self._unk0 = v_uint32()
        self.ts = FILETIME()
        self.data_length2 = v_uint32()  # length of all instance data
        self.extra_padding = v_bytes(size=8)

        self.toc = vstruct.VArray()
        for prop in self.class_layout.properties:
            self.toc.vsAddElement(prop.type.value_parser())

        self.qualifiers_list = QualifiersList()
        self.unk1 = v_uint32()
        self.data_length = v_uint32()  # high bit always set, length of variable data
        self.data = v_bytes(size=0)

        self._property_index_map = {prop.name: i for i, prop in enumerate(self.class_layout.properties)}
        self._property_type_map = {prop.name: prop.type for prop in self.class_layout.properties}

        self._fields = ClassFieldGetter(self.data)

    def pcb_data_length(self):
        self["data"].vsSetLength(self.data_length & 0x7FFFFFFF)

    def __repr__(self):
        # TODO: make this nice
        return "CoreClassInstance()".format()

    @property
    def class_name(self):
        return self._fields.get_string(0x0)

    @cached_property
    def qualifiers(self):
        """ get dict of str to str """
        # TODO: remove duplication
        ret = {}
        for i in range(self.qualifiers_list.count):
            q = self.qualifiers_list.qualifiers[i]
            qk = self._fields.get_qualifier_key(q)
            qv = self._fields.get_qualifier_value(q)
            ret[str(qk)] = qv
        return ret

    @cached_property
    def properties(self):
        """ get dict of str to Property instances """
        ret = []
        for prop in self.class_layout.properties:
            n = prop.name
            i = self._property_index_map[n]
            t = self._property_type_map[n]
            v = self.toc[i]
            ret.append(self._fields.get_value(v, t))
        return ret

    def get_property_value(self, name):
        i = self._property_index_map[name]
        t = self._property_type_map[name]
        v = self.toc[i]
        return self._fields.get_value(v, t)

    def get_property(self, name):
        raise NotImplementedError()


class ClassLayout(LoggingObject):
    def __init__(self, object_resolver, namespace, class_definition):
        super(ClassLayout, self).__init__()
        self.object_resolver = object_resolver
        self.namespace = namespace
        self.class_definition = class_definition

    @cached_property
    def properties(self):
        class_name = self.class_definition.class_name
        class_derivation = []  # initially, ordered from child to parent
        while class_name != "":
            cd = self.object_resolver.get_cd(self.namespace, class_name)
            class_derivation.append(cd)
            if cd.super_class_name:
                self.d("parent of %s is %s", class_name, cd.super_class_name)
            else:
                self.d("%s has no parent", class_name)
            class_name = cd.super_class_name

        # note, derivation now ordered from parent to child
        class_derivation.reverse()

        self.d("%s derivation: %s",
                self.class_definition.class_name,
                list(map(lambda c: c.class_name, class_derivation)))

        ret = []
        while len(class_derivation) > 0:
            cd = class_derivation.pop(0)
            for prop in sorted(cd.properties.values(), key=lambda p: p.entry_number):
                ret.append(prop)

        self.d("%s property layout: %s",
                self.class_definition.class_name,
                list(map(lambda p: p.name, ret)))
        return ret

    @cached_property
    def properties_toc_length(self):
        off = 0
        for prop in self.properties:
            if prop.type.is_array:
                off += 0x4
            else:
                off += CIM_TYPE_SIZES[prop.type.type]
        return off


class ObjectResolver(LoggingObject):
    def __init__(self, cim, index):
        super(ObjectResolver, self).__init__()
        self._cim = cim
        self._index = index

        self._cdcache = {}  # type: Mapping[str, ClassDefinition]
        self._clcache = {}  # type: Mapping[str, ClassLayout]

        # until we can correctly compute instance key hashes, maintain a cache mapping
        #   from encountered keys (serialized) to the instance hashes
        self._ihashcache = {}  # type: Mapping[str,str]

    def _build(self, prefix, name=None):
        if name is None:
            return prefix
        else:
            return prefix + self._index.hash(name.upper().encode("UTF-16LE"))

    def NS(self, name=None):
        return self._build("NS_", name)

    def CD(self, name=None):
        return self._build("CD_", name)

    def CR(self, name=None):
        return self._build("CR_", name)

    def R(self, name=None):
        return self._build("R_", name)

    def CI(self, name=None):
        return self._build("CI_", name)

    def KI(self, name=None):
        return self._build("KI_", name)

    def IL(self, name=None, hash=None):
        if hash is not None:
            return "IL_" + hash
        return self._build("IL_", name)

    def I(self, name=None):
        return self._build("I_", name)

    def get_object(self, query):
        """ fetch the first object buffer matching the query """
        self.d("query: %s", str(query))
        ref = one(self._index.lookup_keys(query))
        # TODO: should ensure this query has a unique result
        return self._cim.logical_data_store.get_object_buffer(ref)

    def get_keys(self, query):
        """ return a generator of keys matching the query """
        return self._index.lookup_keys(query)

    def get_objects(self, query):
        """ return a generator of object buffers matching the query """
        for ref in self.get_keys(query):
            yield ref, self._cim.logical_data_store.get_object_buffer(ref)

    @property
    def root_namespace(self):
        return SYSTEM_NAMESPACE_NAME

    def get_cd_buf(self, namespace_name, class_name):
        q = Key("{}/{}".format(
                self.NS(namespace_name),
                self.CD(class_name)))
        # TODO: should ensure this query has a unique result
        ref = one(self._index.lookup_keys(q))

        # some standard class definitions (like __NAMESPACE) are not in the
        #   current NS, but in the __SystemClass NS. So we try that one, too.

        if ref is None:
            self.d("didn't find %s in %s, retrying in %s", class_name, namespace_name, SYSTEM_NAMESPACE_NAME)
            q = Key("{}/{}".format(
                    self.NS(SYSTEM_NAMESPACE_NAME),
                    self.CD(class_name)))
        return self.get_object(q)

    def get_cd(self, namespace_name, class_name):
        c_id = get_class_id(namespace_name, class_name)
        c_cd = self._cdcache.get(c_id, None)
        if c_cd is None:
            self.d("cdcache miss")

            q = Key("{}/{}".format(
                    self.NS(namespace_name),
                    self.CD(class_name)))
            # TODO: should ensure this query has a unique result
            ref = one(self._index.lookup_keys(q))

            # some standard class definitions (like __NAMESPACE) are not in the
            #   current NS, but in the __SystemClass NS. So we try that one, too.

            if ref is None:
                self.d("didn't find %s in %s, retrying in %s", class_name, namespace_name, SYSTEM_NAMESPACE_NAME)
                q = Key("{}/{}".format(
                        self.NS(SYSTEM_NAMESPACE_NAME),
                        self.CD(class_name)))
            c_cdbuf = self.get_object(q)
            c_cd = ClassDefinition()
            c_cd.vsParse(c_cdbuf)
            self._cdcache[c_id] = c_cd
        return c_cd

    def get_cl(self, namespace_name, class_name):
        c_id = get_class_id(namespace_name, class_name)
        c_cl = self._clcache.get(c_id, None)
        if not c_cl:
            self.d("clcache miss")
            c_cd = self.get_cd(namespace_name, class_name)
            c_cl = ClassLayout(self, namespace_name, c_cd)
            self._clcache[c_id] = c_cl
        return c_cl

    def get_ci(self, namespace_name, class_name, instance_key):
        # TODO: this is a major hack! we should build the hash, but the data to hash
        #    has not been described correctly..

        # CI or KI?
        q = Key("{}/{}/{}".format(
                    self.NS(namespace_name),
                    self.CI(class_name),
                    self.IL(hash=self._ihashcache.get(str(instance_key), ""))))

        cl = self.get_cl(namespace_name, class_name)
        for _, buf in self.get_objects(q):
            instance = self.parse_instance(self.get_cl(namespace_name, class_name), buf)
            this_is_it = True
            for k in cl.class_definition.keys:
                if not instance.get_property_value(k) == instance_key[k]:
                    this_is_it = False
                    break
            if this_is_it:
                return instance

        raise IndexError("Key not found: " + str(instance_key))

    def get_ci_buf(self, namespace_name, class_name, instance_key):
        # TODO: this is a major hack!

        # CI or KI?
        q = Key("{}/{}/{}".format(
                    self.NS(namespace_name),
                    self.CI(class_name),
                    self.IL(hash=self._ihashcache.get(str(instance_key), ""))))

        cl = self.get_cl(namespace_name, class_name)
        for _, buf in self.get_objects(q):
            instance = self.parse_instance(self.get_cl(namespace_name, class_name), buf)
            this_is_it = True
            for k in cl.class_definition.keys:
                if not instance.get_property_value(k) == instance_key[k]:
                    this_is_it = False
                    break
            if this_is_it:
                return buf

        raise IndexError("Key not found: " + instance_key)

    @property
    def ns_cd(self):
        return self.get_cd(SYSTEM_NAMESPACE_NAME, NAMESPACE_CLASS_NAME)

    @property
    def ns_cl(self):
        return self.get_cl(SYSTEM_NAMESPACE_NAME, NAMESPACE_CLASS_NAME)

    def parse_instance(self, cl, buf):
        if buf[0x0:0x4] == "\x00\x00\x00\x00":
            i = CoreClassInstance(cl)
        else:
            i = ClassInstance(self._cim.cim_type, cl)
            i.set_buffer(buf)
        i.vsParse(buf)
        return i

    NamespaceSpecifier = namedtuple("NamespaceSpecifier", ["namespace_name"])
    def get_ns_children_ns(self, namespace_name):
        q = Key("{}/{}/{}".format(
                    self.NS(namespace_name),
                    self.CI(NAMESPACE_CLASS_NAME),
                    self.IL()))

        for ref, ns_i in self.get_objects(q):
            i = self.parse_instance(self.ns_cl, ns_i)
            yield self.NamespaceSpecifier(namespace_name + "\\" + i.get_property_value("Name"))

    ClassDefinitionSpecifier = namedtuple("ClassDefintionSpecifier", ["namespace_name", "class_name"])
    def get_ns_children_cd(self, namespace_name):
        q = Key("{}/{}".format(
                    self.NS(namespace_name),
                    self.CD()))

        for _, cdbuf in self.get_objects(q):
            cd = ClassDefinition()
            cd.vsParse(cdbuf)
            yield self.ClassDefinitionSpecifier(namespace_name, cd.class_name)

    ClassInstanceSpecifier = namedtuple("ClassInstanceSpecifier", ["namespace_name", "class_name", "instance_key"])
    def get_cd_children_ci(self, namespace_name, class_name):
        # TODO: CI or KI?
        q = Key("{}/{}/{}".format(
                    self.NS(namespace_name),
                    self.CI(class_name),
                    self.IL()))

        for ref, ibuf in self.get_objects(q):
            instance = self.parse_instance(self.get_cl(namespace_name, class_name), ibuf)
            # str(instance.key) is sorted k-v pairs, should be unique
            self._ihashcache[str(instance.key)] = ref.get_part_hash("IL_")
            yield self.ClassInstanceSpecifier(namespace_name, class_name, instance.key)


def get_class_id(namespace, classname):
    return namespace + ":" + classname


class TreeNamespace(LoggingObject):
    def __init__(self, object_resolver, name):
        super(TreeNamespace, self).__init__()
        self._object_resolver = object_resolver
        self.name = name

    def __repr__(self):
        return "Namespace(name: {:s})".format(self.name)

    @property
    def namespace(self):
        """ get parent namespace """
        if self.name == ROOT_NAMESPACE_NAME:
            return None
        else:
            # TODO
            raise NotImplementedError()

    @property
    def namespaces(self):
        """ return a generator of direct child namespaces """
        yielded = set([])
        for ns in self._object_resolver.get_ns_children_ns(self.name):
            name = ns.namespace_name
            if name not in yielded:
                yielded.add(name)
                yield TreeNamespace(self._object_resolver, ns.namespace_name)

    @property
    def classes(self):
        yielded = set([])
        for cd in self._object_resolver.get_ns_children_cd(self.name):
            name = cd.class_name
            if name not in yielded:
                yielded.add(name)
                yield TreeClassDefinition(self._object_resolver, self.name, cd.class_name)


class TreeClassDefinition(LoggingObject):
    def __init__(self, object_resolver, namespace, name):
        super(TreeClassDefinition, self).__init__()
        self._object_resolver = object_resolver
        self.ns = namespace
        self.name = name

    def __repr__(self):
        return "ClassDefinition(namespace: {:s}, name: {:s})".format(self.ns, self.name)

    @property
    def namespace(self):
        """ get parent namespace """
        return TreeNamespace(self._object_resolver, self.ns)

    @property
    def cd(self):
        return self._object_resolver.get_cd(self.ns, self.name)

    @property
    def cl(self):
        return self._object_resolver.get_cl(self.ns, self.name)

    @property
    def instances(self):
        """ get instances of this class definition """
        yielded = set([])
        for ci in self._object_resolver.get_cd_children_ci(self.ns, self.name):
            key = str(ci.instance_key)
            if key not in yielded:
                yielded.add(key)
                yield TreeClassInstance(self._object_resolver, self.name, ci.class_name, ci.instance_key)


class TreeClassInstance(LoggingObject):
    def __init__(self, object_resolver, namespace_name, class_name, instance_key):
        super(TreeClassInstance, self).__init__()
        self._object_resolver = object_resolver
        self.ns = namespace_name
        self.class_name = class_name
        self.instance_key = instance_key

    def __repr__(self):
        return "ClassInstance(namespace: {:s}, class: {:s}, key: {:s})".format(
            self.ns,
            self.class_name,
            self.instance_key)

    @property
    def klass(self):
        """ get class definition """
        return TreeClassDefinition(self._object_resolver, self.ns, self.class_name)

    @property
    def namespace(self):
        """ get parent namespace """
        return TreeNamespace(self._object_resolver, self.ns)


class Tree(LoggingObject):
    def __init__(self, cim):
        super(Tree, self).__init__()
        self._object_resolver = ObjectResolver(cim, Index(cim.getCimType, cim.logical_index_store))

    def __repr__(self):
        return "Tree"

    @property
    def root(self):
        """ get root namespace """
        return TreeNamespace(self._object_resolver, ROOT_NAMESPACE_NAME)
