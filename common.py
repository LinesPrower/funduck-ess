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

from PyQt4 import QtGui, QtCore
import os
import pickle
import gettext

_realfile = os.path.realpath(__file__)
_rootdir = os.path.realpath(os.path.dirname(_realfile))

APP_NAME = 'Funduck'

#gettext.install(APP_NAME, 'locale', names=['ru'])
tr = gettext.translation(APP_NAME, 'locale', ['ru'], fallback=True)
tr.install()
        
def truncateStr(s, maxlen):
    if len(s) > maxlen:
        return s[:maxlen - 1] + '…'
    return s

def HLine():
    t = QtGui.QFrame()
    t.setFrameShape(QtGui.QFrame.HLine)
    t.setFrameShadow(QtGui.QFrame.Sunken)
    return t

kTopAlign = 1
kBottomAlign = 2

def VBox(items, margin = 0, spacing = 5, align = None, stretch = None):
    box = QtGui.QVBoxLayout()
    box.setMargin(margin)
    box.setSpacing(spacing)
    if stretch == None:
        stretch = [0] * len(items)
    else:
        assert(len(stretch) == len(items))
    if align == kBottomAlign:
        box.setAlignment(QtCore.Qt.AlignBottom)
    elif align == kTopAlign:
        box.setAlignment(QtCore.Qt.AlignTop)
    for x, st in zip(items, stretch):
        if isinstance(x, QtGui.QLayout):
            box.addLayout(x, st)
        else:
            box.addWidget(x, st)
    return box

kLeftAlign = 1
kRightAlign = 2

def HBox(items, margin = 0, spacing = 5, align = None, stretch = None):
    box = QtGui.QHBoxLayout()
    box.setMargin(margin)
    box.setSpacing(spacing)
    if stretch == None:
        stretch = [0] * len(items)
    else:
        assert(len(stretch) == len(items))
    if align == kRightAlign:
        box.setAlignment(QtCore.Qt.AlignRight)
    elif align == kLeftAlign:
        box.setAlignment(QtCore.Qt.AlignLeft)    
    for x, st in zip(items, stretch):
        if isinstance(x, QtGui.QLayout):
            box.addLayout(x, st)
        elif isinstance(x, QtGui.QSpacerItem):            
            box.addSpacerItem(x)
        else:
            box.addWidget(x, st)    
    return box

icons_cache = {}

def GetIcon(fname):
    if not fname:
        fname = ''
    #else:
    #    fname = _rootdir + '/' + fname
    if fname not in icons_cache:
        icons_cache[fname] = QtGui.QIcon(fname)
    return icons_cache[fname] 

def Action(owner, descr, icon, handler = None, shortcut = None, 
           statustip = None, enabled = True, checkable = False,
           checked = None, *, bold = False):
    act = QtGui.QAction(GetIcon(icon), descr, owner)
    act.setIconVisibleInMenu(True)
    
    if bold:
        f = act.font()
        f.setBold(True)
        act.setFont(f)
            
    if not (shortcut is None):
        act.setShortcut(shortcut)
        
    if not (statustip is None):
        act.setStatusTip(statustip)
    if not (handler is None):
        act.triggered.connect(handler)
    act.setEnabled(enabled)
    if checkable:
        act.setCheckable(True)
    if checked != None:
        act.setCheckable(True)
        act.setChecked(checked)
    return act

def Separator(owner):
    res = QtGui.QAction(owner)
    res.setSeparator(True)
    return res

