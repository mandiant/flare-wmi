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
import intervaltree

import cim


logger = logging.getLogger(__name__)


def extract_data_page_slack(repo):
    for i in range(repo.logical_data_store.page_count):
        if not repo.data_mapping.is_physical_page_mapped(i):
            continue

        try:
            page = repo.logical_data_store.get_page(i)
        except IndexError:
            break

        # start by marking the entire page as allocated
        slack = intervaltree.IntervalTree([intervaltree.Interval(0, cim.DATA_PAGE_SIZE)])

        # remove the toc region
        slack.chop(0, len(page.toc))

        # if there is a toc, then we remove the empty entry at the end
        # (this is not included in the list of entries, but its part of the toc).
        if len(page.toc) > 0:
            slack.chop(len(page.toc), len(page.toc) + 0x10)

        # and regions for each of the entries
        for j in range(page.toc.count):
            entry = page.toc[j]
            slack.chop(entry.offset, entry.offset + entry.size)

        pagebuf = repo.logical_data_store.get_logical_page_buffer(i)

        for region in sorted(slack):
            begin, end, _ = region
            if (end - begin) > cim.DATA_PAGE_SIZE:
                continue

            logger.info('extracted %s bytes of slack from logical page %s at offset %s',
                        hex(end - begin), hex(i), hex(begin))
            yield pagebuf[begin:end]


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
