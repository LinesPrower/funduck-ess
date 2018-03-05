from PyQt4 import QtGui, QtCore
import json, sys, copy, os
import io, objects
import common as cmn
from objects import gstate, kProgramName, ESNode
from goals_ui import GoalsDialog
from factors_ui import FactorsDialog
import goals_ui
from checker import CheckResultsPanel
from description_ui import DescriptionDialog
from about_ui import AboutDialog

class DecisionTreeWidget(QtGui.QWidget):


    def __init__(self, owner):
        QtGui.QWidget.__init__(self)
        
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        p = QtGui.QPainter(self)
        objects.ESNode.font_metrics = QtGui.QFontMetrics(objects.ESNode.font, p.device())
        #gstate.getRoot().computeLayout(10, 10)
        self.owner = owner
        
    def mousePressEvent(self, ev):
        x = ev.x()
        y = ev.y()
        def set_sel(node):
            node.selected = node.x <= x <= node.x + node.width and node.y <= y <= node.y + node.height

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
        #key = ev.key()
        key = ev.nativeVirtualKey()
        if key == QtCore.Qt.Key_F:
            self.setFactor(cur)
        elif key == QtCore.Qt.Key_G:
            self.setGoal(cur)
        

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
        self.setCentralWidget(cmn.ensureWidget(self.pbox))

        
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('Файл')
        self.act_new_es = cmn.Action(self, 'Новая экспертная система', 'icons/new.png', self.doNew, 'Ctrl+N')
        self.act_open_es = cmn.Action(self, 'Открыть...', 'icons/open.png', self.doOpen, 'Ctrl+O')
        self.act_save_es = cmn.Action(self, 'Сохранить', 'icons/save.png', self.doSave, 'Ctrl+S')
        self.act_save_es_as = cmn.Action(self, 'Сохранить как...', '', self.doSaveAs)
        self.act_export_png = cmn.Action(self, 'Экспорт дерева решений в PNG...', '', self.doExportPNG)
        self.act_check_es = cmn.Action(self, 'Проверить систему', '', self.doCheckES, 'F8')
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
        pass
                
    def doGoals(self):
        GoalsDialog().exec_()
        
    def doFactors(self):
        FactorsDialog().exec_()        

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

