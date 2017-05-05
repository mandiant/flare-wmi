import os
import logging
import traceback
from collections import namedtuple

from funcy.objects import cached_property
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QApplication
from PyQt5 import uic
from PyQt5.QtCore import QDir
from hexview import HexViewWidget
from vstructui import VstructViewWidget
from vstructui import get_parsers
from vstructui import VstructInstance
from vstruct.primitives import v_bytes
from vstruct.primitives import v_zstr

from cim import CIM
from cim import Key
from cim import Index
from cim import IndexPage
from cim import INDEX_PAGE_TYPES
from cim.objects import TreeNamespace
from cim.objects import TreeClassDefinition
from cim.objects import ObjectResolver
from cim.objects import ObjectPath
from cim.common import h
from cim.common import LoggingObject
from cim.formatters import dump_instance
from cim.formatters import dump_layout

from ui.tree import Item
from ui.tree import TreeModel
from ui.tree import ColumnDef
from ui.uicommon import emptyLayout

Context = namedtuple("Context", ["cim", "index", "object_resolver"])


class PhysicalDataPageItem(Item):
    def __init__(self, ctx, index):
        super(PhysicalDataPageItem, self).__init__()
        self._ctx = ctx
        self.index = index

    def __repr__(self):
        return "PhysicalDataPageItem(index: {:s})".format(h(self.index))

    @property
    def children(self):
        return []

    @property
    def type(self):
        return "meta.physicalDataPage"

    @property
    def name(self):
        return "{:s}".format(h(self.index))

    @property
    def data(self):
        return self._ctx.cim.logical_data_store.get_physical_page_buffer(self.index)


class PhysicalDataPagesItem(Item):
    def __init__(self, ctx):
        super(PhysicalDataPagesItem, self).__init__()
        self._ctx = ctx

    def __repr__(self):
        return "PhysicalDataPagesItem(numEntries: {:s})".format(
            h(len(self.children)))

    @cached_property
    def children(self):
        return [PhysicalDataPageItem(self._ctx, i) for i in
                range(self._ctx.cim.data_mapping.map.header.physical_page_count)]

    @property
    def type(self):
        return "meta"

    @property
    def name(self):
        return "Physical Data Pages"


class LogicalDataPageItem(Item):
    def __init__(self, ctx, index):
        super(LogicalDataPageItem, self).__init__()
        self._ctx = ctx
        self.index = index

    def __repr__(self):
        return "LogicalDataPageItem(index: {:s})".format(h(self.index))

    @property
    def children(self):
        return []

    @property
    def type(self):
        return "meta.logicalDataPage"

    @property
    def name(self):
        return "{:s}".format(h(self.index))

    @property
    def data(self):
        return self._ctx.cim.logical_data_store.get_logical_page_buffer(self.index)

    @property
    def structs(self):
        page = self._ctx.cim.logical_data_store.get_page(self.index)
        ret = [
            VstructInstance(0x0, page.toc, "toc"),
        ]
        for i, data in enumerate(page.objects):
            vbuf = v_bytes(size=len(data.buffer))
            vbuf.vsParse(data.buffer)
            ret.append(VstructInstance(data.offset, vbuf, "Object {:s}".format(h(i))))
        return ret


class LogicalDataPagesItem(Item):
    def __init__(self, ctx):
        super(LogicalDataPagesItem, self).__init__()
        self._ctx = ctx

    def __repr__(self):
        return "LogicalDataPagesItem(numEntries: {:s})".format(
            h(len(self.children)))

    @cached_property
    def children(self):
        return [LogicalDataPageItem(self._ctx, i) for i in
                range(self._ctx.cim.data_mapping.map.header.mapping_entry_count)]

    @property
    def type(self):
        return "meta"

    @property
    def name(self):
        return "Logical Data Pages"


class PhysicalIndexPageItem(Item):
    def __init__(self, ctx, index):
        super(PhysicalIndexPageItem, self).__init__()
        self._ctx = ctx
        self.index = index

    def __repr__(self):
        return "PhysicalIndexPageItem(index: {:s})".format(h(self.index))

    @property
    def children(self):
        return []

    @property
    def type(self):
        return "meta.physicalIndexPage"

    @property
    def name(self):
        return "{:s}".format(h(self.index))

    @property
    def data(self):
        return self._ctx.cim.logical_index_store.get_physical_page_buffer(self.index)

    @property
    def structs(self):
        page = IndexPage(None, self.index)  # note: we're faking the logical_page_number here
        page.vsParse(self.data)
        if page.header.sig == INDEX_PAGE_TYPES.PAGE_TYPE_ACTIVE:
            return VstructInstance(0x0, page, "page"),
        else:
            return VstructInstance(0x0, page.header, "header"),


