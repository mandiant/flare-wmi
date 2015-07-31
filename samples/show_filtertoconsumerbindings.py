import logging
import traceback

from cim import CIM
from cim import Index
from cim.objects import ObjectResolver
from cim.objects import Moniker


def main(type_, path):
    if type_ not in ("xp", "win7"):
        raise RuntimeError("Invalid mapping type: {:s}".format(type_))

    c = CIM(type_, path)
    i = Index(c.cim_type, c.logical_index_store)
    o = ObjectResolver(c, i)

    bindings = []
    ns = "root\\subscription"
    bindingname = "__filtertoconsumerbinding"
    for instance in o.get_cd_children_ci(ns, bindingname):
        ci = o.get_ci(ns, bindingname, instance.instance_key)
        bindings.append(ci)

    for instance in bindings:
        print("binding: ", instance.key)
        filterref = instance.properties["Filter"].value
        consumerref = instance.properties["Consumer"].value

        fm = Moniker("\\\\" + ns + ":" + filterref)
        filter = o.get_ci("root\\subscription", fm.klass, fm.instance)
        print("  filter: ", filter)
        print("    language: ", filter.properties["QueryLanguage"].value)
        print("    query: ", filter.properties["Query"].value)

        cm = Moniker("\\\\" + ns + ":" + consumerref)
        consumer = o.get_ci("root\\subscription", cm.klass, cm.instance)
        print("  consumer: ", consumer)
        if "CommandLineTemplate" in consumer.properties:
            print("    payload: ", consumer.properties["CommandLineTemplate"].value)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    main(*sys.argv[1:])
