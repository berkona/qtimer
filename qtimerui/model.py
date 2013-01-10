from Pyside.QtGui import *
from Pyside.QtCore import *
from sqlalchemy import event


class FilterDelegate(object):
	def filterQuery(self, query, index):
		raise RuntimeError('Implement this method')

	def getParentFields(self, query):
		raise RuntimeError('Implement this method')

	def getChildFields(self, query):
		raise RuntimeError('Implement this method')


class ItemModelAdapter(QAbstractItemModel):
	def __init__(self, session, filterDelegate):
		self.session = session
		self.delegate = filterDelegate
		self._query = None
		event.listen(session, 'after_commit', lambda s: self.dataChanged())

	@property
	def query(self):
		if not (self._query == None):
			return self._query

		fields = None
		if index.parent() == QModelIndex():
			# Use the parent
			fields = self.delegate.getParentFields()
		else:
			fields = self.delegate.getChildFields()

		q = self.session.query(fields)
		q = self.delegate.filterQuery(q)
		self._query = q
		return self._query

	def data(self, index):
		if not index.isValid():
			return None
		try:
			return self.query[index.column()]
		except:
			return None
