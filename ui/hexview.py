import hexdump

from PyQt5 import uic
from PyQt5.QtGui import QBrush
from PyQt5.QtGui import QPalette
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtGui import QTextDocument
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QAbstractTableModel
from PyQt5.QtCore import QIdentityProxyModel
from PyQt5.QtCore import QItemSelection
from PyQt5.QtCore import QModelIndex
from PyQt5.QtCore import QItemSelectionModel
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QApplication

import os.path, sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from common import h
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
        if not index.is_valid():
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


class HexItemSelectionModel(QItemSelectionModel):
    def isInBytesSide(self, qindex):
        return qindex.column() < 0x10

    def isInCharsSide(self, qindex):
        return qindex.column() > 0x10

    # TODO: currently ignoring selectionFlags...
    def select(self, selection, selectionFlags):
        """
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

        the following via: http://stackoverflow.com/questions/10906950/
                             qt-qitemselectionmodel-to-ignore-columns

        have to handle both QItemSelectionModel.select methods::

            1. select(QtCore.QModelIndex, QItemSelectionModel.SelectionFlags)
            2. select(QtGui.QItemSelection, QItemSelectionModel.SelectionFlags)

        The first seems to run on mouse down and mouse up.
        The second seems to run on mouse down, up and drag
        """
        if isinstance(selection, QItemSelection):
            # This is the overload with the QItemSelection passed to arg 0
            qindexes = selection.indexes()

            bSideCount = sum([1 for i in qindexes if self.isInBytesSide(i)])
            cSideCount = sum([1 for i in qindexes if self.isInCharsSide(i)])

            m = self.model()
            indices = []
            if bSideCount >= cSideCount:
                # we assume the main select in on the left side.
                for qindex in qindexes:
                    if not self.isInBytesSide(qindex):
                        continue
                    indices.append(m.qindex2index(qindex))

            else:
                # we assume the main select in on the left side.
                for qindex in qindexes:
                    if not self.isInCharsSide(qindex):
                        continue
                    indices.append(m.qindex2index(qindex))

            if not indices:
                super(HexItemSelectionModel, self).select(QItemSelection(),
                                                        selectionFlags)
                return
            low = min(indices)
            high = max(indices)
            selection = QItemSelection()
            for i in xrange(low, high):
                qib = m.index2qindexb(i)
                selection.select(qib, qib)
                qic = m.index2qindexc(i)
                selection.select(qic, qic)
            super(HexItemSelectionModel, self).select(selection,
                                                    selectionFlags)


        elif isinstance(selection, QModelIndex):
            # This is the overload with the QModelIndex passed to arg 0
            super(HexItemSelectionModel, self).select(selection,
                                                        selectionFlags)

        else:  # Just in case
            raise Exception("Unexpected type for arg 0: '%s'" % type(selection))


class HexViewWidget(QWidget, LoggingObject):
    def __init__(self, buf, parent=None):
        super(HexViewWidget, self).__init__(parent)
        self._buf = buf
        self._model = HexTableModel(self._buf)

        # TODO: maybe subclass the loaded .ui and use that instance directly
        self._ui = uic.loadUi("ui/hexview.ui")
        self._ui.view.setModel(self._model)
        for i in xrange(0x10):
            self._ui.view.setColumnWidth(i, 25)
        self._ui.view.setColumnWidth(0x10, 12)
        for i in xrange(0x11, 0x22):
            self._ui.view.setColumnWidth(i, 10)

        self._hsm = HexItemSelectionModel(self._model)
        self._ui.view.setSelectionModel(self._hsm)

        f = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        self._ui.view.setFont(f)

        mainLayout = QGridLayout()
        mainLayout.addWidget(self._ui, 0, 0)
        self.setLayout(mainLayout)

    def colorRange(self, start, end):
        """ highlight by buffer indices """
        self._model.colorRange(start, end)

    def scrollTo(self, index):
        qi = self._model.index2qindexb(index)
        self._ui.view.scrollTo(qi)


def main():
    buf = []
    for i in xrange(0x100):
        buf.append(chr(i))


    app = QApplication(sys.argv)
    screen = HexViewWidget2(buf)
    screen.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    import sys
    main(*sys.argv[1:])
