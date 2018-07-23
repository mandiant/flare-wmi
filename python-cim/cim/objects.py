from __future__ import absolute_import

# TODO:
#   what is "DYNPROPS: True"?
#   where do descriptions come from?
#   how to determine start of TOC in class instance?
# BUGs:
#   class instance: "root\\CIMV2" Microsoft_BDD_Info NS_68577372C66A7B20658487FBD959AA154EF54B5F935DCC5663E9228B44322805/CI_6FCB95E1CB11D0950DA7AE40A94D774F02DCD34701D9645E00AB9444DBCF640B/IL_EEC4121F2A07B61ABA16414812AA9AFC39AB0A136360A5ACE2240DC19B0464EB.1606.116085.3740

import hashlib
import logging
import traceback
import functools
import contextlib
from datetime import datetime
from collections import namedtuple

from funcy.objects import cached_property
import vstruct
from vstruct.primitives import *

import cim
import cim.common

logger = logging.getLogger(__name__)

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
            self._ts = datetime.utcfromtimestamp(float(q) * 1e-7 - 11644473600)
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
        self.s = v_zstr_utf8()

    def __repr__(self):
        return repr(self.s)

    def vsGetValue(self):
        return self.s.vsGetValue()


# via: https://msdn.microsoft.com/en-us/library/cc250928.aspx
#  CIM-TYPE-SINT16 = % d2
#  CIM-TYPE-SINT32 = % d3
#  CIM-TYPE-REAL32 = % d4
#  CIM-TYPE-REAL64 = % d5
#  CIM-TYPE-STRING = % d8
#  CIM-TYPE-BOOLEAN = % d11
#  CIM-TYPE-SINT8 = % d16
#  CIM-TYPE-UINT8 = % d17
#  CIM-TYPE-UINT16 = % d18
#  CIM-TYPE-UINT32 = % d19
#  CIM-TYPE-SINT64 = % d20
#  CIM-TYPE-UINT64 = % d21
#  CIM-TYPE-DATETIME = % d101
#  CIM-TYPE-REFERENCE = % d102
#  CIM-TYPE-CHAR16 = % d103
#  CIM-TYPE-OBJECT = % d13


CIM_TYPES = v_enum()
CIM_TYPES.CIM_TYPE_INT16 = 0x2
CIM_TYPES.CIM_TYPE_INT32 = 0x3
CIM_TYPES.CIM_TYPE_REAL32 = 0x4
CIM_TYPES.CIM_TYPE_REAL64 = 0x5
CIM_TYPES.CIM_TYPE_STRING = 0x8
CIM_TYPES.CIM_TYPE_BOOLEAN = 0xB
CIM_TYPES.CIM_TYPE_UNKNOWN = 0xD
CIM_TYPES.CIM_TYPE_INT8 = 0x10
CIM_TYPES.CIM_TYPE_UINT8 = 0x11
CIM_TYPES.CIM_TYPE_UINT16 = 0x12
CIM_TYPES.CIM_TYPE_UINT32 = 0x13
CIM_TYPES.CIM_TYPE_INT64 = 0x14
CIM_TYPES.CIM_TYPE_UINT64 = 0x15
CIM_TYPES.CIM_TYPE_REFERENCE = 0x66
CIM_TYPES.CIM_TYPE_DATETIME = 0x65


