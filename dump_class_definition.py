import logging
import traceback

from cim import CIM
from cim import Index
from cim import DATA_PAGE_SIZE
from objects import CimContext
from objects import getClassId
from objects import ClassLayout
from objects import CIM_TYPE_SIZES
from objects import ClassDefinition
from objects import QueryBuilderMixin
from objects import ObjectFetcherMixin
from common import h
from common import one
from common import LoggingObject


def formatKey(k):
    ret = []
    for part in str(k).split("/"):
        if "." in part:
            ret.append(part[:7] + "..." + part.partition(".")[2])
        else:
            ret.append(part[:7])
    return "/".join(ret)


class Querier(LoggingObject, QueryBuilderMixin, ObjectFetcherMixin):
    def __init__(self, context):
        super(Querier, self).__init__()
        self.context = context

    def __repr__(self):
        return "Querier()"

    def get_class_definition(self, namespace, classname):
        classId = getClassId(namespace, classname)
        cd = self.context.cdcache.get(classId, None)
        if cd is None:
            self.d("cdcache miss")
            buf = self.get_class_definition_buffer(namespace, classname)
            cd = ClassDefinition(buf)
            self.context.cdcache[classId] = cd
        return cd

    def getClassLayout(self, namespace, classname):
        cd = self.get_class_definition(namespace, classname)
        return ClassLayout(self.context, namespace, cd)


def dump_class_def(cd, cl):
    print("classname: %s" % cd.class_name())
    print("super: %s" % cd.super_class_name())
    print("ts: %s" % cd.timestamp().isoformat("T"))
    print("qualifiers:")
    for k, v in cd.qualifiers().iteritems():
        print("  %s: %s" % (k, str(v)))
    print("properties:")
    for propname, prop in cd.properties().iteritems():
        print("  name: %s" % prop.name())
        print("    type: %s" % prop.type())
        print("    order: %s" % prop.entry_number())
        print("    qualifiers:")
        for k, v in prop.qualifiers().iteritems():
            print("      %s: %s" % (k, str(v)))
    print("layout:")
    off = 0
    for prop in cl.properties:
        print("  (%s)   %s %s" % (h(off), prop.type(), prop.name()))
        if prop.type().is_array():
            off += 0x4
        else:
            off += CIM_TYPE_SIZES[prop.type().type()]


def main(type_, path, namespaceName, className):
    if type_ not in ("xp", "win7"):
        raise RuntimeError("Invalid mapping type: {:s}".format(type_))

    c = CIM(type_, path)
    ctx = CimContext(
            c,
            Index(c.getCimType(), c.logical_index_store()),
            {}, {})
    q = Querier(ctx)

    while className != "":
        print("%s" % "=" * 80)
        print("namespace: %s" % namespaceName)
        cd = q.get_class_definition(namespaceName, className)
        cl = q.getClassLayout(namespaceName, className)
        try:
            dump_class_def(cd, cl)
        except:
            print("ERROR: failed to dump class definition!")
            print traceback.format_exc()
        className = cd.super_class_name()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    main(*sys.argv[1:])
