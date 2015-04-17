"""
doc
"""
import os
import hashlib
import logging
from datetime import datetime

import hexdump
import vstruct
from vstruct.primitives import *

from common import h
from common import one
from common import LoggingObject

logging.basicConfig(level=logging.DEBUG)
g_logger = logging.getLogger("cim.mapping")


MAPPING_SIGNATURES = v_enum()
MAPPING_SIGNATURES.MAPPING_START_SIGNATURE = 0xABCD
MAPPING_SIGNATURES.MAPPING_END_SIGNATURE = 0xDCBA

MAX_MAPPING_FILES = 0x3

MAPPING_PAGE_ID_MASK = 0x3FFFFFFF
MAPPING_PAGE_UNAVAIL = 0xFFFFFFFF
MAPPING_FILE_CLEAN = 0x1

CIM_TYPE_XP = "xp"
CIM_TYPE_WIN7 = "win7"

DATA_PAGE_SIZE = 0x2000
INDEX_PAGE_SIZE = 0x2000

INDEX_PAGE_INVALID = 0xFFFFFFFF
INDEX_PAGE_INVALID2 = 0x00000000

INDEX_PAGE_TYPES = v_enum()
INDEX_PAGE_TYPES.PAGE_TYPE_UNK = 0x0000
INDEX_PAGE_TYPES.PAGE_TYPE_ACTIVE = 0xACCC
INDEX_PAGE_TYPES.PAGE_TYPE_DELETED = 0xBADD
INDEX_PAGE_TYPES.PAGE_TYPE_ADMIN = 0xADDD


# TODO: maybe stick this onto the CIM class?
#  then it can do lookups against the mapping?
def isIndexPageNumberValid(num):
    return num != INDEX_PAGE_INVALID and num != INDEX_PAGE_INVALID2


