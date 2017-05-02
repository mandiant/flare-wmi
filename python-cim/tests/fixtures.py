import os

import pytest

import cim


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
