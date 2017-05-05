#!/usr/bin/env python2
"""
automatically identify and carve class definitions from WMI repository unused space.

author: Willi Ballenthin
email: william.ballenthin@fireeye.com
"""
import sys
import struct
import logging
import datetime

import argparse

import cim
import cim.recovery


logger = logging.getLogger(__name__)


def filetime2datetime(ft):
    '''
    convert a FILETIME 64-bit integer to a timestamp.
    
    Args:
        ft (int): the FILETIME number.

    Returns:
        datetime.datetime: the python timestamp.
    '''
    return datetime.datetime.utcfromtimestamp(float(ft) * 1e-7 - 11644473600)


def datetime2filetime(ts):
    '''
    convert a timestamp to a FILETIME 64-bit integer.
    
    Args:
        ts (datetime.datetime):  the python timestamp.

    Returns:
        int: the FILETIME number.
    '''
    epoch = datetime.datetime(1970,1,1)
    posix = (ts - epoch).total_seconds()
    return (posix + 11644473600) * 1e7


def find_reasonable_timestamps(buf):
    '''
    find offsets in the given buffer that contain a FILETIME timestamp between 2010 and tomorrow.
    note: tomorrow depends on the current date, so its a bit impure.
    
    Args:
        buf (bytes): the raw bytes to search.

    Yields:
        int: offset into the buffer of a FILETIME timestamp.
    '''
    min_filetime = datetime2filetime(datetime.datetime(2010, 1, 1, 0, 1, 0))
    max_filetime = datetime2filetime(datetime.datetime.now() + datetime.timedelta(days=1))

    for offset in range(len(buf) - 8):
        ft = struct.unpack_from("<Q", buf, offset)[0]
        if min_filetime <= ft < max_filetime:
            yield offset


def find_possible_class_definitions(buf):
    '''
    find places in the given buffer at which class definitions may be carved.
    
    for right now, we only support identifying class definitions with no superclass.
    to support classes with superclasses, we'd have to scan backwards for the super name length.
    
    Args:
        buf (bytes): the data in which to search.

    Yields:
        int: the offset in the buffer at which a class definition may start.
    '''
    for offset in find_reasonable_timestamps(buf):
        if offset < 0x4:
            # need at least four bytes for the superclass name length field
            continue

        superclass_str_length = struct.unpack_from("<I", buf, offset - 0x4)[0]
        if superclass_str_length != 0:
            # for right now, focus on classes without a super class.
            # eg. the classes created interactively via powershell.
            continue

        yield offset - 0x4


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Automatically identify and carve class definitions from WMI repository unused space.")
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
    resolver = cim.objects.ObjectResolver(repo)

    for i in range(repo.data_mapping.map.header.mapping_entry_count):
        try:
            page = repo.logical_data_store.get_page(i)
        except cim.UnmappedPage:
            continue
        except IndexError:
            logger.warn('failed to fetch page 0x%x', i)
            continue

        for region in cim.recovery.extract_data_page_slack(page):
            for offset in find_possible_class_definitions(region.buffer):
                logger.debug('possible class definition on logical page 0x%x in slack space at page offset 0x%x',
                             i, region.page_offset + offset)
                cdbuf = region.buffer[offset:]
                cd = cim.objects.ClassDefinition()
                try:
                    cd.vsParse(cdbuf)
                except Exception as e:
                    logger.debug('failed to parse class definition: %s', str(e))
                    continue
                # unfortunately, we don't know the namespace from which these classes came.
                # so, we'll have to guess it is cimv2.
                # the layout is required to fetch the default values, which is useful for static classes/props.
                # the layout needs the namespace name to resolve superclasses, if there are any.
                cl = cim.objects.ClassLayout(resolver, 'root\\CIMV2', cd)
                print('logical page 0x%x, slack space at page offset 0x%x' % (
                      region.logical_page_number, region.page_offset + offset))
                print(cim.formatters.dump_layout(cd, cl))

    for pnum in cim.recovery.find_unallocated_pages(repo):
        buf = repo.logical_data_store.get_physical_page_buffer(pnum)
        for offset in find_possible_class_definitions(buf):
            logger.debug('possible class definition on unallocatad page 0x%x at page offset 0x%x', pnum, offset)
            cdbuf = buf[offset:]
            cd = cim.objects.ClassDefinition()
            try:
                # if the object runs over multiple pages, we'll be out of luck here.
                # how would we know where to look for the remaining data?
                # must somehow reconstruct the page mapping.
                cd.vsParse(cdbuf)
            except Exception as e:
                logger.debug('failed to parse class definition: %s', str(e))
                continue
            cl = cim.objects.ClassLayout(resolver, cim.objects.ROOT_NAMESPACE_NAME, cd)
            print('unallocated page 0x%x, page offset 0x%x' % (pnum, offset))
            print(cim.formatters.dump_layout(cd, cl))
    return 0


if __name__ == "__main__":
    sys.exit(main())