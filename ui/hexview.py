import hexdump
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtGui import QTextDocument
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QTextEdit

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


