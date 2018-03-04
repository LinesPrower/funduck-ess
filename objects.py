from PyQt4 import QtCore, QtGui
import os, io, json

kProgramName = 'Funduck ES'

kGoal = 1
kFactor = 2
kNode = 3

objTypes = {}

def getId(obj):
    if obj is None:
        return None
    return obj.ident
    
class State:
    objMap = {} # ident -> ESObject
    typedMaps = {} # type -> (ident -> ESObject)
    undo_stack = []
    redo_stack = []
    next_id = 0
    saved = True
    filename = None
    in_transaction = False
    on_update = None
    
    def getName(self):
        if self.filename != None:
            t = os.path.split(self.filename)[1]
            return os.path.splitext(t)[0]
        return 'Без имени'

    def getObject(self, ident):
        if ident in self.objMap:
            return self.objMap[ident]
        return None
    
    def getMap(self, obj_type):
        if obj_type not in self.typedMaps:
            self.typedMaps[obj_type] = {}
        return self.typedMaps[obj_type]
    
    def goalsMap(self):
        return self.getMap(kGoal)
    
    def factorsMap(self):
        return self.getMap(kFactor)
    
    def addObjectRaw(self, obj):
        self.getMap(obj.getType())[obj.ident] = obj
        self.objMap[obj.ident] = obj
        
    def callUpdateHandler(self):
        if self.on_update != None:
            self.on_update()
            
    def wrapInTransaction(self, f):
        if self.in_transaction:
            return f
        else:
            self.beginTransaction()
            try:
                return f()
            finally:
                self.endTransaction()

    def addNewObject(self, obj):
        def f():
            self.saved = False
            self.next_id += 1
            obj.ident = self.next_id
            self.addObjectRaw(obj)
            return obj
        
        return self.wrapInTransaction(f)
        
    def modifyObject(self, obj):
        def f():
            self.saved = False
        
        return self.wrapInTransaction(f)
    
    def deleteObject(self, obj):
        def f():
            self.saved = False
            del self.getMap(obj.getType())[obj.ident]
            del self.objMap[obj.ident]
        
        return self.wrapInTransaction(f)
    
    def canUndo(self):
        return bool(self.undo_stack)
    
    def canRedo(self):
        return bool(self.redo_stack)
    
    def undo(self):
        assert(not self.in_transaction)
        if not self.canUndo():
            return
        self.redo_stack.append(self.getSnapshot())
        self.setSnapshot(self.undo_stack.pop())
        self.saved = False
        self.callUpdateHandler()
        
    def redo(self):
        assert(not self.in_transaction)
        if not self.canRedo():
            return
        self.undo_stack.append(self.getSnapshot())
        self.setSnapshot(self.redo_stack.pop())
        self.saved = False
        self.callUpdateHandler()
    
    def beginTransaction(self, name = 'undefined_op'):
        assert(not self.in_transaction)
        self.undo_stack.append(self.getSnapshot())
        self.redo_stack.clear()
        self.in_transaction = True
    
    def endTransaction(self):
        assert(self.in_transaction)
        self.in_transaction = False
        self.callUpdateHandler()
    
    def getRoot(self):
        # we assume that the root always has id = 0
        return self.objMap[0]
    
    def hasInTree(self, obj):
        def f(node):
            if node.content == obj:
                return True
        return self.getRoot().traverse(f) == True
    
    def getCurrentNode(self):
        def f(node):
            if node.selected:
                return node
        return self.getRoot().traverse(f)
    
    def resetState(self):
        assert(not self.in_transaction)
        self.objMap.clear()
        self.typedMaps.clear()
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.saved = True
        self.filename = None
        self.next_id = 0
        root = ESNode(0)
        root.selected = True
        self.addObjectRaw(root)
    
    def getSnapshot(self):
        data = []
        saved = set()
        def f(obj):
            if obj.ident in saved:
                return
            saved.add(obj.ident)
            data.append(obj.serialize(f))
        for obj in self.objMap.values():
            f(obj)
        return json.dumps({ 'objects' : data, 'version' : 1})
    
    def saveToFile(self, filename):
        assert(not self.in_transaction)
        data = self.getSnapshot()
        with io.open(filename, 'wt', encoding='utf8') as f:
            f.write(data)
        self.filename = filename
        self.saved = True
    
    def setSnapshot(self, data):
        data = json.loads(data)
        self.objMap.clear()
        self.typedMaps.clear()
        self.next_id = 0
        for item in data['objects']:
            obj = objTypes[item['ty']]()
            obj.deserialize(item)
            self.addObjectRaw(obj)
            self.next_id = max(self.next_id, obj.ident)
        
        
    def loadFromFile(self, filename):
        assert(not self.in_transaction)
        with io.open(filename, encoding='utf8') as f:
            data = f.read()
        self.setSnapshot(data)
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.saved = True
        self.filename = filename
        self.getRoot().selected = True
            
        
gstate = State()

