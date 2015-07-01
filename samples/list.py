import logging

from cim import CIM
from cim.objects import Tree


def rec_namespace(namespace):
    print(repr(namespace))
    for klass in namespace.classes:
        print(repr(klass))
        for instance in klass.instances:
            print(repr(instance))
    for ns in namespace.namespaces:
        rec_namespace(ns)


def main(type_, path):
    if type_ not in ("xp", "win7"):
        raise RuntimeError("Invalid mapping type: {:s}".format(type_))

    c = CIM(type_, path)
    tree = Tree(c)
    rec_namespace(tree.root)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    main(*sys.argv[1:])
