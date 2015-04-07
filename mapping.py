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

    def pcb_header(self):
        for i in xrange(self.header.mappingEntries):
            self.entries.vsAddElement(Entry())

    def pcb_numFreeDwords(self):
        self["free"].vsSetLength(self.numFreeDwords * 0x4)


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


class IndexPage(LoggingObject):
    def __init__(self, buf):
        super(IndexPage, self).__init__()
        self._buf = buf
        self.header = IndexPageHeader()
        self.header.vsParse(buf)

    def isValid(self):
        return self.header.sig == INDEX_PAGE_TYPES.PAGE_TYPE_ACTIVE


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

    def getLogicalDataPageBuffer(self, index):
        m = self.getCurrentDataMapping()
        physicalPage = m.entries[index].getPageNumber()
        with open(self._getDataFilePath(), "rb") as f:
            f.seek(DATA_PAGE_SIZE * physicalPage)
            return f.read(DATA_PAGE_SIZE)

    def getLogicalIndexPage(self, index):
        m = self.getCurrentIndexMapping()
        physicalPage = m.entries[index].getPageNumber()
        with open(self._getIndexFilePath(), "rb") as f:
            f.seek(INDEX_PAGE_SIZE * physicalPage)
            return f.read(INDEX_PAGE_SIZE)


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
    #import hexdump
    #for i in xrange(p.tocs.count):
    #    hexdump.hexdump(p._getObjectBufByIndex(i))
    #    print("\n")

    buf = c.getLogicalIndexPage(0)
    p = IndexPage(buf)
    print(p.header.tree())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    main(*sys.argv[1:])
