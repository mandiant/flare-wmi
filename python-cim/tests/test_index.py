import cim
from fixtures import *


def test_root(repo):
    '''
    Args:
        repo (cim.CIM): the deleted-instance repo

    Returns:
        None
    '''

    # collected empirically
    assert repo.logical_index_store.root_page_number == 60

    index = cim.Index(repo.cim_type, repo.logical_index_store)

    # collected empirically
    #
    # this should be the number of all objects in the repository
    assert len(index.lookup_keys(cim.Key('NS_'))) == 47490

