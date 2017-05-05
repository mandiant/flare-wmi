#!/usr/bin/env python2
"""
carve a class definition from a WMI repository.

author: Willi Ballenthin
email: william.ballenthin@fireeye.com
"""
import sys
import logging

import argparse

import cim


logger = logging.getLogger(__name__)


def carve_class_definition(repo, physical_page_number, offset):
    page = repo.logical_data_store.get_physical_page_buffer(physical_page_number)
    buf = page[offset:]
    cd = cim.objects.ClassDefinition()
    cd.vsParse(buf)
    return cd


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Carve a class definition from a WMI repository.")
    parser.add_argument("input", type=str,
                        help="Path to input file")
    parser.add_argument("page", type=lambda i: int(i, 0x10),
                        help="Physical page number that contains the class definition")
    parser.add_argument("offset", type=lambda i: int(i, 0x10),
                        help="Page offset at which the class definition begins")
    parser.add_argument("namespace", type=str, nargs="?", const='root\\CIMV2',
                        help="Guess at the namespace in which the class definition is found")
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
    cd = carve_class_definition(repo, args.page, args.offset)
    resolver = cim.objects.ObjectResolver(repo)
    cl = cim.objects.ClassLayout(resolver, args.namespace, cd)
    print(cim.formatters.dump_layout(cd, cl))

    return 0


if __name__ == "__main__":
    sys.exit(main())