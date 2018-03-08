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
from PyQt4 import QtGui
from objects import gstate

class DescriptionDialog(cmn.Dialog):
    
    def __init__(self):
        self.edit_name = QtGui.QLineEdit(gstate.es_name)
        self.edit_descr = QtGui.QPlainTextEdit(gstate.es_descr)
        cmn.Dialog.__init__(self, 'ESS', 'ESDescription', _('Expert system description'))
        layout = cmn.Table([ (_('Name'), self.edit_name), (_('Description'), self.edit_descr) ])
        self.setDialogLayout(layout, self.doOk)
        
    def doOk(self):
        name = self.edit_name.text().strip()
        descr = self.edit_descr.toPlainText()
        if not name:
            self.sbar.showMessage(_('Name cannot be empty'))
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