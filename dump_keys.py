import logging

from common import h
from common import LoggingObject
from cim import CIM
from cim import is_index_page_number_valid


logging.basicConfig(level=logging.DEBUG)
g_logger = logging.getLogger("cim.printer")


def formatKey(k):
    ret = []
    for part in str(k).split("/"):
        if "." in part:
            ret.append(part[:8] + "..." + part.partition(".")[2])
        else:
            ret.append(part[:8])
    return "/".join(ret)


class Printer(LoggingObject):
    def __init__(self, cim):
        super(Printer, self).__init__()
        self._cim = cim

    def _printPageRec(self, page):
        for i in xrange(page.key_count()):
            key = page.get_key(i)
            print(formatKey(key))

        keyCount = page.key_count()
        for i in xrange(keyCount + 1):
            childIndex = page.get_child(i)
            if not is_index_page_number_valid(childIndex):
                continue
            i = self._cim.logical_index_store()
            i = self._cim.logical_index_store()
            self._printPageRec(i.get_page(childIndex))

    def printKeys(self):
        i = self._cim.logical_index_store()
        self._printPageRec(i.root_page())

def main(type_, path, pageNum=None):
    if type_ not in ("xp", "win7"):
        raise RuntimeError("Invalid mapping type: {:s}".format(type_))

    c = CIM(type_, path)
    p = Printer(c)
    p.printKeys()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    main(*sys.argv[1:])
