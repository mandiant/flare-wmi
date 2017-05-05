#!/usr/bin/env python2
"""
extract data page slack from a CIM repository.

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


def extract_data_page_slack(repo):
    for i in range(repo.logical_data_store.page_count):
        if not repo.data_mapping.is_logical_page_mapped(i):
            continue

        try:
            page = repo.logical_data_store.get_page(i)
        except IndexError:
            logger.warn('failed to fetch page 0x%x', i)
            continue

        for region in cim.recovery.extract_data_page_slack(page):
            logger.info('extracted %s bytes of slack from logical page %s at offset %s',
                        hex(len(region.buffer)), hex(i), hex(region.page_offset))
            yield region.buffer


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Extracted data page slack from a CIM repository.")
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

    for buf in extract_data_page_slack(repo):
        os.write(sys.stdout.fileno(), buf)

    return 0


if __name__ == "__main__":
    sys.exit(main())
