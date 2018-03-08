#===============================================================================
# Funduck ESS
# Copyright (C) 2018 Damir Akhmetzyanov
# 
# This file is part of Funduck ESS
# 
# Funduck ESS is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Funduck ESS is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#===============================================================================

import common as cmn
from PyQt4 import QtCore, QtGui
from objects import gstate, ESGoal, kProgramName
import sys

# returns None, if the name is ok
def checkGoalName(name, allow_same=False):
    if not name:
        return _('Goal name cannot be empty')
    if allow_same:
        return
    for g in gstate.goalsMap().values():
        if g.name == name:
            return _('A goal with this name already exists')

class GoalDialog(cmn.Dialog):
    
    def __init__(self, obj = None):
        cmn.Dialog.__init__(self, 'ESS', 'GoalAdd', _('Add a Goal') if obj is None else _('Edit Goal'))
        self.obj = obj
        self.edit_name = QtGui.QLineEdit()
        self.edit_descr = QtGui.QPlainTextEdit()
        self.new_obj = None
        layout = cmn.Table([
            (_('Name'), self.edit_name),
            (_('Description'), self.edit_descr) 
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
        gstate.beginTransaction()
        try:
            if self.obj == None:
                goal = ESGoal(None, name, descr)
                gstate.addNewObject(goal)
                self.new_obj = goal
            else:
                gstate.modifyObject(self.obj)
                self.obj.name = name
                self.obj.descr = descr
        finally:
            gstate.endTransaction()
        self.accept()

class GoalsDialog(cmn.Dialog):
    
    def __init__(self, is_selecting=False):
        cmn.Dialog.__init__(self, 'ESS', 'Goals', _('Select a Goal') if is_selecting else _('Goals'))
        self.is_selecting = is_selecting
        toolbar = cmn.ToolBar([
            cmn.Action(self, _('Add a goal (Ins)'), 'icons/add.png', self.addGoal, 'Insert'),
            cmn.Action(self, _('Edit goal (Enter)'), 'icons/edit.png', self.editGoalAction),
            cmn.Action(self, _('Delete goal (Del)'), 'icons/delete.png', self.removeGoal, 'Delete')
        ])
        self.list = QtGui.QListWidget(self)
        self.list.itemActivated.connect(self.onActivateItem)
        self.loadList()
        layout = cmn.VBox([toolbar, self.list], spacing=0)
        self.setDialogLayout(layout, self.doSelect, close_btn=not is_selecting, autodefault=False)
    
    def doSelect(self):
        cur = self.list.currentItem()
        if not cur:
            self.sbar.showMessage(_('You should select a goal first'))
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
        if self.list.currentItem():
            self.list.scrollToItem(self.list.currentItem())
        
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
            QtGui.QMessageBox.warning(self, kProgramName, _('This goal is used in the tree and cannot be deleted'))
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