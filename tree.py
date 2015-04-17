import logging
from collections import namedtuple

from common import h
from common import one
from common import LoggingObject

from cim import CIM
from cim import Index
from cim import ClassDefinition as cimClassDefinition
from cim import ClassInstance as cimClassInstance

logging.basicConfig(level=logging.DEBUG)
g_logger = logging.getLogger("cim.tree")


ROOT_NAMESPACE_NAME = "root"
SYSTEM_NAMESPACE_NAME = "__SystemClass"
NAMESPACE_CLASS_NAME = "__namespace"


TreeContext = namedtuple("TreeContext", ["cim", "index", "cdcache", "clcache"])


class QueryBuilderMixin(object):
    def __init__(self):
        # self must have the following fields:
        #   - context:TreeContext
        pass

    def _build(self, prefix, name=None):
        if name is None:
            return prefix
        else:
            return prefix + self.index.hash(name.upper().encode("UTF-16LE"))

    def NS(self, name=None):
        return self._build("NS_", name)

    def CD(self, name=None):
        return self._build("CD_", name)

    def CR(self, name=None):
        return self._build("CR_", name)

    def R(self, name=None):
        return self._build("R_", name)

    def CI(self, name=None):
        return self._build("CI_", name)

    def KI(self, name=None):
        return self._build("KI_", name)

    def IL(self, name=None):
        return self._build("IL_", name)

    def I(self, name=None):
        return self._build("I_", name)

    def getClassDefinitionQuery(self, ns, name):
        return "{}/{}".format(self.NS(ns), self.CD(name))


class ObjectFetcherMixin(object):
    def __init__(self):
        # self must have the following fields:
        #   - cim
        #   - index
        pass

    def getObject(self, query):
        """ fetch the first object buffer matching the query """
        self.d("query: {:s}".format(query))
        ref = one(self.index.lookupKeys(query))
        self.d("result: {:s}".format(ref))
        return self.cim.getLogicalDataStore().getObjectBuffer(ref)

    def getObjects(self, query):
        """ return a generator of object buffers matching the query """
        self.d("query: {:s}".format(query))
        refs = self.index.lookupKeys(query)
        self.d("result: {:d} objects".format(len(refs)))
        for ref in self.index.lookupKeys(query):
            self.d("result: {:s}".format(ref))
            yield self.cim.getLogicalDataStore().getObjectBuffer(ref)

    def getClassDefinitionByQuery(self, query):
        """ return the first cim.ClassDefinition matching the query """
        buf = self.getObject(query)
        return cimClassDefinition(buf)

    def getClassDefinition(self, namespace, classname):
        """ return the first cim.ClassDefinition matching the query """
        q = self.getClassDefinitionQuery(namespace, classname)
        ref = one(self.index.lookupKeys(q))

        # some standard class definitions (like __NAMESPACE) are not in the
        #   current NS, but in the __SystemClass NS. So we try that one, too.

        if ref is None:
            self.d("didn't find %s in %s, retrying in %s",
                    classname, namespace, SYSTEM_NAMESPACE_NAME)
            q = self.getClassDefinitionQuery(SYSTEM_NAMESPACE_NAME, classname)
            return self.getClassDefinitionByQuery(q)
        else:
            return self.getClassDefinitionByQuery(q)


class ClassLayout(LoggingObject, QueryBuilderMixin, ObjectFetcherMixin):
    def __init__(self, cim, index, namespace, classDefinition):
        """
        namespace is a string
        classDefinition is a cim.ClassDefinition object
        """
        super(ClassLayout, self).__init__()
        self.cim = cim
        self.index = index
        self._ns = namespace
        self._cd = classDefinition

    @property
    def properties(self):
        className = self._cd.getClassName()
        classDerivation = []  # initially, ordered from child to parent
        while className != "":
            cd = self.getClassDefinition(self._ns, className)
            classDerivation.append(cd)
            self.d("parent of %s is %s", className, cd.getSuperClassName())
            className = cd.getSuperClassName()

        # note, derivation now from parent to child
        classDerivation.reverse()

        self.d("%s derivation: %s",
                self._cd.getClassName(),
                map(lambda c: c.getClassName(), classDerivation))

        ret = []
        while len(classDerivation) > 0:
            cd = classDerivation.pop(0)
            for prop in cd.getProperties().values():
                ret.append(prop)

        self.d("%s property layout: %s",
                self._cd.getClassName(),
                map(lambda p: p.getName(), ret))

        return ret

    def parseInstance(self, data):
        return cimClassInstance(self.properties, data)


class Namespace(LoggingObject, QueryBuilderMixin, ObjectFetcherMixin):
    def __init__(self, cim, index, name):
        super(Namespace, self).__init__()
        self.cim = cim
        self.index = index
        self.name = name

    def __repr__(self):
        return "Namespace(name: {:s})".format(self.name)

    @property
    def namespace(self):
        """ get parent namespace """
        if self.name == ROOT_NAMESPACE_NAME:
            return None
        else:
            # TODO
            raise NotImplementedError()

    @property
    def namespaces(self):
        """ return a generator direct child namespaces """
        q = self.getClassDefinitionQuery(SYSTEM_NAMESPACE_NAME, NAMESPACE_CLASS_NAME)

        namespaceCD = cimClassDefinition(self.getObject(q))
        namespaceCL = ClassLayout(self.cim, self.index, self.name, namespaceCD)

        q = "{}/{}/{}".format(
                self.NS(self.name),
                self.CI(NAMESPACE_CLASS_NAME),
                self.IL())
        for namespaceInstance in self.getObjects(q):
            namespaceI = namespaceCL.parseInstance(namespaceInstance)
            nsName = namespaceI.getPropertyValue("Name")
            # TODO: perhaps should test if this thing exists?
            yield Namespace(self.cim, self.index, self.name + "\\" + nsName)

    @property
    def classes(self):
        """ get direct child class definitions """
        pass


class ClassDefinition(LoggingObject):
    def __init__(self, cim, index, name):
        super(ClassDefinition, self).__init__()
        self.cim = cim
        self.index = index
        self.name = name

    def __repr__(self):
        return "ClassDefinition(name: {:s})".format(self.name)

    @property
    def namespace(self):
        """ get parent namespace """
        pass

    @property
    def instances(self):
        """ get instances of this class definition """
        pass


class ClassInstance(LoggingObject):
    def __init__(self, cim, index, name):
        super(ClassInstance, self).__init__()
        self.cim = cim
        self.index = index
        self.name = name

    def __repr__(self):
        return "ClassInstance(name: {:s})".format(self.name)

    @property
    def klass(self):
        """ get class definition """
        pass

    @property
    def namespace(self):
        """ get parent namespace """
        pass



class Tree(LoggingObject):
    def __init__(self, cim):
        super(Tree, self).__init__()
        self._cim = cim
        self._index = Index(cim)

    def __repr__(self):
        return "Tree"

    @property
    def root(self):
        """ get root namespace """
        return Namespace(self._cim, self._index, ROOT_NAMESPACE_NAME)



def formatKey(k):
    ret = []
    for part in str(k).split("/"):
        if "." in part:
            ret.append(part[:7] + "..." + part.partition(".")[2])
        else:
            ret.append(part[:7])
    return "/".join(ret)


def rec_ns(ns):
    for c in ns.namespaces:
        g_logger.info(c)
        rec_ns(c)


def main(type_, path):
    if type_ not in ("xp", "win7"):
        raise RuntimeError("Invalid mapping type: {:s}".format(type_))

    c = CIM(type_, path)
    t = Tree(c)
    print(t.root)
    rec_ns(t.root)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    main(*sys.argv[1:])
