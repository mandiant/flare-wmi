from .common import h
from .objects import CIM_TYPE_SIZES


def dump_definition(cd, cl):
    """
    :type cd: ClassDefinition
    :type cl: ClassLayout
    """
    # TODO: migrate to templating?
    ret = []

    ret.append("classname: %s" % cd.class_name)
    ret.append("super: %s" % cd.super_class_name)
    ret.append("ts: %s" % cd.timestamp.isoformat("T"))
    ret.append("qualifiers:")
    for k, v in cd.qualifiers.items():
        ret.append("  %s: %s" % (k, str(v)))
    ret.append("properties:")
    for propname, prop in cd.properties.items():
        ret.append("  name: %s" % prop.name)
        ret.append("    type: %s" % prop.type)
        ret.append("    order: %s" % prop.entry_number)
        ret.append("    qualifiers:")
        for k, v in prop.qualifiers.items():
            ret.append("      %s: %s" % (k, str(v)))
    ret.append("layout:")
    off = 0
    if cl is not None:
        for prop in cl.properties:
            ret.append("  (%s)   %s %s" % (h(off), prop.type, prop.name))
            if prop.type.is_array:
                off += 0x4
            else:
                off += CIM_TYPE_SIZES[prop.type.type]
    ret.append("=" * 80)
    ret.append("keys:")
    for key in cd.keys:
        ret.append("  %s" % (key))
    ret.append("=" * 80)
    ret.append(cd.tree())
    return "\n".join(ret)


def dump_instance(i):
    """ :type i: ClassInstance """
    # TODO: migrate to templating?
    ret = []
    cl = i.class_layout
    cd = cl.class_definition
    ret.append("classname: %s" % cd.class_name)
    ret.append("super: %s" % cd.super_class_name)
    ret.append("key: %s" % str(i.key))
    ret.append("timestamp1: %s" % i.ts1)
    ret.append("timestamp2: %s" % i.ts2)
    ret.append("properties:")
    for propname, prop in cd.properties.items():
        value = i.get_property_value(prop.name)
        if not value:
            continue
        quals = ",".join(["{:s}={:s}".format(str(k), str(v)) for k, v in prop.qualifiers.items()])
        if quals != "":
            quals = "  [{:s}]".format(quals)
            ret.append(quals)

        ret.append("  {key:s}={value:s}".format(
            key=prop.name,
            value=str(value)))
        ret.append("")
    return "\n".join(ret)
