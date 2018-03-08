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

from PyQt4 import QtGui
import common as cmn
from objects import kProgramName
import io

class AboutDialog(cmn.Dialog):
    
    version = '1.0'
    about_text = _('''<b>%s - An expert system shell</b><br/>Version %s
    <br/>
    Copyright © 2018 Damir Akhmetzyanov (linesprower@gmail.com) 
    <br/>
    <br/>
    Funduck ESS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    <br/>
    <br/>
    This program uses icons from the 
    <a href="http://p.yusukekamiyamane.com/index.html.en">Fugue Icons</a>
    set by Yusuke Kamiyamane licensed under <a href="https://creativecommons.org/licenses/by/3.0/">CC BY 3.0</a>
    <br/>
    <br/>
    The "Duckling" logo by <a href="https://smashicons.com/">SmashIcons</a> 
    from <a href="www.flaticon.com">www.flaticon.com</a> 
    ''') % (kProgramName, version)
    
    def __init__(self):
        cmn.Dialog.__init__(self, 'ESS', 'AboutBox', _('About %s') % kProgramName)
        self.setWindowIcon(cmn.GetIcon('icons/info.png'))
        icon = QtGui.QPixmap('icons/duckling.png')
        icon_lbl = QtGui.QLabel()
        icon_lbl.setPixmap(icon)
        lbl = QtGui.QLabel(self.about_text)
        lbl.setWordWrap(True)
        lbl.setOpenExternalLinks(True)
        icon_lbl = cmn.VBox([icon_lbl], align=cmn.kTopAlign)
        layout = cmn.HBox([icon_lbl, lbl], 15, 15)
        self.setDialogLayout(layout, lambda: None, has_statusbar=False, close_btn=True, 
                             extra_buttons=[(_('View license text'), self.showLicense)])
        
    def showLicense(self):
        with io.open('LICENSE.txt', encoding='utf-8') as f:
            text = f.read()
        cmn.showReport(_('License Agreement'), text)


if __name__ == '__main__':
    app = QtGui.QApplication([])
    d = AboutDialog()
    d.exec_()