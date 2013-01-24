def createExpandedBitString(treewidget, idAttrs=[]):
	root = treewidget.invisibleRootItem()
	visitChildren(root, idAttrs)


def visitChildren(item, idAttrs, expanded={}):
	for i in range(item.childCount()):
		child = item.child(i)
		if not child.isExpanded():
			continue
		attrName, itemId = getIdFromAttrs(item, idAttrs)
		try:
		expanded[attrName][itemId] = True
		visitChildren(item)


def getIdFromAttrs(item, idAttrs):
	for attrName in idAttrs:
		if not hasattr(item, attrName):
			continue
		return attrName, getattr(item, attrName).id
