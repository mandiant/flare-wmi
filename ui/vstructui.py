# TODO: fix de-color item

import binascii

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtWidgets import QApplication

from common import h
from common import LoggingObject

from vstruct import VStruct
from vstruct import VArray
from vstruct.primitives import v_prim
from vstruct.primitives import v_number
from vstruct.primitives import v_bytes
from vstruct.primitives import v_uint8
from vstruct.primitives import v_uint16
from vstruct.primitives import v_uint32

from ui.tree import TreeModel
from ui.tree import ColumnDef
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
    def struct(self):
        return self._struct

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
        return [VstructItem(i.struct, i.name, i.start) for i in self._items]


UI, Base = uic.loadUiType("ui/vstruct.ui")
class VstructViewWidget(Base, UI, LoggingObject):
    def __init__(self, items, buf, parent=None):
        """ items is a list of VstructItem """
        super(VstructViewWidget, self).__init__(parent)
        self.setupUi(self)

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

        self._hv = HexViewWidget(self._buf, self.splitter)
        self.splitter.insertWidget(0, self._hv)

        tv = self.treeView
        tv.setModel(self._model)
        tv.header().setSectionResizeMode(QHeaderView.Interactive)

        # used for mouse click
        tv.clicked.connect(self._handle_item_clicked)
        # used for keyboard navigation
        tv.selectionModel().selectionChanged.connect(self._handle_item_selected)

        tv.setContextMenuPolicy(Qt.CustomContextMenu)
        tv.customContextMenuRequested.connect(self._handle_context_menu_requested)

        self._current_range = None  # type: Pair[int, int]

    def _clear_current_range(self):
        if self._current_range is None:
            return
        self._hv.getBorderModel().clear_region(*self._current_range)
        self._current_range = None

    def _handle_item_clicked(self, item_index):
        self._handle_item_activated(item_index)

    def _handle_item_selected(self, item_indices):
        # hint found here: http://stackoverflow.com/a/15214966/87207
        if not item_indices.indexes():
            self._clear_current_range()
        else:
            self._handle_item_activated(item_indices.indexes()[0])

    def _color_item(self, item, color=None):
        start = item.start
        end = start + item.length
        self._hv._hsm.bselect(-1, -1)
        return self._hv.getColorModel().color_region(start, end, color)

    def _is_item_colored(self, item):
        start = item.start
        end = start + item.length
        return self._hv.getColorModel().is_region_colored(start, end)

    def _clear_item(self, item):
        start = item.start
        end = start + item.length
        return self._hv.getColorModel().clear_region(start, end)

    def _handle_item_activated(self, item_index):
        self._clear_current_range()
        item = self._model.getIndexData(item_index)
        s = item.start
        e = item.start + item.length
        self._hv.getBorderModel().border_region(s, e, Qt.black)
        self._current_range = (s, e)
        self._hv.scrollTo(s)

    def _handle_context_menu_requested(self, qpoint):
        index = self.treeView.indexAt(qpoint)
        item = index.model().getIndexData(index)

        action = None
        if self._is_item_colored(item):
            action = QAction("De-color item", self)
            action.setStatusTip("de-color item tip")
            action.triggered.connect(lambda: self._handle_clear_color_item(item))
        else:
            action = QAction("Color item", self)
            action.setStatusTip("color item tip")
            action.triggered.connect(lambda: self._handle_color_item(item))

        menu = QMenu(self)
        menu.addAction(action)

        menu.exec_(self.treeView.mapToGlobal(qpoint))

    def _handle_color_item(self, item):
        # remove current selection to make change of color visible
        range = self._color_item(item)

    def _handle_clear_color_item(self, item):
        # remove current selection to make change of color visible
        self._clear_item(item)


def main():
    buf = []
    for i in xrange(0x100):
        buf.append(chr(i))
    buf = "".join(buf)

    class TestStruct(VStruct):
        def __init__(self):
            VStruct.__init__(self)
            self.a = v_uint8()
            self.b = v_uint16()
            self.c = v_uint32()
            self.d = v_uint8()
            self.e = VArray((v_uint32(), v_uint32(), v_uint32(), v_uint32()))

    t1 = TestStruct()
    t1.vsParse(buf, offset=0x0)

    t2 = TestStruct()
    t2.vsParse(buf, offset=0x40)

    app = QApplication(sys.argv)
    screen = VstructViewWidget((VstructItem(t1, "t1", 0x0), VstructItem(t2, "t2", 0x40)), buf)
    screen.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    import sys
    main(*sys.argv[1:])