CIM_TYPE_SIZES = {
    CIM_TYPES.CIM_TYPE_INT16: 2,
    CIM_TYPES.CIM_TYPE_INT32: 4,
    CIM_TYPES.CIM_TYPE_REAL32: 4,
    CIM_TYPES.CIM_TYPE_REAL64: 4,
    CIM_TYPES.CIM_TYPE_STRING: 4,
    CIM_TYPES.CIM_TYPE_BOOLEAN: 2,
    CIM_TYPES.CIM_TYPE_UNKNOWN: 4,
    CIM_TYPES.CIM_TYPE_INT8: 1,
    CIM_TYPES.CIM_TYPE_UINT8: 1,
    CIM_TYPES.CIM_TYPE_UINT16: 2,
    CIM_TYPES.CIM_TYPE_UINT32: 4,
    CIM_TYPES.CIM_TYPE_INT64: 8,
    CIM_TYPES.CIM_TYPE_UINT64: 8,
    # looks like: stringref to "\x00 00000000000030.000000:000"
    CIM_TYPES.CIM_TYPE_DATETIME: 4,
    CIM_TYPES.CIM_TYPE_REFERENCE: 4,
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
        self.type = v_uint8(enum=CIM_TYPES)
        self.array_state = v_uint8(enum=ARRAY_STATES)
        self.unk0 = v_uint8()
        self.unk2 = v_uint8()

    @property
    def is_array(self):
        # TODO: this is probably a bit-flag
        return self.array_state == ARRAY_STATES.ARRAY

    @property
    def _base_value_parser(self):
        if self.type == CIM_TYPES.CIM_TYPE_INT16:
            return v_int16
        if self.type == CIM_TYPES.CIM_TYPE_INT32:
            return v_int32
        elif self.type == CIM_TYPES.CIM_TYPE_REAL32:
            return v_float
        elif self.type == CIM_TYPES.CIM_TYPE_REAL64:
            return v_double
        elif self.type == CIM_TYPES.CIM_TYPE_STRING:
            return v_uint32
        elif self.type == CIM_TYPES.CIM_TYPE_BOOLEAN:
            return functools.partial(v_uint16, enum=BOOLEAN_STATES)
        elif self.type == CIM_TYPES.CIM_TYPE_INT8:
            return v_int8
        elif self.type == CIM_TYPES.CIM_TYPE_UINT8:
            return v_uint8
        elif self.type == CIM_TYPES.CIM_TYPE_UNKNOWN:
            return v_uint32
        elif self.type == CIM_TYPES.CIM_TYPE_UINT16:
            return v_uint16
        elif self.type == CIM_TYPES.CIM_TYPE_UINT32:
            return v_uint32
        elif self.type == CIM_TYPES.CIM_TYPE_INT64:
            return v_int64
        elif self.type == CIM_TYPES.CIM_TYPE_UINT64:
            return v_uint64
        elif self.type == CIM_TYPES.CIM_TYPE_DATETIME:
            return v_uint32
        elif self.type == CIM_TYPES.CIM_TYPE_REFERENCE:
            return v_uint32
        else:
            raise RuntimeError("unknown type: %s" % (hex(self.type)))

    @property
    def value_parser(self):
        if self.is_array:
            return v_uint32
        else:
            return self._base_value_parser

    def __repr__(self):
        r = ""
        if self.is_array:
            r += "arrayref to "
        typename = CIM_TYPES.vsReverseMapping(self.type)
        if typename is None:
            raise RuntimeError("unknown type: %s" % (hex(self.type)))
        r += typename
        return r

    @property
    def base_type_clone(self):
        return BaseType(self.type, self._base_value_parser)


class CimTypeArray(vstruct.VStruct):
    def __init__(self, cim_type):
        vstruct.VStruct.__init__(self)
        self._type = cim_type
        self.count = v_uint32()
        self.elements = vstruct.VArray()

    def pcb_count(self):
        self.elements.vsAddElements(self.count, self._type)


BUILTIN_QUALIFIERS = v_enum()
BUILTIN_QUALIFIERS.PROP_QUALIFIER_KEY = 0x1
BUILTIN_QUALIFIERS.PROP_QUALIFIER_READ_ACCESS = 0x3
BUILTIN_QUALIFIERS.CLASS_QUALIFIER_PROVIDER = 0x6
BUILTIN_QUALIFIERS.CLASS_QUALIFIER_DYNAMIC = 0x7
BUILTIN_QUALIFIERS.PROP_QUALIFIER_TYPE = 0xA

BUILTIN_PROPERTIES = v_enum()
BUILTIN_PROPERTIES.PRIMARY_KEY = 0x1
BUILTIN_PROPERTIES.READ = 0x3
BUILTIN_PROPERTIES.WRITE = 0x4
BUILTIN_PROPERTIES.VOLATILE = 0x5
BUILTIN_PROPERTIES.PROVIDER = 0x6
BUILTIN_PROPERTIES.DYNAMIC = 0x7
BUILTIN_PROPERTIES.TYPE = 0xA


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
            str(self.value_type),
            self.is_builtin_key,
            hex(self.key)
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
        raise NotImplementedError()


class _ClassDefinitionProperty(vstruct.VStruct):
    """
    this is the on-disk property definition structure
    """

    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.type = CimType()  # the on-disk type for this property's value
        self.index = v_uint16()  # the on-disk order for this property
        self.offset = v_uint32()
        self.level = v_uint32()
        self.qualifiers = QualifiersList()


class ClassDefinitionProperty(object):
    """
    this is the logical property object parsed from a standalone class definition.
    it is not aware of default values and inheritance behavior.
    """

    def __init__(self, class_def, propref):
        super(ClassDefinitionProperty, self).__init__()
        self._class_definition = class_def
        self._propref = propref

        # this is the raw struct, without references/strings resolved
        self._prop = _ClassDefinitionProperty()
        property_offset = self._propref.offset_property_struct
        self._prop.vsParse(self._class_definition.property_data.data, offset=property_offset)

    def __repr__(self):
        return "Property(name: {:s}, type: {:s}, qualifiers: {:s})".format(
            self.name,
            CIM_TYPES.vsReverseMapping(self.type.type),
            ",".join("%s=%s" % (k, str(v)) for k, v in self.qualifiers.items()))

    @property
    def name(self):
        if self._propref.is_builtin_property:
            return self._propref.builtin_property_name
        else:
            return self._class_definition.property_data.get_string(self._propref.offset_property_name)

    @property
    def type(self):
        return self._prop.type

    @property
    def index(self):
        return self._prop.index

    @property
    def offset(self):
        return self._prop.offset

    @property
    def level(self):
        return self._prop.level

    @property
    def qualifiers(self):
        """ get dict of str to str """
        ret = {}
        for i in range(self._prop.qualifiers.count):
            q = self._prop.qualifiers.qualifiers[i]
            # TODO: don't reach
            qk = self._class_definition.property_data.get_qualifier_key(q)
            qv = self._class_definition.property_data.get_qualifier_value(q)
            ret[str(qk)] = qv
        return ret


class PropertyReference(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.offset_property_name = v_uint32()
        self.offset_property_struct = v_uint32()

    @property
    def is_builtin_property(self):
        return self.offset_property_name & 0x80000000 > 0

    @property
    def builtin_property_name(self):
        if not self.is_builtin_property:
            raise RuntimeError("property is not builtin")
        key = self.offset_property_name & 0x7FFFFFFF
        return BUILTIN_PROPERTIES.vsReverseMapping(key)

    def __repr__(self):
        if self.is_builtin_property:
            return "PropertyReference(isBuiltinKey: true, name: {:s}, structref: {:s})".format(
                self.builtin_property_name,
                hex(self.offset_property_struct))
        else:
            return "PropertyReference(isBuiltinKey: false, nameref: {:s}, structref: {:s})".format(
                hex(self.offset_property_name),
                hex(self.offset_property_struct))


class PropertyReferenceList(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.count = v_uint32()
        self.refs = vstruct.VArray()

    def pcb_count(self):
        self.refs.vsAddElements(self.count, PropertyReference)


class ClassDefinitionHeader(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.super_class_unicode_length = v_uint32()
        self.super_class_unicode = v_wstr(size=0)  # not present if no superclass
        self.timestamp = FILETIME()
        self.data_length = v_uint32()  # size of data from this point forwards
        self.unk1 = v_uint8()
        self.offset_class_name = v_uint32()
        self.property_default_values_length = v_uint32()
        self.super_class_ascii_length = v_uint32()  # len(super class ascii string) + 8
        self.super_class_ascii = WMIString()  # not present if no superclass
        self.super_class_ascii_length2 = v_uint32()  # not present if no superclass, length of super class ascii string

    def pcb_super_class_unicode_length(self):
        self["super_class_unicode"].vsSetLength(self.super_class_unicode_length * 2)

    def pcb_super_class_ascii_length(self):
        if self.super_class_ascii_length == 0x4:
            self.vsSetField("super_class_ascii", v_str(size=0))
            self.vsSetField("super_class_ascii_length2", v_str(size=0))


ClassDefinitionPropertyState = namedtuple("ClassDefinitionPropertyState", ["is_inherited", "has_default_value"])


def compute_property_state_length(num_properties):
    """
    get number of bytes required to describe state of a bunch of properties.
    two bits per property, rounded up to the nearest byte.
    :rtype: int
    """
    required_bits = 2 * num_properties
    if required_bits % 8 == 0:
        delta_to_nearest_byte = 0
    else:
        delta_to_nearest_byte = 8 - (required_bits % 8)
    total_bits = required_bits + delta_to_nearest_byte
    total_bytes = total_bits // 8
    return total_bytes


class PropertyStates(vstruct.VArray):
    # two bits per property, rounded up to the nearest byte
    def __init__(self, bit_struct, num_properties):
        vstruct.VArray.__init__(self)
        self._bit_struct = bit_struct
        self._num_properties = num_properties

        total_bytes = compute_property_state_length(self._num_properties)
        self.vsAddElements(total_bytes, v_uint8)

    def get_by_index(self, prop_index):
        if prop_index > self._num_properties:
            raise RuntimeError("invalid prop_index")

        state_index = prop_index // 4
        byte_of_state = self[state_index]
        rotations = prop_index % 4
        state_flags = (byte_of_state >> (2 * rotations)) & 0x3
        p = self._bit_struct(state_flags & 0b10 > 0, state_flags & 0b01 == 0)
        return p


class PropertyDefaultValues(vstruct.VArray):
    # two bits per property, rounded up to the nearest byte
    def __init__(self, properties):
        vstruct.VArray.__init__(self)
        self._properties = properties

        self.state = PropertyStates(ClassDefinitionPropertyState, len(self._properties))
        self.default_values_toc = vstruct.VArray()
        for prop in self._properties:
            P = prop.type.value_parser
            self.default_values_toc.vsAddElement(P())


class DataRegion(vstruct.VStruct):
    """
    size field, then variable length of binary data.
    provides accessors for common types.
    """

    def __init__(self):
        vstruct.VStruct.__init__(self)

        self._size = v_uint32()
        self.data = v_bytes(size=0)

    def pcb__size(self):
        self["data"].vsSetLength(self.size)

    @property
    def size(self):
        return self._size & 0x7FFFFFFF

    def pcb_size(self):
        self["data"].vsSetLength(self.size)

    def get_string(self, ref):
        s = WMIString()
        s.vsParse(self.data, offset=int(ref))
        return s.s

    def get_array(self, ref, item_type):
        Parser = item_type.value_parser
        data = self.data

        array_size = v_uint32()
        array_size.vsParse(data, offset=int(ref))

        items = []
        offset = ref + 4  # sizeof(array_size:uint32_t)
        for i in range(array_size):
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
        if t == CIM_TYPES.CIM_TYPE_REFERENCE:
            return self.get_string(value)
        elif t == CIM_TYPES.CIM_TYPE_BOOLEAN:
            return value != 0
        elif t == CIM_TYPES.CIM_TYPE_DATETIME:
            return self.get_string(value)
        elif CIM_TYPES.vsReverseMapping(t):
            # TODO: why are we getting mixed vstruct/Python types?
            if hasattr(value, "vsGetValue"):
                return value.vsGetValue()
            else:
                return value
        else:
            raise RuntimeError("unknown type: %s" % (str(value_type)))

    def get_qualifier_value(self, qualifier):
        return self.get_value(qualifier.value, qualifier.value_type)

    def get_qualifier_key(self, qualifier):
        if qualifier.is_builtin_key:
            return BUILTIN_QUALIFIERS.vsReverseMapping(qualifier.key)
        return self.get_string(qualifier.key)


class ClassDefinition(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)

        self.header = ClassDefinitionHeader()
        self.qualifiers_list = QualifiersList()
        self.property_references = PropertyReferenceList()
        # useful with the PropertyDefaultValues structure, but that requires
        #  a complete list of properties from the ClassLayout
        self.property_default_values_data = v_bytes(size=0)
        self.property_data = DataRegion()
        self.method_data = DataRegion()

    def pcb_property_references(self):
        self["property_default_values_data"].vsSetLength(self.header.property_default_values_length)

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
                if k == "PROP_QUALIFIER_KEY" and v is True:
                    ret.append(propname)
        return ret

    @property
    def class_name(self):
        """ :rtype: str """
        return self.property_data.get_string(self.header.offset_class_name)

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
            qk = self.property_data.get_qualifier_key(q)
            qv = self.property_data.get_qualifier_value(q)
            ret[str(qk)] = qv
        return ret

    @cached_property
    def properties(self):
        """
        Get the Properties specific to this Class Definition.
        That is, don't return Properties inherited from ancestors.
        Note, you can't compute default values using only this field, since
          the complete class layout is required.

        :rtype: Mapping[str, ClassDefinitionProperty]
        """
        ret = {}
        proprefs = self.property_references
        for i in range(proprefs.count):
            propref = proprefs.refs[i]
            prop = ClassDefinitionProperty(self, propref)
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
        if len(self._d) == 0:
            return "default"
        else:
            return ",".join(["{:s}={:s}".format(str(k), str(self[k])) for k in sorted(self._d.keys())])


class ClassInstanceProperty(object):
    def __init__(self, prop, class_instance, state, value):
        """
        :type prop:  ClassLayoutProperty
        :type class_instance: ClassInstance
        :type value: variant
        """
        super(ClassInstanceProperty, self).__init__()
        self._prop = prop
        self.class_instance = class_instance
        self._value = value
        self.state = state

    # its a little ugly that we repeat Property fields for
    #    the base Property class, ClassLayouts, and ClassInstances
    # but we favor composition over inheritance

    @property
    def type(self):
        return self._prop.type

    @property
    def qualifiers(self):
        return self._prop.qualifiers

    @property
    def name(self):
        return self._prop.name

    @property
    def index(self):
        return self._prop.index

    @property
    def offset(self):
        return self._prop.offset

    @property
    def level(self):
        return self._prop.level

    def __repr__(self):
        return "Property(name: {name:s}, type: {type_:s}, qualifiers: {quals:s}, value: {val:s})".format(
            name=self.name,
            type_=CIM_TYPES.vsReverseMapping(self.type.type),
            quals=",".join("%s=%s" % (k, str(v)) for k, v in self.qualifiers.items()),
            val=str(self.value))

    @property
    def is_inherited(self):
        return self._prop.is_inherited

    @property
    def has_default_value(self):
        return self._prop.has_default_value

    @property
    def default_value(self):
        return self._prop.default_value

    @property
    def is_initialized(self):
        return self.state.is_initialized

    @property
    def is_default_value(self):
        if self.is_initialized:
            return self.state.use_default_value
        return False

    @property
    def value(self):
        if not self.is_initialized:
            raise RuntimeError("property is not initialized")
        return self._value


InstancePropertyState = namedtuple("InstancePropertyState", ["use_default_value", "is_initialized"])

DYNPROPS_STATE = v_enum()
DYNPROPS_STATE.NO_DYNPROPS = 0x1
DYNPROPS_STATE.HAS_DYNPROPS = 0x2


class DynpropQualifiers(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.size = v_uint32()
        # TODO: need to figure out this structure.
        # looks like a few leading DWORDs, then some Qualifier references
        self.data = v_bytes(size=0)

    def pcb_size(self):
        self["data"].vsSetLength(self.size)


class Dynprops(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self._has_dynprops = v_uint8()
        # self.count = v_uint32()
        # self.dynprops = vstruct.VArray(self.count * DynpropQualifiers)

    @property
    def has_dynprops(self):
        # we've only seen possible values 0x1 and 0x2
        return self._has_dynprops == DYNPROPS_STATE.HAS_DYNPROPS

    def vsParse(self, bytez, offset=0, fast=False):
        offset = self["_has_dynprops"].vsParse(bytez, offset=offset)
        if not self.has_dynprops:
            return offset

        self.vsAddField("count", v_uint32())
        self.vsAddField("dynprops", vstruct.VArray())
        offset = self["count"].vsParse(bytez, offset=offset)

        self["dynprops"].vsAddElements(self.count, DynpropQualifiers)
        offset = self["count"].vsParse(bytez, offset=offset)
        return offset

    def vsParseFd(self, fd):
        raise NotImplementedError()


class ClassInstance(vstruct.VStruct):
    def __init__(self, cim_type, class_layout):
        vstruct.VStruct.__init__(self)

        self._cim_type = cim_type
        self.class_layout = class_layout

        if self._cim_type == cim.CIM_TYPE_XP:
            self.name_hash = v_wstr(size=0x20)
        elif self._cim_type == cim.CIM_TYPE_WIN7:
            self.name_hash = v_wstr(size=0x40)
        else:
            raise RuntimeError("Unexpected CIM type: " + str(self._cim_type))

        self.ts1 = FILETIME()
        self.ts2 = FILETIME()
        self.data_length2 = v_uint32()  # length of entire instance data
        self.offset_instance_class_name = v_uint32()
        self.unk0 = v_uint8()
        self.property_state = PropertyStates(InstancePropertyState, len(self.class_layout.properties))

        self.toc = vstruct.VArray()
        for prop in sorted(self.class_layout.properties.values(), key=lambda p: p.index):
            P = prop.type.value_parser
            self.toc.vsAddElement(P())

        self.qualifiers_list = QualifiersList()
        self.dynprops = Dynprops()
        self.data = DataRegion()

    def __repr__(self):
        # TODO: make this nice
        return "ClassInstance(class: {:s}, key: {:s})".format(
            self.class_layout.class_definition.class_name, str(self.key))

    @property
    def class_name(self):
        return self.data.get_string(0x0)

    @cached_property
    def qualifiers(self):
        """ get dict of str to str """
        # TODO: remove duplication
        ret = {}
        for i in range(self.qualifiers_list.count):
            q = self.qualifiers_list.qualifiers[i]
            qk = self.data.get_qualifier_key(q)
            qv = self.data.get_qualifier_value(q)
            ret[str(qk)] = qv
        return ret

    @cached_property
    def properties(self):
        """ get dict of str to concrete Property values"""
        ret = {}
        for prop in self.class_layout.properties.values():
            state = self.property_state.get_by_index(prop.index)
            v = None
            if state.is_initialized:
                if state.use_default_value:
                    v = prop.default_value
                else:
                    v = self.data.get_value(self.toc[prop.index], prop.type)
            ret[prop.name] = ClassInstanceProperty(prop, self, state, v)
        return ret

    def get_property(self, name):
        return self.properties[name]

    @property
    def key(self):
        ret = InstanceKey()
        for prop_name in self.class_layout.class_definition.keys:
            ret[prop_name] = self.get_property(prop_name).value
        return ret


class CoreClassInstance(vstruct.VStruct):
    """
    begins with DWORD:0x0 and has no hash field
    seen at least for __NAMESPACE on an XP repo
    """

    def __init__(self, class_layout):
        vstruct.VStruct.__init__(self)

        self.class_layout = class_layout
        self._buf = None

        self._unk0 = v_uint32()
        self.ts = FILETIME()
        self.data_length2 = v_uint32()  # length of all instance data
        # TODO: what to do here about initialized values???
        self.extra_padding = v_bytes(size=8)

        self.toc = vstruct.VArray()
        for prop in self.class_layout.properties.values():
            self.toc.vsAddElement(prop.type.value_parser())

        self.qualifiers_list = QualifiersList()
        self.unk1 = v_uint32()
        self.data = DataRegion()

    def __repr__(self):
        # TODO: make this nice
        return "CoreClassInstance()".format()

    @property
    def class_name(self):
        return self.data.get_string(0x0)

    @cached_property
    def qualifiers(self):
        """ get dict of str to str """
        # TODO: remove duplication
        ret = {}
        for i in range(self.qualifiers_list.count):
            q = self.qualifiers_list.qualifiers[i]
            qk = self.data.get_qualifier_key(q)
            qv = self.data.get_qualifier_value(q)
            ret[str(qk)] = qv
        return ret

    @cached_property
    def properties(self):
        """ get dict of str to concrete Property values"""
        # TODO
        ret = {}
        for prop in self.class_layout.properties.values():
            n = prop.name
            i = prop.index
            t = prop.type
            v = self.toc[i]
            ret[n] = self.data.get_value(v, t)
        return ret

    def get_property(self, name):
        p = self.class_layout.properties[name]
        return self.data.get_value(self.toc[p.index], p.type)


class ClassLayoutProperty(object):
    def __init__(self, prop, class_layout):
        """
        :type prop:  ClassDefinitionProperty
        :type class_layout: ClassLayout
        """
        super(ClassLayoutProperty, self).__init__()
        self._prop = prop
        self.class_layout = class_layout

    @property
    def type(self):
        return self._prop.type

    @property
    def qualifiers(self):
        return self._prop.qualifiers

    @property
    def name(self):
        return self._prop.name

    @property
    def index(self):
        return self._prop.index

    @property
    def offset(self):
        return self._prop.offset

    @property
    def level(self):
        return self._prop.level

    def __repr__(self):
        return "Property(name: {:s}, type: {:s}, qualifiers: {:s})".format(
            self.name,
            CIM_TYPES.vsReverseMapping(self.type.type),
            ",".join("%s=%s" % (k, str(v)) for k, v in self.qualifiers.items()))

    @property
    def is_inherited(self):
        return self.class_layout.property_default_values.state.get_by_index(self.index).is_inherited

    @property
    def has_default_value(self):
        return self.class_layout.property_default_values.state.get_by_index(self.index).has_default_value

    @property
    def default_value(self):
        if not self.has_default_value:
            raise RuntimeError("property has no default value!")

        if not self.is_inherited:
            # then the data is stored nicely in the CD prop data section
            v = self.class_layout.property_default_values.default_values_toc[self.index]
            return self.class_layout.class_definition.property_data.get_value(v, self.type)
        else:
            # we have to walk up the derivation path looking for the default value
            rderivation = self.class_layout.derivation[:]
            rderivation.reverse()

            for ancestor_cl in rderivation:
                defaults = ancestor_cl.property_default_values
                state = defaults.state.get_by_index(self.index)
                if not state.has_default_value:
                    raise RuntimeError("prop with inherited default value has bad ancestor (no default value)")

                if state.is_inherited:
                    # keep trucking! look further up the ancestry tree.
                    continue

                # else, this must be where the default value is defined
                v = defaults.default_values_toc[self.index]
                return ancestor_cl.class_definition.property_data.get_value(v, self.type)
            raise RuntimeError("unable to find ancestor class with default value")


class QueryError(ValueError):
    pass


class ClassLayout(object):
    def __init__(self, object_resolver, namespace, class_definition):
        """
        :type object_resolver: ObjectResolver
        :type namespace: str
        :type class_definition: ClassDefinition
        """
        super(ClassLayout, self).__init__()
        self.object_resolver = object_resolver
        self.namespace = namespace
        self.class_definition = class_definition

    def __repr__(self):
        return "ClassLayout(name: {:s})".format(self.class_definition.class_name)

    @cached_property
    def derivation(self):
        """
        list from root to leaf of class layouts
        """
        derivation = []

        cl = self
        super_class_name = self.class_definition.super_class_name

        while super_class_name != "":
            derivation.append(cl)
            cl = self.object_resolver.get_cl(self.namespace, super_class_name)
            super_class_name = cl.class_definition.super_class_name
        derivation.append(cl)
        derivation.reverse()
        return derivation

    @cached_property
    def property_default_values(self):
        """ :rtype: PropertyDefaultValues """
        props = self.properties.values()
        props = sorted(props, key=lambda p: p.index)
        default_values = PropertyDefaultValues(props)
        d = self.class_definition.property_default_values_data
        default_values.vsParse(d)
        return default_values

    @cached_property
    def properties(self):
        props = {}  # :type: Mapping[int, ClassLayoutProperty]
        for cl in self.derivation:
            for prop in cl.class_definition.properties.values():
                props[prop.index] = ClassLayoutProperty(prop, self)
        return {prop.name: prop for prop in props.values()}

    @cached_property
    def properties_length(self):
        off = 0
        for prop in self.properties.values():
            if prop.type.is_array:
                off += 0x4
            else:
                off += CIM_TYPE_SIZES[prop.type.type]
        return off


class ObjectResolver(object):
    def __init__(self, repo, index=None):
        """
        Args:
            repo (CIM): the CIM repository
            index (cim.Index): the page index
        """
        super(ObjectResolver, self).__init__()

        self._repo = repo
        if not index:
            self._index = cim.Index(repo.cim_type, repo.logical_index_store)
        else:
            self._index = index

        self._cdcache = {}  # :type: Mapping[str, ClassDefinition]
        self._clcache = {}  # :type: Mapping[str, ClassLayout]

        # until we can correctly compute instance key hashes, maintain a cache mapping
        #   from encountered keys (serialized) to the instance hashes
        self._ihashcache = {}  # :type: dict[str,str]

    def hash(self, s):
        if self._repo.cim_type == cim.CIM_TYPE_XP:
            h = hashlib.md5()
        elif self._repo.cim_type == cim.CIM_TYPE_WIN7:
            h = hashlib.sha256()
        else:
            raise RuntimeError("Unexpected CIM type: {:s}".format(str(self._repo.cim_type)))
        h.update(s)
        return h.hexdigest().upper()

    def _build(self, prefix, name=None):
        if name is None:
            return prefix
        else:
            return prefix + self.hash(name.upper().encode("UTF-16LE"))

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

    def IL(self, name=None, known_hash=None):
        if known_hash is not None:
            return "IL_" + known_hash
        return self._build("IL_", name)

    def I(self, name=None):
        return self._build("I_", name)

    def get_object(self, query):
        """ fetch the first object buffer matching the query """
        logger.debug("query: %s", str(query))
        refs = self._index.lookup_keys(query)
        if not refs:
            raise QueryError('not found: ' + str(query))
        if refs and len(refs) > 1:
            raise QueryError('too many results: ' + str(query))
        ref = refs[0]
        return self._repo.logical_data_store.get_object_buffer(ref)

    def get_keys(self, query):
        """ return a generator of keys matching the query """
        return self._index.lookup_keys(query)

    def get_objects(self, query):
        """ return a generator of object buffers matching the query """
        for ref in self.get_keys(query):
            try:
                yield ref, self._repo.logical_data_store.get_object_buffer(ref)
            except cim.IndexKeyNotFoundError:
                logger.warning("Expected object not found in object store: %s", ref)
                continue

    @property
    def root_namespace(self):
        return SYSTEM_NAMESPACE_NAME

    def get_cd_buf(self, namespace_name, class_name):
        q = cim.Key("{}/{}".format(
            self.NS(namespace_name),
            self.CD(class_name)))

        refs = self._index.lookup_keys(q)

        if refs is None:
            # some standard class definitions (like __NAMESPACE) are not in the
            #   current NS, but in the __SystemClass NS. So we try that one, too.
            logger.debug("didn't find %s in %s, retrying in %s", class_name, namespace_name, SYSTEM_NAMESPACE_NAME)
            q = cim.Key("{}/{}".format(
                self.NS(SYSTEM_NAMESPACE_NAME),
                self.CD(class_name)))
        elif refs and len(refs) > 1:
            raise QueryError('to many results: ' + str(q))

        return self.get_object(q)

    def get_cd(self, namespace_name, class_name):
        c_id = get_class_id(namespace_name, class_name)
        c_cd = self._cdcache.get(c_id, None)
        if c_cd is None:
            logger.debug("cdcache miss")

            q = cim.Key("{}/{}".format(
                self.NS(namespace_name),
                self.CD(class_name)))

            refs = self._index.lookup_keys(q)
            if refs and len(refs) > 1:
                raise QueryError('too many results: ' + str(q))
            elif not refs:
                # some standard class definitions (like __NAMESPACE) are not in the
                #   current NS, but in the __SystemClass NS. So we try that one, too.
                logger.debug("didn't find %s in %s, retrying in %s", class_name, namespace_name, SYSTEM_NAMESPACE_NAME)
                q = cim.Key("{}/{}".format(
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
            logger.debug("clcache miss")
            c_cd = self.get_cd(namespace_name, class_name)
            c_cl = ClassLayout(self, namespace_name, c_cd)
            self._clcache[c_id] = c_cl

        return c_cl

    def get_ci(self, namespace_name, class_name, instance_key):
        # TODO: this is a major hack! we should build the hash, but the data to hash
        #    has not been described correctly..

        # CI or KI?
        q = cim.Key("{}/{}/{}".format(
            self.NS(namespace_name),
            self.CI(class_name),
            self.IL(known_hash=self._ihashcache.get(str(instance_key), ""))))

        cl = self.get_cl(namespace_name, class_name)
        for _, buf in self.get_objects(q):
            instance = self.parse_instance(self.get_cl(namespace_name, class_name), buf)
            this_is_it = True
            for k in cl.class_definition.keys:
                if instance.get_property(k).value != instance_key[k]:
                    this_is_it = False
                    break

            if this_is_it:
                return instance

        raise IndexError("Key not found: " + str(instance_key))

    def get_ci_buf(self, namespace_name, class_name, instance_key):
        # TODO: this is a major hack!

        # CI or KI?
        q = cim.Key("{}/{}/{}".format(
            self.NS(namespace_name),
            self.CI(class_name),
            self.IL(known_hash=self._ihashcache.get(str(instance_key), ""))))

        cl = self.get_cl(namespace_name, class_name)
        for _, buf in self.get_objects(q):
            instance = self.parse_instance(self.get_cl(namespace_name, class_name), buf)
            this_is_it = True
            for k in cl.class_definition.keys:
                if not instance.get_property(k).value == instance_key[k]:
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
            i = ClassInstance(self._repo.cim_type, cl)
        i.vsParse(buf)
        return i

    NamespaceSpecifier = namedtuple("NamespaceSpecifier", ["namespace_name"])

    def get_ns_children_ns(self, namespace_name):
        q = cim.Key("{}/{}/{}".format(
            self.NS(namespace_name),
            self.CI(NAMESPACE_CLASS_NAME),
            self.IL()))

        for ref, ns_i in self.get_objects(q):
            i = self.parse_instance(self.ns_cl, ns_i)
            yield self.NamespaceSpecifier(namespace_name + "\\" + i.get_property("Name").value)

        if namespace_name == ROOT_NAMESPACE_NAME:
            yield self.NamespaceSpecifier(SYSTEM_NAMESPACE_NAME)

    ClassDefinitionSpecifier = namedtuple("ClassDefintionSpecifier", ["namespace_name", "class_name"])

    def get_ns_children_cd(self, namespace_name):
        q = cim.Key("{}/{}".format(
            self.NS(namespace_name),
            self.CD()))

        for _, cdbuf in self.get_objects(q):
            cd = ClassDefinition()
            cd.vsParse(cdbuf)
            yield self.ClassDefinitionSpecifier(namespace_name, cd.class_name)

    ClassInstanceSpecifier = namedtuple("ClassInstanceSpecifier", ["namespace_name", "class_name", "instance_key"])

    def get_cd_children_ci(self, namespace_name, class_name):
        # TODO: CI or KI?
        q = cim.Key("{}/{}/{}".format(
            self.NS(namespace_name),
            self.CI(class_name),
            self.IL()))

        for ref, ibuf in self.get_objects(q):
            logger.debug("result for %s:%s:  %s", namespace_name, class_name, ref)
            try:
                instance = self.parse_instance(self.get_cl(namespace_name, class_name), ibuf)
            except:
                logger.error("failed to parse instance: %s %s at %s", namespace_name, class_name, ref)
                logger.error(traceback.format_exc())
                continue

            # str(instance.key) is sorted k-v pairs, should be unique
            self._ihashcache[str(instance.key)] = ref.get_part_hash("IL_")
            yield self.ClassInstanceSpecifier(namespace_name, class_name, instance.key)


def get_class_id(namespace, classname):
    return namespace + ":" + classname


ObjectPath = namedtuple("ObjectPath", ["hostname", "namespace", "klass", "instance"])


class TreeNamespace(object):
    def __init__(self, object_resolver, name):
        super(TreeNamespace, self).__init__()
        self._object_resolver = object_resolver
        self.name = name

    def __repr__(self):
        return "\\{namespace:s}".format(namespace=self.name)

    @property
    def parent(self):
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

        # all namespaces inherit classes from __SystemClass
        if self.name != SYSTEM_NAMESPACE_NAME:
            for cd in self._object_resolver.get_ns_children_cd(SYSTEM_NAMESPACE_NAME):
                name = cd.class_name
                if name not in yielded:
                    yielded.add(name)
                    yield TreeClassDefinition(self._object_resolver, self.name, cd.class_name)

        for cd in self._object_resolver.get_ns_children_cd(self.name):
            name = cd.class_name
            if name not in yielded:
                yielded.add(name)
                yield TreeClassDefinition(self._object_resolver, self.name, cd.class_name)

    def class_(self, name):
        n = name.lower()
        for c in self.classes:
            if c.name.lower() == n:
                return c
        raise IndexError()

    def namespace(self, name):
        n = self.name + "\\" + name.lower()
        for s in self.namespaces:
            if s.name.lower() == n:
                return n
        raise IndexError()

    def parse_object_path(self, object_path):
        """
        given a textual query string, parse it into an object path that we can query.
       
        supported schemas:
            cimv2 --> namespace
            //./root/cimv2 --> namespace
            //HOSTNAME/root/cimv2 --> namespace
            winmgmts://./root/cimv2 --> namespace
            Win32_Service --> class
            //./root/cimv2:Win32_Service --> class
            Win32_Service.Name='Beep' --> instance
            //./root/cimv2:Win32_Service.Name="Beep" --> instance

        we'd like to support this, but can't differentiate this
          from a class:
            //./root/cimv2/Win32_Service --> class
             
        Args:
            object_path (str): the textual query string.

        Returns:
            ObjectPath: a path we can use to query.
        """
        o_object_path = object_path
        object_path = object_path.replace("\\", "/")

        if object_path.startswith("winmgmts:"):
            # winmgmts://./root/cimv2 --> namespace
            object_path = object_path[len("winmgmts:"):]

        hostname = "localhost"
        namespace = self.name
        instance = {}

        is_rooted = False
        if object_path.startswith("//"):
            is_rooted = True

            # //./root/cimv2 --> namespace
            # //HOSTNAME/root/cimv2 --> namespace
            # //./root/cimv2:Win32_Service --> class
            # //./root/cimv2:Win32_Service.Name="Beep" --> instance
            object_path = object_path[len("//"):]

            # ./root/cimv2 --> namespace
            # HOSTNAME/root/cimv2 --> namespace
            # ./root/cimv2:Win32_Service --> class
            # ./root/cimv2:Win32_Service.Name="Beep" --> instance
            hostname, _, object_path = object_path.partition("/")
            if hostname == ".":
                hostname = "localhost"

        # cimv2 --> namespace
        # Win32_Service --> class
        # Win32_Service.Name='Beep' --> instance
        # root/cimv2 --> namespace
        # root/cimv2 --> namespace
        # root/cimv2:Win32_Service --> class
        # root/cimv2:Win32_Service.Name="Beep" --> instance
        if ":" in object_path:
            namespace, _, object_path = object_path.partition(":")
        elif "." not in object_path:
            if is_rooted:
                ns = object_path.replace("/", "\\")
                return ObjectPath(hostname, ns, "", {})
            else:
                try:
                    # relative namespace
                    self.namespace(object_path)
                    ns1 = self.name.replace("/", "\\")
                    ns2 = object_path.replace("/", "\\")
                    return ObjectPath(hostname, ns1 + "\\" + ns2, "", {})
                except IndexError:
                    try:
                        self.class_(object_path)
                        namespace = self.name
                    except IndexError:
                        raise RuntimeError("Unknown ObjectPath schema: %s" % o_object_path)

        # Win32_Service --> class
        # Win32_Service.Name="Beep" --> instance
        if "." in object_path:
            object_path, _, keys = object_path.partition(".")
            if keys:
                for key in keys.split(","):
                    k, _, v = key.partition("=")
                    instance[k] = v.strip("\"'")
        classname = object_path
        ns = namespace.replace("/", "\\")
        return ObjectPath(hostname, ns, classname, instance)

    def get(self, object_path):
        """
        :type object_path: ObjectPath
        """
        if object_path.hostname != "localhost":
            raise NotImplementedError("Unsupported hostname: {:s}".format(str(object_path.hostname)))
        if object_path.instance:
            return TreeClassInstance(self._object_resolver,
                                     object_path.namespace,
                                     object_path.klass,
                                     object_path.instance)
        elif object_path.klass:
            return TreeClassDefinition(self._object_resolver,
                                       object_path.namespace,
                                       object_path.klass)
        elif object_path.namespace:
            return TreeClassDefinition(self._object_resolver,
                                       object_path.namespace)
        else:
            raise RuntimeError("Invalid ObjectPath: {:s}".format(str(object_path)))


class TreeClassDefinition(object):
    def __init__(self, object_resolver, namespace, name):
        super(TreeClassDefinition, self).__init__()
        self._object_resolver = object_resolver
        self.ns = namespace
        self.name = name

    def __repr__(self):
        return "\\{namespace:s}:{klass:s}".format(namespace=self.ns, klass=self.name)

    @property
    def parent(self):
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
                yield TreeClassInstance(self._object_resolver, self.ns, ci.class_name, ci.instance_key)


class TreeClassInstance(object):
    def __init__(self, object_resolver, namespace_name, class_name, instance_key):
        super(TreeClassInstance, self).__init__()
        self._object_resolver = object_resolver
        self.ns = namespace_name
        self.class_name = class_name
        self.instance_key = instance_key

    def __repr__(self):
        return "\\{namespace:s}:{klass:s}.{key:s}".format(
            namespace=self.ns, klass=self.class_name, key=repr(self.instance_key))

    def __str__(self):
        return "\\{namespace:s}:{klass:s}.{key:s}".format(
            namespace=self.ns, klass=self.class_name, key=str(self.instance_key))

    @property
    def parent(self):
        """ get class definition """
        return TreeClassDefinition(self._object_resolver, self.ns, self.class_name)

    @property
    def cl(self):
        return self._object_resolver.get_cl(self.ns, self.class_name)

    @property
    def cd(self):
        return self._object_resolver.get_cd(self.ns, self.class_name)

    @property
    def ci(self):
        return self._object_resolver.get_ci(self.ns, self.class_name, self.instance_key)

    def __getattr__(self, attr):
        try:
            return super(TreeClassInstance, self).__getattr__(attr)
        except AttributeError:
            pass
        return getattr(self.ci, attr)


class Tree(object):
    def __init__(self, repo):
        super(Tree, self).__init__()
        self._object_resolver = ObjectResolver(repo)

    def __repr__(self):
        return "Tree"

    @property
    def root(self):
        """ get root namespace """
        return TreeNamespace(self._object_resolver, ROOT_NAMESPACE_NAME)


@contextlib.contextmanager
def Namespace(repo, namespace_name):
    """
    operate on the given namespace.
    
    Args:
        repo: the CIM repository.
        namespace_name:  the namespace name to open.

    Returns:
        TreeNamespace: the namespace.
    """
    yield TreeNamespace(ObjectResolver(repo), namespace_name)
