# TODO: add "add new origin" action
# TODO: add origin offset status bar entry

import base64
import binascii
from collections import namedtuple
from collections import defaultdict

import hexdump
import intervaltree
from intervaltree import IntervalTree

from PyQt5 import uic
from PyQt5.QtGui import QBrush
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtGui import QFontDatabase
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtCore import QObject
from PyQt5.QtCore import QMimeData
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QModelIndex
from PyQt5.QtCore import QItemSelection
from PyQt5.QtCore import QItemSelectionModel
from PyQt5.QtCore import QAbstractTableModel
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QTableView
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QItemDelegate
from PyQt5.QtWidgets import QAbstractItemView

import os.path, sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from common import LoggingObject
from mutablenamedtuple import mutablenamedtuple
from ui.colortheme import SolarizedColorTheme


def row_start_index(index):
    """ get index of the start of the 0x10 byte row containing the given index """
    return index - (index % 0x10)


def row_end_index(index):
    """ get index of the end of the 0x10 byte row containing the given index """
    return index - (index % 0x10) + 0xF


def row_number(index):
    """ get row number of the 0x10 byte row containing the given index """
    return index / 0x10

def column_number(index):
    return index % 0x10


class HexItemDelegate(QItemDelegate):
    def __init__(self, model, parent, *args):
        super(HexItemDelegate, self).__init__(parent)
        self._model = model

    def paint(self, qpainter, option, qindex):
        super(HexItemDelegate, self).paint(qpainter, option, qindex)
        border = self._model.data(qindex, ROLE_BORDER)

        if border is None:
            return

        qpainter.setPen(border.theme.color)
        r = option.rect
        if border.top:
            qpainter.drawLine(r.topLeft(), r.topRight())

        if border.bottom:
            qpainter.drawLine(r.bottomLeft(), r.bottomRight())

        if border.left:
            qpainter.drawLine(r.topLeft(), r.bottomLeft())

        if border.right:
            qpainter.drawLine(r.topRight(), r.bottomRight())


ColoredRange = namedtuple("ColorRange", ["begin", "end", "color"])


class ColorModel(QObject):
    rangeChanged = pyqtSignal([ColoredRange])

    def __init__(self, parent, color_theme=SolarizedColorTheme):
        super(ColorModel, self).__init__(parent)
        self._db = IntervalTree()
        self._theme = SolarizedColorTheme

    def color_region(self, begin, end, color=None):
        if color is None:
            color = self._theme.get_accent(len(self._db))
        range = ColoredRange(begin, end, color)
        self.color_range(range)
        return range

    def clear_region(self, begin, end):
        span = end - begin
        to_remove = []
        for range in self._db[begin:end]:
            if range.end - range.begin == span:
                to_remove.append(range)
        for range in to_remove:
            self.clear_range(range.data)

    def color_range(self, range):
        # note we use (end + 1) to ensure the entire selection gets captured
        self._db.addi(range.begin, range.end, range)
        self.rangeChanged.emit(range)

    def clear_range(self, range):
        self._db.removei(range.begin, range.end, range)
        self.rangeChanged.emit(range)

    def get_color(self, index):
        # ranges is a (potentially empty) list of intervaltree.Interval instances
        # we sort them here from shorted length to longest, because we want
        #    the most specific color
        ranges = sorted(self._db[index], key=lambda r: r.end - r.begin)
        if len(ranges) > 0:
            return ranges[0].data.color
        return None

    def is_index_colored(self, index):
        return len(self._db[index]) > 0

    def is_region_colored(self, begin, end):
        span = end - begin
        for range in self._db[begin:end]:
            if range.end - range.begin == span:
                return True
        return False


ROLE_BORDER = 0xF
BorderTheme = namedtuple("BorderTheme", ["color"])
BorderData = namedtuple("BorderData", ["top", "bottom", "left", "right", "theme"])
BorderedRange = namedtuple("BorderedRange", ["begin", "end", "theme", "cells"])


CellT = mutablenamedtuple("CellT", ["top", "bottom", "left", "right"])
def Cell(top=False, bottom=False, left=False, right=False):
    return CellT(top, bottom, left, right)


