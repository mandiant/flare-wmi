import cim
import cim.objects
from fixtures import *


def test_parse_object_path_bare_namespace(root):
    """
    Args:
        root (cim.objects.TreeNamespace): the root namespace

    Returns:
        None
    """
    path = root.parse_object_path('cimv2')
    assert path.hostname == 'localhost'
    assert path.namespace == 'root\\cimv2'
    assert not path.klass
    assert not path.instance


def test_parse_object_path_host_relative_namespace(root):
    path = root.parse_object_path('\\\\.\\root\\cimv2')
    assert path.hostname == 'localhost'
    assert path.namespace == 'root\\cimv2'
    assert not path.klass
    assert not path.instance


def test_parse_object_path_absolute_namespace(root):
    path = root.parse_object_path('\\\\HOSTNAME\\root\\cimv2')
    assert path.hostname == 'HOSTNAME'
    assert path.namespace == 'root\\cimv2'
    assert not path.klass
    assert not path.instance


def test_parse_object_path_winmgmts_namespace(root):
    path = root.parse_object_path('winmgmts://./root/cimv2')
    assert path.hostname == 'localhost'
    assert path.namespace == 'root\\cimv2'
    assert not path.klass
    assert not path.instance


def test_parse_object_path_ns_relative_class(root):
    path = root.parse_object_path('CIM_Error')
    assert path.hostname == 'localhost'
    assert path.namespace == 'root'
    assert path.klass == 'CIM_Error'
    assert not path.instance


def test_parse_object_path_host_relative_class(root):
    path = root.parse_object_path('\\\\.\\root\\cimv2:Win32_Service')
    assert path.hostname == 'localhost'
    assert path.namespace == 'root\\cimv2'
    assert path.klass == 'Win32_Service'
    assert not path.instance


def test_parse_object_path_ns_relative_class_instance(repo):
    # note: we are using the root\CIMV2 namespace here
    with cim.objects.Namespace(repo, 'root\cimv2') as ns:
        path = ns.parse_object_path('Win32_Service.Name="Beep"')
        assert path.hostname == 'localhost'
        assert path.namespace == 'root\\cimv2'
        assert path.klass == 'Win32_Service'
        assert path.instance == {'Name': 'Beep'}


def test_parse_object_path_host_relative_class_instance(root):
    path = root.parse_object_path('\\\\.\\root\\cimv2:Win32_Service.Name="Beep"')
    assert path.hostname == 'localhost'
    assert path.namespace == 'root\\cimv2'
    assert path.klass == 'Win32_Service'
    assert path.instance == {'Name': 'Beep'}
