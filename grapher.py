import logging

from common import h
from common import LoggingObject
from cim import CIM
from cim import isIndexPageNumberValid


logging.basicConfig(level=logging.DEBUG)
g_logger = logging.getLogger("cim.grapher")


def formatKey(k):
    ret = []
    for part in str(k).split("/"):
        if "." in part:
            ret.append(part[:7] + "..." + part.partition(".")[2])
        else:
            ret.append(part[:7])
    return "/".join(ret)


class Grapher(LoggingObject):
    def __init__(self, cim):
        super(Grapher, self).__init__()
        self._cim = cim

    def _formatIndexPage(self, page):
        ret = []
        ret.append("<header> logical page: {:s} | physical page: {:s} | count: {:s}".format(
            h(page.logicalPage),
            h(page.physicalPage),
            h(page.getKeyCount())))
        for i in xrange(page.getKeyCount()):
            key = page.getKey(i)
            ret.append(" | {{ {key:s} | <child_{i:s}> {child:s} }}".format(
                key=formatKey(key),
                i=h(i),
                child=h(page.getChildByIndex(i))))
        return "".join(ret)

    def _graphIndexPageRec(self, page):
        print("  \"node{:s}\" [".format(h(page.logicalPage)))
        print("     label = \"{:s}\"".format(self._formatIndexPage(page)))
        print("     shape = \"record\"")
        print("  ];")

        keyCount = page.getKeyCount()
        for i in xrange(keyCount + 1):
            childIndex = page.getChildByIndex(i)
            if not isIndexPageNumberValid(childIndex):
                continue
            i = self._cim.getLogicalIndexStore()
            self._graphIndexPageRec(i.getPage(childIndex))

        for i in xrange(keyCount):
            childIndex = page.getChildByIndex(i)
            if not isIndexPageNumberValid(childIndex):
                continue
            print("  \"node{num:s}\":child_{i:s} -> \"node{child:s}\"".format(
                num=h(page.logicalPage),
                i=h(i),
                child=h(childIndex)))
        # last entry has two links, to both less and greater children nodes
        finalChildIndex = page.getChildByIndex(keyCount)
        if isIndexPageNumberValid(finalChildIndex):
            print("  \"node{num:s}\":child_{i:s} -> \"node{child:s}\"".format(
                num=h(page.logicalPage),
                i=h(keyCount - 1),
                child=h(finalChildIndex)))

    def graphIndexFromPage(self, page):
        print("digraph g {")
        print("  graph [ rankdir = \"LR\" ];")
        print("  node [")
        print("     fontsize = \"16\"")
        print("     shape = \"ellipse\"")
        print("  ];")
        print("  edge [];")

        self._graphIndexPageRec(page)

        print("}")

    def graphIndex(self):
        i = self._cim.getLogicalIndexStore()
        self.graphIndexFromPage(i.getRootPage())

def main(type_, path, pageNum=None):
    if type_ not in ("xp", "win7"):
        raise RuntimeError("Invalid mapping type: {:s}".format(type_))

    c = CIM(type_, path)
    g = Grapher(c)
    if pageNum is None:
        g.graphIndex()
    else:
        pageNum = int(pageNum)
        i = c.getLogicalIndexStore()
        p = i.getPage(pageNum)
        g.graphIndexFromPage(p)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    main(*sys.argv[1:])
