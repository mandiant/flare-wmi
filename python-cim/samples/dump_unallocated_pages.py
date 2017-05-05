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
import cim.recovery


logger = logging.getLogger(__name__)


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
    for pnum in cim.recovery.find_unallocated_pages(repo):
        logger.info('found unallocated physical page: 0x%x', pnum)
        os.write(sys.stdout.fileno(), repo.logical_data_store.get_physical_page_buffer(pnum))

    return 0


if __name__ == "__main__":
    sys.exit(main())
