import logging

from cim.common import h
from cim.common import LoggingObject
from cim import CIM
from cim import is_index_page_number_valid

logging.basicConfig(level=logging.DEBUG)
g_logger = logging.getLogger("cim.grapher")


class Grapher(LoggingObject):
    def __init__(self, cim):
        super(Grapher, self).__init__()
        self._cim = cim

    @staticmethod
    def _format_index_page(page):
        ret = []
        ret.append("<header> logical page: {:s} | physical page: {:s} | count: {:s}".format(
            h(page.logical_page_number),
            h(page.physical_page_number),
            h(page.key_count)))
        for i in xrange(page.key_count):
            key = page.get_key(i)
            ret.append(" | {{ {key:s} | <child_{i:s}> {child:s} }}".format(
                key=key.human_format,
                i=h(i),
                child=h(page.get_child(i))))
        return "".join(ret)

    def _graph_index_page_rec(self, page):
        print("  \"node{:s}\" [".format(h(page.logical_page_number)))
        print("     label = \"{:s}\"".format(self._format_index_page(page)))
        print("     shape = \"record\"")
        print("  ];")

        key_count = page.key_count
        for i in xrange(key_count + 1):
            child_page_number = page.get_child(i)
            if not is_index_page_number_valid(child_page_number):
                continue
            child_page = self._cim.logical_index_store.get_page(child_page_number)
            self._graph_index_page_rec(child_page)

        for i in xrange(key_count):
            child_page_number = page.get_child(i)
            if not is_index_page_number_valid(child_page_number):
                continue
            print("  \"node{num:s}\":child_{i:s} -> \"node{child:s}\"".format(
                num=h(page.logical_page_number),
                i=h(i),
                child=h(child_page_number)))
        # last entry has two links, to both less and greater children nodes
        final_child_index = page.get_child(key_count)
        if is_index_page_number_valid(final_child_index):
            print("  \"node{num:s}\":child_{i:s} -> \"node{child:s}\"".format(
                num=h(page.logical_page_number),
                i=h(key_count - 1),
                child=h(final_child_index)))

    def graph_index_from_page(self, page):
        print("digraph g {")
        print("  graph [ rankdir = \"LR\" ];")
        print("  node [")
        print("     fontsize = \"16\"")
        print("     shape = \"ellipse\"")
        print("  ];")
        print("  edge [];")

        self._graph_index_page_rec(page)

        print("}")

    def graph_index(self):
        root = self._cim.logical_index_store.root_page
        self.graph_index_from_page(root)


def main(type_, path, page_number=None):
    if type_ not in ("xp", "win7"):
        raise RuntimeError("Invalid mapping type: {:s}".format(type_))

    c = CIM(type_, path)
    g = Grapher(c)

    root = c.logical_index_store.root_page
    # print(root)
    # print(root.tree())

    # print(root.get_key(0))
    # print(root.get_key(1))
    # print(root.get_child(0))
    # print(root.get_child(1))


    if page_number is None:
        g.graph_index()
    else:
        page_number = int(page_number)
        i = c.logical_index_store
        p = i.get_page(page_number)
        g.graph_index_from_page(p)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    import sys

    main(*sys.argv[1:])
