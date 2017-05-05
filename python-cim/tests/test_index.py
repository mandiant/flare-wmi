import pytest

import cim
from fixtures import *


def test_index_root(repo):
    """
    make a prefix query against the index assert the number of expected results. 
    
    Args:
        repo (cim.CIM): the deleted-instance repo

    Returns:
        None
    """

    # collected empirically
    assert repo.logical_index_store.root_page_number == 60

    index = cim.Index(repo.cim_type, repo.logical_index_store)

    # collected empirically
    #
    # this should be the number of all objects in the repository
    assert len(index.lookup_keys(cim.Key('NS_'))) == 47490


def test_index_references_are_valid(repo):
    """
    demonstrate that all keys in the index reference valid TOC entries in data pages.
    this means:
      - all pages exist
      - all IDs exist
      - the reported size equals the allocated size
    
    Args:
        repo (cim.CIM): the deleted-instance repo

    Returns:
        None
    """
    index = cim.Index(repo.cim_type, repo.logical_index_store)

    for key in index.lookup_keys(cim.Key('NS_')):
        if not key.is_data_reference:
            continue

        is_found = False
        entry_size = 0
        page = repo.logical_data_store.get_page(key.data_page)
        for i in range(page.toc.count):
            entry = page.toc[i]
            if entry.record_id == key.data_id:
                is_found = True
                entry_size = entry.size
                break

        assert is_found is True
        assert key.data_length == entry_size


def test_find_unreferenced_objects(repo):
    """
    find allocated TOC entries that are not referenced by the index.
    these are items that are inaccessible.
    
    Args:
        repo (cim.CIM): the deleted-instance repo

    Returns:
        None
    """
    index = cim.Index(repo.cim_type, repo.logical_index_store)

    indexed_objects = set([])
    for key in index.lookup_keys(cim.Key('NS_')):
        if not key.is_data_reference:
            continue
        indexed_objects.add((key.data_id, key.data_length))

    unreferenced_objects = []
    for i in range(repo.data_mapping.map.header.mapping_entry_count):
        if not repo.data_mapping.is_logical_page_mapped(i):
            continue

        page = repo.logical_data_store.get_page(i)
        for j in range(page.toc.count):
            entry = page.toc[j]
            if (entry.record_id, entry.size) not in indexed_objects:
                unreferenced_objects.append((i, entry.record_id, entry.size))

    # collected empirically.
    # they all appear to be objects related to RSOP
    assert unreferenced_objects == [(0x674, 0x19ebb, 0x27c),
                                    (0x676, 0x1cc77, 0x274),
                                    (0x677, 0x1c273, 0x240),
                                    (0x677, 0x194dc, 0x240)]
