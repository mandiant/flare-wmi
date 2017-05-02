import logging

from cim import CIM
from cim.objects import Namespace
from cim.objects import ObjectPath


def test(ns, path, expected):
    print("TEST: {:s}".format(path))
    p = ns.parse_object_path(path)
    if p != expected:
        print("got:      {:s}".format(str(p)))
        print("expected: {:s}".format(str(expected)))
        raise RuntimeError("test failed!")


def main(type_, path):
    if type_ not in ("xp", "win7"):
        raise RuntimeError("Invalid mapping type: {:s}".format(type_))

    c = CIM(type_, path)
    with Namespace(c, "root") as ns:
        test(ns, "cimv2", ObjectPath("localhost", "root\\cimv2", "", {}))
        test(ns, "//./root/cimv2", ObjectPath("localhost", "root\\cimv2", "", {}))
        test(ns, "\\\\.\\root\\cimv2", ObjectPath("localhost", "root\\cimv2", "", {}))
        test(ns, "//HOSTNAME/root/cimv2", ObjectPath("HOSTNAME", "root\\cimv2", "", {}))
        test(ns, "winmgmts://./root/cimv2", ObjectPath("localhost", "root\\cimv2", "", {}))

    with Namespace(c, "root\\cimv2") as ns:
        test(ns, "Win32_Service", ObjectPath("localhost", "root\\cimv2", "Win32_Service", {}))
        test(ns, "//./root/cimv2:Win32_Service", ObjectPath("localhost", "root\\cimv2", "Win32_Service", {}))
        test(ns, "Win32_Service.Name='Beep'", ObjectPath("localhost", "root\\cimv2", "Win32_Service", {"Name": "Beep"}))
        test(ns, "//./root/cimv2:Win32_Service.Name='Beep'",
             ObjectPath("localhost", "root\\cimv2", "Win32_Service", {"Name": "Beep"}))
    print("Tests: OK")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys

    main(*sys.argv[1:])
