#!/usr/bin/env python

from cim import __version__
from setuptools import setup


description = "Pure Python parser for Windows WMI CIM respository databases."
setup(name="python-cim",
      version=__version__,
      description=description,
      long_description=description,
      author="Willi Ballenthin",
      author_email="william.ballenthin@fireeye.com",
      url="https://github.com/williballenthin/python-cim",
      license="Apache 2.0 License",
      install_depends=[
          "hexdump",
          "funcy",
          "intervaltree",
          "vivisect-vstruct-wb",
          "python-pyqt5-hexview",
          "python-pyqt5-vstructui"],
      packages=["cim"])
