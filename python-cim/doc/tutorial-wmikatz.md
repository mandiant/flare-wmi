# tutorial: recovering evidence of the wmikatz hacking utility

## background scenario

consider the example data available in [tests/repos/win7/wmikatz](../tests/repos/win7/wmikatz).
it contains a wmi repository in which a malicious actor has installed and used a variant of the Mimikatz credential stealer.
the malware script [wmim2.ps1](../tests/repos/win7/wmikatz/wmim2.ps1_) does the following:

  - decodes mimikatz from an embedded base64 string, and
  - if run with the `local` flag: runs mimikatz, prints results, and exits.
  - if run with the `get` flag: fetches data from the (possibly remote) WMI object `\\$computer\root\cimv2:Win32_AuditCode`.
  - if run with the `delete` flag: deletes data from the (possibly remote) WMI object `\\$computer\root\cimv2:Win32_AuditCode`.
  - otherwise, it:
    - writes the mimikatz payload into the (possibly remote) WMI object `\\$computer\root\cimv2:Win32_AuditCode`, and
    - runs a (possibly remote) powershell command as a new process via WMI to invoke mimikatz and save the result, and
    - fetches the results from the (possibly remote) WMI object `\\$computer\root\cimv2:Win32_AuditCode`, and
    - prints the results.


## analysis

*now lets imagine that we have haven't seen the script*, and are unaware as to what it does.
all we have is the possibly-infected wmi repository, and a suspicion that something bad happened in early 2017.
what information can we recover that would confirm compromise and indicate its scope?


### active metadata

first, we would enumerate the active metadata and look for anomalies.
an intuitive strategy is to timeline all the available timestamps:

```
 $ python timeline.py .
...
2016-06-08T23:47:50.563305Z	ClassInstance.timestamp2	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1003:RSOP_GPO.id=LocalGPO
2016-06-08T23:47:50.563305Z	ClassDefinition.timestamp	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1003:RSoP_PolicySettingLink
2016-06-08T23:47:50.563305Z	ClassDefinition.timestamp	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1003:RSOP_IEPrivacySettings
2016-06-08T23:47:50.563305Z	ClassDefinition.timestamp	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1003:RSOP_IELinkItem
2016-06-08T23:47:50.563305Z	ClassDefinition.timestamp	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1003:RSOP_IEConnectionDialUpSettingsLink
2016-06-08T23:47:50.563305Z	ClassDefinition.timestamp	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1003:RSOP_IEESC
2016-06-08T23:47:50.563307Z	ClassInstance.timestamp1	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1003:RSOP_SOM.id=Local,reason=1
2016-06-08T23:47:50.563307Z	ClassInstance.timestamp1	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1003:RSOP_ExtensionStatus.extensionGuid={00000000-0000-0000-0000-000000000000}
2016-06-08T23:47:50.563307Z	ClassInstance.timestamp1	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1003:RSOP_ExtensionEventSourceLink.eventSource=RSOP_ExtensionEventSource.id="{B449D97E-B9EB-435E-A324-FFBE3FEA3629}",extensionStatus=RSOP_ExtensionStatus.extensionGuid="{00000000-0000-0000-0000-000000000000}"
2016-06-08T23:47:50.563307Z	ClassInstance.timestamp1	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1003:RSOP_GPLink.GPO=RSOP_GPO.id="LocalGPO",SOM=RSOP_SOM.id="Local",reason=1,somOrder=1
2016-06-08T23:47:50.563307Z	ClassInstance.timestamp1	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1003:RSOP_Session.id=Session1
2016-06-08T23:47:50.563307Z	ClassInstance.timestamp1	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1003:RSOP_ExtensionEventSource.id={B449D97E-B9EB-435E-A324-FFBE3FEA3629}
2016-06-08T23:47:50.563307Z	ClassInstance.timestamp1	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1003:RSOP_GPO.id=LocalGPO
2017-04-23T08:03:19.063290Z	ClassInstance.timestamp1	\root\RSOP\User:__NAMESPACE.Name=GS_1_5_21_2905342495_973398862_4115133902_1002
2017-04-23T08:03:19.063290Z	ClassDefinition.timestamp	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1002:CIM_Indication
2017-04-23T08:03:19.063290Z	ClassDefinition.timestamp	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1002:CIM_ClassIndication
2017-04-23T08:03:19.063290Z	ClassDefinition.timestamp	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1002:CIM_ClassDeletion
...
2017-04-23T08:03:19.063299Z	ClassDefinition.timestamp	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1002:RSOP_IEConnectionSettings
2017-04-23T08:03:19.063299Z	ClassDefinition.timestamp	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1002:RSOP_IEFavoriteItem
2017-04-23T08:03:19.063299Z	ClassDefinition.timestamp	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1002:RSOP_IEAdministrativeTemplateFile
2017-04-23T08:03:19.063299Z	ClassDefinition.timestamp	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1002:RSOP_IEProgramSettings
2017-04-23T08:03:19.063299Z	ClassDefinition.timestamp	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1002:RSOP_IEProxySettings
2017-04-23T08:03:19.063299Z	ClassDefinition.timestamp	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1002:RSOP_Session
2017-04-23T08:03:19.063299Z	ClassInstance.timestamp2	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1002:RSOP_Session.id=Session1
2017-04-23T08:03:19.063299Z	ClassDefinition.timestamp	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1002:RSOP_IEAKPolicySetting
2017-04-23T08:03:19.063299Z	ClassDefinition.timestamp	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1002:RSOP_IEToolbarButton
2017-04-23T08:03:19.063299Z	ClassDefinition.timestamp	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1002:RSOP_RegistryPolicySetting
2017-04-23T08:03:19.063299Z	ClassDefinition.timestamp	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1002:RSOP_IEConnectionSettingsLink
2017-04-23T08:03:19.063299Z	ClassDefinition.timestamp	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1002:RSOP_ExtensionEventSource
2017-04-23T08:03:19.063299Z	ClassInstance.timestamp2	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1002:RSOP_ExtensionEventSource.id={1DAA2165-A3F4-470C-98DF-B07E8DD45059}
2017-04-23T08:03:19.063299Z	ClassDefinition.timestamp	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1002:RSOP_IEFavoriteOrLinkItem
2017-04-23T08:03:19.063299Z	ClassDefinition.timestamp	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1002:RSOP_GPO
2017-04-23T08:03:19.063299Z	ClassInstance.timestamp2	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1002:RSOP_GPO.id=LocalGPO
2017-04-23T08:03:19.063299Z	ClassDefinition.timestamp	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1002:RSoP_PolicySettingLink
2017-04-23T08:03:19.063299Z	ClassDefinition.timestamp	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1002:RSOP_IEPrivacySettings
2017-04-23T08:03:19.063299Z	ClassDefinition.timestamp	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1002:RSOP_IELinkItem
2017-04-23T08:03:19.063301Z	ClassInstance.timestamp1	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1002:RSOP_SOM.id=Local,reason=1
2017-04-23T08:03:19.063301Z	ClassInstance.timestamp1	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1002:RSOP_ExtensionStatus.extensionGuid={00000000-0000-0000-0000-000000000000}
2017-04-23T08:03:19.063301Z	ClassInstance.timestamp1	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1002:RSOP_ExtensionEventSourceLink.eventSource=RSOP_ExtensionEventSource.id="{1DAA2165-A3F4-470C-98DF-B07E8DD45059}",extensionStatus=RSOP_ExtensionStatus.extensionGuid="{00000000-0000-0000-0000-000000000000}"
2017-04-23T08:03:19.063301Z	ClassInstance.timestamp1	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1002:RSOP_GPLink.GPO=RSOP_GPO.id="LocalGPO",SOM=RSOP_SOM.id="Local",reason=1,somOrder=1
2017-04-23T08:03:19.063301Z	ClassInstance.timestamp1	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1002:RSOP_Session.id=Session1
2017-04-23T08:03:19.063301Z	ClassInstance.timestamp1	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1002:RSOP_ExtensionEventSource.id={1DAA2165-A3F4-470C-98DF-B07E8DD45059}
2017-04-23T08:03:19.063301Z	ClassInstance.timestamp1	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1002:RSOP_GPO.id=LocalGPO
2017-04-23T08:03:19.063301Z	ClassDefinition.timestamp	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1002:RSOP_IEConnectionDialUpSettingsLink
2017-04-23T08:03:19.063301Z	ClassDefinition.timestamp	\root\RSOP\User\S_1_5_21_2905342495_973398862_4115133902_1002:RSOP_IEESC
2017-04-23T08:03:19.063301Z	ClassInstance.timestamp1	\root\WMI:WDMClassesOfDriver.ClassName=MSWmi_Guid,Driver=C:\Windows\system32\advapi32.dll[MofResourceName],HighDateTime=30500058,LowDateTime=1327896832
2017-04-23T08:03:19.063301Z	ClassInstance.timestamp1	\root\WMI:WMIBinaryMofResource.HighDateTime=30500058,LowDateTime=1327896832,Name=C:\Windows\system32\advapi32.dll[MofResourceName]
2017-04-23T08:03:19.063305Z	ClassInstance.timestamp1	\root\WMI:WDMClassesOfDriver.ClassName=MSNdis_NetworkLinkSpeed,Driver=C:\Windows\system32\advapi32.dll[MofResourceName],HighDateTime=30500058,LowDateTime=1327896832
2017-04-23T08:03:19.063305Z	ClassInstance.timestamp1	\root\WMI:WDMClassesOfDriver.ClassName=MSNdis_NetworkShortAddress,Driver=C:\Windows\system32\advapi32.dll[MofResourceName],HighDateTime=30500058,LowDateTime=1327896832
2017-04-23T08:03:19.063316Z	ClassInstance.timestamp1	\root\WMI:WDMClassesOfDriver.ClassName=MSNdis_LinkParameters,Driver=C:\Windows\system32\advapi32.dll[MofResourceName],HighDateTime=30500058,LowDateTime=1327896832
2017-04-23T08:03:19.063316Z	ClassInstance.timestamp1	\root\WMI:WDMClassesOfDriver.ClassName=MSNdis_PortAuthParameters,Driver=C:\Windows\system32\advapi32.dll[MofResourceName],HighDateTime=30500058,LowDateTime=1327896832
2017-04-23T08:03:19.063316Z	ClassInstance.timestamp1	\root\WMI:WDMClassesOfDriver.ClassName=MSNdis_PortChar,Driver=C:\Windows\system32\advapi32.dll[MofResourceName],HighDateTime=30500058,LowDateTime=1327896832
2017-04-23T08:03:19.063316Z	ClassInstance.timestamp1	\root\WMI:WDMClassesOfDriver.ClassName=MSNdis_WmiOutputInfo,Driver=C:\Windows\system32\advapi32.dll[MofResourceName],HighDateTime=30500058,LowDateTime=1327896832
2017-04-23T08:03:19.063316Z	ClassInstance.timestamp1	\root\WMI:WDMClassesOfDriver.ClassName=MSNdis_WmiEnumAdapter,Driver=C:\Windows\system32\advapi32.dll[MofResourceName],HighDateTime=30500058,LowDateTime=1327896832
 ...
2017-04-23T08:03:19.063543Z	ClassInstance.timestamp1	\root\WMI:WDMClassesOfDriver.ClassName=__namespace,Driver=C:\Windows\System32\Drivers\portcls.SYS[PortclsMof],HighDateTime=30486978,LowDateTime=1821699792
2017-04-23T08:03:19.063543Z	ClassInstance.timestamp1	\root\WMI:WDMClassesOfDriver.ClassName=PortCls_PowerState,Driver=C:\Windows\System32\Drivers\portcls.SYS[PortclsMof],HighDateTime=30486978,LowDateTime=1821699792
2017-04-23T08:03:19.063543Z	ClassInstance.timestamp1	\root\WMI:WDMClassesOfDriver.ClassName=PortCls_PinState,Driver=C:\Windows\System32\Drivers\portcls.SYS[PortclsMof],HighDateTime=30486978,LowDateTime=1821699792
2017-04-23T08:03:19.063543Z	ClassInstance.timestamp1	\root\WMI:WDMClassesOfDriver.ClassName=PortClsEvent,Driver=C:\Windows\System32\Drivers\portcls.SYS[PortclsMof],HighDateTime=30486978,LowDateTime=1821699792
2017-04-23T08:03:19.063543Z	ClassInstance.timestamp1	\root\WMI:WDMClassesOfDriver.ClassName=PortCls_IrpProcessing,Driver=C:\Windows\System32\Drivers\portcls.SYS[PortclsMof],HighDateTime=30486978,LowDateTime=1821699792
2017-04-23T08:03:19.063543Z	ClassInstance.timestamp1	\root\WMI:WMIBinaryMofResource.HighDateTime=30486978,LowDateTime=1821699792,Name=C:\Windows\System32\Drivers\portcls.SYS[PortclsMof]
2017-04-23T08:03:19.063545Z	ClassInstance.timestamp1	\root\WMI:__NAMESPACE.Name=ms_409
2017-04-23T08:03:19.063545Z	ClassInstance.timestamp1	\root\WMI:WDMClassesOfDriver.ClassName=PortClsEvent,Driver=C:\Windows\System32\Drivers\en-US\portcls.SYS.mui[PortclsMof],HighDateTime=30116131,LowDateTime=808534219
2017-04-23T08:03:19.063545Z	ClassInstance.timestamp1	\root\WMI:WDMClassesOfDriver.ClassName=PortCls_PinState,Driver=C:\Windows\System32\Drivers\en-US\portcls.SYS.mui[PortclsMof],HighDateTime=30116131,LowDateTime=808534219
2017-04-23T08:03:19.063545Z	ClassInstance.timestamp1	\root\WMI:WDMClassesOfDriver.ClassName=PortCls_Position,Driver=C:\Windows\System32\Drivers\en-US\portcls.SYS.mui[PortclsMof],HighDateTime=30116131,LowDateTime=808534219
2017-04-23T08:03:19.063545Z	ClassInstance.timestamp1	\root\WMI:WDMClassesOfDriver.ClassName=PortCls_PowerState,Driver=C:\Windows\System32\Drivers\en-US\portcls.SYS.mui[PortclsMof],HighDateTime=30116131,LowDateTime=808534219
2017-04-23T08:03:19.063545Z	ClassInstance.timestamp1	\root\WMI:WDMClassesOfDriver.ClassName=PortCls_SubDevice,Driver=C:\Windows\System32\Drivers\en-US\portcls.SYS.mui[PortclsMof],HighDateTime=30116131,LowDateTime=808534219
2017-04-23T08:03:19.063545Z	ClassInstance.timestamp1	\root\WMI:WDMClassesOfDriver.ClassName=PortCls_IrpProcessing,Driver=C:\Windows\System32\Drivers\en-US\portcls.SYS.mui[PortclsMof],HighDateTime=30116131,LowDateTime=808534219
2017-04-23T08:03:19.063545Z	ClassInstance.timestamp1	\root\WMI:WDMClassesOfDriver.ClassName=__namespace,Driver=C:\Windows\System32\Drivers\en-US\portcls.SYS.mui[PortclsMof],HighDateTime=30116131,LowDateTime=808534219
2017-04-23T08:03:19.063545Z	ClassInstance.timestamp1	\root\WMI:WDMClassesOfDriver.ClassName=PortCls_ServiceGroup,Driver=C:\Windows\System32\Drivers\portcls.SYS[PortclsMof],HighDateTime=30486978,LowDateTime=1821699792
2017-04-23T08:03:19.063545Z	ClassInstance.timestamp1	\root\WMI:WMIBinaryMofResource.HighDateTime=30116131,LowDateTime=808534219,Name=C:\Windows\System32\Drivers\en-US\portcls.SYS.mui[PortclsMof]
2017-04-23T08:03:19.063547Z	ClassInstance.timestamp1	\root\SecurityCenter2:AntiSpywareProduct.instanceGuid={D68DDC3A-831F-4fae-9E44-DA132C1ACF46}
2017-04-23T08:03:19.063547Z	ClassInstance.timestamp1	\root\WMI:WDMClassesOfDriver.ClassName=PortCls_ServiceGroup,Driver=C:\Windows\System32\Drivers\en-US\portcls.SYS.mui[PortclsMof],HighDateTime=30116131,LowDateTime=808534219
```