class MappingHeaderXP(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.startSignature = v_uint32()
        self.version = v_uint32()
        self.physicalPages = v_uint32()
        self.mappingEntries = v_uint32()


class MappingHeaderWin7(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.startSignature = v_uint32()
        self.version = v_uint32()
        self.firstId = v_uint32()
        self.secondId = v_uint32()
        self.physicalPages = v_uint32()
        self.mappingEntries = v_uint32()


MAPPING_HEADER_TYPES = {
    CIM_TYPE_XP: MappingHeaderXP,
    CIM_TYPE_WIN7: MappingHeaderWin7,
}


class EntryWin7(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.pageNumber = v_uint32()
        self.pageCRC = v_uint32()
        self.freeSpace = v_uint32()
        self.usedSpace = v_uint32()
        self.firstId = v_uint32()
        self.secondId = v_uint32()

    def getPageNumber(self):
        # TODO: add lookup against header.physicalPages to ensure range
        return self.pageNumber & MAPPING_PAGE_ID_MASK


class MappingWin7(vstruct.VStruct):
    """
    lookup via:
      m.entries[0x101].getPageNumber()
    """
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.header = MappingHeaderWin7()
        self.entries = vstruct.VArray()
        self.numFreeDwords = v_uint32()
        self.free = v_bytes()
        self.footerSig = v_uint32()

        # from physical page to logical page
        # cached
        self._reverseMapping = None

    def pcb_header(self):
        for i in xrange(self.header.mappingEntries):
            self.entries.vsAddElement(EntryWin7())

    def pcb_numFreeDwords(self):
        self["free"].vsSetLength(self.numFreeDwords * 0x4)

    def _buildReverseMapping(self):
        for i in xrange(self.header.mappingEntries):
            self._reverseMapping[self.entries[i].getPageNumber()] = i

    def getPhysicalPage(self, logicalPage):
        return self.entries[logicalPage].getPageNumber()

    def getLogicalPage(self, physicalPage):
        if self._reverseMapping is None:
            self._buildReverseMapping()

        return self.entries[logicalPage].getPageNumber()


class EntryXP(vstruct.primitives.v_uint32):
    def __init__(self):
        vstruct.primitives.v_uint32.__init__(self)

    def getPageNumber(self):
        # TODO: add lookup against header.physicalPages to ensure range
        return self & MAPPING_PAGE_ID_MASK


# TODO: maybe merge these together
class MappingXP(vstruct.VStruct):
    """
    lookup via:
      m.entries[0x101].getPageNumber()
    """
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.header = MappingHeaderXP()
        self.entries = vstruct.VArray()
        self.numFreeDwords = v_uint32()
        self.free = v_bytes()
        self.footerSig = v_uint32()

        # from physical page to logical page
        # cached
        self._reverseMapping = None

    def pcb_header(self):
        for i in xrange(self.header.mappingEntries):
            self.entries.vsAddElement(EntryXP())

    def pcb_numFreeDwords(self):
        self["free"].vsSetLength(self.numFreeDwords * 0x4)

    def _buildReverseMapping(self):
        for i in xrange(self.header.mappingEntries):
            self._reverseMapping[self.entries[i].getPageNumber()] = i

    def getPhysicalPage(self, logicalPage):
        return self.entries[logicalPage].getPageNumber()

    def getLogicalPage(self, physicalPage):
        if self._reverseMapping is None:
            self._buildReverseMapping()

        return self.entries[logicalPage].getPageNumber()


MAPPING_TYPES = {
    CIM_TYPE_XP: MappingXP,
    CIM_TYPE_WIN7: MappingWin7,
}


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
BUILTIN_QUALIFIERS.PROP_READ_ACCESS = 0x3
BUILTIN_QUALIFIERS.CLASS_NAMESPACE = 0x6
BUILTIN_QUALIFIERS.CLASS_UNK = 0x7
BUILTIN_QUALIFIERS.PROP_TYPE = 0xA


class QualifierReference(vstruct.VStruct):
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


class QualifiersList(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.size = v_uint32()
        self.qualifiers = vstruct.VArray()
        self.count = 0

    def vsParse(self, bytez, offset=0):
        soffset = offset
        size = v_uint32()
        offset = size.vsParse(bytez, offset=offset)
        self.vsSetField("size", size)  # hack?

        self.count = 0
        while offset < soffset + self.size:
            q = QualifierReference()
            offset = q.vsParse(bytez, offset=offset)
            self.qualifiers.vsAddElement(q)
            self.count += 1
        return offset

    def vsParseFd(self, fd):
        # need to be able to peek at 1-bytes worth of data
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

        # this is the raw struct, without references/strings resolved
        self._prop = _Property()
        offsetProperty = self._propref.offsetPropertyStruct
        self._prop.vsParse(self._classDef.getData(), offset=offsetProperty)

    def getName(self):
        return self._classDef.getString(self._propref.offsetPropertyName)

    def getType(self):
        return self._prop.type

    def getQualifiers(self):
        """ get dict of str to str """
        # TODO: can merge this will ClassDef.getQualifiers
        ret = {}
        for i in xrange(self._prop.qualifiers.count):
            q = self._prop.qualifiers.qualifiers[i]
            qk = self._classDef.getQualifierKey(q)
            qv = self._classDef.getQualifierValue(q)
            ret[str(qk)] = str(qv)
            self.d("%s: %s", qk, qv)
        return ret


class ClassDefinitionPropertyReference(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.offsetPropertyName = v_uint32()
        self.offsetPropertyStruct = v_uint32()


class ClassDefinitionPropertyReferences(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.count = v_uint32()
        self.refs = vstruct.VArray()

    def pcb_count(self):
        g_logger.debug("CDPR: pcb_count: %s", h(self.count))
        self.refs.vsAddElements(self.count, ClassDefinitionPropertyReference)


class _ClassDefinition(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.header = ClassDefinitionHeader()
        self.qualifiers = QualifiersList()
        self.propertyReferences = ClassDefinitionPropertyReferences()

    def pcb_header(self):
        g_logger.debug("CD: \n%s", self.header.tree())

    def pcb_qualifiers(self):
        g_logger.debug("CD: \n%s", self.qualifiers.tree())

    def pcb_propertyReferences(self):
        g_logger.debug("CD: \n%s", self.propertyReferences.tree())


class ClassDefinition(LoggingObject):
    def __init__(self, buf):
        super(ClassDefinition, self).__init__()
        #self.d("hex: \n%s", hexdump.hexdump(buf))
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

        while self._buf.find("\xFF" * 3, off, off + 0x10) != -1:
            off = self._buf.find("\xFF" * 3, off, off + 0x10)
            # scan past sequential 0xFF bytes until non-0xFF
            while ord(self._buf[off]) == 0xFF:
                off += 1
            # break if not "FF FF FF" within 0x10 bytes

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
        self.d("ref: %s", h(ref))
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


class Toc(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.recordId = v_uint32()
        self.offset = v_uint32()
        self.size = v_uint32()
        self.CRC = v_uint32()

    def isZero(self):
        return self.recordId == 0 and \
                self.offset == 0 and \
                self.size == 0 and \
                self.CRC == 0


class TocArray(vstruct.VArray):
    def __init__(self):
        vstruct.VArray.__init__(self)
        self.count = 0

    def vsParse(self, bytez, offset=0):
        self.count = 0
        endoffset = bytez.find("\x00" * 0x10, offset)
        while offset < endoffset + 0x10:
            t = Toc()
            offset = t.vsParse(bytez, offset=offset)
            self.vsAddElement(t)
            self.count += 1
        return offset

    def vsParseFd(self, fd):
        self.count = 0
        while True:
            t = Toc()
            t.vsParseFd(fd)
            self.vsAddElement(t)
            self.count += 1
            if t.isZero():
                return


class DataPage(LoggingObject):
    def __init__(self, buf, logicalPage, physicalPage):
        super(DataPage, self).__init__()
        self._buf = buf
        self.logicalPage = logicalPage
        self.physicalPage = physicalPage
        self.tocs = TocArray()
        self.tocs.vsParse(buf)

    def _getObjectBufByIndex(self, index):
        toc = self.tocs[index]
        return self._buf[toc.offset:toc.offset + toc.size]

    def getDataByKey(self, key):
        targetId = key.getDataId()
        targetSize = key.getDataSize()
        for i in xrange(self.tocs.count):
            toc = self.tocs[i]
            if toc.recordId == targetId:
                if toc.size < targetSize:
                    raise RuntimeError("Data size doesn't match TOC size")
                if toc.size > DATA_PAGE_SIZE - toc.offset:
                    self.d("Large data item: key: %s, size: %s",
                            str(key), hex(targetSize))
                return self._buf[toc.offset:toc.offset + toc.size]
        raise RuntimeError("record ID not found: %s", hex(targetId))


class IndexPageHeader(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.sig = v_uint32()
        self.logicalId = v_uint32()
        self.zero0 = v_uint32()
        self.zero1 = v_uint32()
        self.recordCount = v_uint32()


class _IndexPage(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.header = IndexPageHeader()
        self.unk0 = vstruct.VArray()
        self.children = vstruct.VArray()
        self.keys = vstruct.VArray()
        self.stringDefTableSize = v_uint16()
        self.stringDefTable = vstruct.VArray()
        self.stringTableSize = v_uint16()
        self.stringTable = vstruct.VArray()

    def pcb_header(self):
        self.unk0.vsAddElements(self.header.recordCount, v_uint32)
        self.children.vsAddElements(self.header.recordCount + 1, v_uint32)
        self.keys.vsAddElements(self.header.recordCount, v_uint16)

    def pcb_stringDefTableSize(self):
        self.stringDefTable.vsAddElements(self.stringDefTableSize, v_uint16)

    def pcb_stringTableSize(self):
        self.stringTable.vsAddElements(self.stringTableSize + 1, v_uint16)

    def isValid(self):
        return self.header.sig == INDEX_PAGE_TYPES.PAGE_TYPE_ACTIVE


class Key(LoggingObject):
    def __init__(self, string):
        super(Key, self).__init__()
        self._string = string

    def __str__(self):
        return self._string

    def isDataReference(self):
        return "." in self._string

    KEY_INDEX_DATA_PAGE = 1
    KEY_INDEX_DATA_ID = 2
    KEY_INDEX_DATA_SIZE = 3
    def _getDataPart(self, index):
        if not self.isDataReference():
            raise RuntimeError("key is not a data reference: %s", str(self))
        return self._string.split(".")[index]

    def getDataPage(self):
        return int(self._getDataPart(self.KEY_INDEX_DATA_PAGE))

    def getDataId(self):
        return int(self._getDataPart(self.KEY_INDEX_DATA_ID))

    def getDataSize(self):
        return int(self._getDataPart(self.KEY_INDEX_DATA_SIZE))


class IndexPage(LoggingObject):
    def __init__(self, buf, logicalPage, physicalPage):
        super(IndexPage, self).__init__()
        self._buf = buf
        self.logicalPage = logicalPage
        self.physicalPage = physicalPage
        self._page = _IndexPage()
        self._page.vsParse(buf)

    def _getStringPart(self, stringIndex):
        self.d("stringIndex: %s", hex(stringIndex))

        stringOffset = self._page.stringTable[stringIndex]
        self.d("stringOffset: %s", hex(stringOffset))
        pageStringOffset = len(self._page) + stringOffset
        self.d("stringOffset (page): %s", hex(pageStringOffset))

        pageStringEndOffset = self._buf.find("\x00", pageStringOffset)
        string = self._buf[pageStringOffset:pageStringEndOffset].decode("utf-8")
        self.d("stringPart: %s", string)
        return string

    def _getString(self, stringDefIndex):
        self.d("stringDefIndex: %s", hex(stringDefIndex))

        stringPartCount = self._page.stringDefTable[stringDefIndex]
        self.d("stringPartCount: %s", hex(stringPartCount))

        parts = []
        for i in range(stringPartCount):
            stringPartIndex = self._page.stringDefTable[stringDefIndex + 1 + i]
            self.d("stringPartIndex: %s", hex(stringPartIndex))

            part = self._getStringPart(stringPartIndex)
            parts.append(part)

        string = "/".join(parts)
        return string

    def getKeyCount(self):
        return self._page.header.recordCount

    def getKey(self, keyIndex):
        self.d("keyIndex: %s", hex(keyIndex))

        stringDefIndex = self._page.keys[keyIndex]
        self.d("stringDefIndex: %s", hex(stringDefIndex))
        return Key(self._getString(stringDefIndex))

    def getChildByIndex(self, childIndex):
        return self._page.children[childIndex]

    def isValid(self):
        return self._page.isValid()


class LogicalDataStore(LoggingObject):
    """
    provides an interface for accessing data by logical page or object id.
    """
    def __init__(self, cim, filePath, mapping):
        super(LogicalDataStore, self).__init__()
        self._cim = cim
        self._filePath = filePath
        self._mapping = mapping

    def getPhysicalPageBuffer(self, index):
        with open(self._filePath, "rb") as f:
            f.seek(DATA_PAGE_SIZE * index)
            return f.read(DATA_PAGE_SIZE)

    def getPageBuffer(self, index):
        physicalPage = self._mapping.entries[index].getPageNumber()
        return self.getPhysicalPageBuffer(physicalPage)

    def getPage(self, index):
        physicalPage = self._mapping.entries[index].getPageNumber()
        return DataPage(self.getPageBuffer(index), index, physicalPage)

    def getObjectBuffer(self, key):
        if not key.isDataReference():
            raise RuntimeError("Key is not data reference: %s", str(key))

        # this logic of this function is a bit more complex than
        #   we'd want, since we have to handle the case where an
        #   item's data spans multiple pages.
        dataPage = key.getDataPage()
        page = self.getPage(dataPage)

        targetSize = key.getDataSize()
        firstData = page.getDataByKey(key)

        # this is the common case, return early
        if targetSize == len(firstData):
            return firstData

        # here we handle data that spans multiple pages
        data = [firstData]
        foundSize = len(firstData)

        i = 1
        while foundSize < targetSize:
            nextPage = self.getPageBuffer(dataPage + i)
            if foundSize + len(nextPage) > targetSize:
                # this is the last page containing data for this item
                chunkSize = targetSize - foundSize
                data.append(nextPage[:chunkSize])
                foundSize += chunkSize
            else:
                # the entire page is used for this item
                data.append(nextPage)
                foundSize += len(nextPage)
            i += 1

        return "".join(data)


class LogicalIndexStore(LoggingObject):
    """
    provides an interface for accessing index nodes by logical page id.
    indexing logic should go at a higher level.
    """
    def __init__(self, cim, filePath, mapping):
        super(LogicalIndexStore, self).__init__()
        self._cim = cim
        self._filePath = filePath
        self._mapping = mapping

        # cache
        self._rootPageNumber = None

    def getPhysicalPageBuffer(self, index):
        with open(self._filePath, "rb") as f:
            f.seek(INDEX_PAGE_SIZE * index)
            return f.read(INDEX_PAGE_SIZE)

    def getPageBuffer(self, index):
        physicalPage = self._mapping.entries[index].getPageNumber()
        return self.getPhysicalPageBuffer(physicalPage)

    def getPage(self, index):
        physicalPage = self._mapping.entries[index].getPageNumber()
        return IndexPage(self.getPageBuffer(index), index, physicalPage)

    def _getRootPageNumberWin7(self):
        return int(self._mapping.entries[0x0].usedSpace)

    def _getRootPageNumber(self):
        if self._cim.getCimType() == CIM_TYPE_WIN7:
            return self._getRootPageNumberWin7()

        # TODO: for xp, we should be able to inspect page[0] of the index.
        # this algorithm walks all nodes and tracks which nodes are children
        #   of other nodes. we expect there to be a single node that is never
        #   linked as a child --- therefore, its the root.
        possibleRoots = set([])
        impossibleRoots = set([])
        for i in xrange(self._mapping.header.mappingEntries):
            try:
                page = self.getPage(i)
            except:
                # TODO: find out why this is. probably: validate page ranges.
                self.w("bad unpack: %s", hex(i))
                continue

            if not page.isValid():
                continue

            # careful: vstruct returns int-like objects with
            #   no hash-equivalence
            possibleRoots.add(int(i))
            for j in xrange(page.getKeyCount() + 1):
                childPage = page.getChildByIndex(j)
                if not isIndexPageNumberValid(childPage):
                    continue
                # careful: vstruct int types
                impossibleRoots.add(int(childPage))
        ret = possibleRoots - impossibleRoots
        # note: hardcode that the root is not logical page 0
        ret.remove(int(0))
        if len(ret) != 1:
            raise RuntimeError("Unable to determine root index node: %s" % (str(ret)))
        return ret.pop()

    def getRootPageNumber(self):
        if self._rootPageNumber is None:
            self._rootPageNumber = self._getRootPageNumber()
        self.d("root page number: %s", h(self._rootPageNumber))
        return self._rootPageNumber

    def getRootPage(self):
        return self.getPage(self.getRootPageNumber())


class CIM(LoggingObject):
    def __init__(self, cim_type, directory):
        super(CIM, self).__init__()
        self._cim_type = cim_type
        self._directory = directory
        self._mappingClass = MAPPING_TYPES[self._cim_type]
        self._mappingHeaderClass = MAPPING_HEADER_TYPES[self._cim_type]

        # caches
        self._currentMappingFile = None
        self._currentDataMapping = None
        self._currentIndexMapping = None
        self._dataStore = None
        self._indexStore = None

    def _getDataFilePath(self):
        return os.path.join(self._directory, "OBJECTS.DATA")

    def _getIndexFilePath(self):
        return os.path.join(self._directory, "INDEX.BTR")

    def _getCurrentMappingFile(self):
        if self._currentMappingFile is None:
            self.d("finding current mapping file")
            mappingFilePath = None
            maxVersion = 0
            for i in xrange(MAX_MAPPING_FILES):
                fn = "MAPPING{:d}.MAP".format(i + 1)
                fp = os.path.join(self._directory, fn)
                if not os.path.exists(fp):
                    continue
                h = self._mappingHeaderClass()

                with open(fp, "rb") as f:
                    h.vsParseFd(f)

                self.d("%s: version: %s", fn, hex(h.version))
                if h.version > maxVersion:
                    mappingFilePath = fp
                    maxVersion = h.version
            self._currentMappingFile = mappingFilePath
            self.d("current mapping file: %s", self._currentMappingFile)
        return self._currentMappingFile

    def getCimType(self):
        return self._cim_type

    def getMappings(self):
        if self._currentIndexMapping is None:
            fp = self._getCurrentMappingFile()
            dm = self._mappingClass()
            im = self._mappingClass()
            with open(fp, "rb") as f:
                dm.vsParseFd(f)
                im.vsParseFd(f)
            self._currentDataMapping = dm
            self._currentIndexMapping = im
        return self._currentDataMapping, self._currentIndexMapping

    def getDataMapping(self):
        if self._currentDataMapping is None:
            self._currentDataMapping, self._currentIndexMapping = self.getMappings()
        return self._currentDataMapping

    def getIndexMapping(self):
        if self._currentIndexMapping is None:
            self._currentDataMapping, self._currentIndexMapping = self.getMappings()
        return self._currentIndexMapping

    def getLogicalDataStore(self):
        if self._dataStore is None:
            self._dataStore = LogicalDataStore(self, self._getDataFilePath(), self.getDataMapping())
        return self._dataStore

    def getLogicalIndexStore(self):
        if self._indexStore is None:
            self._indexStore = LogicalIndexStore(self, self._getIndexFilePath(), self.getIndexMapping())
        return self._indexStore


class Moniker(LoggingObject):
    def __init__(self, string):
        super(Moniker, self).__init__()
        self._string = string
        self.hostname = None  # type: str
        self.namespace = None  # type: str
        self.klass = None  # type: str
        self.instance = None  # type: dict of str to str
        self._parse()

    def __str__(self):
        return self._string

    def _parse(self):
        """
        supported schemas:
            //./root/cimv2 --> namespace
            //HOSTNAME/root/cimv2 --> namespace
            winmgmts://./root/cimv2 --> namespace
            //./root/cimv2:Win32_Service --> class
            //./root/cimv2:Win32_Service.Name="Beep" --> instance
            //./root/cimv2:Win32_Service.Name='Beep' --> instance

        we'd like to support this, but can't differentiate this
          from a class:
            //./root/cimv2/Win32_Service --> class
        """
        s = self._string
        s = s.replace("\\", "/")

        if s.startswith("winmgmts:"):
            s = s[len("winmgmts:"):]

        if not s.startswith("//"):
            raise RuntimeError("Moniker doesn't contain '//': %s" % (s))
        s = s[len("//"):]

        self.hostname, _, s = s.partition("/")
        if self.hostname == ".":
            self.hostname = "localhost"

        s, _, keys = s.partition(".")
        if keys == "":
            keys = None
        # s must now not contain any special characters
        # we'll process the keys later

        self.namespace, _, self.klass = s.partition(":")
        if self.klass == "":
            self.klass = None
        self.namespace = self.namespace.replace("/", "\\")

        if keys is not None:
            self.instance = {}
            for key in keys.split(","):
                k, _, v = key.partition("=")
                self.instance[k] = v.strip("\"'")


class Index(LoggingObject):
    def __init__(self, cim):
        super(Index, self).__init__()
        self._cim = cim
        self._indexStore = cim.getLogicalIndexStore()

    LEFT_CHILD_DIRECTION = 0
    RIGHT_CHILD_DIRECTION = 1
    def _lookupKeysChild(self, key, page, i, direction):
        childIndex = page.getChildByIndex(i + direction)
        if not isIndexPageNumberValid(childIndex):
            return []
        childPage = self._indexStore.getPage(childIndex)
        return self._lookupKeys(key, childPage)

    def _lookupKeysLeft(self, key, page, i):
        return self._lookupKeysChild(key, page, i, self.LEFT_CHILD_DIRECTION)

    def _lookupKeysRight(self, key, page, i):
        return self._lookupKeysChild(key, page, i, self.RIGHT_CHILD_DIRECTION)

    def _lookupKeys(self, key, page):
        skey = str(key)
        keyCount = page.getKeyCount()

        self.d("index lookup: %s: page: %s",
                formatKey(key),
                h(page.logicalPage))

        matches = []
        for i in xrange(keyCount):
            k = page.getKey(i)
            sk = str(k)

            if i != keyCount - 1:
                # not last
                if skey in sk:
                    self.d("contains match: %s", formatKey(sk))
                    self.d("going left")
                    matches.extend(self._lookupKeysLeft(key, page, i))
                    self.d("including: %s", formatKey(sk))
                    matches.append(k)
                    self.d("going right")
                    matches.extend(self._lookupKeysRight(key, page, i))
                    continue
                if skey < sk:
                    self.d("less-than match, going left: %s", formatKey(sk))
                    matches.extend(self._lookupKeysLeft(key, page, i))
                    break
                if skey > sk:
                    self.d("greater-than, moving along: %s", formatKey(sk))
                    continue
            else:
                # last key
                if skey in sk:
                    matches.extend(self._lookupKeysLeft(key, page, i))
                    matches.append(k)
                    matches.extend(self._lookupKeysRight(key, page, i))
                    break
                if skey < sk:
                    matches.extend(self._lookupKeysLeft(key, page, i))
                    break
                if skey > sk:
                    # we have to be in this node for a reason,
                    #   so it must be the right child
                    matches.extend(self._lookupKeysRight(key, page, i))
                    break
        return matches

    def lookupKeys(self, key):
        """
        get keys that match the given key prefix
        """
        return self._lookupKeys(key, self._indexStore.getRootPage())

    NAMESPACE_PREFIX = "NS_"
    CLASS_DEFINITION_PREFIX = "CD_"  # has data
    MAYBE_CLASS_REFERENCE_PREFIX = "CR_"
    MAYBE_REFERENCE_PREFIX = "R_"
    CLASS_INSTANCE_PREFIX = "CI_"
    UNK_CLASS_INSTANCE_PREFIX = "KI_"
    INSTANCE_NAME_PREFIX = "IL_"  # has data
    UNK_INSTANCE_NAME_PREFIX = "I_"  # has data

    def _hash(self, s):
        cimType = self._cim.getCimType()
        if cimType == CIM_TYPE_XP:
            h = hashlib.md5()
        elif cimType == CIM_TYPE_WIN7:
            h = hashlib.sha256()
        h.update(s)
        return h.hexdigest().upper()

    def _encodeItem(self, prefix, s):
        return "{prefix:s}{hash_:s}".format(
                prefix=prefix,
                hash_=self._hash(s.upper().encode("UTF-16LE")))

    def _encodeNamespace(self, namespace):
        return self._encodeItem(self.NAMESPACE_PREFIX, namespace)

    def _encodeClassDefinition(self, klass):
        return self._encodeItem(self.CLASS_DEFINITION_PREFIX, klass)

    def _lookupMonikerClassInstance(self, moniker):
        self.d("moniker: %s", moniker)

    def _lookupMonikerClassInstances(self, moniker):
        self.d("moniker: %s", moniker)
        keyString = self._encodeNamespace(moniker.namespace)
        keyString += "/" + self._encodeItem(self.CLASS_INSTANCE_PREFIX, moniker.klass)
        keyString += "/" + self.INSTANCE_NAME_PREFIX
        self.d("keystring: %s", keyString)
        key = Key(keyString)
        return self.lookupKeys(key)

    def _lookupMonikerClassDefinition(self, moniker):
        self.d("moniker: %s", moniker)
        keyString = self._encodeNamespace(moniker.namespace)
        keyString += "/" + self._encodeClassDefinition(moniker.klass)
        self.d("keystring: %s", keyString)
        key = Key(keyString)
        return self.lookupKeys(key)

    def _lookupMonikerNamespace(self, moniker):
        self.d("moniker: %s", moniker)
        keyString = self._encodeNamespace(moniker.namespace)
        self.d("keystring: %s", keyString)
        key = Key(keyString)
        return self.lookupKeys(key)

    def lookupMoniker(self, moniker):
        self.d("moniker: %s", moniker)
        if moniker.instance is not None:
            return self._lookupMonikerClassInstance(moniker)
        elif moniker.klass is not None:
            return self._lookupMonikerClassDefinition(moniker)
        elif moniker.namespace is not None:
            return self._lookupMonikerNamespace(moniker)
        else:
            raise RuntimeError("Unsupported moniker lookup: %s" % (str(moniker)))


def formatKey(k):
    ret = []
    for part in str(k).split("/"):
        if "." in part:
            ret.append(part[:7] + "..." + part.partition(".")[2])
        else:
            ret.append(part[:7])
    return "/".join(ret)


def main(type_, path):
    if type_ not in ("xp", "win7"):
        raise RuntimeError("Invalid mapping type: {:s}".format(type_))

    c = CIM(type_, path)

    #print(c.getDataMapping().tree())
    #print(c.getIndexMapping().tree())


    #print(c.getCurrentMapping().tree())
    #with open(os.path.join(path, "OBJECTS.DATA"), "rb") as f:
    #    buf = f.read(DATA_PAGE_SIZE)

    #p = Page(buf)
    #for i in xrange(p.tocs.count):
    #    hexdump.hexdump(p._getObjectBufByIndex(i))
    #    print("\n")

    #buf = c.getLogicalIndexPageBuffer(1)
    #p = IndexPage(buf)
    #print(p._page.tree())

    #for i in xrange(p._page.header.recordCount):
    #    print(p.getItem(i))
    #graphIndex(c)

    #k = Key("NS_FCBAF5A1255D45B1176570C0B63AA60199749700C79A11D5811D54A83A1F4EFD/CD_FD1C1D414B71B5082C266A650E31EF6D5019382724244B685F217C0AAE00A921.3.1.12701")
    #hexdump.hexdump(c.getDataBuffer(k))

    #p = c.getLogicalIndexPage(1)
    #for i in xrange(p.getKeyCount()):
    #    print(formatKey(p.getKey(i)))

    i = Index(c)
    #needle = Key("NS_E1DD43413ED9FD9C458D2051F082D1D739399B29035B455F09073926E5ED9870/CI_CFF")

    #needle = Key("NS_68577372C66A7B20658487FBD959AA154EF54B5F935DCC5663E9228B44322805/CD_FFF2")
    #print("looking for: " + formatKey(needle))
    #for k in i.lookupKeys(needle):
    #    print(formatKey(k))


    #def dump_class_def(cd):
    #    #g_logger.info(cd._def.tree())
    #    g_logger.info("classname: %s", cd.getClassName())
    #    g_logger.info("super: %s", cd.getSuperClassName())
    #    g_logger.info("ts: %s", cd.getTimestamp().isoformat("T"))
    #    g_logger.info("qualifiers:")
    #    for k, v in cd.getQualifiers().iteritems():
    #        g_logger.info("  %s: %s", k, str(v))
    #    g_logger.info("properties:")
    #    for propname, prop in cd.getProperties().iteritems():
    #        g_logger.info("  name: %s", prop.getName())
    #        g_logger.info("    type: %s", prop.getType())
    #        g_logger.info("    qualifiers:")
    #        for k, v in prop.getQualifiers().iteritems():
    #            g_logger.info("      %s: %s", k, str(v))
#
    #className = "Win32_Service"

    #while className != "":
    #    g_logger.info("%s", "=" * 80)
    #    g_logger.info("classname: %s", className)
    #    needle = Moniker("//./root/cimv2:%s" % (className))
    #    g_logger.info("moniker: %s", str(needle))
    #    k = one(i.lookupMoniker(needle))
    #    g_logger.info("database id: %s", formatKey(k))
    #    g_logger.info("objects.data page: %s", h(k.getDataPage()))
    #    physicalOffset = DATA_PAGE_SIZE * \
    #                      c.getDataMapping().getPhysicalPage(k.getDataPage())
    #    g_logger.info("physical offset: %s", h(physicalOffset))
    #    buf = c.getLogicalDataStore().getObjectBuffer(k)
    #    #hexdump.hexdump(buf)
    #    cd = ClassDefinition(buf)
    #    dump_class_def(cd)
    #    className = cd.getSuperClassName()
    #print(c.getIndexRootPageNumber())
    #indexStore = c.getLogicalIndexStore()
    #print(hex(indexStore.getRootPageNumber()))
    className = "ActiveScriptEventConsumer"
    g_logger.info("classname: %s", className)
    needle = Moniker("//./root/subscription:%s" % (className))
    g_logger.info("moniker: %s", str(needle))
    g_logger.info(i._lookupMonikerClassInstances(needle))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    main(*sys.argv[1:])
