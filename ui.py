import sys
import logging
import hexdump
from collections import namedtuple

from funcy.objects import cached_property
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QAbstractItemModel, QFile, QIODevice, QModelIndex, Qt
from PyQt5.QtWidgets import QApplication, QTreeView
from PyQt5 import uic

from cim import CIM
from cim import Index
from cim import formatKey
from cim import DATA_PAGE_SIZE
from objects import CimContext
from objects import getClassId
from objects import ClassLayout
from objects import CIM_TYPE_SIZES
from objects import ClassDefinition
from objects import QueryBuilderMixin
from objects import ObjectFetcherMixin
from objects import TreeNamespace
from objects import TreeClassDefinition
from objects import TreeClassInstance
from common import h
from common import one
from common import LoggingObject


Context = namedtuple("Context", ["cim", "index", "cdcache", "clcache", "querier"])


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
    def type(self):
        raise NotImplementedError()

    @property
    def name(self):
        raise NotImplementedError()


class ListItem(Item):
    """ a node in a list of nodes whose children will be dynamically loaded """
    def __init__(self, name, getter):
        super(ListItem, self).__init__()
        self._name = name
        self._getter = getter
        self._children = None

    def __repr__(self):
        return "ListItem(numChildren: {:s})".format(str(len(self.children)))

    def _getChildren(self):
        if self._children is None:
            self._children = sorted(self._getter(), key=lambda i: i.getName())
        return self._children

    @property
    def children(self):
        return self._getChildren()

    @property
    def type(self):
        return ""

    @property
    def name(self):
        return self._name


class Querier(LoggingObject, QueryBuilderMixin, ObjectFetcherMixin):
    def __init__(self, context):
        super(Querier, self).__init__()
        self.context = context

    def __repr__(self):
        return "Querier()"

    def getClassDefinition(self, namespace, classname):
        classId = getClassId(namespace, classname)
        cd = self.context.cdcache.get(classId, None)
        if cd is None:
            self.d("cdcache miss")
            buf = self.getClassDefinitionBuffer(namespace, classname)
            cd = ClassDefinition(buf)
            self.context.cdcache[classId] = cd
        return cd

    def getClassLayout(self, namespace, classname):
        cd = self.getClassDefinition(namespace, classname)
        return ClassLayout(self.context, namespace, cd)


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
        return self._ctx.cim.getLogicalDataStore().getPhysicalPageBuffer(self.index)


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
                    xrange(self._ctx.cim.getDataMapping().header.physicalPages)]

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
        return self._ctx.cim.getLogicalDataStore().getPageBuffer(self.index)


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
                    xrange(self._ctx.cim.getDataMapping().header.mappingEntries)]

    @property
    def type(self):
        return "meta"

    @property
    def name(self):
        return "Logical Data Pages"


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
        return "{:s}".format(formatKey(str(self._key)))

    @property
    def data(self):
        return self._ctx.querier.getObject(self._key)

    @property
    def isDataReference(self):
        return self._key.isDataReference()


class IndexNodeItem(Item):
    def __init__(self, ctx, pageNumber):
        """
        pageNumber - the integer logical page number in the index file
        """
        super(IndexNodeItem, self).__init__()
        self._ctx = ctx
        self._pageNumber = pageNumber

    def __repr__(self):
        return "IndexNodeItem(pageNumber: {:s})".format(
            h(self._pageNumber))

    @cached_property
    def children(self):
        page = self._ctx.cim.getLogicalIndexStore().getPage(self._pageNumber)
        ret = []
        for i in xrange(page.getKeyCount()):
            ret.append(IndexNodeItem(self._ctx, page.getChildByIndex(i)))
            ret.append(IndexKeyItem(self._ctx, page.getKey(i)))
        ret.append(IndexNodeItem(self._ctx, page.getChildByIndex(page.getKeyCount())))
        return ret

    @property
    def type(self):
        return "meta.indexNode"

    @property
    def name(self):
        return "Node {:s}".format(h(self._pageNumber))

    @property
    def data(self):
        return self._ctx.cim.getLogicalIndexStore().getPageBuffer(self._pageNumber)


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
                self._ctx.cim.getLogicalIndexStore().getRootPageNumber()),
        ]

    @property
    def type(self):
        return "meta.index"

    @property
    def name(self):
        return "Index"


class ClassInstanceItem(Item):
    def __init__(self, ctx, *args, **kwargs):
        # TODO
        super(ClassInstanceItem, self).__init__()
        self._ctx = ctx

    def __repr__(self):
        # TODO
        return "ClassInstanceItem()"

    @cached_property
    def children(self):
        # TODO
        return []

    @property
    def type(self):
        return "objects.classInstance"

    @property
    def name(self):
        # TODO
        return ""


