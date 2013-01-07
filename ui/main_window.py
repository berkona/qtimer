# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/main_window.ui'
#
# Created: Mon Jan  7 10:38:57 2013
#      by: pyside-uic 0.2.13 running on PySide 1.1.1
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_mainwindow(object):
    def setupUi(self, mainwindow):
        mainwindow.setObjectName("mainwindow")
        mainwindow.resize(420, 460)
        self.centralwidget = QtGui.QWidget(mainwindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.comboBox_2 = QtGui.QComboBox(self.centralwidget)
        self.comboBox_2.setObjectName("comboBox_2")
        self.horizontalLayout.addWidget(self.comboBox_2)
        self.comboBox = QtGui.QComboBox(self.centralwidget)
        self.comboBox.setObjectName("comboBox")
        self.horizontalLayout.addWidget(self.comboBox)
        self.pushButton = QtGui.QPushButton(self.centralwidget)
        self.pushButton.setMaximumSize(QtCore.QSize(50, 16777215))
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout.addWidget(self.pushButton)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.list = QtGui.QTreeWidget(self.centralwidget)
        self.list.setAlternatingRowColors(True)
        self.list.setRootIsDecorated(False)
        self.list.setUniformRowHeights(True)
        self.list.setAllColumnsShowFocus(True)
        self.list.setObjectName("list")
        self.verticalLayout.addWidget(self.list)
        mainwindow.setCentralWidget(self.centralwidget)
        self.toolBar = QtGui.QToolBar(mainwindow)
        self.toolBar.setObjectName("toolBar")
        mainwindow.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        mainwindow.insertToolBarBreak(self.toolBar)
        self.toolBar.addSeparator()

        self.retranslateUi(mainwindow)
        QtCore.QMetaObject.connectSlotsByName(mainwindow)

    def retranslateUi(self, mainwindow):
        mainwindow.setWindowTitle(QtGui.QApplication.translate("mainwindow", "qTimer v0.1", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton.setText(QtGui.QApplication.translate("mainwindow", "Do", None, QtGui.QApplication.UnicodeUTF8))
        self.list.setSortingEnabled(True)
        self.list.headerItem().setText(0, QtGui.QApplication.translate("mainwindow", "Name", None, QtGui.QApplication.UnicodeUTF8))
        self.list.headerItem().setText(1, QtGui.QApplication.translate("mainwindow", "Start Date", None, QtGui.QApplication.UnicodeUTF8))
        self.list.headerItem().setText(2, QtGui.QApplication.translate("mainwindow", "Duration", None, QtGui.QApplication.UnicodeUTF8))
        self.list.headerItem().setText(3, QtGui.QApplication.translate("mainwindow", "Actions", None, QtGui.QApplication.UnicodeUTF8))
        self.toolBar.setWindowTitle(QtGui.QApplication.translate("mainwindow", "toolBar", None, QtGui.QApplication.UnicodeUTF8))

