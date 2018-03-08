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

from PyQt4 import QtCore, QtGui
import common as cmn
from objects import gstate, kFactor, getId

kCheckOK = 0
kCheckWarning = 1
kCheckError = 2

class CheckResultsPanel(QtGui.QDockWidget):

    def __init__(self, owner):

        QtGui.QDockWidget.__init__(self, _('ES Check Results'))

        self.owner = owner
        self.setObjectName('results_panel') # for state saving

        self.err_list = QtGui.QListWidget()
        self.err_list.itemActivated.connect(self.onActivated)
        self.setWidget(self.err_list)

        self.setFeatures(QtGui.QDockWidget.DockWidgetMovable)

    def onActivated(self, item):
        if item.node_id != None:
            self.owner.selectNode(item.node_id) 
    
    def reset(self):
        self.err_list.clear()

    def doCheck(self):
        
        self.err_list.clear()
        self.severity = kCheckOK
        
        def addMsg(message, severity, node=None):
            self.severity = max(self.severity, severity)
            item = QtGui.QListWidgetItem(message)
            item.node_id = getId(node)
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
                addMsg(_('Incomplete node'), kCheckError, node)
        gstate.getRoot().traverse(f)
        
        # check for duplicated factors
        used_factors = set()
        def check(node):
            content = node.content
            if content and content.getType() == kFactor:
                if content in used_factors:
                    addMsg(_('Factor "%s" is used more than once in the same branch') % content.name, kCheckError, node)
                    return
                used_factors.add(content)
            for c in node.children:
                check(c)
            if content and content.getType() == kFactor:
                used_factors.remove(content)                
        check(gstate.getRoot())             
        
        # check for unused goals
        for g in gstate.goalsMap().values():
            if not gstate.hasInTree(g):
                addMsg(_('Target "%s" is not used') % g.name, kCheckWarning)
        
        # check for unused factors
        for f in gstate.factorsMap().values():
            if not gstate.hasInTree(f):
                addMsg(_('Factor "%s" is not used') % f.name, kCheckWarning)
                
        if self.err_list.count() == 0:
            addMsg(_('No problems detected'), kCheckOK)
            
        return self.severity


if __name__ == '__main__':
    pass