class ClassInstanceListItem(Item):
    def __init__(self, ctx, namespace, classname, *args, **kwargs):
        super(ClassInstanceListItem, self).__init__()
        self._ctx = ctx
        self._ns = namespace
        self._class = classname
        # TODO

    def __repr__(self):
        return "ClassInstanceListItem(namespace: {:s}, classnamename: {:s})".format(
            self._ns,
            self._class)

    @cached_property
    def children(self):
        # TODO
        return []

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

    @property
    def cd(self):
        return TreeClassDefinition(self._ctx, self._ns, self._name).cd

    @property
    def cl(self):
        return TreeClassDefinition(self._ctx, self._ns, self._name).cl


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
        ns = TreeNamespace(self._ctx, self._name)
        for cd in ns.classes:
            ret.append(ClassDefinitionItem(self._ctx, cd.ns, cd.name))
        return ret

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
        ns = TreeNamespace(self._ctx, self._name)
        for namespace in ns.namespaces:
            ret.append(NamespaceItem(self._ctx, namespace.name))
        return ret

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
            IndexRootItem(self._ctx),
            ObjectsRootItem(self._ctx),
        ]

    @property
    def type(self):
        return "meta"

    @property
    def name(self):
        return "CIM"


class TestItem(Item):
    def __init__(self, name):
        super(TestItem, self).__init__()
        self._name = name

    @property
    def children(self):
        return [
            TestItem(self._name + "1"),
            TestItem(self._name + "2"),
            TestItem(self._name + "3"),
            TestItem(self._name + "4"),
        ]

    @property
    def type(self):
        return "Test"

    @property
    def name(self):
        return self._name


class TreeNode(object):
    """ adapter from Item to QAbstractItemModel interface """
    def __init__(self, parent, data):
        super(TreeNode, self).__init__()
        self._parent = parent
        self._data = data
        self._children = None

    @property
    def parent(self):
        return self._parent

    @property
    def children(self):
        if self._children is None:
            self._children = [TreeNode(self, c) for c in self._data.children]
        return self._children

    @property
    def data(self):
        return self._data

    @property
    def row(self):
        if self._parent:
            return self._parent.children.index(self)
        return 0


class TreeModel(QAbstractItemModel):
    """ adapter from Item to QAbstractItemModel interface """
    def __init__(self, root, parent=None):
        super(TreeModel, self).__init__(parent)
        self._root = TreeNode(None, root)
        self._indexItems = {}  # int to Item
        self._counter = 0

    # index.internalPointer() is not working for me consistently,
    # so we keep track of live objects ourselves
    def _addIndexItem(self, index, item):
        self._indexItems[index.internalId()] = item

    def _getIndexItem(self, id_):
        return self._indexItems[id_]

    def _createIndex(self, row, column, item):
        i = self.createIndex(row, column, item)
        self._addIndexItem(i, item)
        return i

    def columnCount(self, parent):
        return 2

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == self.COLUMN_INDEX_NAME:
                return "Name"
            if section == self.COLUMN_INDEX_TYPE:
                return "Type"
        return None

    COLUMN_INDEX_NAME = 0
    COLUMN_INDEX_TYPE = 1
    def data(self, index, role):
        if not index.isValid():
            return None

        if role != Qt.DisplayRole:
            return None

        item = self._getIndexItem(index.internalId())
        if index.column() == self.COLUMN_INDEX_NAME:
            return item.data.name
        if index.column() == self.COLUMN_INDEX_TYPE:
            return item.data.type
        return None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parentItem = self._root
        else:
            parentItem = self._getIndexItem(parent.internalId())

        childItem = parentItem.children[row]
        if childItem:
            return self._createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        childItem = self._getIndexItem(index.internalId())
        parentItem = childItem.parent

        if parentItem == self._root:
            return QModelIndex()

        return self._createIndex(parentItem.row, 0, parentItem)

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self._root
        else:
            parentItem = self._getIndexItem(parent.internalId())

        return len(parentItem.children)

    def getIndexData(self, itemIndex):
        """
        since we're hacking at the index data storage,
          need to provide an accessor.
        bad design to force the receiver of the index to have
          a reference to the model :-(.
        """
        return self._getIndexItem(itemIndex.internalId()).data


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


class IndexKeyItemView(QWidget, LoggingObject):
    def __init__(self, keyItem, parent=None):
        super(IndexKeyItemView, self).__init__(parent)
        self._keyItem = keyItem

        layout = QGridLayout()
        if self._keyItem.isDataReference:
            hv = HexViewWidget(self._keyItem.data)
            layout.addWidget(hv, 0, 0)
        self.setLayout(layout)


