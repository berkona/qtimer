#! /usr/bin/env python3

import sys

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtDeclarative import *

from model import Timer, Session, Ticket, Project
from ui.main_window import Ui_MainWindow
from util import autocommit, format_time
import qtimer

VERSION = '0.1'

class QTimerMainWindow(QMainWindow):

	def __init__(self, parent=None):
		super().__init__(parent)
		self.backend = qtimer.QTimer()

		self.ui = Ui_MainWindow()
		self.ui.setupUi(self)
		self.setWindowTitle('qTimer v%s' % VERSION)

		session = self.backend.session

		query = session.query(Timer)
		for timer in query.all():
			item = QTreeWidgetItem([
				timer.name,
				format_time(timer.start),
				timer.duration,
				' Start/Pause/Stop/Post'
			])
			item.timer = timer
			item.setCheckState(0, Qt.Unchecked)
			self.ui.list.addTopLevelItem(item)

		self.ui.list.itemChanged.connect(self.on_list_itemChanged)

	def on_list_itemChanged(self, item, column):
		print('item: ', repr(item), 'col: ', repr(item.timer))

if __name__ == '__main__':
	app = QApplication(sys.argv)
	window = QTimerMainWindow()
	window.show()
	sys.exit(app.exec_())
