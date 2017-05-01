from fixtures import *

import cim


############ INDEX MAPPING ###############################################


def test_basic_data_page(repo):
    '''
    Args:
        repo (cim.CIM): the deleted-instance repo

    Returns:
        None
    '''

    datapages = repo.logical_data_store

    # collected empirically
    assert datapages.page_count == 1886

    page = datapages.get_page(0x0)
    # collected empirically
    assert page.toc.count == 22
    assert len(page.objects) == 22

    for i in range(repo.data_mapping.header.mapping_entry_count):
        if not repo.data_mapping.is_logical_page_mapped(i):
            continue

        p = datapages.get_page(i)
        assert p.toc.count == len(p.objects)


def test_toc_is_ascending(repo):
    '''
    demonstrate that the entries in a logical data page TOC are ascending by offset.
    
    Args:
        repo (cim.CIM): the deleted-instance repo

    Returns:
        None
    '''

    datapages = repo.logical_data_store

    for i in range(repo.data_mapping.header.mapping_entry_count):
        if not repo.data_mapping.is_logical_page_mapped(i):
            continue

        page = datapages.get_page(i)
        last_offset = 0
        for j in range(page.toc.count):
            entry = page.toc[j]
            assert entry.offset > last_offset
            last_offset = entry.offset
