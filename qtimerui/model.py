from PySide.QtGui import *
from PySide.QtCore import *
from sqlalchemy import event

from qtimer.model import *
from qtimer.util import *


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


class FilterDelegate(QObject):

	filterChanged = Signal()

	def __init__(self):
		super(FilterDelegate, self).__init__()

	def createQuery(self):
		raise RuntimeError('Implement this method')

	def columnCount(self):
		raise RuntimeError('Implement this method')

	def translateData(self, data, column):
		# No op
		return data


class TimerFilterDelegate(FilterDelegate):

	def __init__(self, backend):
		super(TimerFilterDelegate, self).__init__()
		self.backend = backend
		self.session = self.backend.session

		self.ticketId = None
		self.projectId = None

		# Listen to database changes
		event.listen(self.session, 'after_commit', lambda s: self.filterChanged.emit())

	# Invariant: (self.projectId == !self.ticketId) || (self.projectId == None && self.ticketId == None)
	def reset(self):
		self.ticketId = None
		self.projectId = None
		self.filterChanged.emit()

	def setTicketId(self, ticketId):
		self.projectId = None
		self.ticketId = ticketId

		self.filterChanged.emit()

	def setProjectId(self, projectId):
		self.projectId = projectId
		self.ticketId = None

		self.filterChanged.emit()

	def createQuery(self):
		query = self.session.query(Timer)

		if self.ticketId:
			query = query.filter(Timer.ticket_id == self.ticketId)
		elif self.projectId:
			query = query.join(Ticket).filter(Ticket.project_id == self.projectId)

		return query

	def translateData(self, data, column):
		translationFuncs = [
			lambda t: t.status,
			lambda t: t.name,
			lambda t: format_time(t.start),
			lambda t: str(self.backend.roundTime(t.duration)),
			lambda t: str(t.posted),
		]

		return translationFuncs[column](data)

	def headerData(self, section, orientation, role=Qt.DisplayRole):
		textHeader = [
			'Status',
			'Name',
			'Start Time',
			'Duration',
			'Posted'
		]

		if role == Qt.TextAlignmentRole:
			if orientation == Qt.Horizontal:
				return int(Qt.AlignLeft | Qt.AlignVCenter)
			return Qt.AlignLeft
		elif role == Qt.DisplayRole and orientation == Qt.Horizontal:
			return textHeader[section]

		return None

	def columnCount(self):
		return 5


class ORMListModelAdapter(QAbstractTableModel):
	def __init__(self, filterDelegate):
		super(ORMListModelAdapter, self).__init__()

		# Listen to updates from delegate
		filterDelegate.filterChanged.connect(self.filterChanged)
		self.delegate = filterDelegate
		self.cache = []

		# private fields, no touching
		self._query = None

	@property
	def query(self):
		if self._query != None:
			return self._query

		self._query = self.delegate.createQuery()
		return self._query

	def filterChanged(self):
		self._query = None
		self.cache = []
		self.dataChanged.emit(QModelIndex(), QModelIndex())

	def flags(self, index):
		return Qt.ItemIsSelectable | Qt.ItemIsEnabled

	def headerData(self, section, orientation, role=Qt.DisplayRole):
		return self.delegate.headerData(section, orientation, role)

	def data(self, index, role=Qt.DisplayRole):
		if not index.isValid():
			return None

		if role == Qt.CheckStateRole:
			return None
		elif role == Qt.DecorationRole:
			return None
		elif role == Qt.TextAlignmentRole:
			return int(Qt.AlignLeft | Qt.AlignVCenter)

		if not self.cache:
			self.cache = self.query.all()

		realData = self.cache[index.row()]

		return self.delegate.translateData(realData, index.column())

	def rowCount(self, parent=QModelIndex()):
		return self.query.count()

	def columnCount(self, parent=QModelIndex()):
		return self.delegate.columnCount()
