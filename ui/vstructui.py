import binascii

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtWidgets import QGridLayout

from common import h
from common import LoggingObject
from vstruct import VStruct
from vstruct.primitives import v_prim
from vstruct.primitives import v_number
from vstruct.primitives import v_bytes
from ui.tree import TreeModel
from ui.tree import ColumnDef
from ui.uicommon import emptyLayout
from ui.hexview import HexViewWidget


class Item(object):
    """ interface """

    def __init__(self):
        pass

    def __repr__(self):
        raise NotImplementedError()

    @property
    def children(self):
        return []

    @property
    def name(self):
        raise NotImplementedError()

    @property
    def type(self):
        raise NotImplementedError()

    @property
    def data(self):
        raise NotImplementedError()

    @property
    def start(self):
        raise NotImplementedError()

    @property
    def length(self):
        raise NotImplementedError()

    @property
    def end(self):
        raise NotImplementedError()


class VstructItem(Item):
    def __init__(self, struct, name, start):
        super(VstructItem, self).__init__()
        self._struct = struct
        self._name = name
        self._start = start

    def __repr__(self):
        return "VstructItem(name: {:s}, type: {:s}, start: {:s}, length: {:s}, end: {:s})".format(
                    self.name,
                    self.type,
                    h(self.start),
                    h(self.length),
                    h(self.end),
                )

    @property
    def children(self):
        ret = []
        if isinstance(self._struct, VStruct):
            off = self.start
            # TODO: don't reach
            for fname in self._struct._vs_fields:
                x = self._struct._vs_values.get(fname)
                # TODO: merge these
                if isinstance(x, VStruct):
                    ret.append(VstructItem(x, fname, off))
                else:
                    ret.append(VstructItem(x, fname, off))
                off += len(x)
        return ret

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._struct.__class__.__name__

    @property
    def data(self):
        if isinstance(self._struct, VStruct):
            return ""
        elif isinstance(self._struct, v_number):
            return h(self._struct.vsGetValue())
        elif isinstance(self._struct, v_bytes):
            return binascii.b2a_hex(self._struct.vsGetValue())
        elif isinstance(self._struct, v_prim):
            return self._struct.vsGetValue()
        else:
            return ""

    @property
    def start(self):
        return self._start

    @property
    def length(self):
        return len(self._struct)

    @property
    def end(self):
        return self.start + self.length


class VstructRootItem(Item):
    def __init__(self, items):
        super(VstructRootItem, self).__init__()
        self._items = items

    def __repr__(self):
        return "VstructRootItem()"

    @property
    def children(self):
        return [VstructItem(i.struct, i.name, i.offset) for i in self._items]


class VstructViewWidget(QWidget, LoggingObject):
    def __init__(self, items, buf, parent=None):
        """ items is a list of VstructItem """
        super(VstructViewWidget, self).__init__(parent)
        self._items = items
        self._buf = buf
        self._model = TreeModel(
                VstructRootItem(items),
                [
                    ColumnDef("Name", "name"),
                    ColumnDef("Type", "type"),
                    ColumnDef("Data", "data"),
                    ColumnDef("Start", "start", formatter=h),
                    ColumnDef("Length", "length", formatter=h),
                    ColumnDef("End", "end", formatter=h),
                ])

        # TODO: maybe subclass the loaded .ui and use that instance directly
        self._ui = uic.loadUi("ui/vstruct.ui")
        emptyLayout(self._ui.detailsLayout)

        self._hv = HexViewWidget(self._buf, self._ui.detailsFrame)
        self._ui.detailsLayout.addWidget(self._hv)

        tv = self._ui.treeView
        tv.setModel(self._model)
        tv.header().setSectionResizeMode(QHeaderView.Interactive)
        tv.entered.connect(self._handleItemActivated)
        tv.clicked.connect(self._handleItemActivated)
        tv.activated.connect(self._handleItemActivated)

        mainLayout = QGridLayout()
        mainLayout.addWidget(self._ui, 0, 0)
        self.setLayout(mainLayout)

    def _handleItemActivated(self, itemIndex):
        item = self._model.getIndexData(itemIndex)
        start = item.start
        end = start + item.length
        self._hv.colorRange(start, end)
        self._hv.scrollTo(start)
