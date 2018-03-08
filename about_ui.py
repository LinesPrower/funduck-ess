'''
Created on Mar 5, 2018

@author: LinesPrower
'''
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
    This software is free and distributed under the terms and conditions of
    GNU GPL version 3.
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