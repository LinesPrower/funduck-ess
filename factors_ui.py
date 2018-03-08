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
from objects import gstate, ESFactor, kProgramName, ESNode
import sys

# returns None, if the name is ok
def checkFactorName(name, allow_same=False):
    if not name:
        return _('Factor name cannot be empty')
    if allow_same:
        return
    for g in gstate.factorsMap().values():
        if g.name == name:
            return _('Factor with this name already exists')

class FactorDialog(cmn.Dialog):
    
    def __init__(self, obj = None):
        cmn.Dialog.__init__(self, 'ESS', 'FactorAdd', _('Add a Factor') if obj is None else _('Edit Factor'))
        self.init_done = False
        self.obj = obj
        self.edit_name = QtGui.QLineEdit()
        
        def make_rb(text, checked=False):
            rb = QtGui.QRadioButton(text)
            rb.toggled.connect(self.updateUI)
            rb.setChecked(checked)
            return rb
        
        self.edit_choices = cmn.Grid([_('Values')], [500], True)
        self.edit_choices.cellChanged.connect(self.onCellChanged)
        self.rb_binary = make_rb(_('Binary'), True)
        self.rb_text = make_rb(_('Text'))
        
        self.new_obj = None
        layout = cmn.VBox([
            cmn.Table([(_('Name'), self.edit_name),
                       (_('Type'), cmn.VBox([self.rb_binary, self.rb_text]) )]),
            self.edit_choices
        ])
        self.setDialogLayout(layout, self.doOk)
        
        choices = []        
        if obj != None:
            self.edit_name.setText(obj.name)
            if not obj.is_binary:
                self.rb_text.setChecked(True)
                choices = obj.choices
                
        self.edit_choices.setTableData([[s] for s in choices] + [['']])
        self.init_done = True
        self.updateUI()
        
    def resizeEvent(self, ev):
        self.edit_choices.setColumnWidth(0, self.edit_choices.width())
        return cmn.Dialog.resizeEvent(self, ev)
        
    def updateUI(self):
        if self.init_done:
            self.edit_choices.setEnabled(self.rb_text.isChecked())
    
    def get_choice(self, i):
        item = self.edit_choices.item(i, 0)
        if item == None:
            return ''
        return item.text().strip()
    
    def onCellChanged(self):
        rc = self.edit_choices.rowCount()
        if rc == 0:
            return
        if self.get_choice(rc - 1):
            self.edit_choices.setRowCount(rc + 1)
            self.edit_choices.setCurrentCell(rc, 0)
            self.edit_choices.resizeRowToContents(rc)
        
    def doOk(self):
        name = self.edit_name.text().strip()
        is_binary = self.rb_binary.isChecked()
        
        if is_binary:
            choices = ESFactor.getBinaryChoices()
        else:
            choices = [self.get_choice(i) for i in range(self.edit_choices.rowCount())]
            choices = list(filter(None, choices))
        if len(choices) < 2:
            err = _('A factor should have at least two values')
        else:
            err = checkFactorName(name, self.obj != None)
        if err != None:
            self.sbar.showMessage(err)
            return
        gstate.beginTransaction()
        try:
            if self.obj == None:
                factor = ESFactor(None, name)
                gstate.addNewObject(factor)
                self.new_obj = factor
            else:
                factor = self.obj
                gstate.modifyObject(factor)
                factor.name = name
                
            factor.is_binary = is_binary
            
            def update_node(node):
                if node.content != factor:
                    return
                gstate.modifyObject(node)
                while len(node.children) < len(choices):
                    node.children.append(gstate.addNewObject(ESNode()))
                while len(choices) < len(node.children):
                    gstate.deleteNode(node.children.pop())
                    
            if len(factor.choices) != len(choices):
                gstate.getRoot().traverse(update_node)
            factor.choices = choices
                
        finally:
            gstate.endTransaction()        
        self.accept()

class FactorsDialog(cmn.Dialog):
    
    def __init__(self, is_selecting=False):
        cmn.Dialog.__init__(self, 'ESS', 'Factors', _('Select a factor') if is_selecting else _('Factors'))
        self.is_selecting = is_selecting
        toolbar = cmn.ToolBar([
            cmn.Action(self, _('Add a factor (Ins)'), 'icons/add.png', self.addFactor, 'Insert'),
            cmn.Action(self, _('Edit factor (Enter)'), 'icons/edit.png', self.editFactorAction),
            cmn.Action(self, _('Delete factor (Del)'), 'icons/delete.png', self.removeFactor, 'Delete')
        ])
        self.list = QtGui.QListWidget(self)
        self.list.itemActivated.connect(self.onActivateItem)
        self.loadList()
        layout = cmn.VBox([toolbar, self.list], spacing=0)
        self.setDialogLayout(layout, self.doSelect, close_btn=not is_selecting, autodefault=False)
    
    def doSelect(self):
        cur = self.list.currentItem()
        if not cur:
            self.sbar.showMessage(_('You should select a factor first'))
            return
        self.selected_item = cur.obj
        self.accept()
        
    def loadList(self, cur_obj = None):
        if not cur_obj and self.list.currentItem():
            cur_obj = self.list.currentItem().obj
             
        self.list.clear()
        for g in gstate.factorsMap().values():
            item = QtGui.QListWidgetItem(g.name)
            item.obj = g
            self.list.addItem(item)
            if g == cur_obj:
                self.list.setCurrentItem(item)
        self.list.sortItems()
        
    def addFactor(self):
        d = FactorDialog()
        if d.exec_():
            self.loadList(d.new_obj)
    
    def onActivateItem(self, item):
        if self.is_selecting:
            self.doSelect()
        else:
            self.editFactor(item)
            
    def editFactorAction(self):
        cur = self.list.currentItem()
        if cur:
            self.editFactor(cur)
        
    def editFactor(self, item):
        if FactorDialog(item.obj).exec_():
            self.loadList()
        
    def removeFactor(self):
        cur = self.list.currentItem()
        if cur == None:
            return
        if gstate.hasInTree(cur.obj):
            QtGui.QMessageBox.warning(self, kProgramName, _('This factor is used in the tree and cannot be deleted'))
            return
        gstate.deleteObject(cur.obj)
        self.loadList()
    

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    gstate.resetState()
    gstate.addNewObject(ESFactor(None, 'Wanna party?'))
    gstate.addNewObject(ESFactor(None, 'Wanna eat?'))
    d = FactorsDialog()
    d.exec_()