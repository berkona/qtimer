# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/main_window.ui'
#
# Created: Tue Jan  8 01:58:52 2013
#      by: pyside-uic 0.2.13 running on PySide 1.1.1
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_mainwindow(object):
    def setupUi(self, mainwindow):
        mainwindow.setObjectName("mainwindow")
        mainwindow.resize(853, 460)
        self.centralwidget = QtGui.QWidget(mainwindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.date_from_label = QtGui.QCheckBox(self.centralwidget)
        self.date_from_label.setMaximumSize(QtCore.QSize(80, 16777215))
        self.date_from_label.setObjectName("date_from_label")
        self.horizontalLayout.addWidget(self.date_from_label)
        self.date_from = QtGui.QDateEdit(self.centralwidget)
        self.date_from.setCalendarPopup(True)
        self.date_from.setObjectName("date_from")
        self.horizontalLayout.addWidget(self.date_from)
        self.date_to_label = QtGui.QCheckBox(self.centralwidget)
        self.date_to_label.setMaximumSize(QtCore.QSize(50, 16777215))
        self.date_to_label.setObjectName("date_to_label")
        self.horizontalLayout.addWidget(self.date_to_label)
        self.date_to = QtGui.QDateEdit(self.centralwidget)
        self.date_to.setCalendarPopup(True)
        self.date_to.setObjectName("date_to")
        self.horizontalLayout.addWidget(self.date_to)
        self.actions = QtGui.QPushButton(self.centralwidget)
        self.actions.setMaximumSize(QtCore.QSize(100, 16777215))
        self.actions.setObjectName("actions")
        self.horizontalLayout.addWidget(self.actions)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.projects = QtGui.QTreeWidget(self.centralwidget)
        self.projects.setMaximumSize(QtCore.QSize(250, 16777215))
        self.projects.setObjectName("projects")
        self.horizontalLayout_2.addWidget(self.projects)
        self.timers = QtGui.QTreeWidget(self.centralwidget)
        self.timers.setProperty("showDropIndicator", False)
        self.timers.setAlternatingRowColors(True)
        self.timers.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.timers.setRootIsDecorated(False)
        self.timers.setUniformRowHeights(True)
        self.timers.setAllColumnsShowFocus(True)
        self.timers.setObjectName("timers")
        self.horizontalLayout_2.addWidget(self.timers)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        mainwindow.setCentralWidget(self.centralwidget)
        self.actionStart = QtGui.QAction(mainwindow)
        self.actionStart.setObjectName("actionStart")
        self.actionPause = QtGui.QAction(mainwindow)
        self.actionPause.setObjectName("actionPause")
        self.actionStop = QtGui.QAction(mainwindow)
        self.actionStop.setObjectName("actionStop")

        self.retranslateUi(mainwindow)
        QtCore.QMetaObject.connectSlotsByName(mainwindow)

    def retranslateUi(self, mainwindow):
        mainwindow.setWindowTitle(QtGui.QApplication.translate("mainwindow", "qTimer v0.1", None, QtGui.QApplication.UnicodeUTF8))
        self.date_from_label.setText(QtGui.QApplication.translate("mainwindow", "From", None, QtGui.QApplication.UnicodeUTF8))
        self.date_to_label.setText(QtGui.QApplication.translate("mainwindow", "To", None, QtGui.QApplication.UnicodeUTF8))
        self.actions.setText(QtGui.QApplication.translate("mainwindow", "Actions", None, QtGui.QApplication.UnicodeUTF8))
        self.projects.headerItem().setText(0, QtGui.QApplication.translate("mainwindow", "Projects", None, QtGui.QApplication.UnicodeUTF8))
        self.timers.setSortingEnabled(True)
        self.timers.headerItem().setText(0, QtGui.QApplication.translate("mainwindow", "Status", None, QtGui.QApplication.UnicodeUTF8))
        self.timers.headerItem().setText(1, QtGui.QApplication.translate("mainwindow", "Name", None, QtGui.QApplication.UnicodeUTF8))
        self.timers.headerItem().setText(2, QtGui.QApplication.translate("mainwindow", "Start Date", None, QtGui.QApplication.UnicodeUTF8))
        self.timers.headerItem().setText(3, QtGui.QApplication.translate("mainwindow", "Duration", None, QtGui.QApplication.UnicodeUTF8))
        self.timers.headerItem().setText(4, QtGui.QApplication.translate("mainwindow", "Synced", None, QtGui.QApplication.UnicodeUTF8))
        self.actionStart.setText(QtGui.QApplication.translate("mainwindow", "Start", None, QtGui.QApplication.UnicodeUTF8))
        self.actionStart.setToolTip(QtGui.QApplication.translate("mainwindow", "Create a new timer", None, QtGui.QApplication.UnicodeUTF8))
        self.actionStart.setShortcut(QtGui.QApplication.translate("mainwindow", "Ctrl+N", None, QtGui.QApplication.UnicodeUTF8))
        self.actionPause.setText(QtGui.QApplication.translate("mainwindow", "Pause", None, QtGui.QApplication.UnicodeUTF8))
        self.actionPause.setToolTip(QtGui.QApplication.translate("mainwindow", "Pause a running timer", None, QtGui.QApplication.UnicodeUTF8))
        self.actionStop.setText(QtGui.QApplication.translate("mainwindow", "Stop", None, QtGui.QApplication.UnicodeUTF8))
        self.actionStop.setToolTip(QtGui.QApplication.translate("mainwindow", "Stop a running timer (so it cannot be resumed later)", None, QtGui.QApplication.UnicodeUTF8))

