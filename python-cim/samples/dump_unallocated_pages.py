#!/usr/bin/env python2
"""
extract unallocated physical pages from a CIM repository.

author: Willi Ballenthin
email: william.ballenthin@fireeye.com
"""
import os
import sys
import logging

import argparse

import cim

logger = logging.getLogger(__name__)


def extract_unallocated_data_pages(repo):
    for i in range(repo.logical_data_store.page_count):
        if not repo.data_mapping.is_physical_page_mapped(i):
            yield repo.logical_data_store.get_physical_page_buffer(i)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Extracted unallocated physical pages from a CIM repo.")
    parser.add_argument("input", type=str,
                        help="Path to input file")
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
    for page in extract_unallocated_data_pages(repo):
        os.write(sys.stdout.fileno(), page)

    return 0


if __name__ == "__main__":
    sys.exit(main())
