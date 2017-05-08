python-cim
==========
`python-cim` is a pure Python parser for the Microsoft Windows CIM (WMI) repository database.
This database is found in the files `OBJECTS.DATA`, `INDEX.BTR`, and `MAPPING[1-3].MAP`.


Usage
-----
`python-cim` is a library for parsing the Windows CIM repository database.
It is well suited for programmatic access, and users should be able to quickly develop scripts that inspect the database.
You should review the scripts in the [samples directory](./samples) and the [test cases](./tests) to learn how to invoke the library.

For example, you can use `python-cim` to [extract malicious code configured for persistence](./samples/show_filtertoconsumerbindings.py) ([doc](https://www.fireeye.com/content/dam/fireeye-www/global/en/current-threats/pdfs/wp-windows-management-instrumentation.pdf)),
 [identify commonly executed software](./samples/show_CCM_RecentlyUsedApps.py) ([doc](https://www.fireeye.com/blog/threat-research/2016/12/do_you_see_what_icc.html)),
 and [recover deleted data](./doc/data-recovery.md).


Installation
------------

*Ubuntu*

Use the script found [here](https://gist.githubusercontent.com/williballenthin/c14c4f960e25b8ab1cff/raw/87751f91c0b055713f4e8d0d0eaad4a6c14efef7/install_python_cim_ubuntu.sh) to install `python-cim` into a Python3 virtualenv:

```
cd /tmp;
wget https://gist.githubusercontent.com/williballenthin/c14c4f960e25b8ab1cff/raw/87751f91c0b055713f4e8d0d0eaad4a6c14efef7/install_python_cim_ubuntu.sh;
bash install_python_cim_ubuntu.sh;
env/bin/python flare-wmi/python-cim/samples/ui.py win7 ~/Desktop/the/repo;
```

*Arch/Manjaro*

Use the script found [here](https://gist.githubusercontent.com/williballenthin/ddb516208f5481c4e02a/raw/4a8fdb9b9eeffb4843f09803b1303b4b074dc46c/install_python_cim_arch.py) to install `python-cim` into a Python3 virtualenv:

```
cd /tmp;
wget https://gist.githubusercontent.com/williballenthin/ddb516208f5481c4e02a/raw/4a8fdb9b9eeffb4843f09803b1303b4b074dc46c/install_python_cim_arch.py;
bash install_python_cim_arch.sh;
env/bin/python flare-wmi/python-cim/samples/ui.py win7 ~/Desktop/the/repo;
```

*other platforms*

  1. install python 3.4+
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


Dependencies
------------
`python-cim` works with both Python 2.7 and Python 3.x.
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


