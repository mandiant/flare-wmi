from PyQt5 import uic
from PyQt5.QtGui import QBrush
from PyQt5.QtGui import QPalette
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtGui import QFontDatabase
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QModelIndex
from PyQt5.QtCore import QItemSelection
from PyQt5.QtCore import QItemSelectionModel
from PyQt5.QtCore import QAbstractTableModel
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QTableView
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QAbstractItemView

import os.path, sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from common import LoggingObject


class HexTableModel(QAbstractTableModel):
    FILTER = ''.join([(len(repr(chr(x)))==3) and chr(x) or '.' for x in range(256)])
    colorChanged = pyqtSignal()
    def __init__(self, buf, parent=None, *args):
        super(HexTableModel, self).__init__(parent, *args)
        self._buf = buf
        self._colorStart = None
        self._colorEnd = None

    def rowCount(self, parent):
        if len(self._buf) % 0x10 != 0:
            return (len(self._buf) // 0x10) + 1
        else:
            return (len(self._buf) // 0x10)

    def columnCount(self, parent):
        return 0x21

    def data(self, index, role):
        if not index.isValid():
            return None
        elif self.qindex2index(index) >= len(self._buf):
            return None
        elif role == Qt.BackgroundRole:
            if self._colorStart is None or self._colorEnd is None:
                return None
            elif self._colorStart <= self.qindex2index(index) < self._colorEnd:
                color = QApplication.palette().color(QPalette.Highlight)
                return QBrush(color)
            else:
                return None
        elif role == Qt.DisplayRole:
            if index.column() == 0x10:
                return ""
            if index.column() > 0x10:
                c = self._buf[self.qindex2index(index)]
                return chr(ord(c)).translate(HexTableModel.FILTER)
            else:
                c = ord(self._buf[self.qindex2index(index)])
                return "%02x" % (c)

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

    def colorRange(self, start, end):
        self.clearColor()
        self._colorStart = start
        self._colorEnd = end
        for i in xrange(start, end):
            # mark data changed to encourage re-rendering of cell
            qib = self.index2qindexb(i)
            qic = self.index2qindexc(i)
            self.dataChanged.emit(qib, qib)
            self.dataChanged.emit(qic, qic)
        self.colorChanged.emit()

    def clearColor(self):
        oldstart = self._colorStart
        oldend = self._colorEnd
        self._colorStart = None
        self._colorEnd = None
        if oldstart is not None and oldend is not None:
            # mark data changed to encourage re-rendering of cell
            for i in xrange(oldstart, oldend):
                qib = self.index2qindexb(i)
                qic = self.index2qindexc(i)
                self.dataChanged.emit(qib, qib)
                self.dataChanged.emit(qic, qic)
        self.colorChanged.emit()

    def qindex2index(self, index):
        if index.column() > 0x10:
            return (0x10 * index.row()) + index.column() - 0x11
        else:
            return (0x10 * index.row()) + index.column()

    def index2qindexb(self, index):
        """ for the byte side """
        r = index // 0x10
        c = index % 0x10
        return self.index(r, c)

    def index2qindexc(self, index):
        """ for the char side """
        r = (index // 0x10)
        c = index % 0x10 + 0x11
        return self.index(r, c)


def row_start_index(index):
    return index - (index % 0x10)

def row_end_index(index):
    return index - (index % 0x10) + 0xF

def row_number(index):
    return index / 0x10


class HexItemSelectionModel(QItemSelectionModel):
    def __init__(self, model, view):
        """
        :type view: HexTableView
        """
        super(HexItemSelectionModel, self).__init__(model)
        self._model = model
        self._view = view

        self._start_qindex = None
        self._view.mousePressedIndex.connect(self._handle_mouse_pressed)
        self._view.mouseMovedIndex.connect(self._handle_mouse_moved)
        self._view.mouseReleasedIndex.connect(self._handle_mouse_released)

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
    mousePressed = pyqtSignal([QMouseEvent])
    mousePressedIndex = pyqtSignal([QModelIndex])
    mouseMoved = pyqtSignal([QMouseEvent])
    mouseMovedIndex = pyqtSignal([QModelIndex])
    mouseReleased = pyqtSignal([QMouseEvent])
    mouseReleasedIndex = pyqtSignal([QModelIndex])

    def __init__(self, *args, **kwargs):
        super(HexTableView, self).__init__(*args, **kwargs)
        self.mousePressed.connect(self._handle_mouse_press)
        self.mouseMoved.connect(self._handle_mouse_move)
        self.mouseReleased.connect(self._handle_mouse_release)

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
        self.mousePressed.emit(event)

    def mouseMoveEvent(self, event):
        super(HexTableView, self).mouseMoveEvent(event)
        self.mouseMoved.emit(event)

    def mouseReleaseEvent(self, event):
        super(HexTableView, self).mousePressEvent(event)
        self.mouseReleased.emit(event)

    def _handle_mouse_press(self, key_event):
        self._resetPressState()

        self._pressStartIndex = self.indexAt(key_event.pos())
        self._isTrackingMouse = True

        self.mousePressedIndex.emit(self._pressStartIndex)

    def _handle_mouse_move(self, key_event):
        if self._isTrackingMouse:
            i = self.indexAt(key_event.pos())
            if i != self._pressCurrentIndex:
                self._pressCurrentIndex = i
                self.mouseMovedIndex.emit(i)

    def _handle_mouse_release(self, key_event):
        self._pressEndIndex = self.indexAt(key_event.pos())
        self._isTrackingMouse = False

        self.mouseReleasedIndex.emit(self._pressEndIndex)


class HexViewWidget(QWidget, LoggingObject):
    def __init__(self, buf, parent=None):
        super(HexViewWidget, self).__init__(parent)
        self._buf = buf
        self._model = HexTableModel(self._buf)

        # TODO: maybe subclass the loaded .ui and use that instance directly
        self._ui = uic.loadUi("ui/hexview.ui")

        # ripped from pyuic5 ui/hexview.ui
        #   at commit 6c9edffd32706097d7eba8814d306ea1d997b25a
        self.view = HexTableView(self._ui)
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
        self._ui.horizontalLayout.addWidget(self.view)
        # end rip

        self.view.setModel(self._model)
        for i in xrange(0x10):
            self.view.setColumnWidth(i, 23)
        self.view.setColumnWidth(0x10, 12)
        for i in xrange(0x11, 0x22):
            self.view.setColumnWidth(i, 10)

        self._hsm = HexItemSelectionModel(self._model, self.view)
        self.view.setSelectionModel(self._hsm)

        f = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        self.view.setFont(f)

        mainLayout = QGridLayout()
        mainLayout.addWidget(self._ui, 0, 0)
        self.setLayout(mainLayout)

        selection = QItemSelection()

        selection.select(self._model.index2qindexb(0x12), self._model.index2qindexb(0x1F))
        selection.select(self._model.index2qindexb(0x20), self._model.index2qindexb(0x2F))
        selection.select(self._model.index2qindexb(0x30), self._model.index2qindexb(0x33))

        self._hsm.select(selection, QItemSelectionModel.SelectCurrent)

    def colorRange(self, start, end):
        """ highlight by buffer indices """
        self._model.colorRange(start, end)

    def scrollTo(self, index):
        qi = self._model.index2qindexb(index)
        self.view.scrollTo(qi)


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
