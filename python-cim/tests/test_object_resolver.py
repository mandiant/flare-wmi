import cim
import cim.objects
from fixtures import *


def test_object_resolver(repo):
    """
    Args:
        repo (cim.CIM): the deleted-instance repo

    Returns:
        None
    """
    resolver = cim.objects.ObjectResolver(repo)

    assert len(resolver.get_keys(cim.Key('NS_'))) == 47490

    for key in resolver.get_keys(cim.Key('NS_')):
        if not key.is_data_reference:
            continue
        o = resolver.get_object(key)
        assert o is not None


def test_root_namespace(repo):
    """
    Args:
        repo (cim.CIM): the deleted-instance repo

    Returns:
        None
    """
    with cim.objects.Namespace(repo, cim.objects.ROOT_NAMESPACE_NAME) as ns:
        ''':type: ns: cim.objects.TreeNamespace '''
        assert ns.parent == None

        # children namespaces
        assert sorted(map(lambda n: n.name, ns.namespaces)) == ['__SystemClass',
                                                                'root\\CIMV2',
                                                                'root\\Cli',
                                                                'root\\DEFAULT',
                                                                'root\\Interop',
                                                                'root\\Microsoft',
                                                                'root\\PEH',
                                                                'root\\Policy',
                                                                'root\\RSOP',
                                                                'root\\SECURITY',
                                                                'root\\SecurityCenter',
                                                                'root\\SecurityCenter2',
                                                                'root\\ServiceModel',
                                                                'root\\ThinPrint',
                                                                'root\\WMI',
                                                                'root\\aspnet',
                                                                'root\\directory',
                                                                'root\\nap',
                                                                'root\\subscription', ]

        # children classes
        assert sorted(map(lambda n: n.name, ns.classes)) == ['CIM_ClassCreation',
                                                             'CIM_ClassDeletion',
                                                             'CIM_ClassIndication',
                                                             'CIM_ClassModification',
                                                             'CIM_Error',
                                                             'CIM_Indication',
                                                             'CIM_InstCreation',
                                                             'CIM_InstDeletion',
                                                             'CIM_InstIndication',
                                                             'CIM_InstModification',
                                                             'MSFT_ExtendedStatus',
                                                             'MSFT_WmiError',
                                                             '__ACE',
                                                             '__AbsoluteTimerInstruction',
                                                             '__AggregateEvent',
                                                             '__ArbitratorConfiguration',
                                                             '__CIMOMIdentification',
                                                             '__CacheControl',
                                                             '__ClassCreationEvent',
                                                             '__ClassDeletionEvent',
                                                             '__ClassModificationEvent',
                                                             '__ClassOperationEvent',
                                                             '__ClassProviderRegistration',
                                                             '__ConsumerFailureEvent',
                                                             '__Event',
                                                             '__EventConsumer',
                                                             '__EventConsumerProviderCacheControl',
                                                             '__EventConsumerProviderRegistration',
                                                             '__EventDroppedEvent',
                                                             '__EventFilter',
                                                             '__EventGenerator',
                                                             '__EventProviderCacheControl',
                                                             '__EventProviderRegistration',
                                                             '__EventQueueOverflowEvent',
                                                             '__EventSinkCacheControl',
                                                             '__ExtendedStatus',
                                                             '__ExtrinsicEvent',
                                                             '__FilterToConsumerBinding',
                                                             '__IndicationRelated',
                                                             '__InstanceCreationEvent',
                                                             '__InstanceDeletionEvent',
                                                             '__InstanceModificationEvent',
                                                             '__InstanceOperationEvent',
                                                             '__InstanceProviderRegistration',
                                                             '__IntervalTimerInstruction',
                                                             '__ListOfEventActiveNamespaces',
                                                             '__MethodInvocationEvent',
                                                             '__MethodProviderRegistration',
                                                             '__NAMESPACE',
                                                             '__NTLMUser9X',
                                                             '__NamespaceCreationEvent',
                                                             '__NamespaceDeletionEvent',
                                                             '__NamespaceModificationEvent',
                                                             '__NamespaceOperationEvent',
                                                             '__NotifyStatus',
                                                             '__ObjectProviderCacheControl',
                                                             '__ObjectProviderRegistration',
                                                             '__PARAMETERS',
                                                             '__PropertyProviderCacheControl',
                                                             '__PropertyProviderRegistration',
                                                             '__Provider',
                                                             '__ProviderHostQuotaConfiguration',
                                                             '__ProviderRegistration',
                                                             '__QOSFailureEvent',
                                                             '__SecurityDescriptor',
                                                             '__SecurityRelatedClass',
                                                             '__SystemClass',
                                                             '__SystemEvent',
                                                             '__SystemSecurity',
                                                             '__TimerEvent',
                                                             '__TimerInstruction',
                                                             '__TimerNextFiring',
                                                             '__Trustee',
                                                             '__Win32Provider',
                                                             '__thisNAMESPACE']


def test_object_count(root):
    """
    enumerate all the objects in the repository.
    
    Args:
        root (cim.objects.TreeNamespace): the root namespace

    Returns:
        None
    """
    namespaces = []
    classes = []
    instances = []

    def collect(ns):
        for namespace in ns.namespaces:
            namespaces.append(namespace)

        for klass in ns.classes:
            classes.append(klass)

            for instance in klass.instances:
                instances.append(instance)

        for namespace in ns.namespaces:
            collect(namespace)

    collect(root)

    # collected empirically
    assert len(namespaces) == 55
    assert len(classes) == 8162
    assert len(instances) == 1887

    for instance in instances:
        print(str(instance))


def test_class_definitions(root):
    """
    parse all qualifiers and properties from all class definitions in the repository.
    demonstrates there's no critical errors encountered while enumerating classes.
    
    Args:
        root (cim.objects.TreeNamespace): the root namespace

    Returns:
        None
    """
    classes = []
    def collect(ns):
        for klass in ns.classes:
            classes.append(klass)

        for namespace in ns.namespaces:
            collect(namespace)
    collect(root)

    qualifiers = []
    properties = []
    propqualifiers = []
    for klass in classes:
        definition = klass.cd

        # these are the qualifiers that apply to the class itself
        for qualname, qualval in definition.qualifiers.items():
            qualifiers.append((klass.ns, klass.name, qualname, qualval))

        # these are the properties defined on the class
        for propname, propref in definition.properties.items():
            properties.append((klass.ns, klass.name, propname))

            # these are the qualifiers that apply to the property on the class
            for qualname, qualval in propref.qualifiers.items():
                propqualifiers.append((klass.ns, klass.name, propname, qualname, qualval))


    assert len(qualifiers) == 17650
    assert len(properties) == 27431
    assert len(propqualifiers) == 66948
