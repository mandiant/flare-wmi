from fixtures import *

import cim


def test_index_mapping(repo):
    '''
    Args:
        repo (cim.CIM): the deleted-instance repo

    Returns:
        None
    '''
    mapping = repo.index_mapping

    # collected empirically.
    assert len(mapping.entries) == 7824
    assert mapping.free_dword_count == 241
    assert mapping.header.physical_page_count == 547
    assert mapping.header.mapping_entry_count == 326

    assert mapping.get_physical_page_number(logical_page_number=0) == 13
    assert mapping.get_logical_page_number(physical_page_number=13) == 0


def test_index_mapping_inconsistencies(repo):
    '''
    find logical pages where the physical page does not map back to it.
    this is probably where there are two logical pages that point to the
      same physical page.
    maybe this is unallocated/deleted regions?
    
    Args:
        repo (cim.CIM): the deleted-instance repo

    Returns:
        None
    '''
    mapping = repo.index_mapping

    # logical pages where the physical page does not map back to it.
    # that is, there must be two logical pages that point here.
    inconsistencies = []
    for i in range(mapping.header.mapping_entry_count):
        try:
            pnum = mapping.get_physical_page_number(logical_page_number=i)
            if i != mapping.get_logical_page_number(physical_page_number=pnum):
                inconsistencies.append(i)
        except cim.UnmappedPage:
            continue
    assert inconsistencies == []


def test_unmapped_pages(repo):
    mapping = repo.index_mapping

    unmapped_pages = []
    for i in range(mapping.header.mapping_entry_count):
        try:
            _ = mapping.get_physical_page_number(i)
        except cim.UnmappedPage:
            unmapped_pages.append(i)
            continue

    assert unmapped_pages == [91, 160, 201, 202, 203, 204, 205, 206, 207, 208,
                              209, 210, 211, 212, 213, 214, 215, 227, 228, 230]