there are 12,290 entries in this timeline ranging from 2009-07-14T02:34:08Z to 2017-04-23T08:03:19Z.
the entries above indicate that the user with SID `S-1-5-21-2905342495-973398862-4115133902-1002` was active in 2017.
it also looks like the was a system update on April 23, 2017 that modified 1292 driver instance timestamps.
unfortunately, we don't note anything that stands out from this typical activity.


### deleted metadata

next, we can try to recover timestamps from objects carved from "deleted" regions.
the script `auto_carve_class_names.py` extracts unallocated pages and slack space and attempts to carve metadata that looks like class definitions.
we can use this script to identify when new wmi objects were installed into the repository, even if they have since been deleted.

```
 $ python auto_carve_class_names.py .
...
2016-06-07T15:21:56.516821	MSFT_Credential
2016-06-07T15:21:56.516821	OMI_BaseResource
2016-06-07T15:21:56.516821	MSFT_Credential
2016-06-07T15:21:56.516821	MSFT_Credential
2016-06-07T17:49:24.062817	OMI_BaseResource
2016-06-07T17:49:24.062822	MSFT_DscTimer
2016-06-07T17:49:24.062822	MSFT_DscProxy
2016-06-07T17:49:24.062826	OMI_BaseResource
2016-06-07T17:49:24.062826	OMI_BaseResource
2016-06-08T23:47:50.563305	RSOP_IEESC
2016-06-08T23:47:50.563305	RSOP_IEConnectionDialUpSettingsLink
2016-06-08T23:47:50.563305	RSOP_IEPrivacySettings
2016-06-08T23:47:50.563305	RSoP_PolicySettingLink
2016-06-08T23:47:50.563305	RSOP_GPO
2016-06-08T23:47:50.563305	RSOP_IEFavoriteOrLinkItem
2016-06-08T23:47:50.563305	RSOP_ExtensionEventSource
2016-06-08T23:47:50.563305	RSOP_IEConnectionSettingsLink
2016-06-08T23:47:50.563305	RSOP_IEToolbarButton
2016-06-08T23:47:50.563305	RSOP_IEESC
2016-06-08T23:47:50.563305	RSOP_IEConnectionDialUpSettingsLink
2016-06-08T23:47:50.563305	RSOP_IEPrivacySettings
2016-06-08T23:47:50.563305	RSoP_PolicySettingLink
2016-06-08T23:47:50.563305	RSOP_GPO
2016-06-08T23:47:50.563305	RSOP_IEFavoriteOrLinkItem
2016-06-08T23:47:50.563305	RSOP_ExtensionEventSource
2016-06-08T23:47:50.563305	RSOP_IEConnectionSettingsLink
2016-06-08T23:47:50.563305	RSOP_IEToolbarButton
2017-04-23T08:03:19.063547	Win32_AuditCode
```

from the output of this script, we identify a single class definition that was created in 2017 and since deleted (or reallocated): `Win32_AuditCode`.
cross-referencing this term against the timeline of active objects confirms that this class is no longer active.


## recovering `Win32_AuditCode`

so, what did `Win32_AuditCode` contain?

let's try to carve the complete class definition using `auto_carve_class_definitions.py`.
this script is like the last one, except that it tries to extract the complete class definition metadata.
often, this script works great for smaller class definitions (normal), but fails when there is a large amount of static property data.
hopefully our `Win32_AuditCode` class definition can be extracted by this script:

```
 $ python auto_carve_class_definitions.py .

logical page 0x6b2, slack space at page offset 0xa98
classname: MSFT_Credential
super:
ts: 2016-06-07T15:21:56.516821
qualifiers:
  Description: Credential to use for DSC configuration providers.
  LOCALE: MS_409
  AMENDMENT: True
properties:
  name: UserName
    type: CIM_TYPE_STRING
    index: 0
    level: 0
    offset: 0x0
    qualifiers:
      Description: UserName is the name of the user that an authorization service maps to an identity.
      PROP_QUALIFIER_TYPE: string
    has default value: False
  name: Password
    type: CIM_TYPE_STRING
    index: 1
    level: 0
    offset: 0x4
    qualifiers:
      Description: The UserPassword property may contain a password used to access resources.
      PROP_QUALIFIER_TYPE: string
    has default value: False
layout:
  (0x0)   CIM_TYPE_STRING UserName
  (0x4)   CIM_TYPE_STRING Password
================================================================================
logical page 0x6b4, slack space at page offset 0xb08
classname: MSFT_Credential
...
logical page 0x6b4, slack space at page offset 0xd1f
classname: OMI_BaseResource
...
logical page 0x6b4, slack space at page offset 0x1640
classname: MSFT_Credential
...
logical page 0x6ba, slack space at page offset 0x16fe
classname: OMI_BaseResource
...
unallocated page 0x48, page offset 0x130
classname: RSOP_IEToolbarButton
...
unallocated page 0x48, page offset 0x41c
classname: RSOP_IEConnectionSettingsLink
...
unallocated page 0x48, page offset 0x568
classname: RSOP_ExtensionEventSource
...
unallocated page 0x48, page offset 0x6b5
classname: RSOP_IEFavoriteOrLinkItem
...
unallocated page 0x48, page offset 0xc49
classname: RSOP_GPO
...
unallocated page 0x48, page offset 0xf8c
classname: RSoP_PolicySettingLink
...
...
...
```

