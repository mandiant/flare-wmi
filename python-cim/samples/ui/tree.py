from collections import namedtuple

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QModelIndex
from PyQt5.QtCore import QAbstractItemModel


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
            self._children = sorted(self._getter(), key=lambda i: i.name())
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


_ColumnDef = namedtuple("ColumnDef", ["displayName", "attributeName", "formatter"])


def ColumnDef(displayName, attributeName, formatter=str):
    return _ColumnDef(displayName, attributeName, formatter)


class TreeModel(QAbstractItemModel):
    """ adapter from Item to QAbstractItemModel interface """

    def __init__(self, root, columns, parent=None):
        super(TreeModel, self).__init__(parent)
        self._root = TreeNode(None, root)
        self._columns = columns
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
        return len(self._columns)

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._columns[section].displayName
        return None

    def data(self, index, role):
        if not index.isValid():
            return None

        if role != Qt.DisplayRole:
            return None

        item = self._getIndexItem(index.internalId())
        coldef = self._columns[index.column()]
        return coldef.formatter(getattr(item.data, coldef.attributeName))

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