class PhysicalIndexPagesItem(Item):
    def __init__(self, ctx):
        super(PhysicalIndexPagesItem, self).__init__()
        self._ctx = ctx

    def __repr__(self):
        return "PhysicalIndexPagesItem(numEntries: {:s})".format(
            h(len(self.children)))

    @cached_property
    def children(self):
        mapping = self._ctx.cim.index_mapping.map
        # TODO: does this get all of them?
        return [PhysicalIndexPageItem(self._ctx, i) for i in
                range(mapping.header.mapping_entry_count + mapping.free_dword_count)]

    @property
    def type(self):
        return "meta"

    @property
    def name(self):
        return "Physical Index Pages"


class LogicalIndexPageItem(Item):
    def __init__(self, ctx, index):
        super(LogicalIndexPageItem, self).__init__()
        self._ctx = ctx
        self.index = index

    def __repr__(self):
        return "LogicalIndexPageItem(index: {:s})".format(h(self.index))

    @property
    def children(self):
        return []

    @property
    def type(self):
        return "meta.logicalIndexPage"

    @property
    def name(self):
        return "{:s}".format(h(self.index))

    @property
    def data(self):
        return self._ctx.cim.logical_index_store.get_logical_page_buffer(self.index)

    @property
    def structs(self):
        page = self._ctx.cim.logical_index_store.get_page(self.index)
        if page.header.sig == INDEX_PAGE_TYPES.PAGE_TYPE_ACTIVE:
            return VstructInstance(0x0, page, "page"),
        else:
            return VstructInstance(0x0, page.header, "header"),


class LogicalIndexPagesItem(Item):
    def __init__(self, ctx):
        super(LogicalIndexPagesItem, self).__init__()
        self._ctx = ctx

    def __repr__(self):
        return "LogicalIndexPagesItem(numEntries: {:s})".format(
            h(len(self.children)))

    @cached_property
    def children(self):
        return [LogicalIndexPageItem(self._ctx, i) for i in
                range(self._ctx.cim.index_mapping.map.header.mapping_entry_count)]

    @property
    def type(self):
        return "meta"

    @property
    def name(self):
        return "Logical Index Pages"


class IndexKeyItem(Item):
    def __init__(self, ctx, key):
        super(IndexKeyItem, self).__init__()
        self._ctx = ctx
        self._key = key

    def __repr__(self):
        return "IndexKeyItem(key: {:s})".format(self._key)

    @property
    def children(self):
        return []

    @property
    def type(self):
        return "meta.indexKey"

    @property
    def name(self):
        return "{:s}".format(self._key.human_format)

    @property
    def data(self):
        return self._ctx.object_resolver.get_object(self._key)

    @property
    def is_data_reference(self):
        return self._key.is_data_reference


class IndexNodeItem(Item):
    def __init__(self, ctx, page_number):
        super(IndexNodeItem, self).__init__()
        self._ctx = ctx
        self._page_number = page_number

    def __repr__(self):
        return "IndexNodeItem(pageNumber: {:s})".format(
            h(self._page_number))

    @cached_property
    def children(self):
        page = self._ctx.cim.logical_index_store.get_page(self._page_number)
        ret = []
        for i in range(page.key_count):
            ret.append(IndexNodeItem(self._ctx, page.get_child(i)))
            ret.append(IndexKeyItem(self._ctx, page.get_key(i)))
        ret.append(IndexNodeItem(self._ctx, page.get_child(page.key_count)))
        return ret

    @property
    def type(self):
        return "meta.indexNode"

    @property
    def name(self):
        return "Node {:s}".format(h(self._page_number))

    @property
    def data(self):
        return self._ctx.cim.logical_index_store.get_logical_page_buffer(self._page_number)

    @property
    def structs(self):
        page = self._ctx.cim.logical_index_store.get_page(self._page_number)
        ret = [
            VstructInstance(0x0, page, "node"),
        ]

        data_offset = page.vsGetOffset("data")
        for i in range(page.key_count):
            string_part_count = page.string_definition_table[i]

            for j in range(string_part_count):
                string_part_index = page.string_definition_table[i + 1 + j]

                s = v_zstr()
                string_offset = page.string_table[string_part_index]
                s.vsParse(page.data, offset=string_offset)

                ret.append(VstructInstance(data_offset + string_offset, s,
                                           "String {:s}, fragment {:s}".format(h(i), h(j))))

        return ret


