import logging

import hexdump

from cim import CIM
from cim import Key


def main(type_, path, key):
    if type_ not in ("xp", "win7"):
        raise RuntimeError("Invalid mapping type: {:s}".format(type_))

    c = CIM(type_, path)
    k = Key("a." + key)
    hexdump.hexdump(c.getLogicalDataStore().getObjectBuffer(k))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    main(*sys.argv[1:])
