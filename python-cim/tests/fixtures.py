import os

import pytest

import cim
import cim.objects


@pytest.fixture
def repopath():
    """
    Returns:
        str: path to the repos/win7/deleted-instance repository
    """
    cd = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(cd, 'repos', 'win7', 'deleted-instance')


@pytest.fixture
def repo():
    """
    Returns:
        cim.CIM: repos/win7/deleted-instance repository
    """
    return cim.CIM(cim.CIM_TYPE_WIN7, repopath())


@pytest.yield_fixture
def root():
    """
    
    Returns:
        cim.objects.TreeNamespace: the root namespace of the win7/deleted-instance repo.

    """
    r = repo()
    with cim.objects.Namespace(r, cim.objects.ROOT_NAMESPACE_NAME) as ns:
        yield ns


@pytest.fixture
def classes():
    """
    Returns:
        List[cim.objects.TreeClassDefinition]: the list of classes found in the win7/deleted-instance repo.
    """
    klasses = []
    def collect(ns):
        for klass in ns.classes:
            klasses.append(klass)

        for namespace in ns.namespaces:
            collect(namespace)

    r = repo()
    with cim.objects.Namespace(r, cim.objects.ROOT_NAMESPACE_NAME) as ns:
        collect(ns)

    return klasses

