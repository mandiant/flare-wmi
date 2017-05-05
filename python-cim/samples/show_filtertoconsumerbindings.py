import logging

from cim import CIM
from cim.objects import Namespace


def main(type_, path):
    if type_ not in ("xp", "win7"):
        raise RuntimeError("Invalid mapping type: {:s}".format(type_))

    c = CIM(type_, path)
    with Namespace(c, "root\\subscription") as ns:
        for binding in ns.class_("__filtertoconsumerbinding").instances:
            print("binding: ", binding)
            filterref = binding.properties["Filter"].value
            consumerref = binding.properties["Consumer"].value
            filter = ns.get(ns.parse_object_path(filterref))
            consumer = ns.get(ns.parse_object_path(consumerref))

            print("  filter: ", filter)
            print("    language: ", filter.properties["QueryLanguage"].value)
            print("    query: ", filter.properties["Query"].value)

            print("  consumer: ", consumer)
            if "CommandLineTemplate" in consumer.properties:
                print("    payload: ", consumer.properties["CommandLineTemplate"].value)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys

    main(*sys.argv[1:])
