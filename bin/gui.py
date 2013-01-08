#! /usr/bin/env python3

# System imports
from os import path
import sys

# PySide imports
from PySide.QtCore import *
from PySide.QtGui import *

# QTimer imports
from qtimer.model import Timer, Ticket, Project
from qtimer.util import format_time
import qtimer.core as qtimer

# UI Imports
from qtimer.ui.main_window import Ui_mainwindow

VERSION = '0.1'


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
        for project in session.query(Project):
            parent = QTreeWidgetItem([project.name])
            parent.project = project
            self.ui.projects.addTopLevelItem(parent)
            for ticket in project.tickets:
                child = QTreeWidgetItem([ticket.name])
                child.ticket = ticket
                parent.addChild(child)

        for timer in session.query(Timer):
            item = QTreeWidgetItem([
                '',
                timer.name,
                format_time(timer.start),
                str(self.backend.roundTime(timer.duration)),
                str(timer.posted)
            ])
            item.timer = timer
            self.ui.timers.addTopLevelItem(item)

        self.ui.date_from.setDate(QDate.currentDate())
        self.ui.date_to.setDate(QDate.currentDate())

        self.actionMenu = QMenu()
        self.actionMenu.triggered.connect(self.onActionClicked)
        self.actionMenu.addAction('Start')
        self.actionMenu.addAction('Pause')
        self.actionMenu.addAction('Stop')
        self.actionMenu.addAction('Post')

        self.ui.actions.setMenu(self.actionMenu)

        self.readSettings()

        self.dateFromChanged = lambda date: self.onDateChanged(self.ui.date_from_label)
        self.dateToChanged = lambda date: self.onDateChanged(self.ui.date_to_label)

        self.ui.projects.itemClicked.connect(self.onFilterClicked)
        self.ui.date_from.dateChanged.connect(self.dateFromChanged)
        self.ui.date_to.dateChanged.connect(self.dateToChanged)

        self.durationTimer = QTimer(self)
        self.durationTimer.timeout.connect(self.onRefreshDurations)
        self.durationTimer.start(self.backend.config.rounding * 1000)

    def onDateChanged(self, dateEdit):
        if self.ui.date_from_label.checkState() == Qt.Unchecked:
            self.ui.date_from_label.setCheckState(Qt.Checked)

    def writeSettings(self):
        settingsPath = path.join(self.backend.config.configRoot, 'qtimer.gui.ini')
        settings = QSettings(settingsPath, QSettings.IniFormat)

        settings.beginGroup('MainWindow')
        settings.setValue('size', self.size())
        settings.setValue('pos', self.pos())

        settings.setValue('listColumns', self.ui.timers.header().saveState())
        settings.endGroup()

    def readSettings(self):
        settingsPath = path.join(self.backend.config.configRoot, 'qtimer.gui.ini')
        settings = QSettings(settingsPath, QSettings.IniFormat)

        settings.beginGroup('MainWindow')
        self.resize(settings.value('size', QSize(420, 460)))
        self.move(settings.value('pos', QPoint(200, 200)))

        listCols = settings.value('listColumns', None)
        if listCols:
            self.ui.timers.header().restoreState(listCols)

        settings.endGroup()

    def createErrorText(self, text):
        msgBox = QMessageBox()
        msgBox.setWindowTitle("I'm sorry, Dave. I'm afraid I can't do that.")
        msgBox.setText(text)
        msgBox.exec_()
        return
        setattr(self.ui, text.replace(' .', '_').lower(), msgBox)

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
        elif hasattr(item, 'project'):
            query = query.join(Ticket).filter(Ticket.project_id == item.project.id)

        for timer in query:
            item = QTreeWidgetItem([
                '',
                timer.name,
                format_time(timer.start),
                str(self.backend.roundTime(timer.duration)),
                str(timer.posted)
            ])
            item.timer = timer
            self.ui.timers.addTopLevelItem(item)

    def onActionClicked(self, action):
        print('onActionClicked:', repr(action.text()))
        items = self.ui.timers.selectedItems()
        {
            'start': self.onStartTimers,
            'pause': self.onPauseTimers,
            'stop': self.onStopTimers,
            'post': self.onPostTimers
        }.get(action.text().lower(), self.noAction)(items)

    def onStartTimers(self, items):
        if items:
            # Start any paused timers
            print(repr(items))
        else:
            # Create timer
            text, ok = QInputDialog.getText(self, 'Enter Timer Name', 'Enter new timer name:')
            if not ok:
                return

            tIdx = self.ui.tickets.currentIndex()
            tid = self.ui.tickets.itemData(tIdx)
            args = self.backend.parseArgs(['start', text, '-t', str(tid)])
            self.backend.executeCommand(args)
            self.onTicketClicked(tIdx)

    def onPauseTimers(self, items):
        pass

    def onStopTimers(self, items):
        pass

    def onPostTimers(self, items):
        pass

    def noAction(self, items):
        self.createErrorText('There is no implementation for this action')
        raise RuntimeError('There is no implementation for this action')

    def closeEvent(self, event):
        self.writeSettings()

if __name__ == '__main__':
    # We need to use this contextmanager to ensure the backend cleans up
    with qtimer.create_qtimer() as backend:
        app = QApplication(sys.argv)
        window = QTimerMainWindow(backend)
        window.show()
        sys.exit(app.exec_())