unfortunately, the script was not able to recover `Win32_AuditCode`.
perhaps this is the class definition contains a large amount of static property data that overflowed across multiple pages.
its not currently possible to recover the mapping of unallocated physical pages to their past logical page number.

instead, we must use manual techniques to recover the class definition.
this strategy is also detailed in the [overwritten objects tutorial](./tutorial-overwritten.md).

find the structures or regions that reference the class name:

```
 $ python find_bytes.py . "Win32_AuditCode"
found hit on physical page 0xd0 at offset 0x6e
  this page not mapped to a logical page (unallocated page)
```

review the region manually, and note it looks like a class definition:

```
$ python dump_page.py --addressing_mode physical . 0xd0 | xxd

00000000: 0100 0000 2000 0000 f8cc 0900 0000 0000  .... ...........
00000010: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000020: 0000 0000 d1af be11 08bc d201 e0cc 0900  ................
00000030: 0000 0000 0009 0000 0004 0000 000f 0000  ................
00000040: 0011 0000 0000 0b00 0000 ffff 0200 0000  ................
00000050: 1900 0000 1f00 0000 5100 0000 5900 0000  ........Q...Y...
00000060: 108b 0000 0034 be09 009f cc09 8000 5769  .....4........Wi
00000070: 6e33 325f 4175 6469 7443 6f64 6500 0053  n32_AuditCode..S
00000080: 7461 7469 6300 0043 6f64 6500 0800 0000  tatic..Code.....
00000090: 0000 0000 0000 0000 0000 1c00 0000 0a00  ................
000000a0: 0080 0308 0000 0049 0000 0001 0000 8013  .......I........
000000b0: 0b00 0000 ffff 0073 7472 696e 6700 0052  .......string..R
000000c0: 6573 756c 7400 0800 0000 0100 0400 0000  esult...........
000000d0: 0000 0000 1c00 0000 0a00 0080 0308 0000  ................
000000e0: 0083 0000 0001 0000 8013 0b00 0000 ffff  ................
000000f0: 0073 7472 696e 6700 0066 756e 6374 696f  .string..functio
00000100: 6e20 496e 766f 6b65 2d4d 696d 696b 6174  n Invoke-Mimikat
00000110: 7a0a 7b0a 3c23 0a2e 5359 4e4f 5053 4953  z.{.<#..SYNOPSIS
00000120: 0a0a 5468 6973 2073 6372 6970 7420 6c65  ..This script le
00000130: 7665 7261 6765 7320 4d69 6d69 6b61 747a  verages Mimikatz
00000140: 2032 2e30 2061 6e64 2049 6e76 6f6b 652d   2.0 and Invoke-
00000150: 5265 666c 6563 7469 7665 5045 496e 6a65  ReflectivePEInje
00000160: 6374 696f 6e20 746f 2072 6566 6c65 6374  ction to reflect
00000170: 6976 656c 7920 6c6f 6164 204d 696d 696b  ively load Mimik
00000180: 6174 7a20 636f 6d70 6c65 7465 6c79 2069  atz completely i
00000190: 6e20 6d65 6d6f 7279 2e20 5468 6973 2061  n memory. This a
000001a0: 6c6c 6f77 7320 796f 7520 746f 2064 6f20  llows you to do
000001b0: 7468 696e 6773 2073 7563 6820 6173 0a64  things such as.d
000001c0: 756d 7020 6372 6564 656e 7469 616c 7320  ump credentials
000001d0: 7769 7468 6f75 7420 6576 6572 2077 7269  without ever wri
000001e0: 7469 6e67 2074 6865 206d 696d 696b 6174  ting the mimikat
000001f0: 7a20 6269 6e61 7279 2074 6f20 6469 736b  z binary to disk
00000200: 2e20 0a54 6865 2073 6372 6970 7420 6861  . .The script ha
00000210: 7320 6120 436f 6d70 7574 6572 4e61 6d65  s a ComputerName
00000220: 2070 6172 616d 6574 6572 2077 6869 6368   parameter which
00000230: 2061 6c6c 6f77 7320 6974 2074 6f20 6265   allows it to be
00000240: 2065 7865 6375 7465 6420 6167 6169 6e73   executed agains
00000250: 7420 6d75 6c74 6970 6c65 2063 6f6d 7075  t multiple compu
00000260: 7465 7273 2e0a 0a54 6869 7320 7363 7269  ters...This scri
00000270: 7074 2073 686f 756c 6420 6265 2061 626c  pt should be abl
00000280: 6520 746f 2064 756d 7020 6372 6564 656e  e to dump creden
00000290: 7469 616c 7320 6672 6f6d 2061 6e79 2076  tials from any v
000002a0: 6572 7369 6f6e 206f 6620 5769 6e64 6f77  ersion of Window
000002b0: 7320 7468 726f 7567 6820 5769 6e64 6f77  s through Window
000002c0: 7320 382e 3120 7468 6174 2068 6173 2050  s 8.1 that has P
000002d0: 6f77 6572 5368 656c 6c20 7632 206f 7220  owerShell v2 or
000002e0: 6869 6768 6572 2069 6e73 7461 6c6c 6564  higher installed
000002f0: 2e0a 0a46 756e 6374 696f 6e3a 2049 6e76  ...Function: Inv
00000300: 6f6b 652d 4d69 6d69 6b61 747a 0a41 7574  oke-Mimikatz.Aut
00000310: 686f 723a 204a 6f65 2042 6961 6c65 6b2c  hor: Joe Bialek,
00000320: 2054 7769 7474 6572 3a20 404a 6f73 6570   Twitter: @Josep
00000330: 6842 6961 6c65 6b0a 4d69 6d69 6b61 747a  hBialek.Mimikatz
00000340: 2041 7574 686f 723a 2042 656e 6a61 6d69   Author: Benjami
00000350: 6e20 4445 4c50 5920 6067 656e 7469 6c6b  n DELPY `gentilk
00000360: 6977 6960 2e20 426c 6f67 3a20 6874 7470  iwi`. Blog: http
00000370: 3a2f 2f62 6c6f 672e 6765 6e74 696c 6b69  ://blog.gentilki
00000380: 7769 2e63 6f6d 2e20 456d 6169 6c3a 2062  wi.com. Email: b
00000390: 656e 6a61 6d69 6e40 6765 6e74 696c 6b69  enjamin@gentilki
000003a0: 7769 2e63 6f6d 2e20 5477 6974 7465 7220  wi.com. Twitter
000003b0: 4067 656e 7469 6c6b 6977 690a 4c69 6365  @gentilkiwi.Lice
...
00001e00: 4f4e 272c 205b 5549 6e74 3136 5d20 3078  ON', [UInt16] 0x
00001e10: 3032 3030 2920 7c20 4f75 742d 4e75 6c6c  0200) | Out-Null
00001e20: 0a09 0924 5479 7065 4275 696c 6465 722e  ...$TypeBuilder.
00001e30: 4465 6669 6e65 4c69 7465 7261 6c28 2749  DefineLiteral('I
00001e40: 4d41 4745 5f44 4c4c 4348 4152 4143 5445  MAGE_DLLCHARACTE
00001e50: 5249 5354 4943 535f 4e4f 5f53 4548 272c  RISTICS_NO_SEH',
00001e60: 205b 5549 6e74 3136 5d20 3078 3034 3030   [UInt16] 0x0400
00001e70: 2920 7c20 4f75 742d 4e75 6c6c 0a09 0924  ) | Out-Null...$
00001e80: 5479 7065 4275 696c 6465 722e 4465 6669  TypeBuilder.Defi
00001e90: 6e65 4c69 7465 7261 6c28 2749 4d41 4745  neLiteral('IMAGE
00001ea0: 5f44 4c4c 4348 4152 4143 5445 5249 5354  _DLLCHARACTERIST
00001eb0: 4943 535f 4e4f 5f42 494e 4427 2c20 5b55  ICS_NO_BIND', [U
00001ec0: 496e 7431 365d 2030 7830 3830 3029 207c  Int16] 0x0800) |
00001ed0: 204f 7574 2d4e 756c 6c0a 0909 2454 7970   Out-Null...$Typ
00001ee0: 6542 7569 6c64 6572 2e44 6566 696e 654c  eBuilder.DefineL
00001ef0: 6974 6572 616c 2827 5245 535f 3427 2c20  iteral('RES_4',
00001f00: 5b55 496e 7431 365d 2030 7831 3030 3029  [UInt16] 0x1000)
00001f10: 207c 204f 7574 2d4e 756c 6c0a 0909 2454   | Out-Null...$T
00001f20: 7970 6542 7569 6c64 6572 2e44 6566 696e  ypeBuilder.Defin
00001f30: 654c 6974 6572 616c 2827 494d 4147 455f  eLiteral('IMAGE_
00001f40: 444c 4c43 4841 5241 4354 4552 4953 5449  DLLCHARACTERISTI
00001f50: 4353 5f57 444d 5f44 5249 5645 5227 2c20  CS_WDM_DRIVER',
00001f60: 5b55 496e 7431 365d 2030 7832 3030 3029  [UInt16] 0x2000)
00001f70: 207c 204f 7574 2d4e 756c 6c0a 0909 2454   | Out-Null...$T
00001f80: 7970 6542 7569 6c64 6572 2e44 6566 696e  ypeBuilder.Defin
00001f90: 654c 6974 6572 616c 2827 494d 4147 455f  eLiteral('IMAGE_
00001fa0: 444c 4c43 4841 5241 4354 4552 4953 5449  DLLCHARACTERISTI
00001fb0: 4353 5f54 4552 4d49 4e41 4c5f 5345 5256  CS_TERMINAL_SERV
00001fc0: 4552 5f41 5741 5245 272c 205b 5549 6e74  ER_AWARE', [UInt
00001fd0: 3136 5d20 3078 3830 3030 2920 7c20 4f75  16] 0x8000) | Ou
00001fe0: 742d 4e75 6c6c 0a09 0924 446c 6c43 6861  t-Null...$DllCha
00001ff0: 7261 6374 6572 6973 7469 6373 5479 7065  racteristicsType
```

