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
    assert page.toc.count == 23
    assert len(page.objects) == 23

    for i in range(repo.data_mapping.header.mapping_entry_count):
        if not repo.data_mapping.is_logical_page_mapped(i):
            continue

        p = datapages.get_page(i)
        assert p.toc.count == len(p.objects)


