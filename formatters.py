from common import h
from objects import CIM_TYPE_SIZES


def dump_definition(cd, cl):
    print(cd.tree())

    print("classname: %s" % cd.class_name)
    print("super: %s" % cd.super_class_name)
    print("ts: %s" % cd.timestamp.isoformat("T"))
    print("qualifiers:")
    for k, v in cd.qualifiers.iteritems():
        print("  %s: %s" % (k, str(v)))
    print("properties:")
    for propname, prop in cd.properties.iteritems():
        print("  name: %s" % prop.name)
        print("    type: %s" % prop.type)
        print("    order: %s" % prop.entry_number)
        print("    qualifiers:")
        for k, v in prop.qualifiers.iteritems():
            print("      %s: %s" % (k, str(v)))
    print("layout:")
    off = 0
    for prop in cl.properties:
        print("  (%s)   %s %s" % (h(off), prop.type, prop.name))
        if prop.type.is_array:
            off += 0x4
        else:
            off += CIM_TYPE_SIZES[prop.type.type]
    print("keys:")
    for key in cd.keys:
        print("  %s" % (key))


def dump_instance(i):
    """ :type i: ClassInstance """
    cl = i.class_layout
    cd = cl.class_definition
    print("classname: %s" % cd.class_name)
    print("super: %s" % cd.super_class_name)
    print("ts: %s" % cd.timestamp.isoformat("T"))
    print("qualifiers:")
    for k, v in cd.qualifiers.iteritems():
        print("  %s: %s" % (k, str(v)))
    print("properties:")
    for propname, prop in cd.properties.iteritems():
        print("  name: %s" % prop.name)
        print("    type: %s" % prop.type)
        print("    order: %s" % prop.entry_number)
        print("    qualifiers:")
        for k, v in prop.qualifiers.iteritems():
            print("      %s: %s" % (k, str(v)))
    print("layout:")
    off = 0
    for prop in cl.properties:
        print("  (%s)   %s %s" % (h(off), prop.type, prop.name))
        if prop.type.is_array:
            off += 0x4
        else:
            off += CIM_TYPE_SIZES[prop.type.type]
    print("values:")
    props = cd.properties
    for propname, prop in props.iteritems():
        print("%s=%s" % (
            prop.name, str(i.get_property_value(prop.name))))
