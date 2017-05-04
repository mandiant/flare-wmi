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


def build_rainbow_table(repo):
    """
    build a mapping from WMI repository hash to human readable path fragments.
    
    Args:
        repo (cim.CIM): the repository

    Returns:
        dict[str, str]: hash fragment to human readable name
    """
    namespaces = []
    classes = []
    instances = []

    def collect(ns):
        for namespace in ns.namespaces:
            namespaces.append(namespace)

        for klass in ns.classes:
            classes.append(klass)

            for instance in klass.instances:
                instances.append(instance)

        for namespace in ns.namespaces:
            collect(namespace)

    with cim.objects.Namespace(repo, cim.objects.ROOT_NAMESPACE_NAME) as root:
        collect(root)

    resolver = cim.objects.ObjectResolver(repo)

    rainbow_table = {}

    for namespace in namespaces:
        thehash = resolver.NS(namespace.name).partition('_')[2]
        rainbow_table[thehash] = namespace.name

    for klass in classes:
        thehash = resolver.CD(klass.name).partition('_')[2]
        rainbow_table[thehash] = klass.name

    for instance in instances:
        thehash = resolver.CI(str(instance.instance_key)).partition('_')[2]
        rainbow_table[thehash] = str(instance.instance_key)

    return rainbow_table


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Search for a byte pattern in WMI repository structures.")
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
    for k, v in build_rainbow_table(repo).items():
        print('%s\t%s' % (k, v))

    return 0


if __name__ == "__main__":
    sys.exit(main())
