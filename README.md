# flare-wmi

This repository contains various documentation and code projects that describe the Windows Management Instrumentation (WMI) technology.
The research was first introduced at [Defcon 23](https://www.defcon.org/html/defcon-23/dc-23-index.html) in 2015, and the associated slides are available here: [DEFCON_23-WMI-Attacks-Defense-Forensics.pdf](DEFCON_23_Presentation/DEFCON_23-WMI-Attacks-Defense-Forensics.pdf).

## python-cim (active development)
[python-cim](./python-cim) is a pure Python parser for the WMI repository database.
It supports read access to WMI structures via a flexible API.
You can use the provided "sample" scripts to 
 [dump persistence locations](./python-cim/samples/show_filtertoconsumerbindings.py),
 [identify commonly executed software](./python-cim/samples/show_CCM_RecentlyUsedApps.py),
 [timeline activity](./python-cim/samples/timeline.py), and
 [recover deleted data](./python-cim/doc/data-recovery.md).

## WMIParser (unmaintained)
[WMIParser](WMIParser) is a forensic parser for the WMI repository database files that can extract `FilterToConsumerBindings` that malicious actors have hijacked.
The parser is written in C.

## WMI-IDS (unmaintained)
[WMI-IDS](./WMI-IDS) is a proof-of-concept agent-less host intrusion detection system designed to showcase 
 the unique ability of WMI to respond to and react to operating system events in real-time.
WMI-IDS is a PowerShell module that serves as an installer of WMI events on a local or remote system. 
