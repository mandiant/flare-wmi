function New-AlertTrigger {
<#
.SYNOPSIS

Creates a hashtable that describes an alert trigger.

Author: Matthew Graeber (@mattifestation)
Copyright: 2015 FireEye, Inc.
License: BSD 3-Clause
Required Dependencies: None
Optional Dependencies: None

.DESCRIPTION

New-AlertTrigger creates a hashtable for consumption by the
New-AlertAction function. The hashtable describes the type of item to
trigger off of as well as the trigger condition.

.PARAMETER EventConsumer

Specifies the type of event consumer to trigger off of.
CommandLineEventConsumer and ActiveScriptEventConsumer are the only
supported event consumer types at the moment. It is unlikely that an
attacker will use any other event consumer types.

.PARAMETER StartupCommand

Specifies that an alert should trigger for any of the following
persistence items:

* HKLM\Software\Microsoft\Windows\CurrentVersion\Run
* HKLM\Software\Microsoft\Windows\CurrentVersion\RunOnce
* HKCU\Software\Microsoft\Windows\CurrentVersion\Run
* HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce
* HKU\ProgID\Software\Microsoft\Windows\CurrentVersion\Run
* Current user Startup directory
* All user's Startup directory

WMI has a built-in WMI class - Win32_StartupCommand that captures
the modification of any of these startup items. This is ideal over
some of the limitations imposed by using the -RegistryKey parameter.

.PARAMETER RegistryKey

Specifies that an alert should trigger upon any change to the
specified registry key. Note: Only HKLM registry keys can be
provided. Because event consumer execute in the SYSTEM context, they
do not have access to the HKEY_CLASSES_ROOT and HKEY_CURRENT_USER
hives.

.PARAMETER TriggerType

Specifies the condition by which an event is triggered - i.e. the
creation, modification, or deletion of a persistence item.

.PARAMETER TriggerName

Optionally, specify the name under which the event trigger will
register. Hardcoded names are used in the absence of a specified
trigger name.

.PARAMETER PollingInterval

Optionally, specify the event trigger polling interval in seconds.
New-AlertTrigger defaults to a 60 second polling interval.

.EXAMPLE

$Trigger = New-AlertTrigger -EventConsumer CommandLineEventConsumer -TriggerType Creation

Description
-----------
Trigger upon the creation of a CommandLineEventConsumer.

.EXAMPLE

$Trigger = New-AlertTrigger -EventConsumer ActiveScriptEventConsumer -TriggerType Deletion

Description
-----------
Trigger upon the removal of an ActiveScriptEventConsumer.

.EXAMPLE

$Trigger = New-AlertTrigger -StartupCommand

.EXAMPLE

$Trigger = New-AlertTrigger -RegistryKey HKLM:\SYSTEM\CurrentControlSet\Control\Lsa

Description
-----------
Trigger upon creation, modification, or deletion of any value in the 'Lsa' key.

.OUTPUTS

System.Hashtable

Outputs a Hashtable that describes the WMI event trigger (filter).

.INPUTS

None
#>

    [OutputType([Hashtable])]
    Param (
        [Parameter(Mandatory = $True, ParameterSetName = 'EventConsumer')]
        [ValidateSet('CommandLineEventConsumer', 'ActiveScriptEventConsumer')]
        [String]
        $EventConsumer,

        [Parameter(Mandatory = $True, ParameterSetName = 'StartupCommand')]
        [Switch]
        $StartupCommand,

        [Parameter(Mandatory = $True, ParameterSetName = 'Registry')]
        [ValidateScript({(Test-Path $_) -and ((Get-Item $_)[0] -is [Microsoft.Win32.RegistryKey]) -and ((Get-Item $_)[0].Name.StartsWith('HKEY_LOCAL_MACHINE\'))})]
        [String]
        $RegistryKey,

        [Parameter(ParameterSetName = 'EventConsumer')]
        [Parameter(ParameterSetName = 'StartupCommand')]
        [ValidateSet('Creation', 'Modification', 'Deletion')]
        [String]
        $TriggerType = 'Creation',

        [ValidateNotNullOrEmpty()]
        [String]
        $TriggerName,

        [ValidateRange(1, 86400)]
        [Int]
        $PollingInterval = 60
    )

    $TriggerTable = @{
        'Creation' = '__InstanceCreationEvent'
        'Modification' = '__InstanceModificationEvent'
        'Deletion' = '__InstanceDeletionEvent'
    }

    switch ($PsCmdlet.ParameterSetName) {
        'EventConsumer' {
            switch ($EventConsumer) {
                'CommandLineEventConsumer' {
                    if ($TriggerName) {
                        $Name = $TriggerName
                    } else {
                        $Name = 'CommandLineEventConsumerCreationEvent'
                    }

                    $Result = @{
                        Name = $Name
                        EventNameSpace = 'root\subscription'
                        QueryLanguage = 'WQL'
                        Query = "SELECT * FROM $($TriggerTable[$TriggerType]) WITHIN " +
                            "$PollingInterval WHERE TargetInstance ISA 'CommandLineEventConsumer'"
                    }

                    $Result.PSObject.TypeNames.Insert(0, "WMI.EventTrigger.CommandLineEventConsumer.$TriggerType")
                    return $Result
                }

                'ActiveScriptEventConsumer' {
                    if ($TriggerName) {
                        $Name = $TriggerName
                    } else {
                        $Name = 'ActiveScriptEventConsumerCreationEvent'
                    }

                    $Result = @{
                        Name = $Name
                        EventNameSpace = 'root\subscription'
                        QueryLanguage = 'WQL'
                        Query = "SELECT * FROM $($TriggerTable[$TriggerType]) WITHIN " +
                            "$PollingInterval WHERE TargetInstance ISA 'ActiveScriptEventConsumer'"
                    }

                    $Result.PSObject.TypeNames.Insert(0, "WMI.EventTrigger.ActiveScriptEventConsumer.$TriggerType")
                    return $Result
                }
            }
        }

        'StartupCommand' {
            if ($TriggerName) {
                $Name = $TriggerName
            } else {
                $Name = 'StartupCommandEvent'
            }

            $Result = @{
                Name = $Name
                EventNameSpace = 'root\CIMV2'
                QueryLanguage = 'WQL'
                Query = "SELECT * FROM $($TriggerTable[$TriggerType]) WITHIN " +
                    "$PollingInterval WHERE TargetInstance ISA 'Win32_StartupCommand'"
            }

            $Result.PSObject.TypeNames.Insert(0, "WMI.EventTrigger.StartupCommand.$TriggerType")
            return $Result
        }

        'Registry' {
            if ($TriggerName) {
                $Name = $TriggerName
            } else {
                $Name = 'RegistryKeyChangeEvent'
            }

            $Path = Get-Item $RegistryKey
            $KeyComponents = $Path[0].Name.Split('\\')
            $Hive = $KeyComponents[0]
            $Key = $KeyComponents[1..($KeyComponents.Length-1)] -join '\\'

            $Result = @{
                Name = $Name
                EventNameSpace = 'root\default'
                QueryLanguage = 'WQL'
                Query = "SELECT * FROM RegistryKeyChangeEvent WITHIN " +
                    "$PollingInterval WHERE Hive='$Hive' AND KeyPath='$Key'"
            }

            $Result.PSObject.TypeNames.Insert(0, "WMI.EventTrigger.Registry")
            return $Result
        }
    }
}

function New-AlertAction {
<#
.SYNOPSIS

Creates a hashtable that describes the action to take upon triggering
an alert.

Author: Matthew Graeber (@mattifestation)
Copyright: 2015 FireEye, Inc.
License: BSD 3-Clause
Required Dependencies: New-AlertTrigger
Optional Dependencies: None

.DESCRIPTION

New-AlertAction creates a hashtable for consumption by the
Register-Alert function. The hashtable describes the action to be
taken upon triggering an event. In other words, it prepares the
creation of a __FilterToConsumerBinding WMI object.

.PARAMETER Trigger

Specifies the trigger object returned by the New-AlertTrigger
function.

.PARAMETER Uri

Specifies that an HTTP GET request should be made to the specified
URI consisting of parameters that describe the triggered event.

.PARAMETER EventLogEntry

Specifies that an event log entry should be created upon triggering
an event. Event log entries are added to the Application event log,
use event source - 'WSH', and event ID - 8.

.PARAMETER ActionName

Optionally, specify the name under which the event consumer will
register. Hardcoded names are used in the absence of a specified
consumer name.

.EXAMPLE

New-AlertTrigger -EventConsumer ActiveScriptEventConsumer -TriggerType Creation | New-AlertAction -EventLogEntry

Description
-----------
Create an event log entry every time an ActiveScriptEventConsumer object is created.

.EXAMPLE

New-AlertTrigger -EventConsumer CommandLineEventConsumer -TriggerType Modification | New-AlertAction -Uri 'http://www.example.com'

Description
-----------
Send an HTTP GET request to the specified URI upon modification of a CommandLineEventConsumer class. Upon triggering the event, the full URI would take the following form:
http://www.example.com//checkin.php?Type=CommandLineEventConsumer&Hostname=<HOSTNAME>&Name=<Base64-encoded event consumer Name>&CommandLineTemplate=<Base64-encoded event consumer CommandLineTemplate>&ExecutablePath=<Base64-encoded event consumer ExecutablePath>

.OUTPUTS

System.Hashtable

Outputs a Hashtable that describes the WMI event trigger (filter) and event action (consumer).

.INPUTS

System.Hashtable

Accepts the output from the New-AlertTrigger object.
#>

    [OutputType([Hashtable])]
    Param (
        [Parameter(Mandatory = $True, ValueFromPipeline = $True)]
        [ValidateScript({$_.PSObject.TypeNames[0].StartsWith('WMI.EventTrigger')})]
        [Hashtable]
        $Trigger,

        [Parameter(Mandatory = $True, ParameterSetName = 'AlertUri')]
        [ValidateScript({$_.AbsoluteUri})]
        [Uri]
        $Uri,

        [Parameter(Mandatory = $True, ParameterSetName = 'EventLog')]
        [Switch]
        $EventLogEntry,

        [ValidateNotNullOrEmpty()]
        [String]
        $ActionName
    )

    # The type of alert trigger will dictate the corresponding alert action.
    $TriggerObject = $Trigger.PSObject.TypeNames[0].Split('.')[2]
    $TriggerType = $Trigger.PSObject.TypeNames[0].Split('.')[3]

    $Action = $null

    switch ($PsCmdlet.ParameterSetName) {
        'AlertUri' {
            $Base64Encoder = @'
                Function Base64Encode(inData)
                  '2001 Antonin Foller, Motobit Software, http://Motobit.cz
                  Const Base64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
                  Dim cOut, sOut, I
  
                  For I = 1 To Len(inData) Step 3
                    Dim nGroup, pOut, sGroup
    
                    nGroup = &H10000 * Asc(Mid(inData, I, 1)) + _
                      &H100 * MyASC(Mid(inData, I + 1, 1)) + MyASC(Mid(inData, I + 2, 1))
    
                    nGroup = Oct(nGroup)
    
                    nGroup = String(8 - Len(nGroup), "0") & nGroup
    
                    pOut = Mid(Base64, CLng("&o" & Mid(nGroup, 1, 2)) + 1, 1) + _
                      Mid(Base64, CLng("&o" & Mid(nGroup, 3, 2)) + 1, 1) + _
                      Mid(Base64, CLng("&o" & Mid(nGroup, 5, 2)) + 1, 1) + _
                      Mid(Base64, CLng("&o" & Mid(nGroup, 7, 2)) + 1, 1)
    
                    sOut = sOut + pOut
    
                  Next
                  Select Case Len(inData) Mod 3
                    Case 1: '8 bit final
                      sOut = Left(sOut, Len(sOut) - 2) + "=="
                    Case 2: '16 bit final
                      sOut = Left(sOut, Len(sOut) - 1) + "="
                  End Select
                  Base64Encode = sOut
                End Function

                Function MyASC(OneChar)
                  If OneChar = "" Then MyASC = 0 Else MyASC = Asc(OneChar)
                End Function
'@

            switch ($TriggerObject) {
                'CommandLineEventConsumer' {
                    $VBScript = @"
                        On Error Resume Next

                        $($Base64Encoder)

                        Dim name
                        Dim cmdtemplate
                        Dim executablepath
                        Dim hostname

                        Set objWMISvc = GetObject( "winmgmts:\\.\root\cimv2" )
                        Set colItems = objWMISvc.ExecQuery( "Select * from Win32_ComputerSystem", , 48 )
                        For Each objItem in colItems
                            hostname = objItem.Name
                        Next

                        name="NIL"
                        cmdtemplate="NIL"
                        executablepath="NIL"

                        if Not IsNull(TargetEvent.TargetInstance.Name) Then
                          name=Base64Encode(TargetEvent.TargetInstance.Name)
                        End If

                        if Not IsNull(TargetEvent.TargetInstance.CommandLineTemplate) Then
                          cmdtemplate=Base64Encode(TargetEvent.TargetInstance.CommandLineTemplate)
                        End If

                        if Not IsNull(TargetEvent.TargetInstance.ExecutablePath) Then
                          executablepath=Base64Encode(TargetEvent.TargetInstance.ExecutablePath)
                        End If

                        Set o = CreateObject("MSXML2.XMLHTTP")
                        o.Open "GET", "$($Uri.AbsoluteUri)checkin.php?Type=CommandLineEventConsumer" & _
                          "&Action=$TriggerType" & _
                          "&Hostname=" & hostname & _
                          "&Name=" & name & _
                          "&CommandLineTemplate=" & cmdtemplate & _
                          "&ExecutablePath=" & executablepath, False
                        o.Send
"@

                    if ($ActionName) {
                        $Name = $ActionName
                    } else {
                        $Name = 'CommandLineEventConsumerCreationTrigger'
                    }
                }

                'ActiveScriptEventConsumer' {
                    $VBScript = @"
                        On Error Resume Next

                        $($Base64Encoder)

                        Dim name
                        Dim engine
                        Dim scripttext
                        Dim filename
                        Dim hostname

                        Set objWMISvc = GetObject( "winmgmts:\\.\root\cimv2" )
                        Set colItems = objWMISvc.ExecQuery( "Select * from Win32_ComputerSystem", , 48 )
                        For Each objItem in colItems
                            hostname = objItem.Name
                        Next

                        name="NIL"
                        engine="NIL"
                        scripttext="NIL"
                        filename="NIL"

                        if Not IsNull(TargetEvent.TargetInstance.Name) Then
                          name=Base64Encode(TargetEvent.TargetInstance.Name)
                        End If

                        if Not IsNull(TargetEvent.TargetInstance.ScriptingEngine) Then
                          engine=TargetEvent.TargetInstance.ScriptingEngine
                        End If

                        if Not IsNull(TargetEvent.TargetInstance.ScriptText) Then
                          scripttext=Base64Encode(TargetEvent.TargetInstance.ScriptText)
                        End If

                        if Not IsNull(TargetEvent.TargetInstance.ScriptFileName) Then
                          filename=Base64Encode(TargetEvent.TargetInstance.ScriptFileName)
                        End If

                        Set o = CreateObject("MSXML2.XMLHTTP")
                        o.Open "GET", "$($Uri.AbsoluteUri)checkin.php?Type=ActiveScriptEventConsumer" & _
                          "&Action=$TriggerType" & _
                          "&Hostname=" & hostname & _
                          "&Name=" & name & _
                          "&ScriptingEngine=" & engine & _
                          "&ScriptText=" & scripttext & _
                          "&ScriptFileName=" & filename, False
                        o.Send
"@

                    if ($ActionName) {
                        $Name = $ActionName
                    } else {
                        $Name = 'ActiveScriptEventConsumerCreationTrigger'
                    }
                }

                'StartupCommand' {
                    $VBScript = @"
                        On Error Resume Next

                        $($Base64Encoder)

                        Dim SettingID
                        Dim User
                        Dim Location
                        Dim Name
                        Dim Description
                        Dim UserSID
                        Dim Command
                        Dim Caption

                        Set objWMISvc = GetObject( "winmgmts:\\.\root\cimv2" )
                        Set colItems = objWMISvc.ExecQuery( "Select * from Win32_ComputerSystem", , 48 )
                        For Each objItem in colItems
                            hostname = objItem.Name
                        Next

                        SettingID="NIL"
                        User="NIL"
                        Location="NIL"
                        Name="NIL"
                        Description="NIL"
                        UserSID="NIL"
                        Command="NIL"
                        Caption="NIL"

                        if Not IsNull(TargetEvent.TargetInstance.SettingID) Then
                          SettingID=Base64Encode(TargetEvent.TargetInstance.SettingID)
                        End If

                        if Not IsNull(TargetEvent.TargetInstance.User) Then
                          User=Base64Encode(TargetEvent.TargetInstance.User)
                        End If

                        if Not IsNull(TargetEvent.TargetInstance.Location) Then
                          Location=Base64Encode(TargetEvent.TargetInstance.Location)
                        End If

                        if Not IsNull(TargetEvent.TargetInstance.Name) Then
                          Name=Base64Encode(TargetEvent.TargetInstance.Name)
                        End If

                        if Not IsNull(TargetEvent.TargetInstance.Description) Then
                          Description=Base64Encode(TargetEvent.TargetInstance.Description)
                        End If

                        if Not IsNull(TargetEvent.TargetInstance.UserSID) Then
                          UserSID=Base64Encode(TargetEvent.TargetInstance.UserSID)
                        End If

                        if Not IsNull(TargetEvent.TargetInstance.Command) Then
                          Command=Base64Encode(TargetEvent.TargetInstance.Command)
                        End If

                        if Not IsNull(TargetEvent.TargetInstance.Caption) Then
                          Caption=Base64Encode(TargetEvent.TargetInstance.Caption)
                        End If

                        Set o = CreateObject("MSXML2.XMLHTTP")
                        o.Open "GET", "$($Uri.AbsoluteUri)checkin.php?Type=StartupCommand" & _
                          "&Action=$TriggerType" & _
                          "&Hostname=" & hostname & _
                          "&SettingID=" & SettingID & _
                          "&User=" & User & _
                          "&Location=" & Location & _
                          "&Name=" & Name & _
                          "&Description=" & Description & _
                          "&UserSID=" & UserSID & _
                          "&Command=" & Command & _
                          "&Caption=" & Caption, False
                        o.Send
"@

                    if ($ActionName) {
                        $Name = $ActionName
                    } else {
                        $Name = 'StartupCommandTrigger'
                    }
                }

                'Registry' {
                    $VBScript = @"
                        On Error Resume Next

                        $($Base64Encoder)

                        Dim hostname

                        Set objWMISvc = GetObject( "winmgmts:\\.\root\cimv2" )
                        Set colItems = objWMISvc.ExecQuery( "Select * from Win32_ComputerSystem", , 48 )
                        For Each objItem in colItems
                            hostname = objItem.Name
                        Next

                        Set o = CreateObject("MSXML2.XMLHTTP")
                        o.Open "GET", "$($Uri.AbsoluteUri)checkin.php?Type=RegistryKeyChangeEvent" & _
                          "&Hostname=" & hostname & _
                          "&Hive=" & Base64Encode(TargetEvent.Hive) & _
                          "&KeyPath=" & Base64Encode(TargetEvent.KeyPath), False
                        o.Send
"@

                    if ($ActionName) {
                        $Name = $ActionName
                    } else {
                        $Name = 'RegistryKeyChangeEventTrigger'
                    }
                }
            }

            $Action = @{
                Name = $Name
                ScriptingEngine = 'VBScript'
                ScriptText = $VBScript
                KillTimeout = [UInt32] 10
            }
        }

        'EventLog' {
            
            $ActionString = $null

            switch ($TriggerType) {
                'Creation' { $ActionString = 'created' }
                'Modification' { $ActionString = 'modified' }
                'Deletion' { $ActionString = 'deleted' }
            }

            switch ($TriggerObject) {
                'CommandLineEventConsumer' {
                    if ($ActionName) {
                        $Name = $ActionName
                    } else {
                        $Name = 'CommandLineEventConsumerLogEntryCreator'
                    }

                    $Template = @(
                        "A CommandLineEventConsumer instance was $ActionString.",
                        'Name: %TargetInstance.Name%',
                        'CommandLineTemplate: %TargetInstance.CommandLineTemplate%',
                        'ExecutablePath: %TargetInstance.ExecutablePath%'
                    )
                }

                'ActiveScriptEventConsumer' {
                    if ($ActionName) {
                        $Name = $ActionName
                    } else {
                        $Name = 'ActiveScriptEventConsumerLogEntryCreator'
                    }

                    $Template = @(
                        "An ActiveScriptEventConsumer instance was $ActionString.",
                        'Name: %TargetInstance.Name%',
                        'ScriptingEngine: %TargetInstance.ScriptingEngine%',
                        'ScriptFileName: %TargetInstance.ScriptFileName%',
                        'ScriptText: %TargetInstance.ScriptText%'
                    )
                }

                'StartupCommand' {
                    if ($ActionName) {
                        $Name = $ActionName
                    } else {
                        $Name = 'StartupCommandLogEntryCreator'
                    }

                    $Template = @(
                        "An StartupCommand instance was $ActionString.",
                        'SettingID: %TargetInstance.SettingID%',
                        'User: %TargetInstance.User%',
                        'Location: %TargetInstance.Location%',
                        'Name: %TargetInstance.Name%'
                        'Description: %TargetInstance.Description%'
                        'UserSID: %TargetInstance.UserSID%'
                        'Command: %TargetInstance.Command%'
                        'Caption: %TargetInstance.Caption%'
                    )
                }

                'Registry' {
                    if ($ActionName) {
                        $Name = $ActionName
                    } else {
                        $Name = 'RegistryKeyChangeEventLogEntryCreator'
                    }

                    $Template = @(
                        "A registry key was modified.",
                        'Hive: %TargetInstance.Hive%',
                        'KeyPath: %TargetInstance.KeyPath%'
                    )
                }
            }

            $Action = @{
                Name = $Name
                Category = [UInt16] 0
                EventType = [UInt32] 2 # Warning
                EventID = [UInt32] 8
                SourceName = 'WSH'
                NumberOfInsertionStrings = [UInt32] $Template.Length
                InsertionStringTemplates = $Template
            }
        }
    }

    $Result = @{
        Filter = $Trigger
        Consumer = $Action
        AlertType = $PsCmdlet.ParameterSetName
    }

    $Result.PSObject.TypeNames.Insert(0, 'WMI.FilterToConsumerBinding')
    return $Result
}

function Register-Alert {
<#
.SYNOPSIS

Registers an alert trigger/action combination on the specified
computer.

Author: Matthew Graeber (@mattifestation)
Copyright: 2015 FireEye, Inc.
License: BSD 3-Clause
Required Dependencies: New-AlertTrigger, New-AlertAction
Optional Dependencies: None

.DESCRIPTION

Register-Alert uses WMI to register an alert trigger/action
combination. Register-Alert requires that an alert trigger and alert
action be defined using the New-AlertTrigger and New-AlertAction
functions, respectively.

.PARAMETER Binding

Specifies the binding object returned by the New-AlertAction
function.

.PARAMETER ComputerName

Specifies the hostname or IP address of the computer where the alert
trigger/action is to be installed.

.PARAMETER Credential

Specifies a user account that has permission to perform this action.
The default is the current user. Type a user name, such as "User01",
"Domain01\User01", or User@Contoso.com. Or, enter a PSCredential
object, such as an object that is returned by the Get-Credential
cmdlet. When you type a user name, you are prompted for a password.

.EXAMPLE

New-AlertTrigger -EventConsumer CommandLineEventConsumer -TriggerType Creation | New-AlertAction -EventLogEntry | Register-Alert -ComputerName hostname123

Description
-----------
Registers an alert on 'hostname123' that creates an event log entry every time a CommandLineEventConsumer object is created.

.EXAMPLE

New-AlertTrigger -EventConsumer ActiveScriptEventConsumer -TriggerType Creation | New-AlertAction -Uri 'http://www.example.com' | Register-Alert

Description
-----------
Registers an alert on 'localhost' that creates sends an HTTP GET request every time an ActiveScriptEventConsumer object is created.

.OUTPUTS

PSObject

Outputs a custom object consisting of the registered Consumer,
Filter, and FilterToConsumer bindings.

.INPUTS

System.Hashtable

Accepts the output from the New-AlertAction object.
#>

    [OutputType([PSObject])]
    [CmdletBinding()] Param (
        [Parameter(Mandatory = $True, ValueFromPipeline = $True)]
        [ValidateScript({$_.PSObject.TypeNames[0] -eq 'WMI.FilterToConsumerBinding'})]
        [Hashtable]
        $Binding,

        [String]
        [ValidateNotNullOrEmpty()]
        [Alias('Cn')]
        $ComputerName = '.',

        [Management.Automation.PSCredential]
        $Credential
    )

    $FilterParams = @{
        Namespace = 'root\subscription'
        Class = '__EventFilter'
        ComputerName = $ComputerName
        Credential = $Credential
        Arguments = $Binding['Filter']
        ErrorAction = 'Stop'
    }

    $Filter = Set-WmiInstance @FilterParams
    
    $ClassName = $null

    switch ($Binding.AlertType) {
        'AlertUri' { $ClassName = 'ActiveScriptEventConsumer' }
        'EventLog' { $ClassName = 'NTEventLogEventConsumer' }
    }

    $ConsumerParams = @{
        Namespace = 'root\subscription'
        Class = $ClassName
        ComputerName = $ComputerName
        Credential = $Credential
        Arguments = $Binding['Consumer']
        ErrorAction = 'Stop'
    }

    $Consumer = Set-WmiInstance @ConsumerParams

    $BindingParams = @{
        Namespace = 'root\subscription'
        Class = '__FilterToConsumerBinding'
        ComputerName = $ComputerName
        Credential = $Credential
        Arguments = @{ Filter = $Filter; Consumer = $Consumer }
        ErrorAction = 'Stop'
    }

    $FilterConsumerBinding = Set-WmiInstance @BindingParams
    
    $Result = New-Object PSObject -Property @{
        Filter = $Filter
        Consumer = $Consumer
        Binding = $FilterConsumerBinding
    }

    $Result.PSObject.TypeNames.Insert(0, 'WMI.RegisteredAlert')
    return $Result
}

filter Get-WMIPersistenceItem {
<#
.SYNOPSIS

Returns all WMI classes associated with traditional WMI persistence
techniques.

Author: Matthew Graeber (@mattifestation)
Copyright: 2015 FireEye, Inc.
License: BSD 3-Clause
Required Dependencies: None
Optional Dependencies: None

.DESCRIPTION

Get-WMIPersistenceItem uses WMI to query for any WMI class
traditionally associated with WMI persistence, including the WMI
classes registered upon calling the Register-Alert function. It
queries the following WMI classes: __EventFilter,
__FilterToConsumerBinding, CommandLineEventConsumer,
ActiveScriptEventConsumer.

.PARAMETER ComputerName
 
Specifies the hostname or IP address of the computer on which to
execute the WMI queries.

.PARAMETER Credential

Specifies a user account that has permission to perform this action.
The default is the current user. Type a user name, such as "User01",
"Domain01\User01", or User@Contoso.com. Or, enter a PSCredential
object, such as an object that is returned by the Get-Credential
cmdlet. When you type a user name, you are prompted for a password.

.EXAMPLE

Get-WMIPersistenceItem

.EXAMPLE

Get-WMIPersistenceItem -ComputerName host123, host456 | Remove-WmiObject

Description
-----------
Removes all WMI persistence objects from the specified hosts.

.OUTPUTS

System.Management.ManagementObject

Outputs the WMI objects repesenting all possible WMI persistence
items.

.INPUTS

System.String[]

Accepts an array or hostname or IP addresses.
#>

    [OutputType([System.Management.ManagementObject])]
    Param (
        [Parameter(ValueFromPipeline = $True)]
        [String[]]
        [ValidateNotNullOrEmpty()]
        [Alias('Cn')]
        $ComputerName = '.',

        [Management.Automation.PSCredential]
        $Credential
    )

    $CommonArgs = @{
        Namespace = 'root\subscription'
        ComputerName = $ComputerName
        Credential = $Credential
    }

    Get-WmiObject @CommonArgs -Class '__EventFilter'
    Get-WmiObject @CommonArgs -Class '__EventConsumer'
    Get-WmiObject @CommonArgs -Class '__FilterToConsumerBinding'
}

