import logging
import traceback

import hexdump

from cim import CIM
from cim import Index
from cim.objects import InstanceKey
from cim.objects import ObjectResolver
from cim.formatters import dump_instance

# this is surprising... what happens to unicode data?
ENCODING = "ascii"


def compute_instance_hash(index, instance):
    keys = instance.class_layout.class_definition.keys
    key = instance.key
    print(key)
    parts = []
    for k in keys:
        print(k, key[k])
        parts.append(key[k].encode(ENCODING) + "\x00".encode(ENCODING))

    import itertools
    for u in itertools.permutations(parts):
        hexdump.hexdump(b"\xff\xff".join(u))
        print("  -->" + index.hash(b"\xff\xff".join(u)))
        print("  -->" + index.hash(b"\xff".join(u)))
        print("  -->" + index.hash(b"".join(u)))
    print(str(keys))
    return ""


def main(type_, path, namespaceName, className, key_specifier=None):
    if type_ not in ("xp", "win7"):
        raise RuntimeError("Invalid mapping type: {:s}".format(type_))

    c = CIM(type_, path)
    index = Index(c.cim_type, c.logical_index_store)
    o = ObjectResolver(c, index)

    cd = o.get_cd(namespaceName, className)
    cl = o.get_cl(namespaceName, className)

    instances = []
    if key_specifier:
        key_values = key_specifier.split(",")
        key = InstanceKey()
        for key_value in key_values:
            if "=" not in key_value:
                raise RuntimeError("Invalid key specifier: " + str(key_value))
            k, _, v = key_value.partition("=")
            key[k] = v
        print(str(key))
        ci = o.get_ci(namespaceName, className, key)
        instances.append(ci)

    else:
        for instance in o.get_cd_children_ci(namespaceName, className):
            ci = o.get_ci(namespaceName, className, instance.instance_key)
            instances.append(ci)

    for instance in instances:
        print("%s" % "=" * 80)
        # print(compute_instance_hash(index, instance))
        try:
            print(dump_instance(instance, encoding='ascii', encoding_errors='ignore'))
        except:
            print("ERROR: failed to dump class instance!")
            print(traceback.format_exc())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys

    main(*sys.argv[1:])