class ESObject:
    def __init__(self, ident):
        self.ident = ident
        
    def getType(self):
        return None

    def serialize(self, f):
        return { 'id' : self.ident, 'ty' : self.getType() }

    def deserialize(self, data):
        self.ident = data['id']


class ESGoal(ESObject):
    def __init__(self, ident = None, name = 'Undefined', descr = 'Undefined'):
        ESObject.__init__(self, ident)
        self.name = name
        self.descr = descr
        
    def getType(self):
        return kGoal

    def serialize(self, f):
        res = super().serialize(f)
        res['name'] = self.name
        res['descr'] = self.descr
        return res

    def deserialize(self, data):
        super().deserialize(data)
        self.name = data['name']
        self.descr = data['descr']
        
objTypes[kGoal] = ESGoal

class ESFactor(ESObject):
    def __init__(self, ident = None, name = 'Undefined'):
        ESObject.__init__(self, ident)
        self.name = name
        self.is_binary = True 
        self.choices = self.getBinaryChoices()
        
    def getType(self):
        return kFactor

    def serialize(self, f):
        res = super().serialize(f)
        res['name'] = self.name
        res['is_binary'] = self.is_binary
        res['choices'] = self.choices
        return res

    def deserialize(self, data):
        super().deserialize(data)
        self.name = data['name']
        self.is_binary = data['is_binary']
        self.choices = data['choices']
 
    @staticmethod
    def getBinaryChoices():
        return ['Да', 'Нет']
    
    
        
objTypes[kFactor] = ESFactor


class ESNode(ESObject):
    def __init__(self, ident = None, content = None):
        ESObject.__init__(self, ident)
        self.children = []
        self.content = content

        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.lineheight = 0
        self.selected = False
        
    def getType(self):
        return kNode

    def serialize(self, f):
        res = super().serialize(f)
        def id(obj):
            if obj:
                f(obj)
            return getId(obj)
        
        res['content'] = id(self.content)
        res['children'] = [id(x) for x in self.children]
        return res

    def deserialize(self, data):
        super().deserialize(data)
        self.content = gstate.getObject(data['content'])
        self.children = [gstate.getObject(x) for x in data['children']]

    def traverse(self, f):
        t = f(self)
        if t != None:
            return t
        for c in self.children:
            t = c.traverse(f)
            if t != None:
                return t

    font = QtGui.QFont("Arial", 10)
    font_metrics = QtGui.QFontMetrics(font)
    kDefaultText = 'Add a factor or a goal'
    kVerticalMargin = 5
    kHorizontalMargin = 5
    kChoicesSpacing = 6

    # arguments: upper left corner of this subtree
    # returns: height of this subtree
    def computeLayout(self, x, y):
        self.computeDimensions()
        self.x = x
        self.y = y
        res = self.height
        kVerticalSpan = 5
        res2 = 0
        for c in self.children:
            res2 += c.computeLayout(x + self.width + 20, y + res2) + kVerticalSpan
        return max(res, res2 - kVerticalSpan)

    def getEntryPoint(self):
        return QtCore.QPointF(self.x, self.y + self.kVerticalMargin + self.lineheight / 2)

    def getExitPoint(self, idx):
        return QtCore.QPointF(self.x + self.width, self.kVerticalMargin + self.lineheight * (idx + 0.5) + self.kChoicesSpacing * idx)

    def computeDimensions(self):
        text = self.getText()
        self.lineheight = self.font_metrics.height()
        self.width = max(self.font_metrics.boundingRect(x).width() for x in text) + 2 * self.kHorizontalMargin
        self.height = self.lineheight * len(text) + self.kChoicesSpacing * (len(text) - 1) + 2 * self.kVerticalMargin

    def getText(self):
        if self.content:
            ty = self.content.getType()
            if ty == kGoal:
                return [self.content.name]
            if ty == kFactor:
                return [self.content.name] + self.content.choices
        return [self.kDefaultText]

    def getColor(self):
        if self.content:
            ty = self.content.getType()
            if ty == kGoal:
                return QtGui.QColor(128, 255, 128)
            if ty == kFactor:
                return QtGui.QColor(128, 128, 255)
        return QtGui.QColor(255, 255, 0)

    def render(self, p):
        #p = QtGui.QPainter()
        p.setBrush(self.getColor())
        
        if self.selected:
            pen = QtGui.QPen(QtGui.QColor("blue"))
            pen.setWidth(3)
            p.setPen(pen)
        p.drawRect(self.x, self.y, self.width, self.height)
        if self.selected:
            p.setPen(QtGui.QColor("black"))
            
        text = self.getText()
        y = self.y + self.kVerticalMargin
        x = self.x
        for s in text:
            p.drawText(x + self.kHorizontalMargin, y + self.lineheight, s)
            y += self.lineheight + self.kChoicesSpacing
            
        # connect to the children
        start_idx = 1 if self.content and self.content.getType() == kFactor else 0
        for i, c in enumerate(self.children, start_idx):
            p.drawLine(self.getExitPoint(i), c.getEntryPoint())
            c.render(p)

objTypes[kNode] = ESNode



