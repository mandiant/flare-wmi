import logging
from collections import namedtuple

from common import h
from common import one
from common import LoggingObject

from cim import CIM
from cim import Index
from cim import ClassDefinition as cimClassDefinition
from cim import ClassInstance as cimClassInstance

logging.basicConfig(level=logging.DEBUG)
g_logger = logging.getLogger("cim.tree")


ROOT_NAMESPACE_NAME = "root"
SYSTEM_NAMESPACE_NAME = "__SystemClass"
NAMESPACE_CLASS_NAME = "__namespace"


# usually I'd avoid a "context", but its useful here to
#   maintain multiple caches and shared objects.
# cim is a cim.CIM object
# index is a cim.Index object
# cdcache is a dict from class id to cim.ClassDefinition object
# clcache is a dict from class id to .ClassLayout objects
TreeContext = namedtuple("TreeContext", ["cim", "index", "cdcache", "clcache"])


class QueryBuilderMixin(object):
    def __init__(self):
        # self must have the following fields:
        #   - context:TreeContext
        pass

    def _build(self, prefix, name=None):
        if name is None:
            return prefix
        else:
            return prefix + self.context.index.hash(name.upper().encode("UTF-16LE"))

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

    def IL(self, name=None):
        return self._build("IL_", name)

    def I(self, name=None):
        return self._build("I_", name)

    def getClassDefinitionQuery(self, ns, name):
        return "{}/{}".format(self.NS(ns), self.CD(name))


class ObjectFetcherMixin(object):
    def __init__(self):
        # self must have the following fields:
        #   - context:TreeContext
        pass

    def getObject(self, query):
        """ fetch the first object buffer matching the query """
        self.d("query: {:s}".format(query))
        ref = one(self.context.index.lookupKeys(query))
        self.d("result: {:s}".format(ref))
        return self.context.cim.getLogicalDataStore().getObjectBuffer(ref)

    def getObjects(self, query):
        """ return a generator of object buffers matching the query """
        self.d("query: {:s}".format(query))
        refs = self.context.index.lookupKeys(query)
        self.d("result: {:d} objects".format(len(refs)))
        for ref in self.context.index.lookupKeys(query):
            self.d("result: {:s}".format(ref))
            yield self.context.cim.getLogicalDataStore().getObjectBuffer(ref)

    def getClassDefinitionByQuery(self, query):
        """ return the first cim.ClassDefinition matching the query """
        buf = self.getObject(query)
        return cimClassDefinition(buf)

    def getClassDefinitionBuffer(self, namespace, classname):
        """ return the first raw class definition buffer matching the query """
        q = self.getClassDefinitionQuery(namespace, classname)
        ref = one(self.context.index.lookupKeys(q))

        # some standard class definitions (like __NAMESPACE) are not in the
        #   current NS, but in the __SystemClass NS. So we try that one, too.

        if ref is None:
            self.d("didn't find %s in %s, retrying in %s",
                    classname, namespace, SYSTEM_NAMESPACE_NAME)
            q = self.getClassDefinitionQuery(SYSTEM_NAMESPACE_NAME, classname)
        return self.getObject(q)

    def getClassDefinition(self, namespace, classname):
        """ return the first cim.ClassDefinition matching the query """
        # TODO: remove me
        return cimClassDefinition(self.getClassDefinitionBuffer(namespace, classname))


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
        self._ts = datetime.utcfromtimestamp(float(q) * 1e-7 - 11644473600 )
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
        self.superClassNameWLen = v_uint32()
        self.superClassNameW = v_wstr(size=0)  # not present if no superclass
        self.timestamp = FILETIME()
        self.unk0 = v_uint8()
        self.unk1 = v_uint32()
        self.offsetClassNameA = v_uint32()
        self.unk2 = v_uint32()
        self.unk3 = v_uint32()
        self.superClassNameA = WMIString()  # not present if no superclass
        self.unk4 = v_uint32()  # not present if no superclass

    def pcb_superClassNameWLen(self):
        self["superClassNameW"].vsSetLength(self.superClassNameWLen * 2)
        if self.superClassNameWLen == 0:
            self.vsSetField("superClassNameA", v_str(size=0))
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
    CIM_TYPES.CIM_TYPE_DATETIME: 8   # guess
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
    def __init__(self, type_, valueParser):
        self._type = type_
        self._valueParser = valueParser

    def getType(self):
        return self._type

    def isArray(self):
        return False

    def getValueParser(self):
        return self._valueParser

    def __repr__(self):
        return CIM_TYPES.vsReverseMapping(self._type)

    def getBaseTypeClone(self):
        return self