class Grid(QtGui.QTableWidget):
    
    def __init__(self, col_names, widths=None, allow_deleting_rows=False):
        super(Grid, self).__init__(0, len(col_names))
        self.setHorizontalHeaderLabels(col_names)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.allow_deleting_rows = allow_deleting_rows
        if widths:
            self.load(widths)
    
    def keyPressEvent(self, event):
        if self.allow_deleting_rows and event.key() == QtCore.Qt.Key_Delete:
            if self.currentItem() and self.currentRow() + 1 < self.rowCount():
                self.removeRow(self.currentRow())            
            return
        return QtGui.QTableWidget.keyPressEvent(self, event)
    
    def contextMenuEvent(self, event):
        if self.allow_deleting_rows and self.currentItem() and self.currentRow() + 1 < self.rowCount():
            menu = QtGui.QMenu(self)
            menu.addAction(Action(self, _('Delete'), '', lambda: self.removeRow(self.currentRow()), 'Delete'))
            menu.exec_(event.globalPos())
        
    def load(self, widths):
        for i, w in enumerate(widths):
            self.setColumnWidth(i, w)
    
    def save(self):        
        return [self.columnWidth(i) for i in range(self.columnCount())]
    
    def setRowData(self, row, data, editable=True):
        for j in range(self.columnCount()):                    
            tmp = QtGui.QTableWidgetItem(data[j])
            if not editable:
                tmp.setFlags(tmp.flags() ^ QtCore.Qt.ItemIsEditable)                
            self.setItem(row, j, tmp)
    
    def setTableData(self, data, editable=True, fix_height=None):        
        self.setRowCount(len(data))        
        for i, x in enumerate(data):
            self.setRowData(i, x, editable)
        if fix_height == None:              
            self.resizeRowsToContents()
        else:
            for i in range(len(data)):
                self.setRowHeight(i, fix_height)

class Table(QtGui.QGridLayout):
    
    def __init__(self, items, margin = 0):
        """
        items: [(string, widget)]
        """
        QtGui.QGridLayout.__init__(self)
        self.setMargin(margin)
        for (i, (s, item)) in enumerate(items):
            lbl = QtGui.QLabel(s)
            lbl.setMinimumHeight(20)
            self.addWidget(lbl, i, 0, QtCore.Qt.AlignTop)
            self.addWidget(ensureWidget(item), i, 1)
            self.setAlignment(lbl, QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)

def ToolBar(actions):
    res = QtGui.QToolBar()
    res.setStyleSheet("QToolBar { border: 0px }")
    for x in actions:
        if x:
            if x.__class__.__name__ == 'QAction':
                res.addAction(x)
            else:
                res.addWidget(x)
        else:
            res.addSeparator()
    return res

def ToolBtn(action):
    res = QtGui.QToolButton()
    res.setDefaultAction(action)
    res.setAutoRaise(True)
    return res

def ToolBtnStack(actions):
    items = [ToolBtn(a) for a in actions]
    return HBox(items, spacing=0, align=kLeftAlign)

def Button(caption, handler, *, enabled=True, autodefault=True):
    btn = QtGui.QPushButton(caption)
    btn.setAutoDefault(autodefault)
    btn.clicked.connect(handler)
    btn.setEnabled(enabled)
    return btn

def ensureLayout(widget):
    if isinstance(widget, QtGui.QWidget):
        return VBox([widget])
    return widget
        
def ensureWidget(layout):
    if isinstance(layout, QtGui.QWidget):
        return layout
    tmp = QtGui.QWidget()
    tmp.setLayout(layout)
    return tmp
    
