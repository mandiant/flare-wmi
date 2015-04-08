"""
doc
"""
import os
import inspect
import logging

import vstruct
from vstruct.primitives import *

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


class LoggingObject(object):
    def __init__(self):
        self._logger = logging.getLogger("{:s}.{:s}".format(
            __file__, self.__class__.__name__))

    def _getCallerFunction(self):
        FUNCTION_NAME_INDEX = 3
        return inspect.stack()[3][FUNCTION_NAME_INDEX]

    def _formatFormatString(self, args):
        return [self._getCallerFunction() + ": " + args[0]] + [a for a in args[1:]]

    def d(self, *args, **kwargs):
        self._logger.debug(*self._formatFormatString(args), **kwargs)

    def i(self, *args, **kwargs):
        self._logger.info(*self._formatFormatString(args), **kwargs)

    def w(self, *args, **kwargs):
        self._logger.warn(*self._formatFormatString(args), **kwargs)

    def e(self, *args, **kwargs):
        self._logger.error(*self._formatFormatString(args), **kwargs)


class XPHeader(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.startSignature = v_uint32()
        self.version = v_uint32()
        self.physicalPages = v_uint32()
        self.mappingEntries = v_uint32()


class Win7Header(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.startSignature = v_uint32()
        self.version = v_uint32()
        self.firstId = v_uint32()
        self.secondId = v_uint32()
        self.physicalPages = v_uint32()
        self.mappingEntries = v_uint32()


MAPPING_HEADER = {
    CIM_TYPE_XP: XPHeader,
    CIM_TYPE_WIN7: Win7Header,
}


class Entry(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.pageNumber = v_uint32()
        self.pageCRC = v_uint32()
        self.freeSpace = v_uint32()
        self.userData = v_uint32()
        self.firstId = v_uint32()
        self.secondId = v_uint32()

    def getPageNumber(self):
        # TODO: add lookup against header.physicalPages to ensure range
        return self.pageNumber & MAPPING_PAGE_ID_MASK


class Mapping(vstruct.VStruct):
    """
    lookup via:
      m.entries[0x101].getPageNumber()
    """
    def __init__(self, headerClass):
        vstruct.VStruct.__init__(self)
        self.header = headerClass()
        self.entries = vstruct.VArray()
        self.numFreeDwords = v_uint32()
        self.free = v_bytes()
        self.footerSig = v_uint32()

        # from physical page to logical page
        # cached
        self._reverseMapping = None

    def pcb_header(self):
        for i in xrange(self.header.mappingEntries):
            self.entries.vsAddElement(Entry())

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


class Object(vstruct.VStruct):
    # TODO
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.nameLen = v_uint32()
        self.name = v_wstr()
        self.unknown0 = v_uint64()
        self.unknown1 = v_uint32()

    def pcb_nameLen(self):
        self.name = v_wstr(size=self.nameLen / 2)


class DataPage(LoggingObject):
    def __init__(self, buf):
        super(DataPage, self).__init__()
        self._buf = buf
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


INDEX_PAGE_TYPES = v_enum()
INDEX_PAGE_TYPES.PAGE_TYPE_UNK = 0x0000
INDEX_PAGE_TYPES.PAGE_TYPE_ACTIVE = 0xACCC
INDEX_PAGE_TYPES.PAGE_TYPE_DELETED = 0xBADD
INDEX_PAGE_TYPES.PAGE_TYPE_ADMIN = 0xADDD


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
    def __init__(self, buf):
        super(IndexPage, self).__init__()
        self._buf = buf
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


class Template(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)


class CIM(LoggingObject):
    def __init__(self, cim_type, directory):
        super(CIM, self).__init__()
        self._cim_type = cim_type
        self._directory = directory
        self._mappingHeaderClass = MAPPING_HEADER[self._cim_type]

        # caches
        self._currentMappingFile = None
        self._currentDataMapping = None
        self._currentIndexMapping = None

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
                h = self._mappingHeaderClass()

                with open(fp, "rb") as f:
                    h.vsParseFd(f)

                self.d("%s: version: %s", fn, hex(h.version))
                if h.version > maxVersion:
                    mappingFilePath = fp
                    maxVersion = h.version
            self._currentMappingFile = mappingFilePath
        return self._currentMappingFile

    def getCurrentMappings(self):
        if self._currentIndexMapping is None:
            fp = self._getCurrentMappingFile()
            dm = Mapping(self._mappingHeaderClass)
            im = Mapping(self._mappingHeaderClass)
            with open(fp, "rb") as f:
                dm.vsParseFd(f)
                im.vsParseFd(f)
            self._currentDataMapping = dm
            self._currentIndexMapping = im
        return self._currentDataMapping, self._currentIndexMapping

    def getCurrentDataMapping(self):
        if self._currentDataMapping is None:
            self._currentDataMapping, self._currentIndexMapping = self.getCurrentMappings()
        return self._currentDataMapping

    def getCurrentIndexMapping(self):
        if self._currentIndexMapping is None:
            self._currentDataMapping, self._currentIndexMapping = self.getCurrentMappings()
        return self._currentIndexMapping

    def getPhysicalDataPageBuffer(self, index):
        with open(self._getDataFilePath(), "rb") as f:
            f.seek(DATA_PAGE_SIZE * index)
            return f.read(DATA_PAGE_SIZE)

    def getPhysicalIndexPageBuffer(self, index):
        with open(self._getIndexFilePath(), "rb") as f:
            f.seek(INDEX_PAGE_SIZE * index)
            return f.read(INDEX_PAGE_SIZE)

    def getLogicalDataPageBuffer(self, index):
        m = self.getCurrentDataMapping()
        physicalPage = m.entries[index].getPageNumber()
        return self.getPhysicalDataPageBuffer(physicalPage)

    def getLogicalIndexPageBuffer(self, index):
        m = self.getCurrentIndexMapping()
        physicalPage = m.entries[index].getPageNumber()
        return self.getPhysicalIndexPageBuffer(physicalPage)

    def getLogicalIndexPage(self, index):
        return IndexPage(self.getLogicalIndexPageBuffer(index))

    def getLogicalDataPage(self, index):
        return DataPage(self.getLogicalDataPageBuffer(index))

    def getDataBuffer(self, key):
        if not key.isDataReference():
            raise RuntimeError("key is not data reference: %s", str(key))

        # this logic of this function is a bit more complex than
        #   we'd want, since we have to handle the case where an
        #   item's data spans multiple pages.
        dataPage = key.getDataPage()
        page = self.getLogicalDataPage(dataPage)

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
            nextPage = self.getLogicalDataPageBuffer(dataPage + i)
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


def formatKey(k):
    ret = []
    for part in str(k).split("/"):
        if "." in part:
            ret.append(part[:7] + "..." + part.partition(".")[2])
        else:
            ret.append(part[:7])
    return "/".join(ret)


def formatIndexPage(c, p, num):
    ret = []
    ret.append("<header> logical page: {:s} | physical page: {:s} | count: {:s}".format(
        hex(num).strip("L"),
        hex(c.getCurrentIndexMapping().getPhysicalPage(num)).strip("L"),
        hex(p.getKeyCount()).strip("L")))
    for i in xrange(p.getKeyCount()):
        key = p.getKey(i)
        g_logger.debug("%s", str(key))
        ret.append(" | {{ {key:s} | <child_{child:s}> {child:s} }}".format(
            key=formatKey(key),
            child=hex(p.getChildByIndex(i)).strip("L")))
    return "".join(ret)


def graphIndexPageRec(c, p, num):
    print("  \"node{:s}\" [".format(hex(num).strip("L")))
    print("     label = \"{:s}\"".format(formatIndexPage(c, p, num)))
    print("     shape = \"record\"")
    print("  ];")

    for i in xrange(p.getKeyCount()):
        childIndex = p.getChildByIndex(i)
        if childIndex == INDEX_PAGE_INVALID:
            continue
        graphIndexPageRec(c, c.getLogicalIndexPage(childIndex), childIndex)

    for i in xrange(p.getKeyCount()):
        childIndex = p.getChildByIndex(i)
        if childIndex == INDEX_PAGE_INVALID:
            continue
        print("  \"node{num:s}\":child{child:s} -> \"node{child:s}\"".format(
            num=hex(num).strip("L"),
            child=hex(childIndex).strip("L")))


def graphIndex(c):
    print("digraph g {")
    print("  graph [ rankdir = \"LR\" ];")
    print("  node [")
    print("     fontsize = \"16\"")
    print("     shape = \"ellipse\"")
    print("  ];")
    print("  edge [];")

    p = c.getLogicalIndexPage(1)
    graphIndexPageRec(c, p, 1)

    print("}")


def main(type_, path):
    if type_ not in ("xp", "win7"):
        raise RuntimeError("Invalid mapping type: {:s}".format(type_))

    c = CIM(type_, path)

    #print(c.getCurrentDataMapping().tree())
    #print(c.getCurrentIndexMapping().tree())


    #print(c.getCurrentMapping().tree())
    #with open(os.path.join(path, "OBJECTS.DATA"), "rb") as f:
    #    buf = f.read(DATA_PAGE_SIZE)

    #p = Page(buf)
    import hexdump
    #for i in xrange(p.tocs.count):
    #    hexdump.hexdump(p._getObjectBufByIndex(i))
    #    print("\n")

    #buf = c.getLogicalIndexPageBuffer(1)
    #p = IndexPage(buf)
    #print(p._page.tree())

    #for i in xrange(p._page.header.recordCount):
    #    print(p.getItem(i))
    #graphIndex(c)

    k = Key("NS_FCBAF5A1255D45B1176570C0B63AA60199749700C79A11D5811D54A83A1F4EFD/CD_FD1C1D414B71B5082C266A650E31EF6D5019382724244B685F217C0AAE00A921.3.1.12701")
    hexdump.hexdump(c.getDataBuffer(k))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    main(*sys.argv[1:])
