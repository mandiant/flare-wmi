import hexdump

from PyQt5 import uic
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtGui import QTextDocument
from PyQt5.QtCore import Qt
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


class HexViewWidget(QWidget, LoggingObject):
    def __init__(self, buf, parent=None):
        super(HexViewWidget, self).__init__(parent)
        self._buf = buf
        layout = QGridLayout()
        te = QTextEdit()
        te.setReadOnly(True)
        f = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        td = QTextDocument()
        td.setDefaultFont(f)
        td.setPlainText(hexdump.hexdump(buf, result="return"))
        te.setDocument(td)
        layout.addWidget(te, 0, 0)
        self.setLayout(layout)


class HexTableModel(QAbstractTableModel):
    def __init__(self, buf, parent=None, *args):
        super(HexTableModel, self).__init__(parent, *args)
        self._buf = buf

    def rowCount(self, parent):
        if len(self._buf) % 0x10 != 0:
            return (len(self._buf) // 0x10) + 1
        else:
            return (len(self._buf) // 0x10)

    def columnCount(self, parent):
        return 0x10

    def data(self, index, role):
        if not index.isValid():
            return None
        elif role != Qt.DisplayRole:
            return None
        return ord(self._buf[(index.row() * 0x10) + index.column()])

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return None
        elif orientation == Qt.Horizontal:
            return "%01X" % (section)
        elif orientation == Qt.Vertical:
            return "%04X" % (section * 0x10)
        else:
            return None


class ByteProxyModel(QIdentityProxyModel):
    def data(self, index, role):
        c = self.sourceModel().data(index, role)
        if c is None:
            return None
        else:
            return "%02x" % (c)


class CharProxyModel(QIdentityProxyModel):
    FILTER = ''.join([(len(repr(chr(x)))==3) and chr(x) or '.' for x in range(256)])
    def data(self, index, role):
        c = self.sourceModel().data(index, role)
        if c is None:
            return None
        else:
            return chr(c).translate(CharProxyModel.FILTER)

class RollingItemSelectionModel(QItemSelectionModel):
    def qindex2index(self, index):
        m = self.model()
        return (m.columnCount() * index.row()) + index.column()

    def index2qindex(self, index):
        m = self.model()
        r = index // m.columnCount()
        c = index % m.columnCount()
        return m.index(r, c)

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
            indices = []

            for i in xrange(len(qindexes)):
                qindex = qindexes[i]
                indices.append(self.qindex2index(qindex))

            if indices:
                low = min(indices)
                high = max(indices)

                selection = QItemSelection()
                for i in xrange(low, high):
                    qi = self.index2qindex(i)
                    selection.select(qi, qi)
        elif isinstance(selection, QModelIndex):
            # This is the overload with the QModelIndex passed to arg 0
            pass

        else:  # Just in case
            raise Exception("Unexpected type for arg 0: '%s'" % type(selection))

        # Fall through. Select as normal
        super(RollingItemSelectionModel, self).select(selection, selectionFlags)


class HexViewWidget2(QWidget, LoggingObject):
    def __init__(self, buf, parent=None):
        super(HexViewWidget2, self).__init__(parent)
        self._buf = buf
        self._model = HexTableModel(self._buf)

        self._cp = CharProxyModel()
        self._cp.setSourceModel(self._model)

        self._bp = ByteProxyModel()
        self._bp.setSourceModel(self._model)

        # TODO: maybe subclass the loaded .ui and use that instance directly
        self._ui = uic.loadUi("ui/hexview.ui")
        self._ui.byteView.setModel(self._bp)
        self._ui.charView.setModel(self._cp)

        bvsb = self._ui.byteView.verticalScrollBar()
        cvsb = self._ui.charView.verticalScrollBar()

        bvsb.valueChanged.connect(cvsb.setValue)
        cvsb.valueChanged.connect(bvsb.setValue)

        self._bsm = RollingItemSelectionModel(self._bp)
        self._csm = RollingItemSelectionModel(self._cp)
        self._bsm.selectionChanged.connect(self._handleByteSelectionChanged)
        self._csm.selectionChanged.connect(self._handleCharSelectionChanged)

        self._ui.byteView.setSelectionModel(self._bsm)
        self._ui.charView.setSelectionModel(self._csm)

        mainLayout = QGridLayout()
        mainLayout.addWidget(self._ui, 0, 0)
        self.setLayout(mainLayout)

    def _handleSelectionChanged(self, selected, deselected):
        self._bsm.select(selected, QItemSelectionModel.SelectCurrent)
        self._csm.select(selected, QItemSelectionModel.SelectCurrent)

    def _handleByteSelectionChanged(self, selected, deselected):
        bytesSelectedIndices = set([])
        for qi in selected.indexes():
            bytesSelectedIndices.add(self._bsm.qindex2index(qi))

        charsSelectedIndices = set([])
        for qi in self._csm.selection().indexes():
            charsSelectedIndices.add(self._csm.qindex2index(qi))

        if bytesSelectedIndices == charsSelectedIndices:
            print("breaking cycle")
            return

        selection = QItemSelection()
        for i in bytesSelectedIndices:
            qi = self._bsm.index2qindex(i)
            selection.select(qi, qi)
        print("updating chars from bytes selection update")
        self._csm.select(selection, QItemSelectionModel.Select)

    def _handleCharSelectionChanged(self, selected, deselected):
        charsSelectedIndices = set([])
        for qi in selected.indexes():
            charsSelectedIndices.add(self._csm.qindex2index(qi))

        bytesSelectedIndices = set([])
        for qi in self._bsm.selection().indexes():
            bytesSelectedIndices.add(self._bsm.qindex2index(qi))

        if bytesSelectedIndices == charsSelectedIndices:
            print("breaking cycle")
            return

        selection = QItemSelection()
        for i in bytesSelectedIndices:
            qi = self._bsm.index2qindex(i)
            selection.select(qi, qi)
        print("updating bytes from char selection update")
        self._bsm.select(selection, QItemSelectionModel.Select)


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
