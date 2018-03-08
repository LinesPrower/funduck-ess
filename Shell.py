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
import sys
import objects
import common as cmn
from objects import gstate, kProgramName, ESNode, kFactor, kGoal, getId, getType
from goals_ui import GoalsDialog, GoalDialog
from factors_ui import FactorsDialog, FactorDialog
from checker import CheckResultsPanel, kCheckError
from description_ui import DescriptionDialog
from about_ui import AboutDialog
from es_runner import ESWindow

class DecisionTreeWidget(QtGui.QWidget):


    def __init__(self, owner):
        QtGui.QWidget.__init__(self)
        
        self.panning = False
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        p = QtGui.QPainter(self)
        objects.ESNode.font_metrics = QtGui.QFontMetrics(objects.ESNode.font, p.device())
        
        pal = QtGui.QPalette()
        pal.setColor(QtGui.QPalette.Background, QtGui.QColor('white'))
        self.setAutoFillBackground(True)
        self.setPalette(pal)
        
        self.act_copy = cmn.Action(self, _('Copy'), 'icons/copy.png', self.doCopy, 'Ctrl+C')        
        self.act_paste = cmn.Action(self, _('Paste'), 'icons/paste.png', self.doPaste, 'Ctrl+V')
        self.addActions([self.act_copy, self.act_paste])        
        self.owner = owner
    
    def doCopy(self):
        node = gstate.getCurrentNode()
        if node != None:
            gstate.clipboard = node.serializeSubtree() 
    
    def doPaste(self):
        '''
        Pasting is tricky, because:
        a) some goals/factors may have been deleted since the copy operation.
            In this case, we replace them with empty nodes
        b) some factors may have choices count changed
        '''
        node = gstate.getCurrentNode()
        if node == None or not gstate.clipboard:
            return
        
        data_dict = { x['id'] : x for x in gstate.clipboard }
        
        def updateNode(node, data):
            content_id = data['content']
            if content_id not in gstate.objMap:
                assert(node.content == None)
                return # this node remains empty
            node.content = gstate.objMap[content_id]
            # this is how many children this node should have
            n_children = len(node.content.choices) if node.content.getType() == kFactor else len(data['children'])
            for child_id in data['children'][:n_children]:
                t = gstate.addNewObject(ESNode())
                node.children.append(t)
                updateNode(t, data_dict[child_id])
            while len(node.children) < n_children:
                node.children.append(gstate.addNewObject(ESNode()))             
        
        gstate.beginTransaction('Paste')
        try:
            self.clearNode(node)
            updateNode(node, gstate.clipboard[0])
        finally:
            gstate.endTransaction()
    
    def editCurrent(self, node):
        if node.content.getType() == kFactor:
            FactorDialog(node.content).exec_()
        elif node.content.getType() == kGoal:
            GoalDialog(node.content).exec_()             
    
    def getNodeUnderCursor(self, ev):
        def f(node):
            if node.x <= ev.x() <= node.x + node.width and node.y <= ev.y() <= node.y + node.height:
                return node
        return gstate.getRoot().traverse(f)            
        
    def contextMenuEvent(self, ev):
        node = self.getNodeUnderCursor(ev)
        if not node:
            return
        menu = QtGui.QMenu(self)
        menu.addAction(cmn.Action(self, _('Select a factor'), '', lambda: self.setFactor(node), 'F'))
        menu.addAction(cmn.Action(self, _('Select a goal'), '', lambda: self.setGoal(node), 'G'))
        if getType(node.content) == kGoal and not node.children:
            menu.addAction(cmn.Action(self, _('Add an extra goal'), '', lambda: self.addExtraGoal(node), 'Shift+G'))
        if node.content != None:
            menu.addAction(cmn.Action(self, _('Clear node'), '', lambda: self.clearNodeUI(node), 'X'))
        menu.addSeparator()
        self.act_copy.setEnabled(node.content != None)
        menu.addAction(self.act_copy)
        self.act_paste.setEnabled(bool(gstate.clipboard))
        menu.addAction(self.act_paste)
        if node.content:
            menu.addSeparator()
            t = _('Edit factor') if node.content.getType() == kFactor else _('Edit goal')
            menu.addAction(cmn.Action(self, t, '', lambda: self.editCurrent(node), 'E'))
        menu.exec_(ev.globalPos())        
        
    def mousePressEvent(self, ev):
        if ev.button() == QtCore.Qt.MiddleButton:
            self.panning = True
            gpos = ev.globalPos()
            self.last_x = gpos.x()
            self.last_y = gpos.y()
            return
            
        node = self.getNodeUnderCursor(ev)
        if not node:
            return
                
        def set_sel(x):
            x.selected = x == node
        
        gstate.getRoot().traverse(set_sel)
        self.update()
    
    def mouseMoveEvent(self, ev):
        if not self.panning:
            return
        gpos = ev.globalPos()
        x, y = gpos.x(), gpos.y()
        sb = self.owner.pbox_scroll.horizontalScrollBar()
        if sb:
            sb.setSliderPosition(sb.value() - x + self.last_x)
        sb = self.owner.pbox_scroll.verticalScrollBar()
        if sb:
            sb.setSliderPosition(sb.value() - y + self.last_y)
        self.last_x = x
        self.last_y = y
        
    def mouseReleaseEvent(self, ev):
        self.panning = False
    
    def clearNode(self, node):
        gstate.modifyObject(node)
        node.content = None
        node.children = []
        for c in node.children:
            gstate.deleteNode(c)
            
    def clearNodeUI(self, node):
        if not node.content:
            return
        gstate.beginTransaction('Clear node')
        try:
            self.clearNode(node)
        finally:
            gstate.endTransaction()
    
    def setFactor(self, node):
        dialog = FactorsDialog(True)
        if not dialog.exec_():
            return
        factor = dialog.selected_item
        if node.content == factor:
            return
        gstate.beginTransaction('Set Factor')
        try:
            self.clearNode(node)
            node.content = factor
            node.children = [gstate.addNewObject(ESNode()) for _ in factor.choices]
        finally:
            gstate.endTransaction()
            
    def setGoal(self, node):
        dialog = GoalsDialog(True)
        if not dialog.exec_():
            return
        goal = dialog.selected_item
        if node.content == goal:
            return
        gstate.beginTransaction('Set Goal')
        try:
            self.clearNode(node)
            node.content = goal
        finally:
            gstate.endTransaction() 
            
    def addExtraGoal(self, node):
        if getType(node.content) != kGoal or node.children:
            return
        dialog = GoalsDialog(True)
        if not dialog.exec_():
            return
        goal = dialog.selected_item
        gstate.beginTransaction('Add Extra Goal')
        try:
            gstate.modifyObject(node)
            node.children.append(gstate.addNewObject(ESNode(None, goal)))
        finally:
            gstate.endTransaction()
        
    def keyPressEvent(self, ev):
        key = ev.nativeVirtualKey()
        keyx = ev.key()
        cur = gstate.getCurrentNode()
        
        def getPrevNode(node):
            k = 0
            while True:
                p = node.parent
                if not p:
                    return
                idx = p.children.index(node)
                if idx == 0:
                    k += 1
                else:
                    node = p.children[idx-1]
                    break
                node = p
            for _ in range(k):
                if node.children:
                    node = node.children[-1]
            return node
        
        def getNextNode(node):
            k = 0
            while True:
                p = node.parent
                if not p:
                    return
                idx = p.children.index(node)
                if idx == len(p.children) - 1:
                    k += 1
                else:
                    node = p.children[idx+1]
                    break
                node = p
            for _ in range(k):
                if node.children:
                    node = node.children[0]
            return node
                        
        if keyx in [QtCore.Qt.Key_Left, QtCore.Qt.Key_Right, QtCore.Qt.Key_Up, QtCore.Qt.Key_Down]:
            if not cur:
                tgt = gstate.getRoot()
            elif keyx == QtCore.Qt.Key_Left:
                tgt = cur.parent
            elif keyx == QtCore.Qt.Key_Right:
                tgt = cur.children[0] if cur.children else None
            elif keyx == QtCore.Qt.Key_Up:
                tgt = getPrevNode(cur)
            else:
                tgt = getNextNode(cur)
            self.owner.selectNode(getId(tgt))
            return
            
        if not cur:
            return
        if int(ev.modifiers()) == 0:
            if key == QtCore.Qt.Key_F:
                self.setFactor(cur)
            elif key == QtCore.Qt.Key_G:
                self.setGoal(cur)
            elif key == QtCore.Qt.Key_E:
                self.editCurrent(cur)
            elif key == QtCore.Qt.Key_X:
                self.clearNodeUI(cur)
        elif ev.modifiers() == QtCore.Qt.ShiftModifier:
            if key == QtCore.Qt.Key_G:
                self.addExtraGoal(cur)        

    def paintEvent(self, ev):
        p = QtGui.QPainter(self)
        p.setFont(objects.ESNode.font)       
        gstate.getRoot().render(p)
                    