class CimType(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self._type = v_uint8()
        self._isArray = v_uint8()
        self.unk0 = v_uint8()
        self.unk2 = v_uint8()

    def getType(self):
        return self._type

    def isArray(self):
        return self._isArray == 0x20

    def getValueParser(self):
        if self.isArray():
            return v_uint32
        elif self._type == CIM_TYPES.CIM_TYPE_LANGID:
            return v_uint32
        elif self._type == CIM_TYPES.CIM_TYPE_REAL32:
            return v_float
        elif self._type == CIM_TYPES.CIM_TYPE_STRING:
            return v_uint32
        elif self._type == CIM_TYPES.CIM_TYPE_BOOLEAN:
            return v_uint16
        elif self._type == CIM_TYPES.CIM_TYPE_UINT8:
            return v_uint8
        elif self._type == CIM_TYPES.CIM_TYPE_UINT16:
            return v_uint16
        elif self._type == CIM_TYPES.CIM_TYPE_UINT32:
            return v_uint32
        elif self._type == CIM_TYPES.CIM_TYPE_UINT64:
            return v_uint64
        elif self._type == CIM_TYPES.CIM_TYPE_DATETIME:
            return FILETIME
        else:
            raise RuntimeError("unknown qualifier type: %s", h(self._type))

    def __repr__(self):
        r = ""
        if self.isArray():
            r += "arrayref to "
        r += CIM_TYPES.vsReverseMapping(self._type)
        return r

    def getBaseTypeClone(self):
        return BaseType(self.getType(), self.getValueParser())


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
        self.keyReference = v_uint32()
        self.unk0 = v_uint8()
        self.valueType = CimType()
        self.value = v_bytes(size=0)

    def pcb_valueType(self):
        self.vsSetField("value", self.valueType.getValueParser()())

    def isBuiltinKey(self):
        return self.keyReference & 0x80000000 > 0

    def getKey(self):
        return self.keyReference & 0x7FFFFFFF

    def __repr__(self):
        return "QualifierReference(type: {:s}, isBuiltinKey: {:b}, keyref: {:s})".format(
                self.valueType,
                self.isBuiltinKey(),
                h(self.getKey())
            )


class QualifiersList(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.count = 0
        self.size = v_uint32()
        self.qualifiers = vstruct.VArray()

    def vsParse(self, bytez, offset=0):
        #g_logger.debug("QL: \n%s", hexdump.hexdump(bytez, result="return"))
        soffset = offset
        #g_logger.debug("QL: soffset: %s", h(soffset))
        offset = self["size"].vsParse(bytez, offset=offset)
        eoffset = soffset + self.size
        #g_logger.debug("QL: eoffset: %s", h(eoffset))

        self.count = 0
        while offset + QualifierReference.MIN_SIZE <= eoffset:
            #g_logger.debug("QL: entry: %s", h(offset))
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
        self.type = CimType()
        self.unk0 = v_uint16()
        self.unk1 = v_uint32()
        self.unk2 = v_uint32()
        self.qualifiers = QualifiersList()


class Property(LoggingObject):
    def __init__(self, classDef, propref):
        super(Property, self).__init__()
        self._classDef = classDef
        self._propref = propref


        # hack, fixme
        """
        HIGH_BIT = 1 << 31
        def isHighBitSet(i):
            return i & HIGH_BIT > 0
        if isHighBitSet(self._propref.offsetPropertyName) or \
                isHighBitSet(self._propref.offsetPropertyStruct):
            self._prop = None
            return
        """

        # this is the raw struct, without references/strings resolved
        self._prop = _Property()
        offsetProperty = self._propref.offsetPropertyStruct
        self._prop.vsParse(self._classDef.getData(), offset=offsetProperty)

    def isInherited(self):
        # guess
        return self._propref.offsetPropertyName & 0x80000000 > 0

    def getName(self):
        if self.isInherited():
            return "INHERITED_%s" % h(self._propref.offsetPropertyName & 0x7FFFFFFF)
        return self._classDef.getString(self._propref.offsetPropertyName)

    def getType(self):
        if self.isInherited():
            # hack, fixme
            return None
        return self._prop.type

    def getQualifiers(self):
        """ get dict of str to str """
        # TODO: can merge this will ClassDef.getQualifiers
        ret = {}
        if self.isInherited():
            # hack, fixme
            # there can definitely be a struct here, so how do we find it?
            return ret
        for i in xrange(self._prop.qualifiers.count):
            q = self._prop.qualifiers.qualifiers[i]
            self.d("%s", q)
            qk = self._classDef.getQualifierKey(q)
            qv = self._classDef.getQualifierValue(q)
            ret[str(qk)] = str(qv)
            self.d("%s: %s", qk, qv)
        return ret


class PropertyReference(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.offsetPropertyName = v_uint32()
        self.offsetPropertyStruct = v_uint32()


class PropertyReferenceList(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.count = v_uint32()
        self.refs = vstruct.VArray()

    def pcb_count(self):
        self.refs.vsAddElements(self.count, PropertyReference)


class _ClassDefinition(vstruct.VStruct):
    def __init__(self):
        # TODO: need to know inherited properties
        vstruct.VStruct.__init__(self)
        self.header = ClassDefinitionHeader()
        self.qualifiers = QualifiersList()
        self.propertyReferences = PropertyReferenceList()

    def pcb_header(self):
        #g_logger.debug("CD: \n%s", self.header.tree())
        pass

    def pcb_qualifiers(self):
        #g_logger.debug("CD: \n%s", self.qualifiers.tree())
        pass

    def pcb_propertyReferences(self):
        #g_logger.debug("CD: \n%s", self.propertyReferences.tree())
        pass


class ClassDefinition(LoggingObject):
    # TODO: need to be able to fetch ancestor class info
    #   namely, number of fields
    # This is not a "low level" class. Relies on the index,
    #   data store, current namespace, and query building logic.
    #   How do we make it simple?
    def __init__(self, buf):
        super(ClassDefinition, self).__init__()
        self._buf = buf
        self._def = _ClassDefinition()
        self._def.vsParse(buf)

        self._propDataOffset = self._findPropDataOffset()

        # cache
        self._data = None

    def _findPropDataOffset(self):
        # this is currently a hack.
        # search for the last 0xFF in a big block
        off = len(self._def)

        while self._buf.find("\xFF" * 2, off, off + 0x10) != -1:
            off = self._buf.find("\xFF" * 2, off, off + 0x10)
            # scan past sequential 0xFF bytes until non-0xFF
            while ord(self._buf[off]) == 0xFF:
                off += 1
            # break if not "FF FF" within 0x10 bytes

        self.d("prop data offset: %s", h(off))
        return off

    def getData(self):
        if self._data is None:
            o = self._findPropDataOffset()
            dataLen = v_uint32()
            dataLen.vsParse(self._buf, offset=o)
            o += len(dataLen)
            self._data = self._buf[o:o + dataLen]
        return self._data

    def getString(self, ref):
        s = WMIString()
        s.vsParse(self.getData(), offset=int(ref))
        return str(s.s)

    def getArray(self, ref, itemType):
        self.d("ref: %s, type: %s", ref, itemType)
        Parser = itemType.getValueParser()
        data = self.getData()

        arraySize = v_uint32()
        arraySize.vsParse(data, offset=int(ref))

        items = []
        offset = ref + 4  # sizeof(array_size:uint32_t)
        for i in xrange(arraySize):
            p = Parser()
            p.vsParse(data, offset=offset)
            items.append(self.getValue(p, itemType))
            offset += len(p)
        return items

    def getValue(self, value, valueType):
        """
        value is a parsed value, might need dereferencing
        valueType is a CimType
        """
        self.d("value: %s, type: %s", value, valueType)
        if valueType.isArray():
            self.d("isArray")
            return self.getArray(value, valueType.getBaseTypeClone())

        t = valueType.getType()
        if t == CIM_TYPES.CIM_TYPE_STRING:
            return self.getString(value)
        elif t == CIM_TYPES.CIM_TYPE_BOOLEAN:
            return value != 0
        elif CIM_TYPES.vsReverseMapping(t):
            return value
        else:
            raise RuntimeError("unknown qualifier type: %s",
                    str(valueType))

    def getQualifierValue(self, qualifier):
        return self.getValue(qualifier.value, qualifier.valueType)

    def getQualifierKey(self, qualifier):
        self.d("%s", qualifier)
        self.d("%s", qualifier.getKey())
        if qualifier.isBuiltinKey():
            return BUILTIN_QUALIFIERS.vsReverseMapping(qualifier.getKey())
        return self.getString(qualifier.getKey())

    def getClassName(self):
        """ return string """
        return self.getString(self._def.header.offsetClassNameA)

    def getSuperClassName(self):
        """ return string """
        return str(self._def.header.superClassNameW)

    def getTimestamp(self):
        """ return datetime.datetime """
        return self._def.header.timestamp

    def getQualifiers(self):
        """ get dict of str to str """
        ret = {}
        for i in xrange(self._def.qualifiers.count):
            q = self._def.qualifiers.qualifiers[i]
            qk = self.getQualifierKey(q)
            qv = self.getQualifierValue(q)
            ret[str(qk)] = str(qv)
            self.d("%s: %s", qk, qv)
        return ret

    def getProperties(self):
        """ get dict of str to Property instances """
        ret = []
        for i in xrange(self._def.propertyReferences.count):
            propref = self._def.propertyReferences.refs[i]
            ret.append(Property(self, propref))
        return {p.getName(): p for p in ret}


class _ClassInstance(vstruct.VStruct):
    def __init__(self, properties):
        vstruct.VStruct.__init__(self)
        self.nameHash = v_wstr(size=0x40)
        self.ts1 = FILETIME()
        self.ts2 = FILETIME()
        self.dataLen = v_uint32()
        self.unk0 = v_uint16()
        self.offsetClassNameA = v_uint32()

        self.toc = vstruct.VArray()
        for prop in properties:
            self.toc.vsAddElement(prop.getType().getValueParser()())

        self.qualifiers = QualifiersList()
        self.unk1 = v_uint8()
        self.propDataLen = v_uint32()  # high bit always set
        self.propData = v_bytes(size=0)

    def pcb_propDataLen(self):
        self["propData"].vsSetLength(self.propDataLen & 0x7FFFFFFF)


class ClassInstance(LoggingObject):
    # TODO: pass in the class definition here
    def __init__(self, properties, buf):
        """ properties is an ordered list of Property objects """
        super(ClassInstance, self).__init__()
        self._props = properties
        self._buf = buf
        self._def = _ClassInstance(self._props)
        self._def.vsParse(buf)

        self._propIndexMap = {prop.getName(): i for i, prop in enumerate(self._props)}
        self._propTypeMap = {prop.getName(): prop.getType() for prop in self._props}

    def getData(self):
        return self._def.propData

    def getString(self, ref):
        s = WMIString()
        s.vsParse(self.getData(), offset=int(ref))
        return str(s.s)

    def getArray(self, ref, itemType):
        self.d("ref: %s, type: %s", ref, itemType)
        Parser = itemType.getValueParser()
        data = self.getData()

        arraySize = v_uint32()
        arraySize.vsParse(data, offset=int(ref))

        items = []
        offset = ref + 4  # sizeof(array_size:uint32_t)
        for i in xrange(arraySize):
            p = Parser()
            p.vsParse(data, offset=offset)
            items.append(self.getValue(p, itemType))
            offset += len(p)
        return items

    def getValue(self, value, valueType):
        """
        value is a parsed value, might need dereferencing
        valueType is a CimType
        """
        self.d("value: %s, type: %s", value, valueType)
        if valueType.isArray():
            self.d("isArray")
            return self.getArray(value, valueType.getBaseTypeClone())

        t = valueType.getType()
        if t == CIM_TYPES.CIM_TYPE_STRING:
            return self.getString(value)
        elif t == CIM_TYPES.CIM_TYPE_BOOLEAN:
            return value != 0
        elif CIM_TYPES.vsReverseMapping(t):
            return value
        else:
            raise RuntimeError("unknown qualifier type: %s",
                    str(valueType))

    def getQualifierValue(self, qualifier):
        return self.getValue(qualifier.value, qualifier.valueType)

    def getQualifierKey(self, qualifier):
        if qualifier.isBuiltinKey():
            return BUILTIN_QUALIFIERS.vsReverseMapping(qualifier.getKey())
        return self.getString(qualifier.getKey())

    def getClassName(self):
        """ return string """
        return self.getString(self._def.offsetClassNameA)

    def getClassNameHash(self):
        """ return string """
        return self._def.nameHash

    def getTimestamp1(self):
        """ return datetime.datetime """
        return self._def.ts1

    def getTimestamp2(self):
        """ return datetime.datetime """
        return self._def.ts2

    def getQualifiers(self):
        """ get dict of str to str """
        ret = {}
        for i in xrange(self._def.qualifiers.count):
            q = self._def.qualifiers.qualifiers[i]
            qk = self.getQualifierKey(q)
            qv = self.getQualifierValue(q)
            ret[str(qk)] = str(qv)
            self.d("%s: %s", qk, qv)
        return ret

    def getProperties(self):
        """ get dict of str to Property instances """
        # TODO
        raise NotImplementedError()

    def getPropertyValue(self, name):
        i = self._propIndexMap[name]
        t = self._propTypeMap[name]
        v = self._def.toc[i]
        return self.getValue(v, t)

    def getProperty(self, name):
        # TODO: this should return a Property object
        raise NotImplementedError()



class ClassLayout(LoggingObject, QueryBuilderMixin, ObjectFetcherMixin):
    def __init__(self, context, namespace, classDefinition):
        """
        namespace is a string
        classDefinition is a cim.ClassDefinition object
        """
        super(ClassLayout, self).__init__()
        self.context = context
        self._ns = namespace
        self._cd = classDefinition

        # cache
        self._properties = None

    @property
    def properties(self):
        if self._properties is not None:
            return self._properties[:]

        className = self._cd.getClassName()
        classDerivation = []  # initially, ordered from child to parent
        while className != "":
            cd = self.getClassDefinition(self._ns, className)
            classDerivation.append(cd)
            self.d("parent of %s is %s", className, cd.getSuperClassName())
            className = cd.getSuperClassName()

        # note, derivation now from parent to child
        classDerivation.reverse()

        self.d("%s derivation: %s",
                self._cd.getClassName(),
                map(lambda c: c.getClassName(), classDerivation))

        self._properties = []
        while len(classDerivation) > 0:
            cd = classDerivation.pop(0)
            for prop in cd.getProperties().values():
                self._properties.append(prop)

        self.d("%s property layout: %s",
                self._cd.getClassName(),
                map(lambda p: p.getName(), self._properties))
        return self._properties[:]

    def parseInstance(self, data):
        return cimClassInstance(self.properties, data)


def getClassId(namespace, classname):
    return namespace + ":" + classname


class Namespace(LoggingObject, QueryBuilderMixin, ObjectFetcherMixin):
    def __init__(self, context, name):
        super(Namespace, self).__init__()
        self.context = context
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
        """ return a generator direct child namespaces """
        namespaceClassId = getClassId(SYSTEM_NAMESPACE_NAME, NAMESPACE_CLASS_NAME)
        namespaceCD = self.context.cdcache.get(namespaceClassId, None)
        if namespaceCD is None:
            self.d("cdcache miss")
            q = self.getClassDefinitionQuery(SYSTEM_NAMESPACE_NAME, NAMESPACE_CLASS_NAME)
            namespaceCD = cimClassDefinition(self.getObject(q))
            self.context.cdcache[namespaceClassId] = namespaceCD

        namespaceCL = self.context.clcache.get(namespaceClassId, None)
        if namespaceCL is None:
            self.d("clcache miss")
            namespaceCL = ClassLayout(self.context, self.name, namespaceCD)
            self.context.clcache[namespaceClassId] = namespaceCL

        q = "{}/{}/{}".format(
                self.NS(self.name),
                self.CI(NAMESPACE_CLASS_NAME),
                self.IL())

        for namespaceInstance in self.getObjects(q):
            namespaceI = namespaceCL.parseInstance(namespaceInstance)
            nsName = namespaceI.getPropertyValue("Name")
            # TODO: perhaps should test if this thing exists?
            yield Namespace(self.context, self.name + "\\" + nsName)

    def parseClassDerivation(self, namespace, cdbuf):
        """ get list of classnames from least to most specific """
        # we pass in cdbuf for the same reason as below (parseClassDefinition).
        header = ClassDefinitionHeader()
        header.vsParse(cdbuf)

        parentName = header.superClassNameW
        classDerivation = []  # initially, ordered from child to parent
        while parentName != "":
            classDerivation.append(parentName)
            parentcdbuf = self.getClassDefinitionBuffer(namespace, parentName)
            header.vsParse(parentcdbuf)
            self.d("parent of %s is %s", parentName, header.superClassNameW)
            parentName = header.superClassNameW

        # note, derivation now from parent to child
        classDerivation.reverse()
        return classDerivation

    def parseClassDefinition(self, namespace, cdbuf):
        """ get the cim.ClassDefinition by object buffer """
        # we pass in cdbuf here because we can't correctly parse the classname
        #  without knowing the number of properties. so some queries yield these
        #  buffers that we need to inspect and parse.
        derivation = self.parseClassDerivation(namespace, cdbuf)

        parentClassDef = None
        for derivClassName in derivation:
            derivClassBuf = self.getClassDefinitionBuffer(namespace, derivClassName)
            derivClassDef = ClassDefinition(derivClassBuf, parentClassBuf)
            parentClassDef = derivClassDef

        classDef = ClassDefinition(cdbuf, parentClassDef)
        return classDef

    def getClassDefinition(self, namespace, classname):
        """ get the cim.ClassDefinition by name """
        cdbuf = self.getClassDefinitionBuffer(namespace, classname)
        return self.parseClassDefinition(namespace, cdbuf)

    @property
    def classes(self):
        """ get direct child class definitions """
        q = "{}/{}".format(
                self.NS(self.name),
                self.CD())
        self.d("classes query: %s", q)

        for cdbuf in self.getObjects(q):
            yield self.parseClassDefinition(self._ns, cdbuf)


class ClassDefinition(LoggingObject):
    def __init__(self, context, namespace, name):
        super(ClassDefinition, self).__init__()
        self.context = context
        self.ns = namespace
        self.name = name

    def __repr__(self):
        return "ClassDefinition(namespace: {:s}, name: {:s})".format(self.ns, self.name)

    @property
    def namespace(self):
        """ get parent namespace """
        pass

    @property
    def instances(self):
        """ get instances of this class definition """
        pass


class ClassInstance(LoggingObject):
    def __init__(self, context, name):
        super(ClassInstance, self).__init__()
        self.context = context
        self.name = name

    def __repr__(self):
        return "ClassInstance(name: {:s})".format(self.name)

    @property
    def klass(self):
        """ get class definition """
        pass

    @property
    def namespace(self):
        """ get parent namespace """
        pass


class Tree(LoggingObject):
    def __init__(self, cim):
        super(Tree, self).__init__()
        self._context = TreeContext(cim, Index(cim), {}, {})

    def __repr__(self):
        return "Tree"

    @property
    def root(self):
        """ get root namespace """
        return Namespace(self._context, ROOT_NAMESPACE_NAME)


def formatKey(k):
    ret = []
    for part in str(k).split("/"):
        if "." in part:
            ret.append(part[:7] + "..." + part.partition(".")[2])
        else:
            ret.append(part[:7])
    return "/".join(ret)


def rec_ns(ns):
    g_logger.info(ns)
    for c in ns.namespaces:
        rec_ns(c)


def rec_class(ns):
    g_logger.info(ns)

    for c in ns.classes:
        g_logger.info(c)

    for c in ns.namespaces:
        rec_class(c)


def main(type_, path):
    if type_ not in ("xp", "win7"):
        raise RuntimeError("Invalid mapping type: {:s}".format(type_))

    c = CIM(type_, path)
    t = Tree(c)
    print(t.root)
    rec_class(t.root)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    main(*sys.argv[1:])
