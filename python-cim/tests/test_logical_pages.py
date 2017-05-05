import collections

import cim
from fixtures import *


def test_basic_data_page(repo):
    """
    demonstration extraction of basic information from the page store.
    
    Args:
        repo (cim.CIM): the deleted-instance repo

    Returns:
        None
    """

    datapages = repo.logical_data_store

    # collected empirically
    assert datapages.page_count == 1886

    page = datapages.get_page(0x0)
    # collected empirically
    assert page.toc.count == 22
    assert len(page.objects) == 22

    for i in range(repo.data_mapping.map.header.mapping_entry_count):
        if not repo.data_mapping.is_logical_page_mapped(i):
            continue

        p = datapages.get_page(i)
        assert p.toc.count == len(p.objects)


def test_toc_is_ascending(repo):
    """
    demonstrate that the entries in a logical data page TOC are ascending by offset.
    
    Args:
        repo (cim.CIM): the deleted-instance repo

    Returns:
        None
    """

    datapages = repo.logical_data_store

    for i in range(repo.data_mapping.map.header.mapping_entry_count):
        if not repo.data_mapping.is_logical_page_mapped(i):
            continue

        page = datapages.get_page(i)
        last_offset = 0
        for j in range(page.toc.count):
            entry = page.toc[j]
            assert entry.offset > last_offset
            last_offset = entry.offset


def test_toc_has_large_entries(repo):
    """
    demonstrate that there may be entries listed in a TOC that exceed the page size. 
    
    Args:
        repo (cim.CIM): the deleted-instance repo

    Returns:
        None
    """

    datapages = repo.logical_data_store

    large_entries = []
    for i in range(repo.data_mapping.map.header.mapping_entry_count):
        if not repo.data_mapping.is_logical_page_mapped(i):
            continue

        page = datapages.get_page(i)
        for j in range(page.toc.count):
            entry = page.toc[j]
            if entry.offset + entry.size > cim.DATA_PAGE_SIZE:
                large_entries.append((i, j))

    # collected empirically.
    assert large_entries != []
    # this looks like __SystemSecurity.
    # it has size 0x319D.
    assert large_entries[0] == (0x3, 0x0)


def test_toc_entry_id_conflicts(repo):
    """
    demonstrate that there may be record_ids that are encountered multiple times.
    this is currently pretty dependent upon TOC-detection.
    still, the idea is valid.
    
    Args:
        repo (cim.CIM): the deleted-instance repo

    Returns:
        None
    """

    datapages = repo.logical_data_store

    ids = collections.Counter()
    for i in range(repo.data_mapping.map.header.mapping_entry_count):
        if not repo.data_mapping.is_logical_page_mapped(i):
            continue

        page = datapages.get_page(i)
        for j in range(page.toc.count):
            entry = page.toc[j]
            ids[entry.record_id] += 1

    assert ids.most_common(1)[0][1] > 0
