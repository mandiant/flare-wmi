import logging
import collections

import intervaltree

import cim


logger = logging.getLogger(__name__)


SlackRegion = collections.namedtuple('SlackRegion', ['logical_page_number',
                                                     'page_offset',
                                                     'buffer'])

def extract_data_page_slack(page):
    '''
    extract the slack bytes from the given data page.
    
    Args:
        page (cim.DataPage): the page from which to extract slack space.

    Yields:
        SlackRegion: the raw bytes of the slack space.
    '''

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

    for region in sorted(slack):
        begin, end, _ = region
        if (end - begin) > cim.DATA_PAGE_SIZE:
            continue

        yield SlackRegion(page.logical_page_number, begin, page.buf[begin:end])
