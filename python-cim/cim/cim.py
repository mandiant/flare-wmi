import os
import logging
from collections import namedtuple

from funcy.objects import cached_property
import vstruct
from vstruct.primitives import *

logger = logging.getLogger(__name__)

MAPPING_SIGNATURES = v_enum()
MAPPING_SIGNATURES.MAPPING_START_SIGNATURE = 0xABCD
MAPPING_SIGNATURES.MAPPING_END_SIGNATURE = 0xDCBA

MAX_MAPPING_FILES = 0x3

MAPPING_PAGE_ID_MASK = 0x3FFFFFFF
MAPPING_PAGE_UNAVAIL = 0xFFFFFFFF
MAPPING_FILE_CLEAN = 0x1
UNMAPPED_PAGE_VALUE = 0x3FFFFFFF

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
        return self._page_number & MAPPING_PAGE_ID_MASK


class UnmappedPage(KeyError):
    pass


class MappingWin7(vstruct.VStruct):
    """
    lookup via:
      m.entries[0x101].page_number
    """

    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.header = MappingHeaderWin7()
        self.entries = vstruct.VArray()
        self.free_dword_count = v_uint32()
        self.free = v_bytes()
        self.footer_signature = v_uint32()

    def pcb_header(self):
        for i in range(self.header.mapping_entry_count):
            self.entries.vsAddElement(EntryWin7())

    def pcb_free_dword_count(self):
        self["free"].vsSetLength(self.free_dword_count * 0x4)


class EntryXP(vstruct.primitives.v_uint32):
    def __init__(self):
        vstruct.primitives.v_uint32.__init__(self)

    @property
    def page_number(self):
        return self & MAPPING_PAGE_ID_MASK


# TODO: maybe merge these together
class MappingXP(vstruct.VStruct):
    """
    lookup via:
      m.entries[0x101].page_number
    """

    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.header = MappingHeaderXP()
        self.entries = vstruct.VArray()
        self.free_dword_count = v_uint32()
        self.free = v_bytes()
        self.footer_signature = v_uint32()

    def pcb_header(self):
        for i in range(self.header.mapping_entry_count):
            self.entries.vsAddElement(EntryXP())

    def pcb_free_dword_count(self):
        self["free"].vsSetLength(self.free_dword_count * 0x4)

    def _build_reverse_mapping(self):
        self._reverse_mapping = {}
        for i in range(self.header.mapping_entry_count):
            self._reverse_mapping[self.entries[i].page_number] = i


MAPPING_TYPES = {
    CIM_TYPE_XP: MappingXP,
    CIM_TYPE_WIN7: MappingWin7,
}


class Mapping(object):
    """
    helper routines around fetching page mappings.
    """

    def __init__(self, map):
        """
        Args:
            map (MappingWin7 | MappingXp): the raw map structure.
        """
        self.map = map
        # cache of map from physical page to logical page
        self._reverse_mapping = {}

    def _build_reverse_mapping(self):
        self._reverse_mapping = {}
        for i in range(self.map.header.mapping_entry_count):
            pnum = self.map.entries[i].page_number
            # unknown precisely what this means
            if pnum == UNMAPPED_PAGE_VALUE:
                continue

            if pnum in self._reverse_mapping:
                logger.warning('logical page %d already mapped!', i)

            self._reverse_mapping[pnum] = i

    def is_logical_page_mapped(self, logical_page_number):
        """
        is the given logical page index mapped?
        
        Args:
            logical_page_number (int): the logical page number
            
        Returns:
            bool: if the logical page is mapped.
             
        Raises:
            IndexError: if the page number is too big
        """
        if logical_page_number > int(self.map.header.mapping_entry_count):
            raise IndexError(logical_page_number)

        try:
            entry = self.map.entries[logical_page_number]
        except Exception:
            raise UnmappedPage(logical_page_number)

        return entry.page_number != UNMAPPED_PAGE_VALUE

    def get_physical_page_number(self, logical_page_number):
        """
        given a logical page number, get the physical page number it maps to.
        
        Args:
            logical_page_number (int): the logical page number

        Returns:
            int: the logical page number
            
        Raises:
            UnmappedPage: if the page is unallocated.
            IndexError: if the page number is too big
        """
        if logical_page_number > int(self.map.header.mapping_entry_count):
            raise IndexError(logical_page_number)

        try:
            entry = self.map.entries[logical_page_number]
        except Exception:
            raise UnmappedPage(logical_page_number)
        pnum = entry.page_number
        if pnum == UNMAPPED_PAGE_VALUE:
            raise UnmappedPage(logical_page_number)
        return pnum

    def get_logical_page_number(self, physical_page_number):
        """
        given a physical page number, get the logical page number it maps to.
        
        Args:
            physical_page_number: the physical page number

        Returns:
            int: the logical page number

        Raises:
            UnmappedPage: if the page is unmapped.
        """
        if not self._reverse_mapping:
            self._build_reverse_mapping()

        if physical_page_number in self._reverse_mapping:
            return self._reverse_mapping[physical_page_number]

        raise UnmappedPage(physical_page_number)

    def is_physical_page_mapped(self, physical_page_number):
        """
        is the given physical page index mapped?
        
        Args:
            physical_page_number (int): the physical page number

        Returns:
            bool: if the physical page is mapped.
        """
        if not self._reverse_mapping:
            self._build_reverse_mapping()

        return physical_page_number in self._reverse_mapping


