import cim.recovery
from fixtures import *


def test_page_slack_space(repo):
    """
    demonstrate that a data page with a TOC can have slack space.
    
    Args:
        repo (cim.CIM): the deleted-instance repo

    Returns:
        None

    """
    datapages = repo.logical_data_store
    page = datapages.get_page(0x0)

    regions = list(cim.recovery.extract_data_page_slack(page))

    # collected empirically
    assert len(regions) == 1
    region = regions[0]

    # collected empirically
    #
    # in this case, there's some NULL bytes at the end of the page.
    assert region.logical_page_number == 0x0
    assert region.page_offset == 0x1F6F
    assert len(region.buffer) == 0x91
    assert region.buffer == 0x91 * b'\x00'
