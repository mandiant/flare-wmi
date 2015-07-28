import logging
import traceback

from cim import CIM
from cim import Index
from cim.objects import ObjectResolver
from cim.formatters import dump_layout


def main(type_, path, namespaceName, className):
    if type_ not in ("xp", "win7"):
        raise RuntimeError("Invalid mapping type: {:s}".format(type_))

    c = CIM(type_, path)
    i = Index(c.cim_type, c.logical_index_store)
    o = ObjectResolver(c, i)

    while className != "":
        print("%s" % "=" * 80)
        print("namespace: %s" % namespaceName)
        try:
            cd = o.get_cd(namespaceName, className)
        except IndexError:
            print("ERROR: failed to find requested class definition")
            return
        print(cd.tree())
        cl = o.get_cl(namespaceName, className)
        print(cl.derivation)
        try:
            print(dump_layout(cd, cl))
        except:
            print("ERROR: failed to dump class definition!")
            print(traceback.format_exc())
        className = cd.super_class_name


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    main(*sys.argv[1:])
