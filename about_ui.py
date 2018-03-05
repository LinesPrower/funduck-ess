'''
Created on Mar 5, 2018

@author: LinesPrower
'''
from PyQt4 import QtGui
import common as cmn
from objects import kProgramName
import io

class AboutDialog(cmn.Dialog):
    
    about_text = '''<b>%s - Оболочка для экспертных систем</b>
    <br/>
    Copyright © 2018 Ахметзянов Дамир (linesprower@gmail.com) 
    <br/>
    <br/>
    Данный программный продукт является свободным программным обеспечением
    и распространяется по лицензии GNU GPL версии 3.
    <br/>
    <br/>
    Данный программный продукт использует пиктограммы из набора 
    <a href="http://p.yusukekamiyamane.com/index.html.en">Fugue Icons</a>
    от Yusuke Kamiyamane по лицензии <a href="https://creativecommons.org/licenses/by/3.0/">CC BY 3.0</a>
    <br/>
    <br/>
    Логотип "Duckling" от <a href="https://smashicons.com/">SmashIcons</a> 
    с сайта <a href="www.flaticon.com">www.flaticon.com</a> 
    ''' % kProgramName
    
    def __init__(self):
        cmn.Dialog.__init__(self, 'ESS', 'AboutBox', 'О программе %s' % kProgramName)
        self.setWindowIcon(cmn.GetIcon('icons/info.png'))
        icon = QtGui.QPixmap('icons/duckling.png')
        icon_lbl = QtGui.QLabel()
        icon_lbl.setPixmap(icon)
        lbl = QtGui.QLabel(self.about_text)
        lbl.setWordWrap(True)
        icon_lbl = cmn.VBox([icon_lbl], align=cmn.kTopAlign)
        layout = cmn.HBox([icon_lbl, lbl], 15, 15)
        self.resize(650, 380)
        self.setDialogLayout(layout, lambda: None, has_statusbar=False, close_btn=True, 
                             extra_buttons=[('Лицензионное соглашение', self.showLicense)])
        
    def showLicense(self):
        with io.open('LICENSE.txt', encoding='utf-8') as f:
            text = f.read()
        cmn.showReport('Лицензионное соглашение', text)


if __name__ == '__main__':
    app = QtGui.QApplication([])
    d = AboutDialog()
    d.exec_()