class Dialog(QtGui.QDialog):
    
    def __init__(self, appname, wndname, title, is_modal=True):
        """
        appname [string]: application name (for saving settings)
        wndname [string]: window name (for saving settings)
        title [string]: window title
        """
        QtGui.QDialog.__init__(self)
        self.appname = appname
        self.wndname = wndname
        self.is_modal = is_modal
        self.setWindowTitle(title)        
        self.setWindowIcon(GetIcon('icons/duckling.png'))
        self.state_saver = StateSaver(wndname, appname)
        self.old_cur_wnd = None
    
    # to ensure that settings are saved after OK is clicked 
    def done(self, code):
        QtGui.QDialog.done(self, code)
        self.close()
    
    def setCustomLayout(self, layout, has_statusbar, menu = None):
        if has_statusbar:
            self.sbar = QtGui.QStatusBar()
            layout.setContentsMargins(10, 10, 10, 0)
            layout = VBox([layout, self.sbar], spacing = 0, stretch = [1, 0])

        layout = ensureLayout(layout)
        if menu:
            layout.setMenuBar(menu)                 
        self.setLayout(layout)
        self.loadSettings()        
                 
    def setDialogLayout(self, layout, ok_handler, has_statusbar = True, 
                        close_btn = False, *, 
                        extra_buttons = None, 
                        autodefault = True,
                        menu = None):
        """
        extra_buttons should be an iterable of tuples (caption, handler)
        """
        buttons = []
        if extra_buttons:
            buttons.extend([Button(capt, handler, autodefault=autodefault) 
                            for capt, handler in extra_buttons])

        if close_btn:
            buttons.extend([Button(_('Close'), self.reject, autodefault=autodefault)])
        else:
            buttons.extend([Button('&OK', ok_handler, autodefault=autodefault),
                            Button(_('Cancel'), self.reject, autodefault=autodefault)])
            self.addAction(Action(self, 'OK', '', ok_handler, 'F5'))
        
        buttons = HBox(buttons, align = kRightAlign)
        box = VBox([layout, buttons], 10)
        
        self.setCustomLayout(box, has_statusbar, menu)        

    def loadSettings(self):
        s = QtCore.QSettings(APP_NAME, self.appname)
        t = s.value("%s/geometry" % self.wndname)
        if t:
            self.restoreGeometry(t)
        self.state_saver.load()
    
    def closeEvent(self, event):
        s = QtCore.QSettings(APP_NAME, self.appname)        
        s.setValue("%s/geometry" % self.wndname, self.saveGeometry())
        self.state_saver.save()
        #print('%s: %d x %d' % (self.wndname, self.width(), self.height()))
        
    def registerStateObj(self, name, obj):
        self.state_saver.register(name, obj)

class SaveStateWrapper:
    """
    This class wraps an object having saveState / restoreState methods
    so it can be registered with StateSaver
    """    
    def __init__(self, base):
        self.base = base
    
    def load(self, state):
        self.base.restoreState(state)
        
    def save(self):
        return self.base.saveState()
        

class StateSaver:
    def __init__(self, wndname, appname = APP_NAME):
        self.wndname = wndname
        self.appname = appname
        self.objs = []
        
    def load(self):
        if not self.objs:
            return
        s = QtCore.QSettings(APP_NAME, self.appname)
        for name, obj in self.objs:
            t = s.value('%s/%s' % (self.wndname, name))
            if t != None:
                obj.load(pickle.loads(t))
                
    def save(self):
        if not self.objs:
            return
        s = QtCore.QSettings(APP_NAME, self.appname)
        for name, obj in self.objs:
            s.setValue('%s/%s' % (self.wndname, name), pickle.dumps(obj.save()))
            
    def register(self, name, obj):
        self.objs.append((name, obj))
        

def eventToNum(event):
    """
    return a number (0-9) for keys 1..9, 0
    otherwise, returns None
    event should be QKeyEvent
    """
    if event.key() >= QtCore.Qt.Key_1 and event.key() <= QtCore.Qt.Key_9:
        return event.key() - QtCore.Qt.Key_1
    if event.key() == QtCore.Qt.Key_0:
        return 9
    return None

def showReport(title, text, only_close_button = True, modal=True):
    class ReportDialog(Dialog):
        def __init__(self, title, text):
            Dialog.__init__(self, APP_NAME, 'report_wnd', title)
            e = QtGui.QTextEdit()
            e.setFont(QtGui.QFont('Consolas', 10))
            e.setReadOnly(True)
            e.setPlainText(text)
            self.resize(640, 480)
            self.setDialogLayout(e, 
                                 lambda: self.accept(), 
                                 has_statusbar = False, 
                                 close_btn = only_close_button)        
    
    d = ReportDialog(title, text)
    if modal:
        return d.exec_()
    else:
        d.show()
        return d # keep this reference to prevent garbage collection!

    
def getOpenFileName(owner, ident, title, filters, save=False):
    ident = 'openfile_' + ident
    s = QtCore.QSettings(APP_NAME, APP_NAME)
    path = s.value(ident, defaultValue='')
    if save:
        opts = QtGui.QFileDialog.DontConfirmOverwrite if save == 1 else 0
        fname = QtGui.QFileDialog.getSaveFileName(None, title, path, filters, opts)
    else:
        fname = QtGui.QFileDialog.getOpenFileName(None, title, path, filters)
    if fname:
        path = os.path.dirname(fname)
        s.setValue(ident, path)        
    return fname
    
# debug code
def main():
    pass

if __name__ == '__main__':
    main()