def compute_region_border(start, end):
    # TODO: doc
    cells = defaultdict(Cell)

    start_row = row_number(start)
    end_row = row_number(end)

    ## topmost cells
    if start_row == end_row:
        for i in xrange(start, end):
            cells[i].top = True
    else:
        for i in xrange(start, row_end_index(start) + 1):
            cells[i].top = True
    # cells on second row, top left
    if start_row != end_row:
        next_row_start = row_start_index(start) + 0x10
        for i in xrange(next_row_start, next_row_start + column_number(start)):
            cells[i].top = True

    ## bottommost cells
    if start_row == end_row:
        for i in xrange(start, end):
            cells[i].bottom = True
    else:
        for i in xrange(row_start_index(end), end):
            cells[i].bottom = True
    # cells on second-to-last row, bottom right
    if start_row != end_row:
        prev_row_end = row_end_index(end) - 0x10
        for i in xrange(prev_row_end - (0x10 - column_number(end) - 1), prev_row_end + 1):
            cells[i].bottom = True

    ## leftmost cells
    if start_row == end_row:
        cells[start].left = True
    else:
        second_row_start = row_start_index(start) + 0x10
        for i in xrange(second_row_start, row_start_index(end) + 0x10, 0x10):
            cells[i].left = True
    # cells in first row, top left
    if start_row != end_row:
        cells[start].left = True

    ## rightmost cells
    if start_row == end_row:
        cells[end - 1].right = True
    else:
        penultimate_row_end = row_end_index(end) - 0x10
        for i in xrange(row_end_index(start), penultimate_row_end + 0x10, 0x10):
            cells[i].right = True
    # cells in last row, bottom right
    if start_row != end_row:
        cells[end - 1].right = True

    # convert back to standard dict
    # trick from: http://stackoverflow.com/a/20428703/87207
    cells.default_factory = None
    return cells


class BorderModel(QObject):
    rangeChanged = pyqtSignal([BorderedRange])

    def __init__(self, parent, color_theme=SolarizedColorTheme):
        super(BorderModel, self).__init__(parent)
        self._db = IntervalTree()
        self._theme = SolarizedColorTheme

    def border_region(self, begin, end, color=None):
        if color is None:
            color = self._theme.get_accent(len(self._db))
        range = BorderedRange(begin, end, BorderTheme(color), compute_region_border(begin, end))
        # note we use (end + 1) to ensure the entire selection gets captured
        self._db.addi(range.begin, range.end + 1, range)
        self.rangeChanged.emit(range)

    def clear_region(self, begin, end):
        span = end - begin
        to_remove = []
        for range in self._db[begin:end]:
            if range.end - range.begin - 1 == span:
                to_remove.append(range)
        for range in to_remove:
            self._db.removei(range.begin, range.end, range.data)
            self.rangeChanged.emit(range.data)

    def get_border(self, index):
        # ranges is a (potentially empty) list of intervaltree.Interval instances
        # we sort them here from shorted length to longest, because we want
        #    the most specific border
        ranges = sorted(self._db[index], key=lambda r: r.end - r.begin)
        if len(ranges) > 0:
            range = ranges[0].data
            cell = range.cells.get(index, None)
            if cell is None:
                return None
            ret = BorderData(cell.top, cell.bottom, cell.left, cell.right, range.theme)
            return ret
        return None

    def is_index_bordered(self, index):
        return len(self._db[index]) > 0

    def is_region_bordered(self, begin, end):
        span = end - begin
        for range in self._db[begin:end]:
            if range.end - range.begin == span:
                return True
        return False