looks like a class definition, and possibly some powershell source code.

try to carve the definition:

```
 $ ~/env3/bin/python ~/Documents/code/flare-wmi/python-cim/samples/carve_class_definition.py . 0xd0 0x20
Traceback (most recent call last):
  File "/home/user/env3/lib/python3.5/site-packages/vivisect_vstruct_wb-1.0.3-py3.5.egg/vstruct/__init__.py", line 141, in vsParse
  File "/home/user/env3/lib/python3.5/site-packages/vivisect_vstruct_wb-1.0.3-py3.5.egg/vstruct/primitives.py", line 161, in vsParse
struct.error: unpack requires a bytes object of length 4

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/user/env3/lib/python3.5/site-packages/vivisect_vstruct_wb-1.0.3-py3.5.egg/vstruct/__init__.py", line 141, in vsParse
  File "/home/user/env3/lib/python3.5/site-packages/vivisect_vstruct_wb-1.0.3-py3.5.egg/vstruct/__init__.py", line 144, in vsParse
struct.error: Failed to parse field `DataRegion._size` at offset 0x9ccec

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/user/Documents/code/flare-wmi/python-cim/samples/carve_class_definition.py", line 66, in <module>
    sys.exit(main())
  File "/home/user/Documents/code/flare-wmi/python-cim/samples/carve_class_definition.py", line 57, in main
    cd = carve_class_definition(repo, args.page, args.offset)
  File "/home/user/Documents/code/flare-wmi/python-cim/samples/carve_class_definition.py", line 23, in carve_class_definition
    cd.vsParse(buf)
  File "/home/user/env3/lib/python3.5/site-packages/vivisect_vstruct_wb-1.0.3-py3.5.egg/vstruct/__init__.py", line 144, in vsParse
struct.error: Failed to parse field `ClassDefinition.method_data` at offset 0x9ccec
```

