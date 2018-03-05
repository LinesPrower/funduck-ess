'''
Created on Mar 5, 2018

@author: LinesPrower
'''
import common as cmn
from PyQt4 import QtGui
from objects import gstate

class DescriptionDialog(cmn.Dialog):
    
    def __init__(self):
        self.edit_name = QtGui.QLineEdit(gstate.es_name)
        self.edit_descr = QtGui.QPlainTextEdit(gstate.es_descr)
        cmn.Dialog.__init__(self, 'ESS', 'ESDescription', 'Описание экспертной системы')
        layout = cmn.Table([ ('Название', self.edit_name), ('Описание', self.edit_descr) ])
        self.setDialogLayout(layout, self.doOk)
        
    def doOk(self):
        name = self.edit_name.text().strip()
        descr = self.edit_descr.toPlainText()
        if not name:
            self.sbar.showMessage('Название не может быть пустым')
            return
        gstate.modifyMetadata()
        gstate.es_name = name
        gstate.es_descr = descr
        self.accept()
            

if __name__ == '__main__':
    app = QtGui.QApplication([])
    gstate.resetState()
    d = DescriptionDialog()
    d.exec_()