python-cim
==========
`python-cim` is a pure Python parser for the Microsoft Windows CIM repository database.
The files `OBJECTS.DATA`, `INDEX.BTR`, and `MAPPING[1-3].MAP` commonly make up the database.


Dependencies
------------
`python-cim` works with both Python 2.7 and Python 3.4. 
It uses pure Python packages available via `pip` to implement some functionality.
These packages are documented in the file `requirements.txt`.

A few of the packages were developed to support this project. They are:

  - `vivisect-vstruct-wb`: A mirror of Vivisect's vstruct library that's easily installable (via `pip`).
     source: [github](https://github.com/williballenthin/vivisect-vstruct)
  - `python-pyqt5-hexview`: A hex view widget for PyQt5.
     source: [github](https://github.com/williballenthin/python-pyqt5-hexview)
  - `python-pyqt5-vstructui`: A vstruct parser and view widget for PyQt5.
     source: [github](https://github.com/williballenthin/python-pyqt5-vstructui)
     
All supporting packages will be installed automatically when fetching `python-cim` via pip, as described below.


Installation
------------

*Ubuntu*

Use the script found [here](https://gist.githubusercontent.com/williballenthin/c14c4f960e25b8ab1cff/raw/4e0e45f1e23cb23f983e76f25f78a60f7b6cc36d/install_python_cim_ubuntu.sh) to install `python-cim` into a Python3 virtualenv:

```
cd /tmp;
wget https://gist.githubusercontent.com/williballenthin/c14c4f960e25b8ab1cff/raw/4e0e45f1e23cb23f983e76f25f78a60f7b6cc36d/install_python_cim_ubuntu.sh;
bash install_python_cim_ubuntu.sh;
env/bin/python flare-wmi/python-cim/samples/ui.py win7 ~/Desktop/the/repo;
```

*other platforms*

  1. install python 3.4
    - debian: `apt-get install python3`
    - windows: https://www.python.org/downloads/
  2. install pip
    - debian: `apt-get install python-pip`
    - windows: python 3.4 installer has this option enabled by default
  3. install Qt5
    - debian: `apt-get install qt5-default`
    - windows: <skip this step>
  4. install PyQt5
    - debian: `apt-get install python3-pyqt5`
    - windows: http://www.riverbankcomputing.com/software/pyqt/download5
  5. install python-cim from pip:
    - `pip install python-cim`


Usage
-----
`python-cim` is mainly a library for parsing the Windows CIM repository database.
It is well suited for programmatic access, and users should be able to quickly develop
scripts that inspect the database. The scripts `dump_class_definition.py` and
`dump_class_instance.py` provide sample code.


### `ui.py`

The package also provides a basic GUI interface based on PyQt5. Users can inspect
a CIM repository visually using the following command:

```
python cim.py <xp|win7> /path/to/CIM/directory
```

### `dump_keys.py`

Print all the keys in the database index using a human readable format (hashes are shortened).

    » python3 samples/dump_keys.py xp ~/oh/wmi/toliver/FLLSMMICROS3700
    NS_2DDE/CR_CE89/C_0F2E5
    NS_86C6/CD_664C...94.643943.2401
    NS_8DFC/KI_C010/I_6EF1D...2496.203052.212
    NS_AC3E/CR_0745/C_A5FA2
    NS_DA27/CI_E584/IL_128E...432.760489.124
    NS_DD73/CR_C8B9/R_D5822
    NS_0016/CD_9561...2576.3207458013.467
    NS_0016/CR_3972/C_B169C
    NS_0B28/CD_03D7...2801.3207667479.395
    NS_0B28/CD_8E99...2805.3207675482.430


### `dump_class_definition.py`

Print the class definition, layout, and inheritance chain for a given class name.

    » python3 samples/dump_class_definition.py xp /path/to/CIM/repo root\\subscription NTEventLogEventConsumer      
    ================================================================================
    namespace: root\subscription
    classname: NTEventLogEventConsumer
    super: __EventConsumer
    ts: 2005-05-09T22:07:21.437267
    qualifiers:
    properties:
      name: Name
        type: CIM_TYPE_STRING
        order: 3
        qualifiers:
          PROP_TYPE: string
          PROP_KEY: True
      name: InsertionStringTemplates
        type: arrayref to CIM_TYPE_STRING
        order: 10
        qualifiers:
          PROP_TYPE: string
          Template: True
      name: NameOfUserSIDProperty
        type: CIM_TYPE_STRING
        order: 12
        qualifiers:
          PROP_TYPE: string
      name: EventID
        type: CIM_TYPE_UINT32
        order: 6
        qualifiers:
          NOT_NULL: True
          PROP_TYPE: uint32
      name: NumberOfInsertionStrings
        type: CIM_TYPE_UINT32
        order: 9
        qualifiers:
          NOT_NULL: True
          PROP_TYPE: uint32
      name: SourceName
        type: CIM_TYPE_STRING
        order: 5
        qualifiers:
          NOT_NULL: True
          PROP_TYPE: string
      name: EventType
        type: CIM_TYPE_UINT32
        order: 7
        qualifiers:
          NOT_NULL: True
          PROP_TYPE: uint32
          Values: ['Success', 'Error', 'Warning', 'Information', 'Audit Success', 'Audit Failure']
          ValueMap: ['0', '1', '2', '4', '8', '16']
      name: UNCServerName
        type: CIM_TYPE_STRING
        order: 4
        qualifiers:
          PROP_TYPE: string
      name: NameOfRawDataProperty
        type: CIM_TYPE_STRING
        order: 11
        qualifiers:
          PROP_TYPE: string
      name: Category
        type: CIM_TYPE_UINT16
        order: 8
        qualifiers:
          NOT_NULL: True
          PROP_TYPE: uint16
    layout:                                                                                                                             [175/9717]
      (0x0)   CIM_TYPE_STRING MachineName
      (0x4)   CIM_TYPE_UINT32 MaximumQueueSize
      (0x8)   arrayref to CIM_TYPE_UINT8 CreatorSID
      (0xc)   CIM_TYPE_STRING Name
      (0x10)   CIM_TYPE_STRING UNCServerName
      (0x14)   CIM_TYPE_STRING SourceName
      (0x18)   CIM_TYPE_UINT32 EventID
      (0x1c)   CIM_TYPE_UINT32 EventType
      (0x20)   CIM_TYPE_UINT16 Category
      (0x22)   CIM_TYPE_UINT32 NumberOfInsertionStrings
      (0x26)   arrayref to CIM_TYPE_STRING InsertionStringTemplates
      (0x2a)   CIM_TYPE_STRING NameOfRawDataProperty
      (0x2e)   CIM_TYPE_STRING NameOfUserSIDProperty
    ================================================================================
    keys:
      Name
    ================================================================================
    00000000 (1136) ClassDefinition: ClassDefinition(name: NTEventLogEventConsumer)
    00000000 (80)   header: ClassDefinitionHeader
    00000000 (04)     super_class_unicode_length: 0x0000000f (15)
    00000004 (30)     super_class_unicode: '__EventConsumer'
    00000022 (08)     timestamp: 2005-05-09T22:07:21.437267Z
    0000002a (01)     unk0: 0x00000046 (70)
    0000002b (04)     unk1: 0x00000004 (4)
    0000002f (04)     offset_class_name: 0x00000000 (0)
    00000033 (04)     junk_length: 0x00000036 (54)
    00000037 (04)     unk3: 0x00000019 (25)
    0000003b (17)     super_class_ascii: '__EventConsumer'
    0000003b (01)       zero: 0x00000000 (0)
    0000003c (16)       s: '__EventConsumer'
    0000004c (04)     unk4: 0x00000011 (17)
    00000050 (04)   qualifiers_list: QualifiersList
    00000050 (04)     size: 0x00000004 (4)
    00000054 (00)     qualifiers: VArray
    00000054 (84)   property_references: PropertyReferenceList
    00000054 (04)     count: 0x0000000a (10)
    00000058 (80)     refs: VArray
    00000058 (08)       0: PropertyReference
    00000058 (04)         offset_property_name: 0x00000019 (25)
    0000005c (04)         offset_property_struct: 0x00000023 (35)
    00000060 (08)       1: PropertyReference
    00000060 (04)         offset_property_name: 0x0000005f (95)
    00000064 (04)         offset_property_struct: 0x00000068 (104)
    00000068 (08)       2: PropertyReference
    00000068 (04)         offset_property_name: 0x000000a4 (164)
    0000006c (04)         offset_property_struct: 0x000000af (175)
    00000070 (08)       3: PropertyReference
    00000070 (04)         offset_property_name: 0x000001a6 (422)
    00000074 (04)         offset_property_struct: 0x000001c0 (448)
    00000078 (08)       4: PropertyReference
    00000078 (04)         offset_property_name: 0x000001fc (508)
    0000007c (04)         offset_property_struct: 0x00000202 (514)
    00000080 (08)       5: PropertyReference
    00000080 (04)         offset_property_name: 0x00000234 (564)
    00000084 (04)         offset_property_struct: 0x0000024b (587)
    00000088 (08)       6: PropertyReference
    00000088 (04)         offset_property_name: 0x00000272 (626)
    0000008c (04)         offset_property_struct: 0x00000289 (649)
    00000090 (08)       7: PropertyReference
    00000090 (04)         offset_property_name: 0x000002b0 (688)
    00000094 (04)         offset_property_struct: 0x000002ca (714)
    00000098 (08)       8: PropertyReference
    00000098 (04)         offset_property_name: 0x00000306 (774)
    0000009c (04)         offset_property_struct: 0x00000312 (786)
    000000a0 (08)       9: PropertyReference
    000000a0 (04)         offset_property_name: 0x0000034e (846)
    000000a4 (04)         offset_property_struct: 0x0000035d (861)
    000000a8 (54)   junk: 6f0541fdffffffffffffffffc5000000ffffffffffffffffffffffff0000000001000000ffff0000000084030000ffffffffffffffff
    000000de (04)   _data_length: 0x8000038e (2147484558)
    000000e2 (910)   data: 004e544576656e744c6f674576656e74436f6e737...

### `dump_class_instance.py`

Dump the property field values for the given class instance, or property fields for all instances with the given
class. Use the format `PropName1=PropValue1,PropName2=PropValue2` to specify the instance key.

    » python3 samples/dump_class_instance.py xp /path/to/CIM/repo root\\ccm\\SoftwareMeteringAgent CCM_RecentlyUsedApps "ExplorerFileName=rundll32.exe,FolderPath=C:\Windows\System32,LastUserName=DOMAIN\User"
    classname: CCM_RecentlyUsedApps
    super: 
    key: ExplorerFileName=rundll32.exe,FolderPath=C:\Windows\system32,LastUserName=DOMAIN\User
    timestamp1: 2015-01-09 06:28:28.263854
    timestamp2: 2014-04-09 14:11:55.154609
    properties:
      [PROP_TYPE=string]
      FileVersion=4.9.3.2824
    
      [PROP_TYPE=string]
      ProductVersion=4.9
    
      [PROP_KEY=True,PROP_TYPE=string]
      ExplorerFileName=rundll32.exe
    
      [PROP_TYPE=uint32]
      FileSize=446464
    
      [PROP_TYPE=string]
      FileDescription=RunDll.exe
    
      [PROP_TYPE=string]
      CompanyName=Microsoft, Inc.
    
      [PROP_TYPE=uint32]
      LaunchCount=262
    
      [PROP_TYPE=datetime]
      LastUsedTime=20150127201748.667000+000
    
      [PROP_TYPE=uint32]
      ProductLanguage=1033
    
      [PROP_TYPE=string]
      OriginalFileName=rundll32.exe
    
      [PROP_KEY=True,PROP_TYPE=string]
      FolderPath=C:\Windows\system32
    
      [PROP_KEY=True,PROP_TYPE=string]
      LastUserName=DOMAIN\User
    
      [PROP_TYPE=string]
      ProductName=Microsoft Windows


### `dump_object.py`

Dump the raw binary data for the given object ID.

    » python3 samples/dump_object.py win7 /path/to/CIM/repo 1571.9951877.374 | xxd 
    0000000: 4200 4200 4600 4300 4300 4200 3400 3400  B.B.F.C.C.B.4.4.
    0000010: 3400 4300 4600 3600 3600 4100 4100 3000  4.C.F.6.6.A.A.0.
    0000020: 3900 4100 4500 3600 4600 3100 3500 3900  9.A.E.6.F.1.5.9.
    0000030: 3600 3700 4100 3600 3800 3600 3500 3100  6.7.A.6.8.6.5.1.
    0000040: 3700 3500 4200 4200 3000 4500 4400 3200  7.5.B.B.0.E.D.2.
    0000050: 3100 3600 4400 3100 3900 3900 3700 3000  1.6.D.1.9.9.7.0.
    0000060: 4100 3700 3900 3800 3800 4200 3700 3200  A.7.9.8.8.B.7.2.
    0000070: 4300 4400 4600 3000 4100 3300 4100 3400  C.D.F.0.A.3.A.4.
    0000080: d5d5 313b 91fe cf01 d48e 8290 2b04 ca01  ..1;........+...
    0000090: e600 0000 0000 0000 000f a3aa fcff bf22  ..............."
    00000a0: 0000 0000 0000 0000 2f00 0000 4f00 0000  ......../...O...
    00000b0: 0000 0000 1a00 0000 0000 0000 0000 0000  ................
    00000c0: 0000 0000 0000 5c00 0000 0000 0000 0000  ......\.........
    00000d0: 0000 0000 0000 0000 0000 0000 0000 0000  ................
    00000e0: 0000 0000 0000 0000 0000 0000 0000 0000  ................
    00000f0: 0000 0000 0000 0000 0000 0000 0400 0000  ................
    0000100: 0171 0000 8000 436f 6d6d 616e 644c 696e  .q....CommandLin
    0000110: 6545 7665 6e74 436f 6e73 756d 6572 0000  eEventConsumer..
    0000120: 6373 6372 6970 7420 4b65 726e 4361 702e  cscript KernCap.
    0000130: 7662 7300 1c00 0000 0105 0000 0000 0005  vbs.............
    0000140: 1500 0000 a54e 78fa b7f7 92c6 7ebb f301  .....Nx.....~...
    0000150: f277 0000 0042 5654 436f 6e73 756d 6572  .w...BVTConsumer
    0000160: 0000 433a 5c5c 746f 6f6c 735c 5c6b 6572  ..C:\\tools\\ker
    0000170: 6e72 6174 6500                           nrate.
    
    
### `hash_term.py`

Hash the given terms using the hashing algorithm used in the supplied CIM repository.
The script encodes the given terms as UTF-16LE prior to performing the hashing operation.

    » bin/python3 samples/hash_term.py xp /path/to/CIM/repo "Hello world" "Goodbye world"
    XX_E6760D555C32F66F5E159331DB20FD8E     Hello world
    XX_1A053CC04A1813060EACEABA46ECCFB1     Goodbye world
    
