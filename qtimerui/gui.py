# System imports
from os import path
from datetime import datetime
import sys

# PySide imports
from PySide.QtCore import *
from PySide.QtGui import *

# QTimer imports
from qtimer.util import format_time
from qtimer.model import *
from qtimer.env import *

import qtimer.core as qtimer

# UI Imports
from qtimerui.main_window import Ui_mainwindow

VERSION = '0.1'


class ErrorWithDialog(Exception):
	def __init__(self, text):
		self.createErrorText(text)

	def createErrorText(self, text):
		msgBox = QMessageBox()
		msgBox.setWindowTitle("I'm sorry, Dave. I'm afraid I can't do that.")
		msgBox.setText(text)
		msgBox.exec_()


class NoItemsSelectedError(ErrorWithDialog):
	pass


class NoActionDefinedError(ErrorWithDialog):
	pass


class QTimerMainWindow(QMainWindow):

	def __init__(self, backend, parent=None):
		super().__init__(parent)
		self.backend = backend

		self.ui = Ui_mainwindow()
		self.ui.setupUi(self)
		self.setWindowTitle('qTimer v%s' % VERSION)

		session = self.backend.session

		# Setup initial projects
		self.backend.syncConditionally()

		rootItem = QTreeWidgetItem([ ' - Any - ' ])
		rootItem.project = None
		self.ui.projects.addTopLevelItem(rootItem)
		rootItem.setSelected(True)
		rootItem.setExpanded(True)

		for project in session.query(Project):
			parent = QTreeWidgetItem([ project.name ])
			parent.project = project
			rootItem.addChild(parent)
			for ticket in project.tickets:
				child = QTreeWidgetItem([ ticket.name ])
				child.ticket = ticket
				parent.addChild(child)

		for timer in session.query(Timer):
			item = QTreeWidgetItem([
				timer.status,
				timer.name,
				format_time(timer.start),
				str(self.backend.roundTime(timer.duration)),
				str(timer.posted)
			])
			item.timer = timer
			self.ui.timers.addTopLevelItem(item)

		self.ui.date_from.setDate(QDate.currentDate())
		self.ui.date_to.setDate(QDate.currentDate())

		self.onReadSettings()

		self.dateFromChanged = lambda date: self.onDateChanged(self.ui.date_from_label)
		self.dateToChanged = lambda date: self.onDateChanged(self.ui.date_to_label)

		self.ui.projects.itemClicked.connect(self.onFilterClicked)
		self.ui.date_from.dateChanged.connect(self.dateFromChanged)
		self.ui.date_to.dateChanged.connect(self.dateToChanged)
		self.ui.start.clicked.connect(self.onStartTimers)
		self.ui.stop.clicked.connect(self.onStopTimers)
		self.ui.post.clicked.connect(self.onPostTimers)

		self.durationTimer = QTimer(self)
		self.durationTimer.timeout.connect(self.onRefreshDurations)
		self.durationTimer.start(int(self.backend.config.timers.rounding) * 1000)

	def onDateChanged(self, dateEdit):
		if dateEdit.checkState() == Qt.Unchecked:
			dateEdit.setCheckState(Qt.Checked)

	def onWriteSettings(self):
		settingsPath = path.join(DATA_DIR, 'qtimer.gui.ini')
		settings = QSettings(settingsPath, QSettings.IniFormat)

		settings.beginGroup('MainWindow')
		settings.setValue('size', self.size())
		settings.setValue('pos', self.pos())

		settings.setValue('timersState', self.ui.timers.header().saveState())
		settings.setValue('splitterState', self.ui.splitter.saveState())
		settings.endGroup()

	def onReadSettings(self):
		settingsPath = path.join(DATA_DIR, 'qtimer.gui.ini')
		settings = QSettings(settingsPath, QSettings.IniFormat)

		settings.beginGroup('MainWindow')
		self.resize(settings.value('size', QSize(420, 460)))
		self.move(settings.value('pos', QPoint(200, 200)))

		splitterState = settings.value('splitterState', None)
		if splitterState:
			self.ui.splitter.restoreState(splitterState)

		listColState = settings.value('timersState', None)
		if listColState:
			self.ui.timers.header().restoreState(listColState)

		settings.endGroup()

	def onRefreshDurations(self):
		for i in range(self.ui.timers.topLevelItemCount()):
			# GET CHILD & REFRESH
			item = self.ui.timers.topLevelItem(i)
			item.setText(3, str(self.backend.roundTime(item.timer.duration)))

	def onFilterClicked(self, item, column):
		self.ui.timers.clear()

		query = self.backend.session.query(Timer)
		if hasattr(item, 'ticket'):
			query = query.filter(Timer.ticket_id == item.ticket.id)
		elif hasattr(item, 'project') and item.project:
			query = query.join(Ticket).filter(Ticket.project_id == item.project.id)

		for timer in query:
			item = QTreeWidgetItem([
				timer.status,
				timer.name,
				format_time(timer.start),
				str(self.backend.roundTime(timer.duration)),
				str(timer.posted)
			])
			item.timer = timer
			self.ui.timers.addTopLevelItem(item)

	def onStartTimers(self):
		items = self.ui.timers.selectedItems()
		if items:
			# Start any paused timers
			self.onRestartTimers(items)
		else:
			# Create timer
			self.onCreateTimers(items)

	def onRestartTimers(self, items):
		with qtimer.autocommit(self.backend.session) as sql:
				for item in items:
					status = item.timer.status
					if not status == STATUS_IDLE:
						continue
					session = Session(start=self.backend.roundTime(datetime.utcnow()), timer_id=item.timer.id)
					sql.add(session)

	def onCreateTimers(self, items):
		text, ok = QInputDialog.getText(self, 'Enter Timer Name', 'Enter new timer name:')
		if not ok:
			return

		tid = None
		for item in items:
			if hasattr(item, 'ticket'):
				tid = item.ticket.id

		session = Session(start=self.backend.roundTime(datetime.utcnow()))
		timer = Timer(name=text, ticket_id=tid, sessions=[session])
		self.backend.session.add(timer)
		self.onFilterClicked(item, None)

	def onStopTimers(self):
		items = self.ui.timers.selectedItems()
		if not items:
			raise NoItemsSelectedError('No timers selected.')

		ids = []
		for item in items:
			ids.append(item.timer.id)

		values = {
			Session.end: self.backend.roundTime(datetime.utcnow())
		}

		with qtimer.autocommit(self.backend.session) as session:
			session.query(Session).filter(Session.timer_id.in_(ids))\
				.filter(Session.end == None).update(values, 'fetch')
		self.onFilterClicked(item, None)

	def onPostTimers(self):
		pass

	def closeEvent(self, event):
		self.onWriteSettings()


def main():
	with qtimer.create_qtimer(CONFIG_PATH) as backend:
		app = QApplication(sys.argv)
		window = QTimerMainWindow(backend)
		window.show()
		sys.exit(app.exec_())
