import logging
import traceback

import hexdump

from cim import CIM
from cim import Index
from objects import ObjectResolver
from formatters import dump_instance



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
        try:
            dump_instance(o.get_ci(namespaceName, className, instance.instance_key))
        except:
            print("ERROR: failed to dump class instance!")
            print traceback.format_exc()
        return


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    main(*sys.argv[1:])