class DataPageView(QWidget, LoggingObject):
    def __init__(self, pageItem, parent=None):
        super(DataPageView, self).__init__(parent)
        self._pageItem = pageItem

        layout = QGridLayout()
        hv = HexViewWidget(self._pageItem.data)
        layout.addWidget(hv, 0, 0)
        self.setLayout(layout)


class ClassDefinitionItemView(QWidget, LoggingObject):
    def __init__(self, cdItem, parent=None):
        super(ClassDefinitionItemView, self).__init__(parent)
        self._cdItem = cdItem

        layout = QGridLayout()
        te = QTextEdit()
        te.setReadOnly(True)
        f = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        td = QTextDocument()
        td.setDefaultFont(f)
        td.setPlainText(self._classDescription)
        te.setDocument(td)
        layout.addWidget(te, 0, 0)
        self.setLayout(layout)

    @property
    def _classDescription(self):
        cd = self._cdItem.cd
        cl = self._cdItem.cl

        ret = []
        ret.append("classname: %s" % cd.getClassName())
        ret.append("super: %s" % cd.getSuperClassName())
        ret.append("ts: %s" % cd.getTimestamp().isoformat("T"))
        ret.append("qualifiers:")
        for k, v in cd.getQualifiers().iteritems():
            ret.append("  %s: %s" % (k, str(v)))
        ret.append("properties:")
        for propname, prop in cd.getProperties().iteritems():
            ret.append("  name: %s" % prop.getName())
            ret.append("    type: %s" % prop.getType())
            ret.append("    order: %s" % prop.getEntryNumber())
            ret.append("    qualifiers:")
            for k, v in prop.getQualifiers().iteritems():
                ret.append("      %s: %s" % (k, str(v)))
        ret.append("layout:")
        off = 0
        for prop in cl.properties:
            ret.append("  (%s)   %s %s" % (h(off), prop.getType(), prop.getName()))
            if prop.getType().isArray():
                off += 0x4
            else:
                off += CIM_TYPE_SIZES[prop.getType().getType()]
        return "\n".join(ret)


class Form(QWidget, LoggingObject):
    def __init__(self, ctx, parent=None):
        super(Form, self).__init__(parent)
        self._ctx = ctx
        self._treeModel = TreeModel(CimRootItem(ctx))

        self._ui = uic.loadUi("ui.ui")
        self._ui.browseTreeView.setModel(self._treeModel)

        self._ui.browseDetailsTabWidget.clear()
        #self._ui.browseTreeView.header().setSectionResizeMode(QHeaderView.Stretch)
        self._ui.browseTreeView.header().setSectionResizeMode(QHeaderView.Interactive)
        self._ui.browseTreeView.header().resizeSection(0, 250)

        self._ui.browseTreeView.activated.connect(self._handleBrowseItemActivated)

        # TODO: maybe subclass the loaded .ui and use that instance directly
        mainLayout = QGridLayout()
        mainLayout.addWidget(self._ui, 0, 0)

        self.setLayout(mainLayout)
        self.setWindowTitle("cim - ui")

    def _handleBrowseItemActivated(self, itemIndex):
        item = self._treeModel.getIndexData(itemIndex)
        tabs = self._ui.browseDetailsTabWidget
        tabs.clear()

        if isinstance(item, PhysicalDataPageItem):
            v = DataPageView(item, tabs)
            tabs.addTab(v, "Details")

        elif isinstance(item, LogicalDataPageItem):
            v = DataPageView(item, tabs)
            tabs.addTab(v, "Details")

        elif isinstance(item, IndexNodeItem):
            v = DataPageView(item, tabs)
            tabs.addTab(v, "Details")

        elif isinstance(item, IndexKeyItem):
            v = IndexKeyItemView(item, tabs)
            tabs.addTab(v, "Target details")

        elif isinstance(item, ClassDefinitionItem):
            v = ClassDefinitionItemView(item, tabs)
            tabs.addTab(v, "Target details")




def main(type_, path):
    logging.basicConfig(level=logging.INFO)
    if type_ not in ("xp", "win7"):
        raise RuntimeError("Invalid mapping type: {:s}".format(type_))

    c = CIM(type_, path)

    # yuck.
    cimctx = CimContext(
            c,
            Index(c.getCimType(), c.getLogicalIndexStore()),
            {}, {})
    ctx = Context(cimctx.cim, cimctx.index, cimctx.cdcache, cimctx.clcache,
                  Querier(cimctx))

    app = QApplication(sys.argv)
    screen = Form(ctx)
    screen.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    import sys
    main(*sys.argv[1:])
