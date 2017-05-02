import cim
import cim.objects
from fixtures import *


def test_object_resolver(repo):
    """
    Args:
        repo (cim.CIM): the deleted-instance repo

    Returns:
        None
    """
    resolver = cim.objects.ObjectResolver(repo)

    assert len(resolver.get_keys(cim.Key('NS_'))) == 47490

    for key in resolver.get_keys(cim.Key('NS_')):
        if not key.is_data_reference:
            continue
        o = resolver.get_object(key)
        assert o is not None
