import logging

from PySide.QtGui import *
from PySide.QtCore import *
from sqlalchemy import event

from qtimer.model import *
from qtimer.util import *


LOGGER = logging.getLogger(__name__)


# duck-typing to avoid unintended inheritance
class TimerIndexProxy(object):

	def __init__(self, realObject):
		self.wrapped = realObject

		# We have to keep this in state memory b/c we need a reference to ourselves
		self.translationFuncs = [
			lambda t: t.status.title(),
			lambda t: t.name,
			lambda t: format_time(t.start),
			lambda t: str(self.backend.roundTime(t.duration)),
			lambda t: "Posted" if t.posted else "Not posted",
		]

	def __eq__(self, other):
		return self.wrapped.__eq__(other)

	def __lt__(self, other):
		return self.wrapped.__lt__(other)

	def __ne__(self, other):
		return self.wrapped.__ne__(other)

	def child(self, row, column):
		return self.wrapped.child(row, column)

	def column(self):
		return self.wrapped.column()

	def data(self, role=Qt.DisplayRole):
		data = self.wrapped.data(role)
		if not (role == Qt.DisplayRole):
			return data

		LOGGER.info('timer: %r', data)
		return self.translationFuncs[self.column()](data)

	def flags(self):
		return self.wrapped.flags()

	def internalId(self):
		return self.wrapped.internalId()

	def internalPointer(self):
		return self.wrapped.internalPointer()

	def isValid(self):
		return self.wrapped.isValid()

	def model(self):
		return self.wrapped.model()

	def parent(self):
		return self.wrapped.parent()

	def row(self):
		return self.wrapped.row()

	def sibling(self, row, column):
		return self.wrapped.sibling(row, column)


class FilterDelegate(QObject):

	filterChanged = Signal()

	def __init__(self):
		super(FilterDelegate, self).__init__()

	def createQuery(self):
		raise RuntimeError('Implement this method')

	def columnCount(self):
		raise RuntimeError('Implement this method')

	def isActive(self, item):
		return False


class TimerDelegate(QStyledItemDelegate):

	def __init__(self, backend, parent=None):
		super(TimerDelegate, self).__init__(parent)

	def paint(self, painter, option, index):
		# Translate all calls through a proxy
		super(QAbstractItemDelegate, self).paint(painter, option, TimerIndexProxy(index))


class TimerFilterDelegate(FilterDelegate):

	textHeader = [
		'Status',
		'Name',
		'Start Time',
		'Duration',
		'Posted'
	]

	def __init__(self, backend):
		super(TimerFilterDelegate, self).__init__()
		self.backend = backend
		self.session = self.backend.session

		self.ticketId = None
		self.projectId = None

		emitChangeEvent = lambda s: self.filterChanged.emit()
		# Listen to database changes
		event.listen(self.session, 'after_commit', emitChangeEvent)

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

	def headerData(self, section, orientation, role=Qt.DisplayRole):
		if role == Qt.TextAlignmentRole:
			if orientation == Qt.Horizontal:
				return int(Qt.AlignLeft | Qt.AlignVCenter)
			return Qt.AlignLeft
		elif role != Qt.DisplayRole or orientation != Qt.Horizontal:
			return None

		return TimerFilterDelegate.textHeader[section]

	def isActive(self, item):
		return item.status == STATUS_ACTIVE

	def columnCount(self):
		return 5


class ORMCache(object):
	def __init__(self, activeFunc):
		self.activeFunc = activeFunc
		self.items = []
		self.activeItems = []
		self.size = 0
		self.isValid = False

	def insert(self, items):
		itemSize = len(items)
		LOGGER.debug('inserting %d items into cache', itemSize)
		for idx in range(itemSize):
			item = items[idx]
			item.row = (self.size - 1) + idx
			if self.activeFunc(item):
				self.activeItems.append(item)
			self.items.append(item)

		self.size += itemSize

	def empty(self):
		LOGGER.debug('emptyCache')
		self.items = []
		self.activeItems = []
		self.size = 0
		self.isValid = False


class ORMListModelAdapter(QAbstractTableModel):
	def __init__(self, filterDelegate):
		super(ORMListModelAdapter, self).__init__()

		# Listen to updates from delegate
		filterDelegate.filterChanged.connect(self.invalidate)
		self.delegate = filterDelegate

		# private fields, no touching
		self._cache = ORMCache(self.delegate.isActive)

	@property
	def cache(self):
		if self._cache.isValid:
			return self._cache

		q = self.delegate.createQuery()
		self._cache.insert(q.all())
		self._cache.isValid = True

		return self._cache

	def flags(self, index):
		return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

	def headerData(self, section, orientation, role=Qt.DisplayRole):
		return self.delegate.headerData(section, orientation, role)

	def data(self, index, role=Qt.DisplayRole):
		# LOGGER.debug('index', index.isValid(), index.row(), index.column())
		if not index.isValid():
			return None

		if role == Qt.CheckStateRole:
			return None
		elif role == Qt.DecorationRole:
			return None
		elif role == Qt.TextAlignmentRole:
			return int(Qt.AlignLeft | Qt.AlignVCenter)

		return self.getItem(index)

	def setData(self, index, value, role=Qt.EditRole):
		if not (role == Qt.EditRole):
			return False

		return True

	def rowCount(self, parent=QModelIndex()):
		LOGGER.debug('rowCount', self.cache.size)
		return self.cache.size

	def columnCount(self, parent=QModelIndex()):
		return self.delegate.columnCount()

	def invalidate(self, topLeft=QModelIndex(), bottomRight=QModelIndex()):
		isValid = topLeft.isValid() and bottomRight.isValid()
		LOGGER.debug('invalidate', isValid, topLeft.row(), bottomRight.row())
		if not isValid:
			# This invalidates the cache (will be reloaded) as well
			self.cache.empty()
		else:
			# TODO partial cache invalidating
			pass

		self.dataChanged.emit(topLeft, bottomRight)

	def getItem(self, index):
		if not index.isValid():
			return None

		return self.cache.items[index.row()]
