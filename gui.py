#! /usr/bin/env python3

import sys

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtDeclarative import *

from model import Timer, Session, Ticket, Project
from ui.main_window import Ui_mainwindow
from util import autocommit, format_time
import qtimer

VERSION = '0.1'

class QTimerMainWindow(QMainWindow):

	def __init__(self, parent=None):
		super().__init__(parent)
		self.backend = qtimer.QTimer()

		self.ui = Ui_mainwindow()
		self.ui.setupUi(self)
		self.setWindowTitle('qTimer v%s' % VERSION)

		session = self.backend.session

		query = session.query(Timer)
		for timer in query:
			item = QTreeWidgetItem([
				timer.name,
				format_time(timer.start),
				timer.duration,
				' Start/Pause/Stop/Post'
			])
			item.timer = timer
			item.setCheckState(0, Qt.Unchecked)
			self.ui.list.addTopLevelItem(item)

		# Setup initial projects
		self.backend.syncConditionally()
		for project in session.query(Project):
			pass


		self.ui.list.itemClicked.connect(self.onListItemClicked)

	def onListItemClicked(self, item, column):
		if item.checkState(0):
			item.setCheckState(0, Qt.Unchecked)
		else:
			item.setCheckState(0, Qt.Checked)

		# print('item: ', repr(item), 'col: ', repr(item.timer))

if __name__ == '__main__':
	app = QApplication(sys.argv)
	window = QTimerMainWindow()
	window.show()
	sys.exit(app.exec_())
