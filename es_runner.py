'''
Created on Mar 6, 2018

@author: LinesPrower
'''

from PyQt4 import QtGui, QtCore
import common as cmn
from objects import gstate, kFactor, kGoal

class ChoiceLabel(QtGui.QLabel):
    
    fnt = QtGui.QFont('Calibri', 16)
    #fnt.setLetterSpacing(QtGui.QFont.PercentageSpacing, 120)
    
    def __init__(self, owner, idx):
        QtGui.QLabel.__init__(self, 'x')
        self.setFont(self.fnt)
        self.setAlignment(QtCore.Qt.AlignHCenter)
        self.owner = owner
        self.idx = idx
        
    def mousePressEvent(self, e):
        self.owner.selectChoice(self.idx)        


class ESWindow(cmn.Dialog):
    
    def __init__(self):
        cmn.Dialog.__init__(self, 'ESS', 'es_runner', gstate.es_name)
        self.pending_release_idx = None
        
        if gstate.factorsMap():
            self.n_choices = max(len(f.choices) for f in gstate.factorsMap().values())
        else:
            self.n_choices = 0
        
        self.choices_labels = [ChoiceLabel(self, i) for i in range(self.n_choices)]
        
        self.question = QtGui.QLabel()
        self.question.setFont(ChoiceLabel.fnt)
        self.question.setWordWrap(True)
        self.question.setAlignment(QtCore.Qt.AlignTop)
        self.question.setStyleSheet('QLabel { background-color:white; }')
        
        self.addAction(cmn.Action(self, 'Restart', '', self.doRestart, 'F2'))
        
        layout = cmn.VBox([self.question] + self.choices_labels + [cmn.HLine()],
                          stretch=[1] + [0] * (self.n_choices + 1))
        
        self.resize(640, 480)
        self.setDialogLayout(layout, lambda: None, True, True, 
                             extra_buttons = [('Начать сначала (F2)', self.doRestart)], autodefault = False)
        self.cur_node = gstate.getRoot()
        self.updateUI()
        
    
    def updateUI(self):
        cur = self.cur_node.content
        msg = 'Ceaнс завершён'
        if not cur:
            text = '<span style="color:red;">%s</span>' % 'Достигнут незавершённый узел'
            choices = []
        elif cur.getType() == kFactor:
            text = cur.name
            choices = cur.choices
            msg = 'Используйте цифры на клавиатуре для быстрого выбора ответов'
        else:
            assert(cur.getType() == kGoal)
            text = '<span style="color:green;">%s</span><br/>%s<br/><span style="font-size:12pt;">%s</span>' 
            text = text % ('Результат:', cur.name, cur.descr)
            choices = []
        
        self.question.setText(text)
        for i, lbl in enumerate(self.choices_labels):
            if i < len(choices):
                lbl.setStyleSheet('QLabel { background-color:white; }\nQLabel:hover { background-color:#afafff; }')
                lbl.setText('<span style="color:#a0a0a0;">%d. </span>%s' % (i+1, choices[i]))
            lbl.setVisible(i < len(choices))
        self.sbar.showMessage(msg)
            
    def doRestart(self):
        self.cur_node = gstate.getRoot()
        self.updateUI()
        
    def selectChoice(self, idx):
        if idx < len(self.cur_node.children):
            self.cur_node = self.cur_node.children[idx]
        self.updateUI()
        
    def keyPressEvent(self, event):
        if event.isAutoRepeat():
            return
        if self.pending_release_idx != None:
            self.updateUI()
            self.pending_release_idx = None
            return
        idx = cmn.eventToNum(event)
        if idx != None and idx < len(self.cur_node.children):
            self.choices_labels[idx].setStyleSheet('QLabel { background-color:#ffffaf; }')
            self.pending_release_idx = idx
            return
        return cmn.Dialog.keyPressEvent(self, event)
    
    def keyReleaseEvent(self, event):
        '''
        The idea is as follows: when the user presses a choice button, the choice is highlighted
        in yellow. Next, we expect the user to release the same button. If this happens, the choice
        is accepted, otherwise the state is reset.
        This gives the user a nice visual feedback and a chance to revoke a choice even after a
        button is pressed by pressing some other button without releasing the first.
        '''
        if event.isAutoRepeat():
            return
        if self.pending_release_idx != None:
            idx = cmn.eventToNum(event)
            if idx == self.pending_release_idx:
                self.selectChoice(idx)
            else:
                self.updateUI()
            self.pending_release_idx = None
            return
        return cmn.Dialog.keyReleaseEvent(self, event)


if __name__ == '__main__':
    app = QtGui.QApplication([])
    gstate.loadFromFile('demo/test.es')
    d = ESWindow()
    d.exec_()