from PyQt4 import QtGui, QtCore
import sys, copy
import objects
import common as cmn
from objects import gstate, kProgramName, ESNode, kFactor, kGoal
from goals_ui import GoalsDialog, GoalDialog
from factors_ui import FactorsDialog, FactorDialog
from checker import CheckResultsPanel, kCheckError
from description_ui import DescriptionDialog
from about_ui import AboutDialog
from es_runner import ESWindow

class DecisionTreeWidget(QtGui.QWidget):


    def __init__(self, owner):
        QtGui.QWidget.__init__(self)
        
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        p = QtGui.QPainter(self)
        objects.ESNode.font_metrics = QtGui.QFontMetrics(objects.ESNode.font, p.device())
        
        pal = QtGui.QPalette()
        pal.setColor(QtGui.QPalette.Background, QtGui.QColor('white'))
        self.setAutoFillBackground(True)
        self.setPalette(pal)
        
        self.act_copy = cmn.Action(self, 'Копировать', 'icons/copy.png', self.doCopy, 'Ctrl+C')        
        self.act_paste = cmn.Action(self, 'Вставить', 'icons/paste.png', self.doPaste, 'Ctrl+V')
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
        menu.addAction(cmn.Action(self, 'Выбрать фактор', '', lambda: self.setFactor(node), 'F'))
        menu.addAction(cmn.Action(self, 'Выбрать цель', '', lambda: self.setGoal(node), 'G'))
        menu.addSeparator()
        self.act_copy.setEnabled(node.content != None)
        menu.addAction(self.act_copy)
        self.act_paste.setEnabled(bool(gstate.clipboard))
        menu.addAction(self.act_paste)
        if node.content:
            menu.addSeparator()
            t = 'Редактировать фактор' if node.content.getType() == kFactor else 'Редактировать цель'
            menu.addAction(cmn.Action(self, t, '', lambda: self.editCurrent(node), 'E'))
        menu.exec_(ev.globalPos())        
        
    def mousePressEvent(self, ev):
        node = self.getNodeUnderCursor(ev)
        if not node:
            return
                
        def set_sel(x):
            x.selected = x == node
        
        gstate.getRoot().traverse(set_sel)
        self.update()
    
    def clearNode(self, node):
        gstate.modifyObject(node)
        node.content = None
        node.children = []
        for c in node.children:
            gstate.deleteNode(c)
    
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
        
    def keyPressEvent(self, ev):
        cur = gstate.getCurrentNode()
        if not cur:
            return
        key = ev.nativeVirtualKey()
        if key == QtCore.Qt.Key_F:
            self.setFactor(cur)
        elif key == QtCore.Qt.Key_G:
            self.setGoal(cur)
        elif key == QtCore.Qt.Key_E:
            self.editCurrent(cur)

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
        self.setCentralWidget(cmn.ensureWidget(self.pbox_scroll))

        
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('Файл')
        self.act_new_es = cmn.Action(self, 'Новая экспертная система', 'icons/new.png', self.doNew, 'Ctrl+N')
        self.act_open_es = cmn.Action(self, 'Открыть...', 'icons/open.png', self.doOpen, 'Ctrl+O')
        self.act_save_es = cmn.Action(self, 'Сохранить', 'icons/save.png', self.doSave, 'Ctrl+S')
        self.act_save_es_as = cmn.Action(self, 'Сохранить как...', '', self.doSaveAs)
        self.act_export_png = cmn.Action(self, 'Экспорт дерева решений в PNG...', '', self.doExportPNG)
        self.act_check_es = cmn.Action(self, 'Проверить систему', 'icons/flag-blue.png', self.doCheckES, 'F8')
        self.act_run_es = cmn.Action(self, 'Запустить систему', 'icons/run.png', self.doRunES, 'F9')
        self.act_about = cmn.Action(self, 'О программе...', 'icons/info.png', lambda: AboutDialog().exec_())
        
        fileMenu.addAction(self.act_new_es)
        fileMenu.addAction(self.act_open_es)
        fileMenu.addAction(self.act_save_es)
        fileMenu.addAction(self.act_save_es_as)
        fileMenu.addSeparator()
        fileMenu.addAction(self.act_export_png)
        fileMenu.addSeparator()
        fileMenu.addAction(self.act_check_es)
        fileMenu.addAction(self.act_run_es)
        fileMenu.addSeparator()
        fileMenu.addAction(cmn.Action(self, 'Выход', '', self.exitApp))
        
        editMenu = menubar.addMenu('Редактирование')
        self.act_undo = cmn.Action(self, 'Отменить', 'icons/undo.png', gstate.undo, 'Ctrl+Z')
        self.act_redo = cmn.Action(self, 'Повторить', 'icons/redo.png', gstate.redo, 'Ctrl+Shift+Z')
        self.act_goals = cmn.Action(self, 'Цели...', '', self.doGoals, 'Ctrl+G')
        self.act_factors = cmn.Action(self, 'Факторы...', '', self.doFactors, 'Ctrl+F')
        self.act_es_info = cmn.Action(self, 'Описание экспертной системы...', '', self.doEditDescription, 'Ctrl+D')
        editMenu.addAction(self.act_undo)
        editMenu.addAction(self.act_redo)
        editMenu.addSeparator()
        editMenu.addAction(self.act_goals)
        editMenu.addAction(self.act_factors)
        editMenu.addSeparator()
        editMenu.addAction(self.act_es_info)
        
        helpMenu = menubar.addMenu('Справка')
        helpMenu.addAction(self.act_about)
        
        toolbar = cmn.ToolBar([self.act_new_es, self.act_open_es, self.act_save_es, None,
                               self.act_undo, self.act_redo, None, self.act_check_es, self.act_run_es,
                               None, self.act_about])
        toolbar.setObjectName('tlb_main')
        toolbar.setWindowTitle('Панель инструментов')
        self.addToolBar(toolbar)
        
        gstate.on_update = self.updateUI
        self.doNew()
        #self.doOpenRaw('demo/test.es')
        
        self.show()
    
    def closingCheck(self):
        if gstate.saved:
            return True
        ans = QtGui.QMessageBox.question(self, kProgramName, 'Сохранить изменения в экспертной системе "%s"?' % gstate.getName(), 
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
        
    def doNew(self):
        if not self.closingCheck():
            return
        gstate.resetState()
        self.resetUI()

    def doOpenRaw(self, fname):
        try:
            gstate.loadFromFile(fname)
        except:
            QtGui.QMessageBox.critical(self, kProgramName, 'Ошибка открытия файла "%s"' % fname)
            gstate.resetState()
            raise
        self.resetUI()
        
    def doOpen(self):
        if not self.closingCheck():
            return
        fname = cmn.getOpenFileName(self, 'es', 'Открыть файл', 'Expert System Files (*.es)')
        if fname:
            self.doOpenRaw(fname)
    
    def doSaveRaw(self, fname):
        try:
            gstate.saveToFile(fname)
        except:
            QtGui.QMessageBox.critical(self, kProgramName, 'Ошибка записи в файл "%s"' % fname)
            raise
                
    def doSave(self):
        if gstate.filename:
            self.doSaveRaw(gstate.filename)
            return True
        return self.doSaveAs()
        
    def doSaveAs(self):
        fname = cmn.getOpenFileName(self, 'es', 'Сохранить в файл', 'Expert System Files (*.es)', True)
        if fname:
            self.doSaveRaw(fname)
            return True
        return False
    
    def doExportPNG(self):
        fname = cmn.getOpenFileName(self, 'es', 'Экспорт в PNG', 'PNG Images (*.png)', True)
        if not fname:
            return
        w, h = gstate.getExtents()
        img = QtGui.QImage(w, h, QtGui.QImage.Format_RGB32)
        img.fill(QtGui.QColor("white"))
        with QtGui.QPainter(img) as p:
            p.setFont(ESNode.font)
            gstate.getRoot().render(p, True)
        img.save(fname, 'PNG')
        
    def doCheckES(self):
        self.check_results.doCheck()
        
    def doEditDescription(self):
        DescriptionDialog().exec_()
        
    def doRunES(self):
        if self.check_results.doCheck() >= kCheckError:
            QtGui.QMessageBox.warning(self, kProgramName, 'Экспертная система содержит ошибки. Устраните ошибки и попробуйте снова.')
            return
        ESWindow().exec_()
                
    def doGoals(self):
        GoalsDialog().exec_()
        
    def doFactors(self):
        FactorsDialog().exec_()
        
    def selectNode(self, node_id):
        node = gstate.getRoot().traverse(lambda node: node if node.ident == node_id else None)
        if node != None:
            def f(x):
                x.selected = x == node
            gstate.getRoot().traverse(f)
            self.pbox_scroll.ensureVisible(node.x, node.y)
            self.pbox_scroll.ensureVisible(node.x + node.width, node.y + node.height)
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

