#!/usr/bin/env python2
"""
search for bytes in a WMI repository.

author: Willi Ballenthin
email: william.ballenthin@fireeye.com
"""
import sys
import logging
import binascii

import argparse

import cim


logger = logging.getLogger(__name__)


def find_bytes(repo, needle):
    index = cim.Index(repo.cim_type, repo.logical_index_store)

    for i in range(repo.logical_data_store.page_count):
        buf = repo.logical_data_store.get_physical_page_buffer(i)
        if needle not in buf:
            continue

        offset = buf.index(needle)

        print('found hit on physical page %s at offset %s' % (hex(i), hex(offset)))

        try:
            lnum = repo.data_mapping.get_logical_page_number(i)
        except cim.UnmappedPage:
            print('  this page not mapped to a logical page (unallocated page)')
            continue

        print('  mapped to logical page %s' % (hex(lnum)))

        try:
            page = repo.logical_data_store.get_page(lnum)
        except IndexError:
            print('  failed to fetch logical page')
            continue

        if len(page.toc) == 0:
            print('  page does not contain TOC, unknown contents')
            continue

        offset_found = False

        if 0 <= offset < len(page.toc):
            print('  hit in page TOC')
            offset_found = True

        for j in range(page.toc.count):
            entry = page.toc[j]
            if entry.offset <= offset < entry.offset + entry.size:
                print('  hit on object contents at entry index %s id %s' % (hex(j), hex(entry.record_id)))
                offset_found = True

                key_hits = set([])
                for key in index.lookup_keys(cim.Key('NS_')):
                    if not key.is_data_reference:
                        continue

                    if key.data_page != lnum:
                        continue

                    if key.data_id != entry.record_id:
                        continue

                    key = str(key)
                    if key not in key_hits:
                        print('  referred to by key %s' % (key))
                        key_hits.add(key)

        if not offset_found:
            print('  hit in page slack space')


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Search for a byte pattern in WMI repository structures.")
    parser.add_argument("input", type=str,
                        help="Path to input file")
    parser.add_argument("needle", type=str,
                        help="String or bytes for which to search")
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
    try:
        needle = binascii.unhexlify(args.needle)
        find_bytes(repo, needle)
    except ValueError:
        find_bytes(repo, args.needle.encode('ascii'))
        find_bytes(repo, args.needle.encode('utf-16le'))

    return 0


if __name__ == "__main__":
    sys.exit(main())
