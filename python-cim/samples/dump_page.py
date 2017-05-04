#!/usr/bin/env python2
"""
extract page data from a WMI repository.

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

    parser = argparse.ArgumentParser(description="Extracted page data from a CIM repository.")
    parser.add_argument("input", type=str,
                        help="Path to input file")
    parser.add_argument("page_number", type=lambda i: int(i, 0x10),
                        help="Page number to extract (hexidecimal)")
    parser.add_argument("-m", "--addressing_mode", choices=["physical", "logical"], default="physical",
                        help="Extract using physical or logical page number")
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

    if args.addressing_mode == "physical":
        buf = repo.logical_data_store.get_physical_page_buffer(args.page_number)
    elif args.addressing_mode == "logical":
        buf = repo.logical_data_store.get_logical_page_buffer(args.page_number)
    else:
        raise RuntimeError('unexpected mode')

    os.write(sys.stdout.fileno(), buf)

    return 0


if __name__ == "__main__":
    sys.exit(main())