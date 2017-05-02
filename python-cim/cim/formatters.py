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
    for propname, prop in sorted(cd.properties.items(), key=lambda p: p[1].index):
        ret.append("  name: %s" % prop.name)
        ret.append("    type: %s" % prop.type)
        ret.append("    index: %s" % prop.index)
        ret.append("    level: %s" % prop.level)
        ret.append("    offset: %s" % h(prop.offset))
        ret.append("    qualifiers:")
        for k, v in prop.qualifiers.items():
            ret.append("      %s: %s" % (k, str(v)))
    ret.append("layout:")
    off = 0
    if cl is not None:
        for prop in sorted(cl.properties.values(), key=lambda p: p.index):
            ret.append("  (%s)   %s %s" % (h(off), prop.type, prop.name))
            if prop.type.is_array:
                off += 0x4
            else:
                off += CIM_TYPE_SIZES[prop.type.type]
    ret.append("=" * 80)
    ret.append("keys:")
    for key in cd.keys:
        ret.append("  %s" % key)
    ret.append("=" * 80)
    ret.append(cd.tree())
    return "\n".join(ret)


def dump_layout(cd, cl):
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
    for propname, prop in sorted(cl.properties.items(), key=lambda p: p[1].index):
        ret.append("  name: %s" % prop.name)
        ret.append("    type: %s" % prop.type)
        ret.append("    index: %s" % prop.index)
        ret.append("    level: %s" % prop.level)
        ret.append("    offset: %s" % h(prop.offset))
        ret.append("    qualifiers:")
        for k, v in prop.qualifiers.items():
            ret.append("      %s: %s" % (k, str(v)))
        ret.append("    has default value: %s" % str(prop.has_default_value))
        if prop.has_default_value:
            ret.append("      is inherited: %s" % str(prop.is_inherited))
            dv = str(prop.default_value)
            ret.append("      default value: %s" % dv)
    ret.append("layout:")
    off = 0
    if cl is not None:
        for prop in sorted(cl.properties.values(), key=lambda p: p.index):
            ret.append("  (%s)   %s %s" % (h(off), prop.type, prop.name))
            if prop.type.is_array:
                off += 0x4
            else:
                off += CIM_TYPE_SIZES[prop.type.type]
    ret.append("=" * 80)
    ret.append("keys:")
    for key in cd.keys:
        ret.append("  %s" % key)
    ret.append("=" * 80)
    ret.append(cd.tree())
    return "\n".join(ret)


def dump_instance(i, encoding=None, encoding_errors='strict'):
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
    for propname, prop in i.properties.items():
        quals = ",".join(["{:s}={:s}".format(str(k), str(v)) for k, v in prop.qualifiers.items()])
        if quals != "":
            quals = "  [{:s}]".format(quals)
            ret.append(quals)

        if prop.is_initialized:
            ret.append("  {key:s}={value:s}".format(
                key=prop.name,
                value=str(prop.value)))
            if prop.is_default_value:
                ret.append("    default value: true")
        else:
            ret.append("  {key:s}=nil".format(key=prop.name))
        ret.append("")

    instance_str = "\n".join(ret)

    # encode to specified encoding (which returns a byte array),
    # and then decode back to a string
    if encoding:
        instance_str = instance_str.encode(encoding=encoding, errors=encoding_errors).decode(encoding)

    return instance_str
