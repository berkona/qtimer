import logging

LOGGER = logging.getLogger(__name__)


def save_expanded_state(treewidget):
	root = treewidget.invisibleRootItem()
	expanded = {
		'project': [],
		'ticket': [],
	}
	return visit_children(root, ['project', 'ticket'], expanded)


def restore_expanded_state(treewidget, expanded):
	restore_level(treewidget.topLevelItem(0), expanded, 'project')


def restore_level(root, expanded, attrName):
	expandedIds = expanded[attrName]
	for i in range(root.childCount()):
		child = root.child(i)
		if (child.childCount() > 0):
			restore_level(child, expanded, 'ticket')
		if not (getattr(child, attrName).id in expandedIds):
			continue
		child.setExpanded(True)


def visit_children(item, idAttrs, expanded):
	for i in range(item.childCount()):
		child = item.child(i)
		expanded = visit_children(child, idAttrs, expanded)

	# Base cases
	if not item.isExpanded():
			return expanded

	try:
		attrName, itemId = get_id_from_attrs(item, idAttrs)
		expanded[attrName].append(itemId)
	except AttributeError:
		# We can't store it
		LOGGER.exception('%r do not have any attributes from %r', item, idAttrs)

	return expanded


def get_id_from_attrs(item, idAttrs):
	for attrName in idAttrs:
		if not hasattr(item, attrName):
			continue
		return attrName, getattr(item, attrName).id
