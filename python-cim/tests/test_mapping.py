from fixtures import *

import cim


############ INDEX MAPPING ###############################################


def test_index_mapping(repo):
    """
    demonstrate extraction of basic information from the mapping header.
    
    Args:
        repo (cim.CIM): the deleted-instance repo

    Returns:
        None
    """
    mapping = repo.index_mapping

    # collected empirically.
    assert len(mapping.map.entries) == 7824
    assert mapping.map.free_dword_count == 241
    assert mapping.map.header.physical_page_count == 547
    assert mapping.map.header.mapping_entry_count == 326

    assert mapping.get_physical_page_number(logical_page_number=0) == 13
    assert mapping.get_logical_page_number(physical_page_number=13) == 0


def test_index_mapping_inconsistencies(repo):
    """
    find logical pages where the physical page does not map back to it.
    this is probably where there are two logical pages that point to the
      same physical page.
    
    Args:
        repo (cim.CIM): the deleted-instance repo

    Returns:
        None
    """
    mapping = repo.index_mapping

    # logical pages where the physical page does not map back to it.
    # that is, there must be two logical pages that point here.
    inconsistencies = []
    for i in range(mapping.map.header.mapping_entry_count):
        try:
            pnum = mapping.get_physical_page_number(logical_page_number=i)
            if i != mapping.get_logical_page_number(physical_page_number=pnum):
                inconsistencies.append(i)
        except cim.UnmappedPage:
            continue

    # collected empirically.
    assert inconsistencies == []


def test_unmapped_index_logical_pages(repo):
    """
    find logical pages that have no physical page.
    presumably you can't fetch these pages.
    
    Args:
        repo (cim.CIM): the deleted-instance repo

    Returns:
        None
    """
    mapping = repo.index_mapping

    unmapped_pages = []
    for i in range(mapping.map.header.mapping_entry_count):
        if not mapping.is_logical_page_mapped(i):
            unmapped_pages.append(i)
            continue

    # collected empirically.
    assert unmapped_pages == [91, 160, 201, 202, 203, 204, 205, 206, 207, 208,
                              209, 210, 211, 212, 213, 214, 215, 227, 228, 230]


def test_unallocated_index_physical_pages(repo):
    """
    find physical pages that have no logical page.
    to do this, need to actually reference the size of the index.
    this should contain unallocated data.
    
    Args:
        repo (cim.CIM): the deleted-instance repo

    Returns:
        None
    """
    mapping = repo.index_mapping
    index = repo.logical_index_store

    unmapped_pages = []
    for i in range(index.page_count):
        if not mapping.is_physical_page_mapped(i):
            unmapped_pages.append(i)
            continue

    # collected empirically.
    assert unmapped_pages == [4, 8, 40, 48, 62, 70, 74, 84, 116, 117, 118, 119,
                              122, 126, 131, 132, 134, 142, 153, 156, 159, 161,
                              165, 167, 169, 179, 181, 182, 184, 185, 186, 188,
                              190, 192, 195, 199, 203, 205, 207, 209, 210, 212,
                              213, 214, 216, 217, 218, 225, 230, 232, 234, 238,
                              239, 241, 244, 245, 253, 254, 258, 260, 262, 264,
                              265, 266, 268, 269, 273, 274, 275, 277, 279, 283,
                              284, 286, 292, 293, 294, 295, 296, 301, 309, 311,
                              313, 314, 315, 316, 317, 318, 319, 320, 321, 322,
                              325, 330, 331, 334, 341, 347, 349, 352, 354, 355,
                              357, 358, 365, 366, 367, 372, 373, 375, 379, 380,
                              381, 383, 384, 386, 387, 388, 390, 391, 392, 393,
                              394, 395, 396, 398, 401, 403, 404, 406, 407, 408,
                              409, 410, 414, 415, 417, 419, 420, 422, 424, 425,
                              426, 430, 432, 433, 434, 435, 436, 437, 438, 439,
                              440, 442, 443, 447, 448, 449, 452, 453, 454, 455,
                              456, 457, 458, 459, 460, 461, 462, 463, 464, 465,
                              466, 467, 468, 470, 471, 474, 475, 476, 477, 478,
                              479, 480, 481, 486, 487, 489, 490, 491, 496, 497,
                              498, 499, 500, 501, 502, 503, 504, 505, 506, 507,
                              508, 509, 510, 511, 512, 513, 514, 515, 516, 517,
                              518, 519, 520, 521, 522, 523, 524, 525, 526, 527,
                              528, 529, 530, 531, 532, 533, 534, 535, 536, 537,
                              538, 539, 540, 541, 542, 543, 544, 545, 546]


############ DATA MAPPING ###############################################


def test_data_mapping(repo):
    """
    Args:
        repo (cim.CIM): the deleted-instance repo

    Returns:
        None
    """
    mapping = repo.data_mapping

    # collected empirically.
    assert len(mapping.map.entries) == 41448
    assert mapping.map.free_dword_count == 159
    assert mapping.map.header.physical_page_count == 1886
    assert mapping.map.header.mapping_entry_count == 1727

    assert mapping.get_physical_page_number(logical_page_number=0) == 0
    assert mapping.get_logical_page_number(physical_page_number=0) == 0


def test_data_mapping_inconsistencies(repo):
    """
    find logical pages where the physical page does not map back to it.
    this is probably where there are two logical pages that point to the
      same physical page.
    
    Args:
        repo (cim.CIM): the deleted-instance repo

    Returns:
        None
    """
    mapping = repo.data_mapping

    # logical pages where the physical page does not map back to it.
    # that is, there must be two logical pages that point here.
    inconsistencies = []
    for i in range(mapping.map.header.mapping_entry_count):
        try:
            pnum = mapping.get_physical_page_number(logical_page_number=i)
            if i != mapping.get_logical_page_number(physical_page_number=pnum):
                inconsistencies.append(i)
        except cim.UnmappedPage:
            continue

    # collected empirically.
    assert inconsistencies == []


def test_unmapped_data_logical_pages(repo):
    """
    find logical pages that have no physical page.
    presumably you can't fetch these pages.
    
    Args:
        repo (cim.CIM): the deleted-instance repo

    Returns:
        None
    """
    mapping = repo.index_mapping

    unmapped_pages = []
    for i in range(mapping.map.header.mapping_entry_count):
        if not mapping.is_logical_page_mapped(i):
            unmapped_pages.append(i)
            continue

    # collected empirically.
    assert unmapped_pages == [91, 160, 201, 202, 203, 204, 205, 206, 207, 208,
                              209, 210, 211, 212, 213, 214, 215, 227, 228, 230]


def test_unallocated_data_physical_pages(repo):
    """
    find physical pages that have no logical page.
    to do this, need to actually reference the size of the data store.
    this should contain unallocated data.
    
    Args:
        repo (cim.CIM): the deleted-instance repo

    Returns:
        None
    """
    mapping = repo.data_mapping
    data = repo.logical_data_store

    unmapped_pages = []
    for i in range(data.page_count):
        if not mapping.is_physical_page_mapped(i):
            unmapped_pages.append(i)

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