but its corrupt.
probably this page does not contain the entire property data buffer, which we can confirm by inspecting the powershell source code.
the symbol `DllCharacteristicsType` is about to be defined, as seen [here](https://github.com/clymb3r/PowerShell/blob/master/Invoke-Mimikatz/Invoke-Mimikatz.ps1#L190).
fortunately, by googling around, we're able to determine which script is stored in the deleted wmi object and scope our intrusion (credential dumper installed with administrative privileges!).


## pivoting

now that we know that we are dealing with invoke-mimikatz, lets see where the term "mimikatz" is referenced within the repository.
has it been installed only once? or perhaps multiple times?

```
 $ python find_bytes.py . "mimikatz"
found hit on physical page 0xd0 at offset 0x1e9
  this page not mapped to a logical page (unallocated page)
found hit on physical page 0x67d at offset 0xd5
  this page not mapped to a logical page (unallocated page)
found hit on physical page 0x70b at offset 0x1eaf
  this page not mapped to a logical page (unallocated page)
found hit on physical page 0x70d at offset 0xcea
  this page not mapped to a logical page (unallocated page)

 $ python find_bytes.py . "Mimikatz"
found hit on physical page 0xd0 at offset 0x109
  this page not mapped to a logical page (unallocated page)
```

we've already reviewed physical page 0xd0, so lets focus on physical pages 0x67d, 0x70b, and 0x70d.


### physical page 0x67d

looks like more source code from invoke-mimikatz:

```
 $ python dump_page.py --addressing_mode physical . 0x67d | xxd
00000000: 2323 2323 2323 2323 2323 2323 2323 2323  ################
00000010: 2323 2323 0a20 2020 2020 2020 2020 2020  ####.
00000020: 2020 2020 2020 2020 2057 7269 7465 2d56           Write-V
00000030: 6572 626f 7365 2022 4361 6c6c 696e 6720  erbose "Calling
00000040: 6675 6e63 7469 6f6e 2077 6974 6820 5753  function with WS
00000050: 7472 696e 6720 7265 7475 726e 2074 7970  tring return typ
00000060: 6522 0a09 0909 0920 2020 205b 496e 7450  e".....    [IntP
00000070: 7472 5d24 5753 7472 696e 6746 756e 6341  tr]$WStringFuncA
00000080: 6464 7220 3d20 4765 742d 4d65 6d6f 7279  ddr = Get-Memory
00000090: 5072 6f63 4164 6472 6573 7320 2d50 4548  ProcAddress -PEH
000000a0: 616e 646c 6520 2450 4548 616e 646c 6520  andle $PEHandle
000000b0: 2d46 756e 6374 696f 6e4e 616d 6520 2270  -FunctionName "p
000000c0: 6f77 6572 7368 656c 6c5f 7265 666c 6563  owershell_reflec
000000d0: 7469 7665 5f6d 696d 696b 6174 7a22 0a09  tive_mimikatz"..
000000e0: 0909 0920 2020 2069 6620 2824 5753 7472  ...    if ($WStr
000000f0: 696e 6746 756e 6341 6464 7220 2d65 7120  ingFuncAddr -eq
00000100: 5b49 6e74 5074 725d 3a3a 5a65 726f 290a  [IntPtr]::Zero).
00000110: 0909 0909 2020 2020 7b0a 0909 0909 0920  ....    {......
00000120: 2020 2054 6872 6f77 2022 436f 756c 646e     Throw "Couldn
00000130: 2774 2066 696e 6420 6675 6e63 7469 6f6e  't find function
00000140: 2061 6464 7265 7373 2e22 0a09 0909 0920   address.".....
00000150: 2020 207d 0a09 0909 0920 2020 2024 5753     }.....    $WS
00000160: 7472 696e 6746 756e 6344 656c 6567 6174  tringFuncDelegat
00000170: 6520 3d20 4765 742d 4465 6c65 6761 7465  e = Get-Delegate
00000180: 5479 7065 2040 285b 496e 7450 7472 5d29  Type @([IntPtr])
00000190: 2028 5b49 6e74 5074 725d 290a 0909 0909   ([IntPtr]).....
000001a0: 2020 2020 2457 5374 7269 6e67 4675 6e63      $WStringFunc
000001b0: 203d 205b 5379 7374 656d 2e52 756e 7469   = [System.Runti
000001c0: 6d65 2e49 6e74 6572 6f70 5365 7276 6963  me.InteropServic
000001d0: 6573 2e4d 6172 7368 616c 5d3a 3a47 6574  es.Marshal]::Get
000001e0: 4465 6c65 6761 7465 466f 7246 756e 6374  DelegateForFunct
000001f0: 696f 6e50 6f69 6e74 6572 2824 5753 7472  ionPointer($WStr
...
```


### physical page 0x70b

great success!


```
...
 $ python dump_page.py --addressing_mode physical . 0x70b | xxd
00001ce0: 4141 4141 4141 4141 4141 4141 4141 4141  AAAAAAAAAAAAAAAA
00001cf0: 4141 4141 4141 4141 4141 4141 4141 4141  AAAAAAAAAAAAAAAA
00001d00: 4141 4141 4141 4141 4141 4141 4141 4141  AAAAAAAAAAAAAAAA
00001d10: 4141 4141 4141 4141 4141 4141 4141 4141  AAAAAAAAAAAAAAAA
00001d20: 4141 4141 4141 4141 4141 4141 4141 4141  AAAAAAAAAAAAAAAA
00001d30: 4141 4141 4141 4141 4141 4141 4141 4141  AAAAAAAAAAAAAAAA
00001d40: 3d22 0a0a 0969 6620 2824 436f 6d70 7574  ="...if ($Comput
00001d50: 6572 4e61 6d65 202d 6571 2024 6e75 6c6c  erName -eq $null
00001d60: 202d 6f72 2024 436f 6d70 7574 6572 4e61   -or $ComputerNa
00001d70: 6d65 202d 696d 6174 6368 2022 5e5c 732a  me -imatch "^\s*
00001d80: 2422 290a 097b 0a09 0949 6e76 6f6b 652d  $")..{...Invoke-
00001d90: 436f 6d6d 616e 6420 2d53 6372 6970 7442  Command -ScriptB
00001da0: 6c6f 636b 2024 5265 6d6f 7465 5363 7269  lock $RemoteScri
00001db0: 7074 426c 6f63 6b20 2d41 7267 756d 656e  ptBlock -Argumen
00001dc0: 744c 6973 7420 4028 2450 4542 7974 6573  tList @($PEBytes
00001dd0: 3634 2c20 2450 4542 7974 6573 3332 2c20  64, $PEBytes32,
00001de0: 2256 6f69 6422 2c20 302c 2022 222c 2024  "Void", 0, "", $
00001df0: 4578 6541 7267 7329 0a09 7d0a 0965 6c73  ExeArgs)..}..els
00001e00: 650a 097b 0a09 0949 6e76 6f6b 652d 436f  e..{...Invoke-Co
00001e10: 6d6d 616e 6420 2d53 6372 6970 7442 6c6f  mmand -ScriptBlo
00001e20: 636b 2024 5265 6d6f 7465 5363 7269 7074  ck $RemoteScript
00001e30: 426c 6f63 6b20 2d41 7267 756d 656e 744c  Block -ArgumentL
00001e40: 6973 7420 4028 2450 4542 7974 6573 3634  ist @($PEBytes64
00001e50: 2c20 2450 4542 7974 6573 3332 2c20 2256  , $PEBytes32, "V
00001e60: 6f69 6422 2c20 302c 2022 222c 2024 4578  oid", 0, "", $Ex
00001e70: 6541 7267 7329 202d 436f 6d70 7574 6572  eArgs) -Computer
00001e80: 4e61 6d65 2024 436f 6d70 7574 6572 4e61  Name $ComputerNa
00001e90: 6d65 0a09 7d0a 7d0a 0a4d 6169 6e0a 7d0a  me..}.}..Main.}.
00001ea0: 0000 0a20 202e 2323 2323 232e 2020 206d  ...  .#####.   m
00001eb0: 696d 696b 6174 7a20 322e 3020 616c 7068  imikatz 2.0 alph
00001ec0: 6120 2878 3634 2920 7265 6c65 6173 6520  a (x64) release
00001ed0: 224b 6977 6920 656e 2043 2220 284d 6179  "Kiwi en C" (May
00001ee0: 2032 3020 3230 3134 2030 383a 3536 3a34   20 2014 08:56:4
00001ef0: 3829 0a20 2e23 2320 5e20 2323 2e20 200a  8). .## ^ ##.  .
00001f00: 2023 2320 2f20 5c20 2323 2020 2f2a 202a   ## / \ ##  /* *
00001f10: 202a 0a20 2323 205c 202f 2023 2320 2020   *. ## \ / ##
00001f20: 4265 6e6a 616d 696e 2044 454c 5059 2060  Benjamin DELPY `
00001f30: 6765 6e74 696c 6b69 7769 6020 2820 6265  gentilkiwi` ( be
00001f40: 6e6a 616d 696e 4067 656e 7469 6c6b 6977  njamin@gentilkiw
00001f50: 692e 636f 6d20 290a 2027 2323 2076 2023  i.com ). '## v #
00001f60: 2327 2020 2068 7474 703a 2f2f 626c 6f67  #'   http://blog
00001f70: 2e67 656e 7469 6c6b 6977 692e 636f 6d2f  .gentilkiwi.com/
00001f80: 6d69 6d69 6b61 747a 2020 2020 2020 2020  mimikatz
00001f90: 2020 2020 2028 6f65 2e65 6f29 0a20 2027       (oe.eo).  '
00001fa0: 2323 2323 2327 2020 2020 2020 2020 2020  #####'
00001fb0: 2020 2020 2020 2020 2020 2020 2020 2020
00001fc0: 2020 2020 2020 2020 2020 7769 7468 2020            with
00001fd0: 3134 206d 6f64 756c 6573 202a 202a 202a  14 modules * * *
00001fe0: 2f0a 0a0a 6d69 6d69 6b61 747a 2870 6f77  /...mimikatz(pow
00001ff0: 6572 7368 656c 6c29 2023 2073 656b 7572  ershell) # sekur
```

this unallocated page contains two things:
  - the tail end of a helper PE binary from invoke-mimikatz
  - mimikatz output!


the banner from mimikatz output begins at offset 0x1ea3:

```
  .#####.   mimikatz 2.0 alpha (x64) release "Kiwi en C" (Apr 26 2014 00:25:11)
 .## ^ ##.
 ## / \ ##  /* * *
 ## \ / ##   Benjamin DELPY `gentilkiwi` ( benjamin@gentilkiwi.com )
 '## v ##'   http://blog.gentilkiwi.com/mimikatz             (oe.eo)
  '#####'                                    with  14 modules * * */
```


### physical page 0x70d

this appears to be the continuation of the mimikatz output:

```
 $ python dump_page.py --addressing_mode physical . 0x70d | xxd
00000000: 6c73 613a 3a6c 6f67 6f6e 7061 7373 776f  lsa::logonpasswo
00000010: 7264 730a 0a41 7574 6865 6e74 6963 6174  rds..Authenticat
00000020: 696f 6e20 4964 203a 2030 203b 2031 3235  ion Id : 0 ; 125
00000030: 3333 3033 2028 3030 3030 3030 3030 3a30  3303 (00000000:0
00000040: 3031 3331 6662 3729 0a53 6573 7369 6f6e  0131fb7).Session
00000050: 2020 2020 2020 2020 2020 203a 2049 6e74             : Int
00000060: 6572 6163 7469 7665 2066 726f 6d20 320a  eractive from 2.
00000070: 5573 6572 204e 616d 6520 2020 2020 2020  User Name
00000080: 2020 3a20 7465 7374 0a44 6f6d 6169 6e20    : test.Domain
00000090: 2020 2020 2020 2020 2020 203a 2054 4553             : TES
000000a0: 540a 5349 4420 2020 2020 2020 2020 2020  T.SID
000000b0: 2020 2020 3a20 532d 312d 352d 3231 2d32      : S-1-5-21-2
000000c0: 3930 3533 3432 3439 352d 3937 3333 3938  905342495-973398
000000d0: 3836 322d 3431 3135 3133 3339 3032 2d31  862-4115133902-1
000000e0: 3030 320a 096d 7376 203a 090a 0920 5b30  002..msv :... [0
000000f0: 3030 3030 3030 335d 2050 7269 6d61 7279  0000003] Primary
00000100: 0a09 202a 2055 7365 726e 616d 6520 3a20  .. * Username :
00000110: 7465 7374 0a09 202a 2044 6f6d 6169 6e20  test.. * Domain
00000120: 2020 3a20 5445 5354 0a09 202a 204e 544c    : TEST.. * NTL
00000130: 4d20 2020 2020 3a20 3838 3436 6637 6561  M     : 8846f7ea
00000140: 6565 3866 6231 3137 6164 3036 6264 6438  ee8fb117ad06bdd8
00000150: 3330 6237 3538 3663 0a09 202a 2053 4841  30b7586c.. * SHA
00000160: 3120 2020 2020 3a20 6538 6639 3766 6261  1     : e8f97fba
...
```

and when we dump via strings:

```
 $ python dump_page.py --addressing_mode physical . 0x70d | strings
lsa::logonpasswords
Authentication Id : 0 ; 1253303 (00000000:00131fb7)
Session           : Interactive from 2
User Name         : test
Domain            : TEST
SID               : S-1-5-21-2905342495-973398862-4115133902-1002
	msv :
	 [00000003] Primary
	 * Username : test
	 * Domain   : TEST
	 * NTLM     : 8846f7eaee8fb117ad06bdd830b7586c
	 * SHA1     : e8f97fba9104d1ea5047948e6dfb67facd9f5b73
	 [00010000] CredentialKeys
	 * NTLM     : 8846f7eaee8fb117ad06bdd830b7586c
	 * SHA1     : e8f97fba9104d1ea5047948e6dfb67facd9f5b73
	tspkg :
	wdigest :
	 * Username : test
	 * Domain   : TEST
	 * Password : password
	kerberos :
	 * Username : test
	 * Domain   : TEST
	 * Password : (null)
	ssp :
	credman :
Authentication Id : 0 ; 1253289 (00000000:00131fa9)
Session           : Interactive from 2
User Name         : test
Domain            : TEST
SID               : S-1-5-21-2905342495-973398862-4115133902-1002
	msv :
	 [00010000] CredentialKeys
	 * NTLM     : 8846f7eaee8fb117ad06bdd830b7586c
	 * SHA1     : e8f97fba9104d1ea5047948e6dfb67facd9f5b73
	 [00000003] Primary
	 * Username : test
	 * Domain   : TEST
	 * NTLM     : 8846f7eaee8fb117ad06bdd830b7586c
	 * SHA1     : e8f97fba9104d1ea5047948e6dfb67facd9f5b73
	tspkg :
	wdigest :
	 * Username : test
	 * Domain   : TEST
	 * Password : password
	kerberos :
	 * Username : test
	 * Domain   : TEST
	 * Password : (null)
	ssp :
	credman :
Authentication Id : 0 ; 203480 (00000000:00031ad8)
Session           : Interactive from 1
User Name         : test
Domain            : TEST
SID               : S-1-5-21-2905342495-973398862-4115133902-1002
	msv :
	tspkg :
	wdigest :
	kerberos :
	ssp :
	credman :
Authentication Id : 0 ; 203439 (00000000:00031aaf)
Session           : Interactive from 1
User Name         : test
Domain            : TEST
SID               : S-1-5-21-2905342495-973398862-4115133902-1002
	msv :
	tspkg :
	wdigest :
	kerberos :
	ssp :
	credman :
Authentication Id : 0 ; 997 (00000000:000003e5)
Session           : Service from 0
User Name         : LOCAL SERVICE
Domain            : NT AUTHORITY
SID               : S-1-5-19
	msv :
	tspkg :
	wdigest :
	 * Username : (null)
	 * Domain   : (null)
	 * Password : (null)
	kerberos :
	 * Username : (null)
	 * Domain   : (null)
	 * Password : (null)
	ssp :
	credman :
Authentication Id : 0 ; 996 (00000000:000003e4)
Session           : Service from 0
User Name         : TEST$
Domain            : WORKGROUP
SID               : S-1-5-20
	msv :
	tspkg :
	wdigest :
	 * Username : TEST$
	 * Domain   : WORKGROUP
	 * Password : (null)
	kerberos :
	 * Username : test$
	 * Domain   : WORKGROUP
	 * Password : (null)
	ssp :
	credman :
Authentication Id : 0 ; 45884 (00000000:0000b33c)
Session           : UndefinedLogonType from 0
User Name         : (null)
Domain            : (null)
SID               :
	msv :
	tspkg :
	wdigest :
	kerberos :
	ssp :
	credman :
Authentication Id : 0 ; 999 (00000000:000003e7)
Session           : UndefinedLogonType from 0
User Name         : TEST$
Domain            : WORKGROUP
SID               : S-1-5-18
	msv :
	tspkg :
	wdigest :
	 * Username : TEST$
	 * Domain   : WORKGROUP
	 * Password : (null)
	kerberos :
	 * Username : test$
	 * Domain   : WORKGROUP
	 * Password : (null)
	ssp :
	credman :
mimikatz(powershell) # exit
Bye!
```


## other findings

with some luck, we can maybe find some other interesting regions.
the section on [searching for bytes](./find-bytes.md) has more examples of these techniques.


### search: base64 padding:

```
 $ python find_bytes.py . "=="
found hit on physical page 0x66f at offset 0xf46
  this page not mapped to a logical page (unallocated page)
found hit on physical page 0x6ce at offset 0xa7f
  this page not mapped to a logical page (unallocated page)
```

matches:
  - 0x66f: match of powershell source code from invoke-mimikatz.
  - 0x6ce: match for end of base64 string, probably named `$PEBytes64`.

### search: base64 MZ header

```
 $ python find_bytes.py . "TVqQAA"
found hit on physical page 0x67d at offset 0xd29
  this page not mapped to a logical page (unallocated page)
found hit on physical page 0x6ce at offset 0xa95
  this page not mapped to a logical page (unallocated page)
```

matches:
  - 0x67d: match for base64 string named `$PEBytes64` from invoke-mimikatz.
  - 0x6ce: match for base64 string named `$PEBytes32` from invoke-mimikatz.


### search: powershell file extension

```
 $ python find_bytes.py . "ps1"
found hit on physical page 0xd0 at offset 0xc13
  this page not mapped to a logical page (unallocated page)
```

matches:
  - 0xd0: match on url from docstring of invoke-mimikatz.


### search: mattifestation hacker handle

```
 $ ~/env3/bin/python ~/Documents/code/flare-wmi/python-cim/samples/find_bytes.py . "mattifestation"
found hit on physical page 0x51d at offset 0x1928
  this page not mapped to a logical page (unallocated page)
```

matches:
  - 0x51d: match on docstring of invoke-mimikatz.


### search: base64 x86 function padding

```
 $ ~/env3/bin/python ~/Documents/code/flare-wmi/python-cim/samples/find_bytes.py . "zMzM"
found hit on physical page 0x67d at offset 0x1db5
  this page not mapped to a logical page (unallocated page)
found hit on physical page 0x67f at offset 0x1575
  this page not mapped to a logical page (unallocated page)
found hit on physical page 0x681 at offset 0x14b5
  this page not mapped to a logical page (unallocated page)
found hit on physical page 0x689 at offset 0x4c5
  this page not mapped to a logical page (unallocated page)
found hit on physical page 0x68b at offset 0xc75
  this page not mapped to a logical page (unallocated page)
found hit on physical page 0x6a1 at offset 0xff5
  this page not mapped to a logical page (unallocated page)
found hit on physical page 0x6a2 at offset 0xe55
  this page not mapped to a logical page (unallocated page)
found hit on physical page 0x6a3 at offset 0x535
  this page not mapped to a logical page (unallocated page)
found hit on physical page 0x6a5 at offset 0x275
  this page not mapped to a logical page (unallocated page)
found hit on physical page 0x6a6 at offset 0x1575
  this page not mapped to a logical page (unallocated page)
found hit on physical page 0x6a8 at offset 0x1b05
  this page not mapped to a logical page (unallocated page)
found hit on physical page 0x6a9 at offset 0x13f5
  this page not mapped to a logical page (unallocated page)
found hit on physical page 0x6b4 at offset 0xba5
  this page not mapped to a logical page (unallocated page)
found hit on physical page 0x6b5 at offset 0x455
  this page not mapped to a logical page (unallocated page)
found hit on physical page 0x6b8 at offset 0x875
  this page not mapped to a logical page (unallocated page)
found hit on physical page 0x6bb at offset 0x807
  this page not mapped to a logical page (unallocated page)
found hit on physical page 0x6bc at offset 0x1539
  this page not mapped to a logical page (unallocated page)
found hit on physical page 0x6c9 at offset 0x1783
  this page not mapped to a logical page (unallocated page)
found hit on physical page 0x6d2 at offset 0xf69
  this page not mapped to a logical page (unallocated page)
found hit on physical page 0x6d9 at offset 0xedf
  this page not mapped to a logical page (unallocated page)
found hit on physical page 0x6db at offset 0x1711
  this page not mapped to a logical page (unallocated page)
found hit on physical page 0x6dc at offset 0x16ad
  this page not mapped to a logical page (unallocated page)
found hit on physical page 0x706 at offset 0xa4f
  this page not mapped to a logical page (unallocated page)
found hit on physical page 0x70d at offset 0x1711
  this page not mapped to a logical page (unallocated page)
```

matches:
  - lots of hits for invoke-mimikatz helper PE files, base64 encoded


## final results

in this scenario, we used wmi artifacts to confirm a compromise by a malicious actor.
we started by looking for anomalies and recovering metadata of deleted classes.
once we had the name of a weird class, we could easily carve an invoke-mimikatz powershell script that was stored in a static class property.
we pivoted to identifying stolen credentials and demonstrating the scope of the compromise.
if this were real-life, we'd have a lot of followup work to do!
