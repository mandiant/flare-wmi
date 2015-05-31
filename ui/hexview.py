# TODO: add multiple color selections.
# TODO: use hash-based color picking
# TODO: add selection "save as binary" action
# TODO: add selection "save as hex dump text" action
# TODO: add "add new origin" action
# TODO: add origin offset status bar entry

from collections import namedtuple

from intervaltree import IntervalTree

from PyQt5 import uic
from PyQt5.QtGui import QBrush
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtGui import QFontDatabase
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtCore import QObject
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QModelIndex
from PyQt5.QtCore import QItemSelection
from PyQt5.QtCore import QItemSelectionModel
from PyQt5.QtCore import QAbstractTableModel
from PyQt5.QtWidgets import QTableView
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QItemDelegate
from PyQt5.QtWidgets import QAbstractItemView

import os.path, sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from common import LoggingObject


ROLE_BORDER = 0xF
BorderData = namedtuple("BorderData", ["top", "bottom", "left", "right", "color"])

class HexItemDelegate(QItemDelegate):
    def __init__(self, model, parent, *args):
        super(HexItemDelegate, self).__init__(parent)
        self._model = model

    def paint(self, qpainter, option, qindex):
        super(HexItemDelegate, self).paint(qpainter, option, qindex)
        border = self._model.data(qindex, ROLE_BORDER)

        if border is None:
            return

        qpainter.setPen(border.color)
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

    def __init__(self, parent):
        super(ColorModel, self).__init__(parent)
        self._db = IntervalTree()

    def color_range(self, range):
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


class HexTableModel(QAbstractTableModel):
    FILTER = ''.join([(len(repr(chr(x)))==3) and chr(x) or '.' for x in range(256)])

    def __init__(self, buf, parent=None, *args):
        super(HexTableModel, self).__init__(parent, *args)
        self._buf = buf
        self._colors = ColorModel(self)

        self._colors.rangeChanged.connect(self._handle_color_range_changed)

        self._colors.color_range(ColoredRange(0x10, 0x20, Qt.red))

    def getColorModel(self):
        return self._colors

    def setColorModel(self, color_model):
        self._colors.rangeChanged.disconnect(self._handle_color_range_changed)
        self._colors = color_model
        self._colors.rangeChanged.connect(self._handle_color_range_changed)
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
            if index.row() == 2:
                return BorderData(True, False, False, False, Qt.red)
            if index.row() == 4:
                return BorderData(False, True, False, False, Qt.blue)
            if index.row() == 6:
                return BorderData(False, False, True, False, Qt.green)
            if index.row() == 8:
                return BorderData(False, False, False, True, Qt.yellow)
            if index.row() == 10:
                return BorderData(True, True, True, True, Qt.black)

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

    def _handle_color_range_changed(self, range):
        for i in xrange(range.begin, range.end):
            # mark data changed to encourage re-rendering of cell
            qib = self.index2qindexb(i)
            qic = self.index2qindexc(i)
            self.dataChanged.emit(qib, qib)
            self.dataChanged.emit(qic, qic)


def row_start_index(index):
    """ get index of the start of the 0x10 byte row containing the given index """
    return index - (index % 0x10)


def row_end_index(index):
    """ get index of the end of the 0x10 byte row containing the given index """
    return index - (index % 0x10) + 0xF


def row_number(index):
    """ get row number of the 0x10 byte row containing the given index """
    return index / 0x10


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
            self.view.setColumnWidth(i, 10)

        self._hsm = HexItemSelectionModel(self._model, self.view)
        self.view.setSelectionModel(self._hsm)

        self._hsm.selectionRangeChanged.connect(self._handle_selection_range_changed)

        f = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        self.view.setFont(f)
        self.statusLabel.setFont(f)

        self.view.setItemDelegate(HexItemDelegate(self._model, self))

    def getModel(self):
        return self._model

    def scrollTo(self, index):
        qi = self._model.index2qindexb(index)
        self.view.scrollTo(qi)

    def _handle_selection_range_changed(self, start_bindex, end_bindex):
        txt = []
        if start_bindex != -1 and end_bindex != -1:
            txt.append("sel: [{:s}, {:s}]".format(hex(start_bindex), hex(end_bindex)))
            txt.append("len: {:s}".format(hex(end_bindex - start_bindex + 1)))
        self.statusLabel.setText(" ".join(txt))


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
