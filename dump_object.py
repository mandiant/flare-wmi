import sys
import logging

from cim import CIM
from cim import Key


def main(type_, path, key):
    if type_ not in ("xp", "win7"):
        raise RuntimeError("Invalid mapping type: {:s}".format(type_))

    c = CIM(type_, path)
    k = Key("a." + key)
    sys.stdout.write(c.getLogicalDataStore().getObjectBuffer(k))
    sys.stdout.flush()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    main(*sys.argv[1:])
