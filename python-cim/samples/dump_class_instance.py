import logging
import traceback
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('type', help='Type of Windows OS from the target system', choices=['xp','win7'])
    parser.add_argument('target', help='Folder path to target system CIM repo')
    parser.add_argument('cimpath', help='Path inside CIM database including root (ex: root\\ccm\\SoftwareMeteringAgent)')
    parser.add_argument('cimclass', help='Name of CIM class to dump')
    parser.add_argument('--filterkeys', help='Path inside CIM database')
    parser.add_argument('--csv', help='Path to CSV output file')
    parser.add_argument('--addcol', help='Name and value pair to add a column to CSV result (ex: hostname=abc123)')
    args = parser.parse_args()

import hexdump

from cim import CIM
from cim import Index
from cim.objects import InstanceKey
from cim.objects import ObjectResolver
from cim.formatters import dump_instance, dump_instances_csv

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


def main(type_, path, namespaceName, className, key_specifier=None, csv=None, addcol=None):
    #if type_ not in ("xp", "win7"):
    #    raise RuntimeError("Invalid mapping type: {:s}".format(type_))

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

    if csv:
        with open(csv, 'w') as out_file:
            #print(dump_instances_csv(instances, encoding='ascii', encoding_errors='ignore', addcol=addcol))
            out_file.write(dump_instances_csv(instances, encoding='ascii', encoding_errors='ignore', addcol=addcol))
    else:
        for instance in instances:
            print("%s" % "=" * 80)
            #print(compute_instance_hash(index, instance))
            try:
                print(dump_instance(instance, encoding='ascii', encoding_errors='ignore'))
            except:
                print("ERROR: failed to dump class instance!")
                print(traceback.format_exc())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(args.target)
    main (args.type, args.target, args.cimpath, args.cimclass, args.filterkeys, args.csv, args.addcol)
