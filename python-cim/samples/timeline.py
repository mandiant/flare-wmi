import logging
import traceback

g_logger = logging.getLogger("cim.timeline")

from cim import CIM
from cim.objects import Tree


def format_ts(ts):
    return ts.isoformat("T") + "Z"


def rec_namespace(namespace):
    for klass in namespace.classes:
        print("{ts:s},ClassDefinition.timestamp,{id:s}".format(
            ts=format_ts(klass.cd.header.timestamp), id=repr(klass)))
        for instance in klass.instances:
            try:
                print("{ts:s},ClassInstance.timestamp1,{id:s}".format(
                    ts=format_ts(instance.ci.ts1), id=repr(instance)))
                print("{ts:s},ClassInstance.timestamp2,{id:s}".format(
                    ts=format_ts(instance.ci.ts2), id=repr(instance)))
            except:
                g_logger.error(traceback.format_exc())
    for ns in namespace.namespaces:
        rec_namespace(ns)


def main(type_, path):
    if type_ not in ("xp", "win7"):
        raise RuntimeError("Invalid mapping type: {:s}".format(type_))

    c = CIM(type_, path)
    tree = Tree(c)
    rec_namespace(tree.root)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    main(*sys.argv[1:])
