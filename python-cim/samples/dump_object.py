#!/usr/bin/env python2
"""
extract an object buffer from a WMI repository. 

author: Willi Ballenthin
email: william.ballenthin@fireeye.com
"""
import os
import sys
import logging

import argparse

import cim


logger = logging.getLogger(__name__)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Extract an object buffer from a WMI repository.")
    parser.add_argument("input", type=str,
                        help="Path to input file")
    parser.add_argument("key", type=str,
                        help="Key to object, like 889.1.43301")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable debug logging")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="Disable all output but errors")
    args = parser.parse_args(args=argv)

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.quiet:
        logging.basicConfig(level=logging.ERROR)
        logging.getLogger().setLevel(logging.ERROR)
    else:
        logging.basicConfig(level=logging.INFO)
        logging.getLogger().setLevel(logging.INFO)

    repo = cim.CIM.from_path(args.input)
    key = cim.Key('__.' + args.key)
    os.write(sys.stdout.fileno(), repo.logical_data_store.get_object_buffer(key))
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main(sys.argv[1:])
