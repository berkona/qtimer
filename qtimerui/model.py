import logging

from PySide.QtGui import *
from PySide.QtCore import *
from sqlalchemy import event

from qtimer.model import *
from qtimer.util import *


LOGGER = logging.getLogger(__name__)


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

	def translateData(self, data, column):
		translationFuncs = [
			lambda t: t.status.title(),
			lambda t: t.name,
			lambda t: format_time(t.start),
			lambda t: str(self.backend.roundTime(t.duration)),
			lambda t: str(t.posted),
		]
		return translationFuncs[column](data)

	textHeader = [
		'Status',
		'Name',
		'Start Time',
		'Duration',
		'Posted'
	]

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
		return Qt.ItemIsSelectable | Qt.ItemIsEnabled

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

		return self.delegate.translateData(self.getItem(index), index.column())

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
