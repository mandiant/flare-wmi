def emptyLayout(layout):
    for i in reversed(range(layout.count())):
        layout.itemAt(i).widget().setParent(None)
