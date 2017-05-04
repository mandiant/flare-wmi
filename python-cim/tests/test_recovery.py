import cim.recovery
from fixtures import *


def test_page_slack_space(repo):
    """
    demonstrate that a data page with a TOC can have slack space.
    
    Args:
        repo (cim.CIM): the deleted-instance repo

    Returns:
        None

    """
    datapages = repo.logical_data_store
    page = datapages.get_page(0x0)

    regions = list(cim.recovery.extract_data_page_slack(page))

    # collected empirically
    assert len(regions) == 1
    region = regions[0]

    # collected empirically
    #
    # in this case, there's some NULL bytes at the end of the page.
    assert region.logical_page_number == 0x0
    assert region.page_offset == 0x1F6F
    assert len(region.buffer) == 0x91
    assert region.buffer == 0x91 * b'\x00'


def test_unallocated_pages(repo):
    """
    find physical pages that have no logical page.
    
    Args:
        repo (cim.CIM): the deleted-instance repo

    Returns:
        None
    """
    unmapped_pages = sorted(cim.recovery.find_unallocated_pages(repo))

    # collected empirically.
    assert unmapped_pages == [302, 1164, 1192, 1204, 1210, 1237, 1274, 1284, 1295, 1357, 1623, 1653, 1654, 1658, 1665,
                              1672, 1673, 1675, 1676, 1681, 1684, 1685, 1686, 1687, 1688, 1689, 1690, 1691, 1692, 1693,
                              1694, 1695, 1697, 1698, 1699, 1700, 1701, 1702, 1703, 1704, 1705, 1706, 1707, 1708, 1709,
                              1710, 1711, 1712, 1713, 1714, 1715, 1716, 1717, 1718, 1719, 1720, 1721, 1722, 1723, 1724,
                              1725, 1726, 1727, 1728, 1729, 1730, 1732, 1733, 1734, 1735, 1736, 1737, 1738, 1739, 1740,
                              1741, 1742, 1743, 1744, 1745, 1746, 1747, 1748, 1749, 1750, 1751, 1753, 1754, 1757, 1760,
                              1761, 1762, 1764, 1765, 1767, 1768, 1776, 1781, 1789, 1792, 1795, 1797, 1798, 1799, 1801,
                              1802, 1803, 1805, 1806, 1807, 1808, 1811, 1812, 1813, 1816, 1817, 1818, 1819, 1823, 1825,
                              1826, 1833, 1844, 1846, 1847, 1848, 1849, 1850, 1855, 1856, 1857, 1858, 1859, 1860, 1861,
                              1862, 1863, 1864, 1865, 1866, 1867, 1868, 1869, 1870, 1871, 1872, 1873, 1874, 1875, 1876,
                              1877, 1878, 1879, 1880, 1881, 1882, 1883, 1884, 1885]