class IndexRootItem(Item):
    def __init__(self, ctx):
        super(IndexRootItem, self).__init__()
        self._ctx = ctx

    def __repr__(self):
        return "IndexRootItem()"

    @property
    def children(self):
        return [
            IndexNodeItem(self._ctx,
                          self._ctx.cim.logical_index_store.root_page_number),
        ]

    @property
    def type(self):
        return "meta.index"

    @property
    def name(self):
        return "Index"


class ClassInstanceItem(Item):
    def __init__(self, ctx, namespace, classname, instance_key):
        super(ClassInstanceItem, self).__init__()
        self._ctx = ctx
        self._ns = namespace
        self._class = classname
        self._instance_key = instance_key

    def __repr__(self):
        return "ClassInstanceItem(namespace: {:s}, classnamename: {:s}, key: {:s})".format(
            self._ns, self._class, self._instance_key)

    @cached_property
    def children(self):
        return []

    @property
    def type(self):
        return "objects.classInstance"

    @property
    def name(self):
        return str(self._instance_key)

    @property
    def data(self):
        return self._ctx.object_resolver.get_ci_buf(self._ns, self._class, self._instance_key)

    @cached_property
    def ci(self):
        return self._ctx.object_resolver.get_ci(self._ns, self._class, self._instance_key)

    @cached_property
    def cd(self):
        return self._ctx.object_resolver.get_cd(self._ns, self._class)

    @cached_property
    def cl(self):
        return self._ctx.object_resolver.get_cl(self._ns, self._class)

    @cached_property
    def structs(self):
        ret = [
            VstructInstance(0x0, self.ci, "instance"),
        ]
        return ret


class ClassInstanceListItem(Item):
    def __init__(self, ctx, namespace, classname):
        super(ClassInstanceListItem, self).__init__()
        self._ctx = ctx
        self._ns = namespace
        self._class = classname

    def __repr__(self):
        return "ClassInstanceListItem(namespace: {:s}, classnamename: {:s})".format(
            self._ns,
            self._class)

    @cached_property
    def children(self):
        ret = []
        cd = TreeClassDefinition(self._ctx.object_resolver, self._ns, self._class)
        for instance in cd.instances:
            ret.append(ClassInstanceItem(self._ctx, self._ns, self._class, instance.instance_key))
        return sorted(ret, key=lambda r: r.name)

    @property
    def type(self):
        # TODO
        return ""

    @property
    def name(self):
        # TODO
        return "Instances"


class ClassDefinitionItem(Item):
    def __init__(self, ctx, namespace, name):
        super(ClassDefinitionItem, self).__init__()
        self._ctx = ctx
        self._ns = namespace
        self._name = name

    def __repr__(self):
        return "ClassDefinitionItem(namespace: {:s}, name: {:s})".format(
            self._ns,
            self._name)

    @cached_property
    def children(self):
        return [
            ClassInstanceListItem(self._ctx, self._ns, self._name)
        ]

    @property
    def type(self):
        return "objects.classDefinition"

    @property
    def name(self):
        return "{:s}".format(self._name)

    @cached_property
    def cd(self):
        return self._ctx.object_resolver.get_cd(self._ns, self._name)

    @cached_property
    def cl(self):
        return self._ctx.object_resolver.get_cl(self._ns, self._name)

    @property
    def data(self):
        return self._ctx.object_resolver.get_cd_buf(self._ns, self._name)

    @cached_property
    def structs(self):
        cd = self.cd
        ret = [
            VstructInstance(0x0, cd, "definition"),
        ]
        return ret


class ClassDefinitionListItem(Item):
    def __init__(self, ctx, namespace):
        super(ClassDefinitionListItem, self).__init__()
        self._ctx = ctx
        self._name = namespace

    def __repr__(self):
        return "ClassDefinitionListItem(namespace: {:s})".format(
            self._name)

    @cached_property
    def children(self):
        ret = []
        ns = TreeNamespace(self._ctx.object_resolver, self._name)
        for cd in ns.classes:
            ret.append(ClassDefinitionItem(self._ctx, cd.ns, cd.name))
        return sorted(ret, key=lambda r: r.name)

    @property
    def type(self):
        return ""

    @property
    def name(self):
        return "Class Defintions"


