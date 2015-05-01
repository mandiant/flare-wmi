"""
doc
"""
import os
import hashlib
import logging
from datetime import datetime
from collections import namedtuple

import hexdump
from funcy.objects import cached_property
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
def is_index_page_number_valid(num):
    return num != INDEX_PAGE_INVALID and num != INDEX_PAGE_INVALID2


class MappingHeaderXP(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.start_signature = v_uint32()
        self.version = v_uint32()
        self.physical_page_count = v_uint32()
        self.mapping_entry_count = v_uint32()


class MappingHeaderWin7(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.start_signature = v_uint32()
        self.version = v_uint32()
        self.first_id = v_uint32()
        self.second_id = v_uint32()
        self.physical_page_count = v_uint32()
        self.mapping_entry_count = v_uint32()


MAPPING_HEADER_TYPES = {
    CIM_TYPE_XP: MappingHeaderXP,
    CIM_TYPE_WIN7: MappingHeaderWin7,
}


class EntryWin7(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self._page_number = v_uint32()
        self.page_crc = v_uint32()
        self.free_space = v_uint32()
        self.used_space = v_uint32()
        self.first_id = v_uint32()
        self.second_id = v_uint32()

    @property
    def page_number(self):
        # TODO: add lookup against header.physicalPages to ensure range
        return self._page_number & MAPPING_PAGE_ID_MASK


class MappingWin7(vstruct.VStruct):
    """
    lookup via:
      m.entries[0x101].getPageNumber()
    """
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.header = MappingHeaderWin7()
        self.entries = vstruct.VArray()
        self.free_dword_count = v_uint32()
        self.free = v_bytes()
        self.footer_signature = v_uint32()

        # from physical page to logical page
        # cached
        self._reverse_mapping = None

    def pcb_header(self):
        for i in xrange(self.header.mapping_entry_count):
            self.entries.vsAddElement(EntryWin7())

    def pcb_free_dword_count(self):
        self["free"].vsSetLength(self.free_dword_count * 0x4)

    def _build_reverse_mapping(self):
        for i in xrange(self.header.mapping_entry_count):
            self._reverse_mapping[self.entries[i].page_number] = i

    def get_physical_page_number(self, logical_page_number):
        return self.entries[logical_page_number].page_number

    def get_logical_page_number(self, physical_page_number):
        if self._reverseMapping is None:
            self._build_reverse_mapping()

        return self._reverse_mapping[physical_page_number].page_number


class EntryXP(vstruct.primitives.v_uint32):
    def __init__(self):
        vstruct.primitives.v_uint32.__init__(self)

    @property
    def page_number(self):
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
        self.free_dword_count = v_uint32()
        self.free = v_bytes()
        self.footer_signature = v_uint32()

        # from physical page to logical page
        # cached
        self._reverse_mapping = None

    def pcb_header(self):
        for i in xrange(self.header.mapping_entries_count):
            self.entries.vsAddElement(EntryXP())

    def pcb_free_dword_count(self):
        self["free"].vsSetLength(self.free_dword_count * 0x4)

    def _build_reverse_mapping(self):
        for i in xrange(self.header.mapping_entries_count):
            self._reverse_mapping[self.entries[i].page_number] = i

    def get_physical_page_number(self, logical_page_number):
        return self.entries[logical_page_number].page_number

    def get_logical_page_number(self, physical_page_number):
        if self._reverseMapping is None:
            self._build_reverse_mapping()

        return self._reverse_mapping[physical_page_number].page_number


MAPPING_TYPES = {
    CIM_TYPE_XP: MappingXP,
    CIM_TYPE_WIN7: MappingWin7,
}


class TOCEntry(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.record_id = v_uint32()
        self.offset = v_uint32()
        self.size = v_uint32()
        self.CRC = v_uint32()

    @property
    def is_zero(self):
        return self.record_id == 0 and \
                self.offset == 0 and \
                self.size == 0 and \
                self.CRC == 0


class TOC(vstruct.VArray):
    def __init__(self):
        vstruct.VArray.__init__(self)
        self.count = 0

    def vsParse(self, bytez, offset=0, fast=False):
        self.count = 0
        endoffset = bytez.find("\x00" * 0x10, offset)
        while offset < endoffset + 0x10:
            t = TOCEntry()
            offset = t.vsParse(bytez, offset=offset)
            self.vsAddElement(t)
            self.count += 1
        return offset

    def vsParseFd(self, fd):
        self.count = 0
        while True:
            t = TOCEntry()
            t.vsParseFd(fd)
            self.vsAddElement(t)
            self.count += 1
            if t.is_zero:
                return


class DataPage(LoggingObject):
    def __init__(self, buf, logical_page_number, physical_page_number):
        super(DataPage, self).__init__()
        self._buf = buf
        self.logical_page_number = logical_page_number
        self.physical_page_number = physical_page_number
        self.toc = TOC()
        self.toc.vsParse(buf)

    def _get_object_buffer_by_index(self, toc_index):
        toc_entry = self.toc[toc_index]
        return self._buf[toc_entry.offset:toc_entry.offset + toc_entry.size]

    def get_data_by_key(self, key):
        """
        Prefer to use __getitem__.

        key: Key instance
        """
        target_id = key.data_id()
        target_size = key.data_length()
        for i in xrange(self.toc.count):
            toc = self.toc[i]
            if toc.record_id == target_id:
                if toc.size < target_size:
                    raise RuntimeError("Data size doesn't match TOC size")
                if toc.size > DATA_PAGE_SIZE - toc.offset:
                    self.d("Large data item: key: %s, size: %s",
                            str(key), hex(target_size))
                return self._buf[toc.offset:toc.offset + toc.size]
        raise RuntimeError("record ID not found: %s", hex(target_id))

    def __getitem__(self, key):
        """
        key: Key instance
        """
        return self.get_data_by_key(key)

    @property
    def objects(self):
        """
        Get a list of the object buffers and their offsets in this page.

        return: list of objects with fields ["offset", "buffer"]
        """
        ObjectItem = namedtuple("ObjectItem", ["offset", "buffer"])
        ret = []
        for i in xrange(self.toc.count):
            toc = self.toc[i]
            buf = self._buf[toc.offset:toc.offset + toc.size]
            ret.append(ObjectItem(toc.offset, buf))
        return ret


class IndexPageHeader(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.sig = v_uint32()
        self.logical_id = v_uint32()
        self.zero0 = v_uint32()
        self.zero1 = v_uint32()
        self.record_count = v_uint32()


class _IndexPage(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.header = IndexPageHeader()
        self.unk0 = vstruct.VArray()
        self.children = vstruct.VArray()
        self.keys = vstruct.VArray()
        self.string_definition_table_length = v_uint16()
        self.string_definition_table = vstruct.VArray()
        self.string_table_length = v_uint16()
        self.string_table = vstruct.VArray()

    def pcb_header(self):
        self.unk0.vsAddElements(self.header.record_count, v_uint32)
        self.children.vsAddElements(self.header.record_count + 1, v_uint32)
        self.keys.vsAddElements(self.header.record_count, v_uint16)

    def pcb_stringDefTableSize(self):
        self.string_definition_table.vsAddElements(self.string_definition_table_length, v_uint16)

    def pcb_stringTableSize(self):
        self.string_table.vsAddElements(self.string_table_length + 1, v_uint16)

    @property
    def is_valid(self):
        return self.header.sig == INDEX_PAGE_TYPES.PAGE_TYPE_ACTIVE




class Key(LoggingObject):
    def __init__(self, string):
        super(Key, self).__init__()
        self._string = string

    def __repr__(self):
        return "Key({:s})".format(self.human_format)

    def __str__(self):
        return self._string

    @property
    def human_format(self):
        ret = []
        for part in str(self._string).split("/"):
            if "." in part:
                ret.append(part[:7] + "..." + part.partition(".")[2])
            else:
                ret.append(part[:7])
        return "/".join(ret)

    @property
    def is_data_reference(self):
        return "." in self._string

    KEY_INDEX_DATA_PAGE = 1
    KEY_INDEX_DATA_ID = 2
    KEY_INDEX_DATA_SIZE = 3
    def _get_data_part(self, index):
        if not self.is_data_reference:
            raise RuntimeError("key is not a data reference: %s", str(self))
        return self._string.split(".")[index]

    @property
    def data_page(self):
        return int(self._get_data_part(self.KEY_INDEX_DATA_PAGE))

    @property
    def data_id(self):
        return int(self._get_data_part(self.KEY_INDEX_DATA_ID))

    @property
    def data_length(self):
        return int(self._get_data_part(self.KEY_INDEX_DATA_SIZE))


class IndexPage(LoggingObject):
    def __init__(self, buf, logical_page_number, physical_page_number):
        super(IndexPage, self).__init__()
        self._buf = buf
        self.logical_page_number = logical_page_number
        self.physical_page_number = physical_page_number
        self._page = _IndexPage()
        self._page.vsParse(buf)

        # cache
        self._keys = {}

    def _get_string_part(self, string_index):
        string_offset = self._page.string_table[string_index]
        string_page_offset = len(self._page) + string_offset

        string_page_end_offset = self._buf.find("\x00", string_page_offset)
        string = self._buf[string_page_offset:string_page_end_offset].decode("utf-8")
        return string

    def _get_string(self, string_def_index):
        stringPartCount = self._page.string_definition_table[string_def_index]

        parts = []
        for i in range(stringPartCount):
            stringPartIndex = self._page.string_definition_table[string_def_index + 1 + i]

            part = self._get_string_part(stringPartIndex)
            parts.append(part)

        string = "/".join(parts)
        return string

    @property
    def key_count(self):
        return self._page.header.record_count

    def get_key(self, key_index):
        if key_index not in self._keys:
            string_def_index = self._page.keys[key_index]
            self._keys[key_index] = Key(self._get_string(string_def_index))
        return self._keys[key_index]

    def get_child(self, child_index):
        return self._page.children[child_index]

    @property
    def is_valid(self):
        return self._page.is_valid


class LogicalDataStore(LoggingObject):
    """
    provides an interface for accessing data by logical page or object id.
    """
    def __init__(self, cim, file_path, mapping):
        super(LogicalDataStore, self).__init__()
        self._cim = cim
        self._file_path = file_path
        self._mapping = mapping

    def get_physical_page_buffer(self, index):
        # TODO: keep an open handle
        with open(self._file_path, "rb") as f:
            f.seek(DATA_PAGE_SIZE * index)
            return f.read(DATA_PAGE_SIZE)

    def get_logical_page_buffer(self, index):
        physical_page_number = self._mapping.entries[index].page_number
        return self.get_physical_page_buffer(physical_page_number)

    def get_page(self, index):
        """
        return: DataPage instance
        """
        physical_page_number = self._mapping.entries[index].page_number
        return DataPage(self.get_logical_page_buffer(index), index, physical_page_number)

    def get_object_buffer(self, key):
        if not key.is_data_reference:
            raise RuntimeError("Key is not data reference: %s", str(key))

        # this logic of this function is a bit more complex than
        #   we'd want, since we have to handle the case where an
        #   item's data spans multiple pages.
        page = self.get_page(key.data_page)

        target_length = key.data_length
        first_data = page.get_data_by_key(key)

        # this is the common case, return early
        if target_length == len(first_data):
            return first_data

        # here we handle data that spans multiple pages
        data = [first_data]
        found_length = len(first_data)

        i = 1
        while found_length < target_length:
            # TODO: should simply foreach an iterable here
            next_page_buffer = self.get_logical_page_buffer(key.data_page + i)
            if found_length + len(next_page_buffer) > target_length:
                # this is the last page containing data for this item
                chunk_size = target_length - found_length
                data.append(next_page_buffer[:chunk_size])
                found_length += chunk_size
            else:
                # the entire page is used for this item
                data.append(next_page_buffer)
                found_length += len(next_page_buffer)
            i += 1

        return "".join(data)


class LogicalIndexStore(LoggingObject):
    """
    provides an interface for accessing index nodes by logical page id.
    indexing logic should go at a higher level.
    """
    def __init__(self, cim, file_path, mapping):
        super(LogicalIndexStore, self).__init__()
        self._cim = cim
        self._file_path = file_path
        self._mapping = mapping

    def get_physical_page_buffer(self, index):
        # TODO: keep an open file handle
        with open(self._file_path, "rb") as f:
            f.seek(INDEX_PAGE_SIZE * index)
            return f.read(INDEX_PAGE_SIZE)

    def get_logical_page_buffer(self, index):
        physical_page_number = self._mapping.entries[index].page_number()
        return self.get_physical_page_buffer(physical_page_number)

    def get_page(self, index):
        physical_page_number = self._mapping.entries[index].page_number()
        return IndexPage(self.get_logical_page_buffer(index), index, physical_page_number)

    @property
    def _root_page_number_win7(self):
        return int(self._mapping.entries[0x0].used_space)

    @property
    def _root_page_number(self):
        if self._cim.cim_type == CIM_TYPE_WIN7:
            return self._root_page_number_win7

        # TODO: for xp, we should be able to inspect page[0] of the index.
        # this algorithm walks all nodes and tracks which nodes are children
        #   of other nodes. we expect there to be a single node that is never
        #   linked as a child --- therefore, its the root.
        possible_roots = set([])
        impossible_roots = set([])
        for i in xrange(self._mapping.header.mapping_entries):
            try:
                page = self.get_page(i)
            except:
                # TODO: find out why this is. probably: validate page ranges.
                self.w("bad unpack: %s", hex(i))
                continue

            if not page.is_valid:
                continue

            # careful: vstruct returns int-like objects with
            #   no hash-equivalence
            possible_roots.add(int(i))
            for j in xrange(page.key_count + 1):
                child_page = page.get_child(j)
                if not is_index_page_number_valid(child_page):
                    continue
                # careful: vstruct int types
                impossible_roots.add(int(child_page))
        ret = possible_roots - impossible_roots
        # note: hardcode that the root is not logical page 0
        ret.remove(int(0))
        if len(ret) != 1:
            raise RuntimeError("Unable to determine root index node: %s" % (str(ret)))
        return ret.pop()

    @cached_property
    def root_page_number(self):
        return self._root_page_number

    @property
    def root_page(self):
        return self.get_page(self.root_page_number)


class CachedLogicalIndexStore(LoggingObject):
    def __init__(self, index_store):
        super(CachedLogicalIndexStore, self).__init__()
        self._index_store = index_store

        # cache
        self._pages = {}

    def get_physical_page_buffer(self, index):
        return self._index_store.get_physical_page_buffer(index)

    def get_logical_page_buffer(self, index):
        return self._index_store.get_logical_page_buffer(index)

    def get_page(self, index):
        if index not in self._pages:
            self._pages[index] = self._index_store.get_page(index)
        return self._pages[index]

    @property
    def root_page_number(self):
        return self._index_store.root_page_number

    @property
    def root_page(self):
        return self.get_page(self.root_page_number)


class Index(LoggingObject):
    def __init__(self, cim_type, indexStore):
        super(Index, self).__init__()
        self.cim_type = cim_type
        self._index_store = CachedLogicalIndexStore(indexStore)

    LEFT_CHILD_DIRECTION = 0
    RIGHT_CHILD_DIRECTION = 1
    def _lookup_keys_child(self, key, page, i, direction):
        child_index = page.get_child(i + direction)
        if not is_index_page_number_valid(child_index):
            return []
        child_page = self._index_store.get_page(child_index)
        return self._lookup_keys(key, child_page)

    def _lookup_keys_left(self, key, page, i):
        return self._lookup_keys_child(key, page, i, self.LEFT_CHILD_DIRECTION)

    def _lookup_keys_right(self, key, page, i):
        return self._lookup_keys_child(key, page, i, self.RIGHT_CHILD_DIRECTION)

    def _lookup_keys(self, key, page):
        skey = str(key)
        key_count = page.key_count

        self.d("index lookup: %s: page: %s", key.human_format, h(page.logical_page))

        matches = []
        for i in xrange(key_count):
            k = page.get_key(i)
            sk = str(k)

            if i != key_count - 1:
                # not last
                if skey in sk:
                    matches.extend(self._lookup_keys_left(key, page, i))
                    matches.append(k)
                    matches.extend(self._lookup_keys_right(key, page, i))
                    continue
                if skey < sk:
                    matches.extend(self._lookup_keys_left(key, page, i))
                    break
                if skey > sk:
                    continue
            else:
                # last key
                if skey in sk:
                    matches.extend(self._lookup_keys_left(key, page, i))
                    matches.append(k)
                    matches.extend(self._lookup_keys_right(key, page, i))
                    break
                if skey < sk:
                    matches.extend(self._lookup_keys_left(key, page, i))
                    break
                if skey > sk:
                    # we have to be in this node for a reason,
                    #   so it must be the right child
                    matches.extend(self._lookup_keys_right(key, page, i))
                    break
        return matches

    def lookup_keys(self, key):
        """
        get keys that match the given key prefix
        """
        return self._lookup_keys(key, self._index_store.root_page())

    def hash(self, s):
        if self.cim_type == CIM_TYPE_XP:
            h = hashlib.md5()
        elif self.cim_type == CIM_TYPE_WIN7:
            h = hashlib.sha256()
        else:
            raise RuntimeError("Unexpected CIM type: {:s}".format(self.cim_type))
        h.update(s)
        return h.hexdigest().upper()


class CIM(LoggingObject):
    def __init__(self, cim_type, directory):
        super(CIM, self).__init__()
        self.cim_type = cim_type
        self._directory = directory
        self._mapping_class = MAPPING_TYPES[self.cim_type]
        self._mapping_header_class = MAPPING_HEADER_TYPES[self.cim_type]

        # caches
        self._data_store = None
        self._index_store = None

    @property
    def _data_file_path(self):
        return os.path.join(self._directory, "OBJECTS.DATA")

    @property
    def _index_file_path(self):
        return os.path.join(self._directory, "INDEX.BTR")

    @cached_property
    def _current_mapping_file(self):
        self.d("finding current mapping file")
        mapping_file_path = None
        max_version = 0
        for i in xrange(MAX_MAPPING_FILES):
            fn = "MAPPING{:d}.MAP".format(i + 1)
            fp = os.path.join(self._directory, fn)
            if not os.path.exists(fp):
                continue
            h = self._mapping_header_class()

            with open(fp, "rb") as f:
                h.vsParseFd(f)

            self.d("%s: version: %s", fn, hex(h.version))
            if h.version > max_version:
                mapping_file_path = fp
                max_version = h.version
        self.d("current mapping file: %s", mapping_file_path)
        return mapping_file_path

    @cached_property
    def mappings(self):
        fp = self._current_mapping_file
        dm = self._mapping_class()
        im = self._mapping_class()
        with open(fp, "rb") as f:
            dm.vsParseFd(f)
            im.vsParseFd(f)
        return dm, im

    @property
    def data_mapping(self):
        current_data_mapping, _ = self.mappings
        return current_data_mapping

    @property
    def index_mapping(self):
        _, current_index_mapping = self.mappings
        return current_index_mapping

    @cached_property
    def logical_data_store(self):
        return LogicalDataStore(self, self._data_file_path, self.data_mapping)

    @cached_property
    def logical_index_store(self):
        return LogicalIndexStore(self, self._index_file_path, self.index_mapping)


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