class MainW(QtGui.QMainWindow):

    def __init__(self):
        QtGui.QMainWindow.__init__(self)

        self.resize(800, 600)
        self.setWindowTitle(kProgramName)
        self.setWindowIcon(cmn.GetIcon('icons/duckling.png'))
        
        
        self.check_results = CheckResultsPanel(self)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.check_results)

        s = QtCore.QSettings('PlatBox', 'Hal0')
        t = s.value("mainwnd/geometry")
        if t:
            self.restoreGeometry(t)
        t = s.value("mainwnd/dockstate")
        if t:
            self.restoreState(t, 0)

        self.pbox = DecisionTreeWidget(self)
        self.pbox_scroll = QtGui.QScrollArea(self)
        self.pbox_scroll.setWidget(self.pbox)
        self.pbox_scroll.setWidgetResizable(True)
        self.pbox_scroll.setFocusProxy(self.pbox)
        layout = self.pbox_scroll
        self.setCentralWidget(cmn.ensureWidget(layout))

        
        menubar = self.menuBar()
        fileMenu = menubar.addMenu(_('File'))
        self.act_new_es = cmn.Action(self, _('New expert system'), 'icons/new.png', self.doNew, 'Ctrl+N')
        self.act_open_es = cmn.Action(self, _('Open...'), 'icons/open.png', self.doOpen, 'Ctrl+O')
        self.act_save_es = cmn.Action(self, _('Save'), 'icons/save.png', self.doSave, 'Ctrl+S')
        self.act_save_es_as = cmn.Action(self, _('Save as...'), '', self.doSaveAs)
        self.act_export_png = cmn.Action(self, _('Export the decision tree to PNG...'), '', self.doExportPNG)
        self.act_export_rules = cmn.Action(self, _('Export the rules list...'), '', self.doExportRules)
        self.act_check_es = cmn.Action(self, _('Check the system'), 'icons/flag-blue.png', self.doCheckES, 'F8')
        self.act_run_es = cmn.Action(self, _('Run the system'), 'icons/run.png', self.doRunES, 'F9')
        self.act_about = cmn.Action(self, _('About...'), 'icons/info.png', lambda: AboutDialog().exec_())
        
        fileMenu.addAction(self.act_new_es)
        fileMenu.addAction(self.act_open_es)
        fileMenu.addAction(self.act_save_es)
        fileMenu.addAction(self.act_save_es_as)
        fileMenu.addSeparator()
        fileMenu.addAction(self.act_export_png)
        fileMenu.addAction(self.act_export_rules)
        fileMenu.addSeparator()
        fileMenu.addAction(self.act_check_es)
        fileMenu.addAction(self.act_run_es)
        fileMenu.addSeparator()
        fileMenu.addAction(cmn.Action(self, _('Exit'), '', self.exitApp))
        
        editMenu = menubar.addMenu(_('Edit'))
        self.act_undo = cmn.Action(self, _('Undo'), 'icons/undo.png', gstate.undo, 'Ctrl+Z')
        self.act_redo = cmn.Action(self, _('Redo'), 'icons/redo.png', gstate.redo, 'Ctrl+Shift+Z')
        self.act_goals = cmn.Action(self, _('Goals...'), '', self.doGoals, 'Ctrl+G')
        self.act_factors = cmn.Action(self, _('Factors...'), '', self.doFactors, 'Ctrl+F')
        self.act_es_info = cmn.Action(self, _('Expert system description...'), '', self.doEditDescription, 'Ctrl+D')
        editMenu.addAction(self.act_undo)
        editMenu.addAction(self.act_redo)
        editMenu.addSeparator()
        editMenu.addAction(self.act_goals)
        editMenu.addAction(self.act_factors)
        editMenu.addSeparator()
        editMenu.addAction(self.act_es_info)
        
        helpMenu = menubar.addMenu(_('Help'))
        helpMenu.addAction(self.act_about)
        
        toolbar = cmn.ToolBar([self.act_new_es, self.act_open_es, self.act_save_es, None,
                               self.act_undo, self.act_redo, None, self.act_check_es, self.act_run_es,
                               None, self.act_about])
        toolbar.setObjectName('tlb_main')
        toolbar.setWindowTitle(_('Toolbar'))
        self.addToolBar(toolbar)
        
        gstate.on_update = self.updateUI
        self.doNew()       
        self.show()
    
    def closingCheck(self):
        if gstate.saved:
            return True
        ans = QtGui.QMessageBox.question(self, kProgramName, _('Save changes in expert system "%s"?') % gstate.getName(), 
                                         QtGui.QMessageBox.Yes | QtGui.QMessageBox.No | QtGui.QMessageBox.Cancel, 
                                         QtGui.QMessageBox.Yes)
        if ans == QtGui.QMessageBox.No:
            return True
        if ans == QtGui.QMessageBox.Cancel:
            return False
        return self.doSave()
    
    def exitApp(self):
        if self.closingCheck():
            QtGui.qApp.quit()
            
    def updateUI(self):
        self.setWindowTitle(gstate.getName() + ' - ' + kProgramName)
        self.act_undo.setEnabled(gstate.canUndo())
        self.act_redo.setEnabled(gstate.canRedo())
        gstate.getRoot().computeLayout(ESNode.kDiagramMargin, ESNode.kDiagramMargin)
        w, h = gstate.getExtents()
        self.pbox.setMinimumSize(w, h)
        self.pbox.update()
        
    def resetUI(self):
        self.check_results.reset()
        self.updateUI()
        self.pbox.setFocus()
        
    def doNew(self):
        if not self.closingCheck():
            return
        gstate.resetState()
        self.resetUI()

    def doOpenRaw(self, fname):
        try:
            gstate.loadFromFile(fname)
        except:
            QtGui.QMessageBox.critical(self, kProgramName, _('An error occurred while opening file "%s"') % fname)
            gstate.resetState()
            raise
        self.resetUI()
        
    def doOpen(self):
        if not self.closingCheck():
            return
        fname = cmn.getOpenFileName(self, 'es', _('Open File'), 'Expert System Files (*.es)')
        if fname:
            self.doOpenRaw(fname)
    
    def doSaveRaw(self, fname):
        try:
            gstate.saveToFile(fname)
        except:
            QtGui.QMessageBox.critical(self, kProgramName, _('An error occurred while writing to file "%s"') % fname)
            raise
                
    def doSave(self):
        if gstate.filename:
            self.doSaveRaw(gstate.filename)
            return True
        return self.doSaveAs()
        
    def doSaveAs(self):
        fname = cmn.getOpenFileName(self, 'es', _('Save to File'), 'Expert System Files (*.es)', True)
        if fname:
            self.doSaveRaw(fname)
            self.updateUI() # window title
            return True
        return False
    
    def doExportPNG(self):
        fname = cmn.getOpenFileName(self, 'es', _('Export to PNG'), 'PNG Images (*.png)', True)
        if not fname:
            return
        w, h = gstate.getExtents()
        img = QtGui.QImage(w, h, QtGui.QImage.Format_RGB32)
        img.fill(QtGui.QColor("white"))
        with QtGui.QPainter(img) as p:
            p.setFont(ESNode.font)
            gstate.getRoot().render(p, True)
        img.save(fname, 'PNG')
        
    def doExportRules(self):
        if self.check_results.doCheck() >= kCheckError:
            QtGui.QMessageBox.warning(self, kProgramName, _('There are errors in the expert system. Fix the errors and try again.'))
            return            
        
        rules = []
        def gen(node, conds, ex_goals = []):
            if not node.children:
                conds = _(' AND ').join('"%s" = "%s"' % c for c in conds) if conds else 'True'
                result = ', '.join(ex_goals + [node.content.name])
                rule = _('IF %s\nTHEN %s;') % (conds, result)
                rules.append(rule)
                return
            if node.content.getType() == kFactor:
                for child, choice in zip(node.children, node.content.choices):
                    gen(child, conds + [(node.content.name, choice)])
            else:
                gen(node.children[0], conds, ex_goals + [node.content.name])
                    
        gen(gstate.getRoot(), [])
        data = _('Number of rules: %d\n') % len(rules) + '\n'.join(rules)
        cmn.showReport(_('Rules'), data)            
        
    def doCheckES(self):
        self.check_results.doCheck()
        
    def doEditDescription(self):
        DescriptionDialog().exec_()
        
    def doRunES(self):
        if self.check_results.doCheck() >= kCheckError:
            QtGui.QMessageBox.warning(self, kProgramName, )
            return
        ESWindow().exec_()
                
    def doGoals(self):
        GoalsDialog().exec_()
        
    def doFactors(self):
        FactorsDialog().exec_()
        
    def selectNode(self, node_id):
        node = gstate.getRoot().traverse(lambda node: node if node.ident == node_id else None)
        if node != None:
            gstate.setCurrentNode(node)
            self.pbox_scroll.ensureVisible(node.x + node.width, node.y + node.height)
            self.pbox_scroll.ensureVisible(node.x, node.y) # this part is more important
            self.pbox.update()

    def closeEvent(self, event):
        if not self.closingCheck():
            event.ignore()
            return
        s = QtCore.QSettings('PlatBox', 'Hal0')
        s.setValue("mainwnd/geometry", self.saveGeometry())
        s.setValue('mainwnd/dockstate', self.saveState(0))

app = None

def main():    
    app = QtGui.QApplication(sys.argv)
    _ = MainW()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