class NamespaceItem(Item):
    def __init__(self, ctx, name):
        super(NamespaceItem, self).__init__()
        self._ctx = ctx
        self._name = name

    def __repr__(self):
        return "NamespaceItem(namespace: {:s})".format(self._name)

    @cached_property
    def children(self):
        ret = [
            NamespaceListItem(self._ctx, self._name),
            ClassDefinitionListItem(self._ctx, self._name),
        ]
        return ret

    @property
    def type(self):
        return "objects.namespace"

    @property
    def name(self):
        return "{:s}".format(self._name)


class NamespaceListItem(Item):
    def __init__(self, ctx, name):
        super(NamespaceListItem, self).__init__()
        self._ctx = ctx
        self._name = name

    def __repr__(self):
        return "NamespaceListItem(namespace: {:s})".format(self._name)

    @cached_property
    def children(self):
        ret = []
        ns = TreeNamespace(self._ctx.object_resolver, self._name)
        for namespace in ns.namespaces:
            ret.append(NamespaceItem(self._ctx, namespace.name))
        return sorted(ret, key=lambda r: r.name)

    @property
    def type(self):
        return ""

    @property
    def name(self):
        return "Namespaces"


class ObjectsRootItem(Item):
    def __init__(self, ctx):
        super(ObjectsRootItem, self).__init__()
        self._ctx = ctx

    def __repr__(self):
        return "ObjectsRootItem()"

    @property
    def children(self):
        return [
            NamespaceItem(self._ctx, "root")
        ]

    @property
    def type(self):
        return "objects.root"

    @property
    def name(self):
        return "Objects"


class CimRootItem(Item):
    def __init__(self, ctx):
        super(CimRootItem, self).__init__()
        self._ctx = ctx

    def __repr__(self):
        return "CimRootItem()"

    @property
    def children(self):
        return [
            PhysicalDataPagesItem(self._ctx),
            LogicalDataPagesItem(self._ctx),
            PhysicalIndexPagesItem(self._ctx),
            LogicalIndexPagesItem(self._ctx),
            IndexRootItem(self._ctx),
            ObjectsRootItem(self._ctx),
        ]

    @property
    def type(self):
        return "meta"

    @property
    def name(self):
        return "CIM"


class IndexKeyItemView(QTabWidget, LoggingObject):
    def __init__(self, key_item, parent=None):
        super(IndexKeyItemView, self).__init__(parent)
        self._key_item = key_item
        if self._key_item.is_data_reference:
            hv = HexViewWidget(self._key_item.data)
            self.addTab(hv, "Target hex view")


class PhysicalDataPageItemView(QTabWidget, LoggingObject):
    def __init__(self, page_item, parent=None):
        super(PhysicalDataPageItemView, self).__init__(parent)
        self._page_item = page_item
        hv = HexViewWidget(self._page_item.data)
        self.addTab(hv, "Hex view")


class LogicalDataPageItemView(QTabWidget, LoggingObject):
    def __init__(self, page_item, parent=None):
        super(LogicalDataPageItemView, self).__init__(parent)
        self._page_item = page_item

        # TODO: hack get_parsers() until we have a unified repo/config
        vv = VstructViewWidget(get_parsers(), self._page_item.structs, self._page_item.data)
        self.addTab(vv, "Structures")

        hv = HexViewWidget(self._page_item.data)
        self.addTab(hv, "Hex view")


class PhysicalIndexPageItemView(QTabWidget, LoggingObject):
    def __init__(self, page_item, parent=None):
        super(PhysicalIndexPageItemView, self).__init__(parent)
        self._page_item = page_item

        vv = VstructViewWidget(get_parsers(), self._page_item.structs, self._page_item.data)
        self.addTab(vv, "Structures")

        hv = HexViewWidget(self._page_item.data)
        self.addTab(hv, "Hex view")


class LogicalIndexPageItemView(QTabWidget, LoggingObject):
    def __init__(self, page_item, parent=None):
        super(LogicalIndexPageItemView, self).__init__(parent)
        self._page_item = page_item

        vv = VstructViewWidget(get_parsers(), self._page_item.structs, self._page_item.data)
        self.addTab(vv, "Structures")

        hv = HexViewWidget(self._page_item.data)
        self.addTab(hv, "Hex view")


class IndexNodeItemView(QTabWidget, LoggingObject):
    def __init__(self, node_item, parent=None):
        super(IndexNodeItemView, self).__init__(parent)
        self._node_item = node_item

        # TODO: hack get_parsers() until we have a unified repo/config
        vv = VstructViewWidget(get_parsers(), self._node_item.structs, self._node_item.data)
        self.addTab(vv, "Structures")

        hv = HexViewWidget(self._node_item.data)
        self.addTab(hv, "Hex view")


