import logging
import traceback

from cim import CIM
from cim import Index
from objects import ObjectResolver
from objects import CIM_TYPE_SIZES
from common import h


def dump_class_def(cd, cl):
    print(cd.tree())



    print("classname: %s" % cd.class_name)
    print("super: %s" % cd.super_class_name)
    print("ts: %s" % cd.timestamp.isoformat("T"))
    print("qualifiers:")
    for k, v in cd.qualifiers.iteritems():
        print("  %s: %s" % (k, str(v)))
    print("properties:")
    for propname, prop in cd.properties.iteritems():
        print("  name: %s" % prop.name)
        print("    type: %s" % prop.type)
        print("    order: %s" % prop.entry_number)
        print("    qualifiers:")
        for k, v in prop.qualifiers.iteritems():
            print("      %s: %s" % (k, str(v)))
    print("layout:")
    off = 0
    for prop in cl.properties:
        print("  (%s)   %s %s" % (h(off), prop.type, prop.name))
        if prop.type.is_array:
            off += 0x4
        else:
            off += CIM_TYPE_SIZES[prop.type.type]


def main(type_, path, namespaceName, className):
    if type_ not in ("xp", "win7"):
        raise RuntimeError("Invalid mapping type: {:s}".format(type_))

    c = CIM(type_, path)
    i = Index(c.cim_type, c.logical_index_store)
    o = ObjectResolver(c, i)

    while className != "":
        print("%s" % "=" * 80)
        print("namespace: %s" % namespaceName)
        cd = o.get_cd(namespaceName, className)
        cl = o.get_cl(namespaceName, className)
        try:
            dump_class_def(cd, cl)
        except:
            print("ERROR: failed to dump class definition!")
            print traceback.format_exc()
        className = cd.super_class_name


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    main(*sys.argv[1:])
