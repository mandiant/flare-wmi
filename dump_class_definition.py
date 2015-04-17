import logging
import traceback

from cim import CIM
from cim import Index
from cim import Moniker
from cim import DATA_PAGE_SIZE
from cim import ClassDefinition
from common import h
from common import one


def formatKey(k):
    ret = []
    for part in str(k).split("/"):
        if "." in part:
            ret.append(part[:7] + "..." + part.partition(".")[2])
        else:
            ret.append(part[:7])
    return "/".join(ret)


def dump_class_def(cd):
    print("classname: %s" % cd.getClassName())
    print("super: %s" % cd.getSuperClassName())
    print("ts: %s" % cd.getTimestamp().isoformat("T"))
    print("qualifiers:")
    for k, v in cd.getQualifiers().iteritems():
        print("  %s: %s" % (k, str(v)))
    print("properties:")
    for propname, prop in cd.getProperties().iteritems():
        print("  name: %s" % prop.getName())
        print("    type: %s" % prop.getType())
        print("    qualifiers:")
        for k, v in prop.getQualifiers().iteritems():
            print("      %s: %s" % (k, str(v)))


def main(type_, path, namespaceName, className):
    if type_ not in ("xp", "win7"):
        raise RuntimeError("Invalid mapping type: {:s}".format(type_))

    c = CIM(type_, path)
    i = Index(c)

    while className != "":
        print("%s" % "=" * 80)
        print("namespace: %s" % namespaceName)
        print("classname: %s" % className)
        needle = Moniker("//./%s:%s" % (namespaceName, className))
        print("moniker: %s" % str(needle))
        k = one(i.lookupMoniker(needle))
        if k is None:
            print("ERROR: not found!")
            return
        print("database id: %s" % formatKey(k))
        print("objects.data page: %s" % h(k.getDataPage()))
        physicalOffset = DATA_PAGE_SIZE * \
                          c.getDataMapping().getPhysicalPage(k.getDataPage())
        print("physical offset: %s" % h(physicalOffset))
        buf = c.getLogicalDataStore().getObjectBuffer(k)
        cd = ClassDefinition(buf)
        try:
            dump_class_def(cd)
        except:
            print("ERROR: failed to dump class definition!")
            print traceback.format_exc()
        className = cd.getSuperClassName()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    main(*sys.argv[1:])
