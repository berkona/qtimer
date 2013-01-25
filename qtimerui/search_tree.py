class BinaryNode(object):
	def __init__(self, index, element, left=None, right=None):
		self.index = index
		self.element = element
		self.left = left
		self.right = right


class BinarySearchTree(object):
	def __init__(self, compFunc, root=None):
		self.compFunc = compFunc
		self.root = root

	def makeEmpty(self):
		self.root = None

	def isEmpty(self):
		return self.root == None

	def find(self, index):
		return self._find(index, self.root)

	def _find(self, index, rootNode):
		if not (rootNode):
			return None

		comparison = self.compFunc(index, rootNode.index)
		if (comparison < 0):
			return self._find(index, rootNode.left)
		elif (comparison > 0):
			return self._find(index, rootNode.right)
		else:
			return rootNode.element