class HexTableModel(QAbstractTableModel):
    FILTER = ''.join([(len(repr(chr(x)))==3) and chr(x) or '.' for x in range(256)])

    def __init__(self, buf, parent=None, *args):
        super(HexTableModel, self).__init__(parent, *args)
        self._buf = buf
        self._colors = ColorModel(self)
        self._borders = BorderModel(self)

        self._colors.rangeChanged.connect(self._handle_color_range_changed)
        self._borders.rangeChanged.connect(self._handle_border_range_changed)

    def getColorModel(self):
        return self._colors

    def setColorModel(self, color_model):
        self._colors.rangeChanged.disconnect(self._handle_color_range_changed)
        self._colors = color_model
        self._colors.rangeChanged.connect(self._handle_color_range_changed)
        # TODO: re-render all cells

    def getBorderModel(self):
        return self._borders

    def setBorderModel(self, color_model):
        self._borders.rangeChanged.disconnect(self._handle_border_range_changed)
        self._borders = color_model
        self._borders.rangeChanged.connect(self._handle_border_range_changed)
        # TODO: re-render all cells

    @staticmethod
    def qindex2index(index):
        """ from a QIndex (row/column coordinate system), get the buffer index of the byte """
        r = index.row()
        c = index.column()
        if c > 0x10:
            return (0x10 * r) + c - 0x11
        else:
            return (0x10 * r) + c

    def index2qindexb(self, index):
        """ from a buffer index, get the QIndex (row/column coordinate system) of the byte pane """
        r = index // 0x10
        c = index % 0x10
        return self.index(r, c)

    def index2qindexc(self, index):
        """ from a buffer index, get the QIndex (row/column coordinate system) of the char pane """
        r = (index // 0x10)
        c = index % 0x10 + 0x11
        return self.index(r, c)

    def rowCount(self, parent):
        if len(self._buf) % 0x10 != 0:
            return (len(self._buf) // 0x10) + 1
        else:
            return len(self._buf) // 0x10

    def columnCount(self, parent):
        return 0x21

    def data(self, index, role):
        if not index.isValid():
            return None

        elif self.qindex2index(index) >= len(self._buf):
            return None

        bindex = self.qindex2index(index)
        if role == Qt.BackgroundRole:
            # don't color the divider column
            if index.column() == 0x10:
                return None

            color = self._colors.get_color(bindex)
            if color is not None:
                return QBrush(color)
            return None

        elif role == Qt.DisplayRole:
            if index.column() == 0x10:
                return ""

            c = ord(self._buf[bindex])
            if index.column() > 0x10:
                return chr(c).translate(HexTableModel.FILTER)
            else:
                return "%02x" % (c)

        elif role == ROLE_BORDER:
            if index.column() == 0x10:
                return None

            return self._borders.get_border(bindex)

        else:
            return None

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return None

        elif orientation == Qt.Horizontal:
            if section < 0x10:
                return "%01X" % (section)
            else:
                return ""
        elif orientation == Qt.Vertical:
            return "%04X" % (section * 0x10)

        else:
            return None

    def _emit_data_changed(self, start_bindex, end_bindex):
        for i in xrange(start_bindex, end_bindex):
            # mark data changed to encourage re-rendering of cell
            qib = self.index2qindexb(i)
            qic = self.index2qindexc(i)
            self.dataChanged.emit(qib, qib)
            self.dataChanged.emit(qic, qic)

    def _handle_color_range_changed(self, range):
        self._emit_data_changed(range.begin, range.end + 1)

    def _handle_border_range_changed(self, range):
        self._emit_data_changed(range.begin, range.end + 1)


class HexItemSelectionModel(QItemSelectionModel):
    selectionRangeChanged = pyqtSignal([int, int])

    def __init__(self, model, view):
        """
        :type view: HexTableView
        """
        super(HexItemSelectionModel, self).__init__(model)
        self._model = model
        self._view = view

        self._start_qindex = None
        self._view.leftMousePressedIndex.connect(self._handle_mouse_pressed)
        self._view.leftMouseMovedIndex.connect(self._handle_mouse_moved)
        self._view.leftMouseReleasedIndex.connect(self._handle_mouse_released)

        self.start = None
        self.end = None

    def _bselect(self, selection, start_bindex, end_bindex):
        """ add the given buffer indices to the given QItemSelection, both byte and char panes """
        selection.select(self._model.index2qindexb(start_bindex), self._model.index2qindexb(end_bindex))
        selection.select(self._model.index2qindexc(start_bindex), self._model.index2qindexc(end_bindex))

    def _do_select(self, start_bindex, end_bindex):
        """
        select the given range by buffer indices

        selects items like this:

            ..................
            ......xxxxxxxxxxxx
            xxxxxxxxxxxxxxxxxx
            xxxxxxxxxxxxxxxxxx
            xxxxxxxxxxxx......
            ..................

        *not* like this:

            ..................
            ......xxxxxx......
            ......xxxxxx......
            ......xxxxxx......
            ......xxxxxx......
            ..................
         """
        self.select(QItemSelection(), QItemSelectionModel.Clear)
        if start_bindex > end_bindex:
            start_bindex, end_bindex = end_bindex, start_bindex

        selection = QItemSelection()
        if row_number(end_bindex) - row_number(start_bindex) == 0:
            # all on one line
            self._bselect(selection, start_bindex, end_bindex)
        elif row_number(end_bindex) - row_number(start_bindex) == 1:
            # two lines
            self._bselect(selection, start_bindex, row_end_index(start_bindex))
            self._bselect(selection, row_start_index(end_bindex), end_bindex)
        else:
            # many lines
            self._bselect(selection, start_bindex, row_end_index(start_bindex))
            self._bselect(selection, row_start_index(start_bindex) + 0x10, row_end_index(end_bindex) - 0x10)
            self._bselect(selection, row_start_index(end_bindex), end_bindex)

        self.select(selection, QItemSelectionModel.SelectCurrent)
        self.selectionRangeChanged.emit(start_bindex, end_bindex)
        self.start = start_bindex
        self.end = end_bindex

    def bselect(self, start_bindex, end_bindex):
        """  the public interface to _do_select """
        return self._do_select(start_bindex, end_bindex)

    def _update_selection(self, qindex1, qindex2):
        """  select the given range by qmodel indices """
        m = self.model()
        self._do_select(m.qindex2index(qindex1), m.qindex2index(qindex2))

    def _handle_mouse_pressed(self, qindex):
        self._start_qindex = qindex
        self._update_selection(qindex, qindex)

    def _handle_mouse_moved(self, qindex):
        self._update_selection(self._start_qindex, qindex)

    def _handle_mouse_released(self, qindex):
        self._update_selection(self._start_qindex, qindex)
        self._start_qindex = None


class HexTableView(QTableView, LoggingObject):
    """ table view that handles click events for better selection handling """
    leftMousePressed = pyqtSignal([QMouseEvent])
    leftMousePressedIndex = pyqtSignal([QModelIndex])
    leftMouseMoved = pyqtSignal([QMouseEvent])
    leftMouseMovedIndex = pyqtSignal([QModelIndex])
    leftMouseReleased = pyqtSignal([QMouseEvent])
    leftMouseReleasedIndex = pyqtSignal([QModelIndex])

    def __init__(self, *args, **kwargs):
        super(HexTableView, self).__init__(*args, **kwargs)
        self.leftMousePressed.connect(self._handle_mouse_press)
        self.leftMouseMoved.connect(self._handle_mouse_move)
        self.leftMouseReleased.connect(self._handle_mouse_release)

        self._pressStartIndex = None
        self._pressCurrentIndex = None
        self._pressEndIndex = None
        self._isTrackingMouse = False

    def _resetPressState(self):
        self._pressStartIndex = None
        self._pressCurrentIndex = None
        self._pressEndIndex = None

    def mousePressEvent(self, event):
        super(HexTableView, self).mousePressEvent(event)
        if event.buttons() & Qt.LeftButton:
            self.leftMousePressed.emit(event)

    def mouseMoveEvent(self, event):
        super(HexTableView, self).mouseMoveEvent(event)
        if event.buttons() & Qt.LeftButton:
            self.leftMouseMoved.emit(event)

    def mouseReleaseEvent(self, event):
        super(HexTableView, self).mousePressEvent(event)
        if event.buttons() & Qt.LeftButton:
            self.leftMouseReleased.emit(event)

    def _handle_mouse_press(self, key_event):
        self._resetPressState()

        self._pressStartIndex = self.indexAt(key_event.pos())
        self._isTrackingMouse = True

        self.leftMousePressedIndex.emit(self._pressStartIndex)

    def _handle_mouse_move(self, key_event):
        if self._isTrackingMouse:
            i = self.indexAt(key_event.pos())
            if i != self._pressCurrentIndex:
                self._pressCurrentIndex = i
                self.leftMouseMovedIndex.emit(i)

    def _handle_mouse_release(self, key_event):
        self._pressEndIndex = self.indexAt(key_event.pos())
        self._isTrackingMouse = False

        self.leftMouseReleasedIndex.emit(self._pressEndIndex)


# reference: http://stackoverflow.com/questions/10612467/pyqt4-custom-widget-uic-loaded-added-to-layout-is-invisible
UI, Base = uic.loadUiType("ui/hexview.ui")
class HexViewWidget(Base, UI, LoggingObject):
    def __init__(self, buf, parent=None):
        super(HexViewWidget, self).__init__(parent)
        self.setupUi(self)
        self._buf = buf
        self._model = HexTableModel(self._buf)

        self._colored_regions = intervaltree.IntervalTree()

        # ripped from pyuic5 ui/hexview.ui
        #   at commit 6c9edffd32706097d7eba8814d306ea1d997b25a
        # so we can add our custom HexTableView instance
        self.view = HexTableView(self)
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.view.sizePolicy().hasHeightForWidth())
        self.view.setSizePolicy(sizePolicy)
        self.view.setMinimumSize(QSize(660, 0))
        self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setSelectionMode(QAbstractItemView.NoSelection)
        self.view.setShowGrid(False)
        self.view.setWordWrap(False)
        self.view.setObjectName("view")
        self.view.horizontalHeader().setDefaultSectionSize(25)
        self.view.horizontalHeader().setMinimumSectionSize(25)
        self.view.verticalHeader().setDefaultSectionSize(21)
        self.mainLayout.insertWidget(0, self.view)
        # end rip

        # TODO: provide a HexViewWidget.setModel method, and don't build it ourselves
        self.view.setModel(self._model)
        for i in xrange(0x10):
            self.view.setColumnWidth(i, 23)
        self.view.setColumnWidth(0x10, 12)
        for i in xrange(0x11, 0x22):
            self.view.setColumnWidth(i, 11)

        self._hsm = HexItemSelectionModel(self._model, self.view)
        self.view.setSelectionModel(self._hsm)

        self.view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self._handle_context_menu_requested)

        self._hsm.selectionRangeChanged.connect(self._handle_selection_range_changed)

        f = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        self.view.setFont(f)
        self.statusLabel.setFont(f)

        self.view.setItemDelegate(HexItemDelegate(self._model, self))

        self.statusLabel.setText("")

    def getModel(self):
        return self._model

    def getColorModel(self):
        """ this is a shortcut, to make it easy to add/remove colored ranges """
        return self.getModel().getColorModel()

    def getBorderModel(self):
        """ this is a shortcut, to make it easy to add/remove bordered ranges """
        return self.getModel().getBorderModel()

    def getSelectionModel(self):
        return self._hsm

    def scrollTo(self, index):
        qi = self._model.index2qindexb(index)
        self.view.scrollTo(qi)

    def _handle_selection_range_changed(self, start_bindex, end_bindex):
        txt = []
        if start_bindex != -1 and end_bindex != -1:
            txt.append("sel: [{:s}, {:s}]".format(hex(start_bindex), hex(end_bindex)))
            txt.append("len: {:s}".format(hex(end_bindex - start_bindex + 1)))
        self.statusLabel.setText(" ".join(txt))

    def _handle_context_menu_requested(self, qpoint):
        menu = QMenu(self)

        color_selection_action = QAction("Color selection", self)
        color_selection_action.triggered.connect(self._handle_color_selection)
        menu.addAction(color_selection_action)

        menu.addSeparator()

        copy_binary_action = QAction("Copy selection (binary)", self)
        copy_binary_action.triggered.connect(self._handle_copy_binary)
        menu.addAction(copy_binary_action)

        copy_menu = menu.addMenu("Copy...")
        copy_menu.addAction(copy_binary_action)

        copy_text_action= QAction("Copy selection (text)", self)
        copy_text_action.triggered.connect(self._handle_copy_text)
        copy_menu.addAction(copy_text_action)

        copy_hex_action = QAction("Copy selection (hex)", self)
        copy_hex_action.triggered.connect(self._handle_copy_hex)
        copy_menu.addAction(copy_hex_action)

        copy_hexdump_action = QAction("Copy selection (hexdump)", self)
        copy_hexdump_action.triggered.connect(self._handle_copy_hexdump)
        copy_menu.addAction(copy_hexdump_action)

        copy_base64_action = QAction("Copy selection (base64)", self)
        copy_base64_action.triggered.connect(self._handle_copy_base64)
        copy_menu.addAction(copy_base64_action)

        menu.exec_(self.view.mapToGlobal(qpoint))

    def _handle_color_selection(self):
        s = self._hsm.start
        e = self._hsm.end
        range = self.getColorModel().color_region(s, e)
        self.getBorderModel().border_region(s, e, Qt.black)
        # seems to be a bit of duplication here and in the ColorModel?
        self._colored_regions.addi(s, e, range)

    @property
    def _selected_data(self):
        start = self._hsm.start
        end = self._hsm.end
        return self._buf[start:end]

    def _handle_copy_binary(self):
        mime = QMimeData()
        # mime type suggested here: http://stackoverflow.com/a/6783972/87207
        mime.setData("application/octet-stream", self._selected_data)
        QApplication.clipboard().setMimeData(mime)

    def _handle_copy_text(self):
        mime = QMimeData()
        mime.setText(self._selected_data)
        QApplication.clipboard().setMimeData(mime)

    def _handle_copy_hex(self):
        mime = QMimeData()
        mime.setText(binascii.b2a_hex(self._selected_data))
        QApplication.clipboard().setMimeData(mime)

    def _handle_copy_hexdump(self):
        mime = QMimeData()
        t = hexdump.hexdump(self._selected_data, result="return")
        mime.setText(t)
        QApplication.clipboard().setMimeData(mime)

    def _handle_copy_base64(self):
        mime = QMimeData()
        mime.setText(base64.b64encode(self._selected_data))
        QApplication.clipboard().setMimeData(mime)


def main():
    buf = []
    for i in xrange(0x100):
        buf.append(chr(i))


    app = QApplication(sys.argv)
    screen = HexViewWidget(buf)
    screen.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    import sys
    main(*sys.argv[1:])
