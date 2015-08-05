import logging

from cim import CIM
from cim import Index


def main(type_, path, *s):
    if type_ not in ("xp", "win7"):
        raise RuntimeError("Invalid mapping type: {:s}".format(type_))

    c = CIM(type_, path)
    i = Index(c.cim_type, c.logical_index_store)
    for ss in s:
        print("XX_%s\t%s" % (str(i.hash(ss.encode("utf-16le"))), str(ss)))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    main(*sys.argv[1:])