class FixedWidthTextView(QTextEdit):
    def __init__(self, s, *args, **kwargs):
        super(FixedWidthTextView, self).__init__(*args, **kwargs)
        self.setReadOnly(True)
        f = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        td = QTextDocument()
        td.setDefaultFont(f)
        td.setPlainText(s)
        self.setDocument(td)


class ClassDefinitionItemView(QTabWidget, LoggingObject):
    def __init__(self, cd_item, parent=None):
        super(ClassDefinitionItemView, self).__init__(parent)
        self._cd_item = cd_item

        try:
            txt = dump_layout(cd_item.cd, cd_item.cl)
        except:
            txt = traceback.format_exc()
        self.addTab(FixedWidthTextView(txt), "Class details")

        # TODO: hack get_parsers() until we have a unified repo/config
        vv = VstructViewWidget(get_parsers(), self._cd_item.structs, self._cd_item.data)
        self.addTab(vv, "Structures")

        hv = HexViewWidget(self._cd_item.data)
        self.addTab(hv, "Hex view")


class ClassInstanceItemView(QTabWidget, LoggingObject):
    def __init__(self, ci_item, parent=None):
        super(ClassInstanceItemView, self).__init__(parent)
        self._ci_item = ci_item

        try:
            txt = dump_instance(ci_item.ci)
        except:
            txt = traceback.format_exc()
        self.addTab(FixedWidthTextView(txt), "Instance details")

        self.addTab(FixedWidthTextView(dump_layout(ci_item.cd, ci_item.cl)), "Definition details")

        # TODO: hack get_parsers() until we have a unified repo/config
        vv = VstructViewWidget(get_parsers(), self._ci_item.structs, self._ci_item.data)
        self.addTab(vv, "Structures")

        hv = HexViewWidget(self._ci_item.data)
        self.addTab(hv, "Hex view")


