#!/usr/bin/env python2
"""
timeline metadata from a WMI repository.

author: Willi Ballenthin
email: william.ballenthin@fireeye.com
"""
import sys
import logging
import collections

import argparse

import cim
import cim.objects


logger = logging.getLogger(__name__)


def format_ts(ts):
    '''
    format a timestamp object nicely.
    
    Args:
        ts (datetime.datetime): the timestamp instance.

    Returns:
        str: the formatted timestamp string.
    '''
    return ts.isoformat("T") + "Z"


TimelineEntry = collections.namedtuple("TimelineEntry", ["ts", "label", "key"])


def timeline(repo):
    '''
    extract the timestamps from a wmi repository into an ordered list.
    
    Args:
        repo (cim.CIM): the repository form which to extract timestamps.

    Returns:
        List[TimelineEntry]: the timeline of timestamps in the repository.
    '''
    entries = []
    def rec(namespace):
        for klass in namespace.classes:
            entries.append(TimelineEntry(ts=klass.cd.header.timestamp,
                                         label="ClassDefinition.timestamp",
                                         key=str(klass)))
            for instance in klass.instances:
                entries.append(TimelineEntry(ts=instance.ci.ts1,
                                             label="ClassInstance.timestamp1",
                                             key=str(instance)))
                entries.append(TimelineEntry(ts=instance.ci.ts2,
                                             label="ClassInstance.timestamp2",
                                             key=str(instance)))
        for ns in namespace.namespaces:
            rec(ns)

    tree = cim.objects.Tree(repo)
    rec(tree.root)
    return sorted(entries, key=lambda e: e.ts)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Timeline metadata in a WMI repository.")
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
    for entry in timeline(repo):
        print('{ts:s}\t{entry.label:s}\t{entry.key:s}'.format(entry=entry, ts=format_ts(entry.ts)))
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main(sys.argv[1:])