class TOCEntry(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.record_id = v_uint32()
        # offset is relative to start of the page
        self.offset = v_uint32()
        self.size = v_uint32()
        # zero on win7
        self.CRC = v_uint32()

    def is_empty(self):
        return self.record_id == 0 and \
               self.offset == 0 and \
               self.size == 0 and \
               self.CRC == 0


class ParseError(Exception):
    pass


class TOC(vstruct.VArray):
    def __init__(self):
        vstruct.VArray.__init__(self)
        # if this is zero, then the TOC has not be parsed correctly.
        self.count = 0

    @staticmethod
    def _is_valid_entry(t):
        # we have to guess where the end of the TOC is
        if int(t.record_id) == 0x0:
            return False

        if int(t.offset) >= DATA_PAGE_SIZE:
            return False

        if int(t.offset) == 0:
            return False

        if int(t.size) == 0:
            return False

        return True

    def _parse_entries(self, bytez, offset):
        entries = []

        endoffset = bytez.find(b"\x00" * 0x10, offset)
        if endoffset == -1:
            raise ParseError('no empty entry')

        while offset < endoffset + 0x10:
            t = TOCEntry()
            offset = t.vsParse(bytez, offset=offset)

            if t.is_empty():
                # there should be a final empty entry to mark the end of the toc
                entries.append(t)
                break

            elif not self._is_valid_entry(t):
                break

            else:
                entries.append(t)
                continue

        if entries and entries[-1].is_empty():
            # don't include the empty entry in the TOC
            return entries[:-1]
        else:
            raise ParseError('failed to parse TOC correctly')

    def vsParse(self, bytez, offset=0, fast=False):
        try:
            # we either want to parse all the entries, or none of them.
            # an empty toc indicates that it hasn't been parsed correctly.
            entries = self._parse_entries(bytez, offset)
        except ParseError:
            return offset

        for entry in entries:
            self.vsAddElement(entry)
        self.count = len(entries)
        return 0x10 * (len(entries) + 1)


class IndexKeyNotFoundError(Exception):
    pass


class DataPage(object):
    def __init__(self, buf, logical_page_number, physical_page_number):
        """
        Args:
            buf (bytes): the raw bytes of the page
            logical_page_number (int):  the logical page number
            physical_page_number (int):  the physical age nubmer
        """
        super(DataPage, self).__init__()
        self.buf = buf
        self.logical_page_number = logical_page_number
        self.physical_page_number = physical_page_number
        self.toc = TOC()
        self.toc.vsParse(buf)

    def _get_object_buffer_by_index(self, toc_index):
        toc_entry = self.toc[toc_index]
        return self.buf[toc_entry.offset:toc_entry.offset + toc_entry.size]

    def get_data_by_key(self, key):
        """
        fetch the raw bytes for the object identified by the given key.
        
        note: prefer to use __getitem__
        
        Args:
            key (Key): the key of the object to fetch

        Returns:
            bytes: the raw bytes for the requested object.
        """
        target_id = key.data_id
        target_size = key.data_length
        for i in range(self.toc.count):
            toc = self.toc[i]
            if toc.record_id == target_id:
                if toc.size < target_size:
                    raise RuntimeError("Data size doesn't match TOC size")
                if toc.size > DATA_PAGE_SIZE - toc.offset:
                    logger.debug("Large data item: key: %s, size: %s",
                                 str(key), hex(target_size))
                return self.buf[toc.offset:toc.offset + toc.size]
        raise IndexKeyNotFoundError(key)

    def __getitem__(self, key):
        """
        fetch the raw bytes for the object identified by the given key.
        
        Args:
            key (cim.Key): the key of the object to fetch.

        Returns:
            bytes: the raw bytes of the requested object.

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
        for i in range(self.toc.count):
            toc = self.toc[i]
            buf = self.buf[toc.offset:toc.offset + toc.size]
            ret.append(ObjectItem(toc.offset, buf))
        return ret


class Key(object):
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

    def get_part(self, part_prefix):
        for part in str(self._string).split("/"):
            if part.startswith(part_prefix):
                return part.partition(".")[0]
        return IndexError("Part prefix not found: " + part_prefix)

    def get_part_hash(self, part_prefix):
        return self.get_part(part_prefix).partition("_")[2]


class IndexPageHeader(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.sig = v_uint32(enum=INDEX_PAGE_TYPES)
        self.logical_id = v_uint32()
        self.zero0 = v_uint32()
        self.root_page = v_uint32()
        self.record_count = v_uint32()

    @property
    def is_active(self):
        return self.sig == INDEX_PAGE_TYPES.PAGE_TYPE_ACTIVE

    @property
    def is_admin(self):
        return self.sig == INDEX_PAGE_TYPES.PAGE_TYPE_ADMIN

    @property
    def is_deleted(self):
        return self.sig == INDEX_PAGE_TYPES.PAGE_TYPE_DELETED


class IndexPage(vstruct.VStruct):
    def __init__(self, logical_page_number, physical_page_number):
        vstruct.VStruct.__init__(self)
        self.logical_page_number = logical_page_number
        self.physical_page_number = physical_page_number

        self.header = IndexPageHeader()
        self.unk0 = vstruct.VArray()
        self.children = vstruct.VArray()
        self.keys = vstruct.VArray()
        self.string_definition_table_length = v_uint16()
        self.string_definition_table = vstruct.VArray()
        self.string_table_length = v_uint16()
        self.string_table = vstruct.VArray()
        self.data = v_bytes(size=0)

        # cache
        self._keys = {}

    def pcb_header(self):
        self.unk0.vsAddElements(self.header.record_count, v_uint32)
        self.children.vsAddElements(self.header.record_count + 1, v_uint32)
        self.keys.vsAddElements(self.header.record_count, v_uint16)

    def pcb_string_definition_table_length(self):
        self.string_definition_table.vsAddElements(self.string_definition_table_length, v_uint16)

    def pcb_string_table_length(self):
        self.string_table.vsAddElements(self.string_table_length + 1, v_uint16)

    def pcb_string_table(self):
        self["data"].vsSetLength(INDEX_PAGE_SIZE - len(self))

    @property
    def is_valid(self):
        return self.header.sig == INDEX_PAGE_TYPES.PAGE_TYPE_ACTIVE

    def _get_string_part(self, string_index):
        string_offset = self.string_table[string_index]
        return self.data[string_offset:bytes(self.data).find(b"\x00", string_offset)].decode("utf-8")

    def _get_string(self, string_def_index):
        string_part_count = self.string_definition_table[string_def_index]

        parts = []
        for i in range(string_part_count):
            string_part_index = self.string_definition_table[string_def_index + 1 + i]

            part = self._get_string_part(string_part_index)
            parts.append(part)

        string = "/".join(parts)
        return string

    @property
    def key_count(self):
        return self.header.record_count

    def get_key(self, key_index):
        if key_index not in self._keys:
            string_def_index = self.keys[key_index]
            s = self._get_string(string_def_index)
            self._keys[key_index] = Key(s)
        return self._keys[key_index]

    def get_child(self, child_index):
        """ get the logical page number of the given child index """
        return int(self.children[child_index])


class MissingDataFileError(Exception):
    pass


class LogicalDataStore(object):
    """
    provides an interface for accessing data by logical page or object id.
    
    Args:
        cim (CIM): the repo
        mapping (Mapping): the data mapping.
    """

    def __init__(self, cim, file_path, mapping):
        super(LogicalDataStore, self).__init__()
        self._cim = cim
        self._file_path = file_path
        self._mapping = mapping
        self._file_size = os.path.getsize(file_path)
        self.page_count = self._file_size // INDEX_PAGE_SIZE

    def get_physical_page_buffer(self, physical_page_number):
        """
        fetch the bytes of the page at the give physical index.
        
        Args:
            physical_page_number: the physical page number to fetch

        Returns:
            bytes: the raw page contents.
        """
        if not os.path.exists(self._file_path):
            raise MissingDataFileError()

        if physical_page_number >= self.page_count:
            raise IndexError(physical_page_number)

        with open(self._file_path, "rb") as f:
            f.seek(DATA_PAGE_SIZE * physical_page_number)
            return f.read(DATA_PAGE_SIZE)

    def get_logical_page_buffer(self, logical_page_number):
        """
        fetch the bytes of the page at the give logical index.
        
        Args:
            logical_page_number: the logical page number to fetch

        Returns:
            bytes: the raw page contents.
        """
        if not self._mapping.is_logical_page_mapped(logical_page_number):
            raise UnmappedPage(logical_page_number)
        pnum = self._mapping.get_physical_page_number(logical_page_number)
        return self.get_physical_page_buffer(pnum)

    def get_page(self, logical_page_number):
        """
        fetch the parsed page at the give logical index.
        
        Args:
            logical_page_number: the logical page number to fetch

        Returns:
            DataPage: the parsed page.
        """
        pbuf = self.get_logical_page_buffer(logical_page_number)
        pnum = self._mapping.get_physical_page_number(logical_page_number)
        return DataPage(pbuf, logical_page_number, pnum)

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

        return b"".join(data)


class InvalidMappingEntryIndex(Exception):
    pass


class InvalidPhysicalPageNumber(Exception):
    pass


class InvalidLogicalPageNumber(Exception):
    pass


class MissingIndexFileError(Exception):
    pass


class LogicalIndexStore(object):
    """
    provides an interface for accessing index nodes by logical page id.
    indexing logic should go at a higher level.
    """

    def __init__(self, cim, file_path, mapping):
        """
        
        Args:
            cim (CIM): the CIM repository
            file_path (str): the file containing the index
            mapping (Mapping): the page mapping
        """
        super(LogicalIndexStore, self).__init__()
        self._cim = cim
        self._file_path = file_path
        self._mapping = mapping
        self._file_size = os.path.getsize(file_path)
        self.page_count = self._file_size // INDEX_PAGE_SIZE

    def get_physical_page_buffer(self, index):
        """
        fetch the raw bytes of the page at the given physical page number
        
        Args:
            index (int): the physical page number.

        Returns:
            bytes: the raw data at the given page.
        """
        if not os.path.exists(self._file_path):
            raise MissingIndexFileError()

        if index >= self.page_count:
            raise IndexError(index)

        with open(self._file_path, "rb") as f:
            f.seek(INDEX_PAGE_SIZE * index)
            return f.read(INDEX_PAGE_SIZE)

    def get_logical_page_buffer(self, logical_page_number):
        """
        fetch the raw bytes of the page at the given logical page number.
        
        Args:
            logical_page_number (int): the logical page number.

        Returns:
            bytes: the raw data at the given page.
        """
        pnum = self._mapping.get_physical_page_number(logical_page_number)
        return self.get_physical_page_buffer(pnum)

    def get_page(self, logical_page_number):
        """
        fetch a parsed index page given a logical page number.
        
        Args:
            logical_page_number: the logical page number

        Returns:
            IndexPage: the parsed index page.
        """
        if logical_page_number > self._mapping.map.header.mapping_entry_count:
            raise InvalidMappingEntryIndex()

        pnum = self._mapping.get_physical_page_number(logical_page_number)
        pagebuf = self.get_logical_page_buffer(logical_page_number)
        p = IndexPage(logical_page_number, pnum)
        p.vsParse(pagebuf)
        return p

    @cached_property
    def root_page_number(self):
        """
        fetch the logical page number of the index root.
        
        Returns:
            int: the logical page number.
        """
        if self._cim.cim_type == CIM_TYPE_WIN7:
            return int(self._mapping.map.entries[0x0].used_space)
        elif self._cim.cim_type == CIM_TYPE_XP:
            return self.get_page(0).header.root_page
        else:
            raise RuntimeError("Unexpected CIM type: " + str(self._cim.cim_type))

    @property
    def root_page(self):
        """
        fetch the parsed index page of the index root.
        
        Returns:
            IndexPage: the parsed index page.
        """
        return self.get_page(self.root_page_number)


class CachedLogicalIndexStore(object):
    """
    acts like a LogicalIndexStore, except it caches pages in memory for faster access.
    """

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


class Index(object):
    def __init__(self, cim_type, index_store):
        super(Index, self).__init__()
        self.cim_type = cim_type
        self._index_store = CachedLogicalIndexStore(index_store)

    LEFT_CHILD_DIRECTION = 0
    RIGHT_CHILD_DIRECTION = 1

    def _lookup_keys_child(self, key, page, i, direction):
        child_index = page.get_child(i + direction)
        if child_index == INDEX_PAGE_INVALID or child_index == INDEX_PAGE_INVALID2:
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

        logger.debug("index lookup: %s: page: %s", key.human_format, hex(page.logical_page_number))

        matches = []
        for i in range(key_count):
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
        query the index keys that start with the given prefix.
        
        Args:
            key (Key): the key prefix.

        Returns:
            List[Key]: the matching keys.
        """
        return self._lookup_keys(key, self._index_store.root_page)


class MissingMappingFileError(Exception):
    pass


class CIM(object):
    def __init__(self, cim_type, directory):
        super(CIM, self).__init__()
        self.cim_type = cim_type
        self._directory = directory
        self._mapping_class = MAPPING_TYPES[self.cim_type]
        self._mapping_header_class = MAPPING_HEADER_TYPES[self.cim_type]

        # caches
        self._data_store = None
        self._index_store = None

    @staticmethod
    def guess_cim_type(path):
        mappath = os.path.join(path, "MAPPING1.MAP")
        with open(mappath, 'rb') as f:
            header = f.read(0x18)

        sig, version, first_id, second_id, phys_count, map_count = struct.unpack("<IIIIII", header)
        if sig != 0xABCD:
            raise ParseError('Unexpected mapping file signature')

        # we're going to try to prove this is not a Win7 repo.

        if map_count > phys_count:
            return CIM_TYPE_XP

        if map_count < phys_count // 10:
            # map count *should* be in same order of magnitude as physical page count
            return CIM_TYPE_XP

        if first_id - 1 != second_id:
            return CIM_TYPE_XP

        return CIM_TYPE_WIN7

    @classmethod
    def from_path(cls, path):
        cim_type = cls.guess_cim_type(path)
        logger.debug('auto-detected repository type: %s', cim_type)
        return cls(cim_type, path)

    @property
    def _data_file_path(self):
        return os.path.join(self._directory, "OBJECTS.DATA")

    @property
    def _index_file_path(self):
        return os.path.join(self._directory, "INDEX.BTR")

    @cached_property
    def _current_mapping_file(self):
        mapping_file_path = None
        max_version = 0
        for i in range(MAX_MAPPING_FILES):
            fn = "MAPPING{:d}.MAP".format(i + 1)
            fp = os.path.join(self._directory, fn)
            if not os.path.exists(fp):
                continue
            h = self._mapping_header_class()

            with open(fp, "rb") as f:
                h.vsParseFd(f)

            logging.debug("%s: version: %s", fn, hex(h.version))
            if h.version > max_version:
                mapping_file_path = fp
                max_version = h.version

        if mapping_file_path is None:
            raise MissingMappingFileError()

        logging.debug("current mapping file: %s", mapping_file_path)
        return mapping_file_path

    @cached_property
    def mappings(self):
        fp = self._current_mapping_file
        dm = self._mapping_class()
        im = self._mapping_class()

        if not os.path.exists(fp):
            raise MissingMappingFileError()

        with open(fp, "rb") as f:
            dm.vsParseFd(f)
            im.vsParseFd(f)
        return Mapping(dm), Mapping(im)

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
