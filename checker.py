'''
Created on Mar 4, 2018

@author: LinesPrower
'''
from PyQt4 import QtCore, QtGui
import common as cmn
from objects import gstate

kCheckOK = 0
kCheckWarning = 1
kCheckError = 2

class CheckResultsPanel(QtGui.QDockWidget):

    def __init__(self, owner):

        QtGui.QDockWidget.__init__(self, ' Результаты проверки системы')

        self.owner = owner
        self.setObjectName('results_panel') # for state saving

        self.err_list = QtGui.QListWidget()
        self.setWidget(self.err_list)

        self.setFeatures(QtGui.QDockWidget.DockWidgetMovable)

    def reset(self):
        self.err_list.clear()

    def doCheck(self):
        
        self.err_list.clear()
        self.severity = kCheckOK
        
        def addMsg(message, severity):
            self.severity = max(self.severity, severity)
            item = QtGui.QListWidgetItem(message)
            if severity == kCheckError:
                icon = 'icons/error.png'
            elif severity == kCheckWarning:
                icon = 'icons/warning.png'
            else:
                icon = 'icons/ok.png'
            item.setIcon(cmn.GetIcon(icon))
            self.err_list.addItem(item)
            
        # check for incompleted nodes
        def f(node):
            if node.content == None:
                addMsg('Незавершённый узел в дереве решений', kCheckError)
        gstate.getRoot().traverse(f)
        
        # check for unused goals
        for g in gstate.goalsMap().values():
            if not gstate.hasInTree(g):
                addMsg('Цель "%s" не использована' % g.name, kCheckWarning)
        
        # check for unused factors
        for f in gstate.factorsMap().values():
            if not gstate.hasInTree(f):
                addMsg('Фактор "%s" не использован' % f.name, kCheckWarning)
                
        if self.err_list.count() == 0:
            addMsg('Проблем не обнаружено', kCheckOK)
            
        return self.severity


if __name__ == '__main__':
    pass