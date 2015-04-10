import logging

from cim import CIM
from cim import Index


def main(type_, path, *s):
    if type_ not in ("xp", "win7"):
        raise RuntimeError("Invalid mapping type: {:s}".format(type_))

    c = CIM(type_, path)
    i = Index(c)
    for ss in s:
        print("%s\t%s" % (i._encodeItem("XX_", ss), ss))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    main(*sys.argv[1:])
