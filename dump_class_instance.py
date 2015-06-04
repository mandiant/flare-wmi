import logging
import traceback

import hexdump

from cim import CIM
from cim import Index
from objects import ObjectResolver
from objects import CIM_TYPE_SIZES
from common import h


def dump_instance(cd, cl, i):
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
    hexdump.hexdump(i._buf)
    print(i._def.tree())
    print("values:")
    props = cd.properties
    for propname, prop in props.iteritems():
        print("%s=%s" % (
            prop, str(i.get_property_value(prop.name))))


def main(type_, path, namespaceName, className):
    if type_ not in ("xp", "win7"):
        raise RuntimeError("Invalid mapping type: {:s}".format(type_))

    c = CIM(type_, path)
    index = Index(c.cim_type, c.logical_index_store)
    o = ObjectResolver(c, index)

    print("%s" % "=" * 80)
    print("namespace: %s" % namespaceName)
    cd = o.get_cd(namespaceName, className)
    cl = o.get_cl(namespaceName, className)
    # this is surprising... what happens to unicode data?
    ENCODING = "ascii"
    for instance in o.get_cd_children_ci(namespaceName, className):
        print("instance")
        print(instance.instance_key)
        keys = instance.instance_key
        parts = []
        for k in cd.keys:
            print(k, keys[k])
            parts.append(keys[k].encode(ENCODING) + "\x00".encode(ENCODING))

        import itertools
        for u in itertools.permutations(parts):
            hexdump.hexdump("\xff\xff".join(u))
            print("  -->" + index.hash("\xff\xff".join(u)))
            print("  -->" + index.hash("\xff".join(u)))
            print("  -->" + index.hash("".join(u)))
        print(str(keys))
        ci = o.get_ci(namespaceName, className, instance.instance_key)
        print(ci)
        print("%s" % "=" * 80)
        return
    try:
        dump_instance(cd, cl, instance)
    except:
        print("ERROR: failed to dump class definition!")
        print traceback.format_exc()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    main(*sys.argv[1:])
