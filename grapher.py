import logging

from common import h
from common import LoggingObject
from cim import CIM
from cim import is_index_page_number_valid


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
            h(page.key_count())))
        for i in xrange(page.key_count()):
            key = page.get_key(i)
            ret.append(" | {{ {key:s} | <child_{i:s}> {child:s} }}".format(
                key=formatKey(key),
                i=h(i),
                child=h(page.get_child(i))))
        return "".join(ret)

    def _graphIndexPageRec(self, page):
        print("  \"node{:s}\" [".format(h(page.logicalPage)))
        print("     label = \"{:s}\"".format(self._formatIndexPage(page)))
        print("     shape = \"record\"")
        print("  ];")

        keyCount = page.key_count()
        for i in xrange(keyCount + 1):
            childIndex = page.get_child(i)
            if not is_index_page_number_valid(childIndex):
                continue
            i = self._cim.logical_index_store()
            self._graphIndexPageRec(i.get_page(childIndex))

        for i in xrange(keyCount):
            childIndex = page.get_child(i)
            if not is_index_page_number_valid(childIndex):
                continue
            print("  \"node{num:s}\":child_{i:s} -> \"node{child:s}\"".format(
                num=h(page.logicalPage),
                i=h(i),
                child=h(childIndex)))
        # last entry has two links, to both less and greater children nodes
        finalChildIndex = page.get_child(keyCount)
        if is_index_page_number_valid(finalChildIndex):
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
        i = self._cim.logical_index_store()
        self.graphIndexFromPage(i.root_page())

def main(type_, path, pageNum=None):
    if type_ not in ("xp", "win7"):
        raise RuntimeError("Invalid mapping type: {:s}".format(type_))

    c = CIM(type_, path)
    g = Grapher(c)
    if pageNum is None:
        g.graphIndex()
    else:
        pageNum = int(pageNum)
        i = c.logical_index_store()
        p = i.get_page(pageNum)
        g.graphIndexFromPage(p)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    main(*sys.argv[1:])