class CimUiForm(QWidget, LoggingObject):
    def __init__(self, ctx, parent=None):
        super(CimUiForm, self).__init__(parent)
        self._ctx = ctx
        self._tree_model = TreeModel(
            CimRootItem(ctx),
            [
                ColumnDef("Name", "name"),
                ColumnDef("Type", "type"),
            ])

        # TODO: maybe subclass the loaded .ui and use that instance directly

        uipath = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.join("ui", "ui.ui"))
        self._ui = uic.loadUi(uipath)
        emptyLayout(self._ui.browseDetailsLayout)

        tv = self._ui.browseTreeView
        tv.setModel(self._tree_model)
        tv.header().setSectionResizeMode(QHeaderView.Interactive)
        tv.header().resizeSection(0, 250)  # chosen empirically
        tv.activated.connect(self._handle_browse_item_activated)

        self._query_model = QStandardItemModel(self._ui.queryResultsList)
        self._ui.queryResultsList.setModel(self._query_model)
        self._ui.queryInputLineEdit.returnPressed.connect(self._handle_query)
        self._ui.queryInputActionButton.clicked.connect(self._handle_query)
        self._ui.queryResultsList.activated.connect(self._handle_results_item_activated)

        self._save_buffer = None
        self._ui.queryResultsSaveButton.clicked.connect(self._handle_save)

        mainLayout = QGridLayout()
        mainLayout.addWidget(self._ui, 0, 0)

        self.setLayout(mainLayout)
        self.setWindowTitle("cim - ui")

    def _handle_browse_item_activated(self, itemIndex):
        item = self._tree_model.getIndexData(itemIndex)
        details = self._ui.browseDetails
        details_layout = self._ui.browseDetailsLayout
        emptyLayout(details_layout)

        if isinstance(item, PhysicalDataPageItem):
            v = PhysicalDataPageItemView(item, details)
            details_layout.addWidget(v)

        elif isinstance(item, LogicalDataPageItem):
            v = LogicalDataPageItemView(item, details)
            details_layout.addWidget(v)

        elif isinstance(item, PhysicalIndexPageItem):
            v = PhysicalIndexPageItemView(item, details)
            details_layout.addWidget(v)

        elif isinstance(item, LogicalIndexPageItem):
            v = LogicalIndexPageItemView(item, details)
            details_layout.addWidget(v)

        elif isinstance(item, IndexNodeItem):
            v = IndexNodeItemView(item, details)
            details_layout.addWidget(v)

        elif isinstance(item, IndexKeyItem):
            v = IndexKeyItemView(item, details)
            details_layout.addWidget(v)

        elif isinstance(item, ClassDefinitionItem):
            v = ClassDefinitionItemView(item, details)
            details_layout.addWidget(v)

        elif isinstance(item, ClassInstanceItem):
            v = ClassInstanceItemView(item, details)
            details_layout.addWidget(v)

    def _handle_query(self):
        viewLayout = self._ui.queryResultsViewLayout
        emptyLayout(viewLayout)
        self._query_model.clear()

        query_text = self._ui.queryInputLineEdit.text()
        self.d("query: %s", query_text)
        if query_text.startswith("NS_"):
            self.d("key query")
            for o in self._ctx.object_resolver.get_keys(Key(query_text)):
                self.d("  query result: %s", o)
                item = QStandardItem(o.human_format)
                item.setData(o)
                self._query_model.appendRow(item)
        elif query_text.lower().startswith("root"):
            self.d("logical query (missing host)")
            # TODO: reference to Moniker is broken
            # need reference to a namespace to .parse_object_path(), and .get()
            m = Moniker("//./" + query_text)
            self._handle_moniker_query(m)
        elif query_text.lower().startswith("//"):
            self.d("logical query")
            m = Moniker(query_text)
            self._handle_moniker_query(m)
        elif query_text.lower().startswith("winmgmts:"):
            self.d("logical query (winmgmnts)")
            m = Moniker(query_text)
            self._handle_moniker_query(m)
        else:
            self.w("unknown query schema: %s", query_text)

    def _handle_moniker_query(self, moniker):
        if moniker.instance:
            item = ClassInstanceItem(self._ctx, moniker.namespace, moniker.klass, moniker.instance)
            model_item = QStandardItem(str(moniker))
            model_item.setData(item)
            self._query_model.appendRow(model_item)
        elif moniker.klass:
            model_item = QStandardItem(str(moniker))
            model_item.setData(ClassDefinitionItem(self._ctx, moniker.namespace, moniker.klass))
            self._query_model.appendRow(model_item)
        elif moniker.namespace:
            item = NamespaceItem(self._ctx, moniker.namespace)
            model_item = QStandardItem(str(moniker))
            model_item.setData(item)
            self._query_model.appendRow(model_item)
        else:
            self.w("no meaningful moniker fields: %s", str(moniker))

    def _handle_results_item_activated(self, itemIndex):
        emptyLayout(self._ui.queryResultsViewLayout)
        item = self._query_model.itemFromIndex(itemIndex).data()

        if isinstance(item, Key):
            buf = self._ctx.object_resolver.get_object(item)
            self._save_buffer = buf
            hv = HexViewWidget(buf, self._ui.queryResultsViewFrame)
            self._ui.queryResultsViewLayout.addWidget(hv)

        elif isinstance(item, ClassDefinitionItem):
            v = ClassDefinitionItemView(item, self._ui.queryResultsViewFrame)
            self._save_buffer = item.data
            self._ui.queryResultsViewLayout.addWidget(v)

        elif isinstance(item, ClassInstanceItem):
            v = ClassInstanceItemView(item, self._ui.queryResultsViewFrame)
            self._save_buffer = item.data
            self._ui.queryResultsViewLayout.addWidget(v)

        elif isinstance(item, NamespaceItem):
            l = QLabel(self._ui.queryResultsViewFrame)
            l.setText("Don't know how to display namespaces yet")
            self.w("dont know how to display namespaces")
            self._ui.queryResultsViewLayout.addWidget(l)

    def _handle_save(self):
        if self._save_buffer is None:
            return

        filename, filter = QFileDialog.getSaveFileName(self, "Save binary...", QDir.currentPath(),
                                                       "Binary files (*.bin)")
        if not filename:
            return

        with open(filename, "wb") as f:
            f.write(self._save_buffer)


def main(type_, path):
    logging.basicConfig(level=logging.INFO)
    if type_ not in ("xp", "win7"):
        raise RuntimeError("Invalid mapping type: {:s}".format(type_))

    c = CIM(type_, path)

    index = Index(c.cim_type, c.logical_index_store)
    object_resolver = ObjectResolver(c, index)
    ctx = Context(c, index, object_resolver)

    app = QApplication(sys.argv)
    screen = CimUiForm(ctx)
    screen.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    import sys

    main(*sys.argv[1:])
