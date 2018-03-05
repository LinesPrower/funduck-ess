'''
Created on Mar 3, 2018

@author: LinesPrower
'''
import common as cmn
from PyQt4 import QtCore, QtGui
from objects import gstate, ESGoal, kProgramName
import sys

# returns None, if the name is ok
def checkGoalName(name, allow_same=False):
    if not name:
        return 'Название цели не может быть пустым'
    if allow_same:
        return
    for g in gstate.goalsMap().values():
        if g.name == name:
            return 'Цель с таким названием уже существует'

class GoalDialog(cmn.Dialog):
    
    def __init__(self, obj = None):
        cmn.Dialog.__init__(self, 'ESS', 'GoalAdd', 'Добавление цели' if obj is None else 'Редактирование цели')
        self.obj = obj
        self.edit_name = QtGui.QLineEdit()
        self.edit_descr = QtGui.QPlainTextEdit()
        self.new_obj = None
        layout = cmn.Table([
            ('Название', self.edit_name),
            ('Описание', self.edit_descr) 
        ])
        self.setDialogLayout(layout, self.doOk)
        if obj != None:
            self.edit_name.setText(obj.name)
            self.edit_descr.setPlainText(obj.descr)
        
    def doOk(self):
        name = self.edit_name.text().strip()
        descr = self.edit_descr.toPlainText().strip()
        err = checkGoalName(name, self.obj != None)
        if err != None:
            self.sbar.showMessage(err)
            return
        if self.obj == None:
            goal = ESGoal(None, name, descr)
            gstate.addNewObject(goal)
            self.new_obj = goal
        else:
            gstate.modifyObject(self.obj)
            self.obj.name = name
            self.obj.descr = descr
        self.accept()

class GoalsDialog(cmn.Dialog):
    
    def __init__(self, is_selecting=False):
        cmn.Dialog.__init__(self, 'ESS', 'Goals', 'Выбор цели' if is_selecting else 'Цели')
        self.is_selecting = is_selecting
        toolbar = cmn.ToolBar([
            cmn.Action(self, 'Добавить цель (Ins)', 'icons/add.png', self.addGoal, 'Insert'),
            cmn.Action(self, 'Редактировать цель (Enter)', 'icons/edit.png', self.editGoalAction),
            cmn.Action(self, 'Удалить цель (Del)', 'icons/delete.png', self.removeGoal, 'Delete')
        ])
        self.list = QtGui.QListWidget(self)
        self.list.itemActivated.connect(self.onActivateItem)
        self.loadList()
        layout = cmn.VBox([toolbar, self.list])
        self.setDialogLayout(layout, self.doSelect, close_btn=not is_selecting, autodefault=False)
    
    def doSelect(self):
        cur = self.list.currentItem()
        if not cur:
            self.sbar.showMessage('Необходимо выбрать цель')
            return
        self.selected_item = cur.obj
        self.accept()
            
    def loadList(self, cur_obj = None):
        if not cur_obj and self.list.currentItem():
            cur_obj = self.list.currentItem().obj
             
        self.list.clear()
        for g in gstate.goalsMap().values():
            item = QtGui.QListWidgetItem(g.name)
            item.obj = g
            self.list.addItem(item)
            if g == cur_obj:
                self.list.setCurrentItem(item)
        self.list.sortItems()
        
    def addGoal(self):
        d = GoalDialog()
        if d.exec_():
            self.loadList(d.new_obj)
    
    def onActivateItem(self, item):
        if self.is_selecting:
            self.doSelect()
        else:
            self.editGoal(item)
    
    def editGoalAction(self):
        cur = self.list.currentItem()
        if cur:
            self.editGoal(cur)
        
    def editGoal(self, item):
        if GoalDialog(item.obj).exec_():
            self.loadList()
        
    def removeGoal(self):
        cur = self.list.currentItem()
        if cur == None:
            return
        if gstate.hasInTree(cur.obj):
            QtGui.QMessageBox.warning(self, kProgramName, 'Цель используется в дереве и не может быть удалена')
            return
        gstate.deleteObject(cur.obj)
        self.loadList()
    

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    gstate.resetState()
    gstate.addNewObject(ESGoal(None, 'Ice cream'))
    gstate.addNewObject(ESGoal(None, 'Taco'))
    d = GoalsDialog()
    d.exec_()