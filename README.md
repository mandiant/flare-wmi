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


Installation
------------
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
  5. install pip packages:
    - `pip install -r requirements.txt`


Usage
-----

`python-cim` is mainly a library for parsing the Windows CIM repository database.
It is well suited for programmatic access, and users should be able to quickly develop
scripts that inspect the database. The scripts `dump_class_definition.py` and
`dump_class_instance.py` provide sample code.

The package also provides a basic GUI interface based on PyQt5. Users can inspect
a CIM repository visually using the following command:

```
python cim.py <xp|win7> /path/to/CIM/directory
```

