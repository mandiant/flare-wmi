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

logging.getLogger("cim.IndexPage").setLevel(logging.WARNING)
logging.getLogger("cim.Index").setLevel(logging.WARNING)


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


def formatKey(k):
    ret = []
    for part in str(k).split("/"):
        if "." in part:
            ret.append(part[:7] + "..." + part.partition(".")[2])
        else:
            ret.append(part[:7])
    return "/".join(ret)


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

        # cache
        self._keys = {}

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
        if keyIndex not in self._keys:
            stringDefIndex = self._page.keys[keyIndex]
            self.d("stringDefIndex: %s", hex(stringDefIndex))
            self._keys[keyIndex] = Key(self._getString(stringDefIndex))
        return self._keys[keyIndex]

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
            # TODO: should simply foreach an iterable here
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


class CachedLogicalIndexStore(LoggingObject):
    def __init__(self, indexStore):
        super(CachedLogicalIndexStore, self).__init__()
        self._indexStore = indexStore

        # cache
        self._pages = {}

    def getPhysicalPageBuffer(self, index):
        return self._indexStore.getPhysicalPageBuffer(index)

    def getPageBuffer(self, index):
        return self._indexStore.getPageBuffer(index)

    def getPage(self, index):
        if index not in self._pages:
            self._pages[index] = self._indexStore.getPage(index)
        return self._pages[index]

    def getRootPageNumber(self):
        return self._indexStore.getRootPageNumber()

    def getRootPage(self):
        return self.getPage(self.getRootPageNumber())


class Index(LoggingObject):
    def __init__(self, cimType, indexStore):
        super(Index, self).__init__()
        self._cimType = cimType
        self._indexStore = CachedLogicalIndexStore(indexStore)

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

    def hash(self, s):
        if self._cimType == CIM_TYPE_XP:
            h = hashlib.md5()
        elif self._cimType == CIM_TYPE_WIN7:
            h = hashlib.sha256()
        h.update(s)
        return h.hexdigest().upper()


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


def main(type_, path):
    if type_ not in ("xp", "win7"):
        raise RuntimeError("Invalid mapping type: {:s}".format(type_))
    c = CIM(type_, path)
    print("ok")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    main(*sys.argv[1:])
