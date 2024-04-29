import maya.cmds as mc
from PySide2.QtGui import QIntValidator, QDoubleValidator, QPalette, QColor


#facilities
class Vector:
    def __init__(self, *args):
        self.x = args[0]
        self.y = args[1]
        self.z = args[2]
    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __mul__(self, scalar):
        return Vector(self.x * scalar, self.y * scalar, self.z * scalar)
    
    def __truediv__(self, scalar):
        if scalar != 0:
            return Vector(self.x / scalar, self.y / scalar, self.z / scalar)
        
    def GetLength(self):
        return (self.x ** 2 + self.y ** 2 + self.z ** 2)**0.5
    
    def GetNormalized(self):
        return self/self.GetLength()
    
    def __str__(self):
        return f"<{self.x}, {self.y}, {self.z}>"



def GetObjPos(obj):
    pos = mc.xform(obj, t=True, q=True, ws=True)
    return Vector(pos[0], pos[1], pos[2])

def SetObjPos(obj, pos:Vector):
    mc.setAttr(obj + ".translate", pos.x, pos.y, pos.z, type = "float3")

def SetControllerColor(ctrlName, color:QColor):
    mc.setAttr(ctrlName + ".overrideEnabled",1)
    mc.setAttr(ctrlName + ".overrideRGBColors", 1)
    mc.setAttr(ctrlName + ".overrideColorRGB", color.redF(), color.greenF(), color.blueF())

def CreateCntrollerForJnt(jnt, size = 10, color = QColor(0, 0, 0)):
    ctrlName = "ac_" + jnt
    ctrlGrpName = ctrlName + "_grp"
    
    mc.circle(n=ctrlName, nr=(1, 0, 0), r = size)
    mc.group(ctrlName, n =ctrlGrpName)
    mc.matchTransform(ctrlGrpName, jnt)
    mc.orientConstraint(ctrlName, jnt)
    SetControllerColor(ctrlName, color)
    return ctrlName, ctrlGrpName

def CreateBox(name, size = 10, color = QColor(0, 0, 0)):
    p = ((-0.5,0.5,0.5), (0.5,0.5,0.5), (0.5,0.5,-0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (-0.5, -0.5, 0.5), (0.5, -0.5, 0.5), (0.5, 0.5, 0.5), (0.5, -0.5, 0.5), (0.5, -0.5, -0.5), (0.5, 0.5, -0.5), (0.5, -0.5, -0.5), (-0.5, -0.5, -0.5), (-0.5, 0.5, -0.5), (-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5))
    mc.curve(n =name, d=1, p = p)
    mc.setAttr(name + ".scale", size, size, size, type = "float3")
    mc.makeIdentity(name, apply=True)
    SetControllerColor(name, color)

def CreatePlus(name, size = 10, color = QColor(0, 0, 0)):
    p = ((0.5, 0, 1), (0.5, 0,0.5), (1,0,0.5), (1,0,-0.5), (0.5, 0, -0.5), (0.5,0, -1), (-.5,0,  -1), (-.5, 0,-.5), (-1, 0, -0.5), (-1, 0, 0.5), (-0.5, 0, 0.5),(-0.5, 0, 1), (0.5, 0, 1))
    mc.curve(n=name, d=1, p=p)
    mc.setAttr(name + ".rx", 90)
    mc.setAttr(name + ".scale", size, size, size, type = "float3")
    mc.makeIdentity(name, apply=True)
    SetControllerColor(name, color)

class ThreeJntChain:
    def __init__(self):
        self.root = ""
        self.middle = ""
        self.end = ""
        self.controllerSize = 5
        self.controllerColor = QColor(0, 0, 0)

    def AutoFindJntsBasedOnSelf(self):
        self.root = mc.ls(sl=True, type = "joint")[0]
        self.middle = mc.listRelatives(self.root, c=True, type = "joint")[0]
        self.end = mc.listRelatives(self.middle,c=True, type = "joint")[0]
        print("end")

    def RigThreeJntChain(self, size, color):
        self.controllerColor = color
        rootCtrl, rootCtrlGrp = CreateCntrollerForJnt(self.root, self.controllerSize, self.controllerColor)
        middleCtrl, middleCtrlGrp = CreateCntrollerForJnt(self.middle, self.controllerSize, self.controllerColor)
        endCtrl, endCtrlGrp = CreateCntrollerForJnt(self.end, self.controllerSize, self.controllerColor)
        self.controllerSize = size

        mc.parent(middleCtrlGrp, rootCtrl)
        mc.parent(endCtrlGrp, middleCtrl)

        ikEndCtrl = "ac_ik_" + self.end
        CreateBox(ikEndCtrl, self.controllerSize, self.controllerColor)
        ikEndCtrlGrp = ikEndCtrl + "_grp"
        mc.group(ikEndCtrl, n = ikEndCtrlGrp)
        mc.matchTransform(ikEndCtrlGrp, self.end)
        endOrientConstaint = mc.orientConstraint(ikEndCtrl, self.end)[0]

        ikHandleName = "ikHandle_" + self.end
        mc.ikHandle(n=ikHandleName, sj = self.root, ee = self.end, sol = "ikRPsolver")

        ikMidCtrl = "ac_ik_" + self.middle
        mc.spaceLocator(n=ikMidCtrl)
        SetControllerColor(ikMidCtrl, self.controllerColor)

        rootJntPos = GetObjPos(self.root)
        endJntPos = GetObjPos(self.end)
        poleVec = mc.getAttr(ikHandleName + ".poleVector")[0]
        poleVec = Vector(poleVec[0], poleVec[1], poleVec[2])

        armVec = endJntPos - rootJntPos
        halfArmLength = armVec.GetLength()/2

        poleVecPos = rootJntPos + poleVec * halfArmLength + armVec/2
        ikMidCtrlGrp = ikMidCtrl + "_grp"
        mc.group(ikMidCtrl, n = ikMidCtrlGrp)
        mc.setAttr(ikMidCtrl + ".scale", self.controllerSize/2, self.controllerSize/2, self.controllerSize/2, type = "float3")
        SetObjPos(ikMidCtrlGrp, poleVecPos)

        mc.poleVectorConstraint(ikMidCtrl, ikHandleName)
        mc.parent(ikHandleName, ikEndCtrl)

        ikfkBlendCtrl = "ac_"+self.root + "_ikfk_blend"
        CreatePlus(ikfkBlendCtrl, 2, self.controllerColor)
        ikfkBlendctrlGrp = ikfkBlendCtrl + "_grp"
        mc.group(ikfkBlendCtrl, n = ikfkBlendctrlGrp)

        dir = 1
        if rootJntPos.x < 0:
            dir = -1
        ikfkBlendPos = rootJntPos + Vector(dir * halfArmLength/4, halfArmLength/4, 0)
        SetObjPos(ikfkBlendctrlGrp, ikfkBlendPos)

        ikfkBlendAttr = "ikfkBlend"
        mc.addAttr(ikfkBlendCtrl, ln = ikfkBlendAttr, k=True, at = "float", min = 0, max = 1)
        mc.connectAttr(ikfkBlendCtrl + "." + ikfkBlendAttr, ikHandleName + ".ikBlend")

        ikfkReverse = "reverse_" + self.root + "_ikfkblend"
        mc.createNode("reverse", n = ikfkReverse)

        mc.connectAttr(ikfkBlendCtrl + "."+ikfkBlendAttr, ikfkReverse+".inputX")
        mc.connectAttr(ikfkBlendCtrl + "."+ikfkBlendAttr, ikEndCtrlGrp+".v")
        mc.connectAttr(ikfkBlendCtrl + "."+ikfkBlendAttr, ikMidCtrlGrp+".v")
        mc.connectAttr(ikfkReverse + ".outputX", rootCtrlGrp + ".v")

        mc.connectAttr(ikfkBlendCtrl + "."+ikfkBlendAttr, endOrientConstaint+".w1")
        mc.connectAttr(ikfkReverse + ".outputX", endOrientConstaint+".w0")

        mc.hide(ikHandleName)

        topGrp = self.root + "_rig_grp"
        mc.group(rootCtrlGrp, ikMidCtrlGrp, ikEndCtrlGrp,ikfkBlendctrlGrp, n = topGrp)

#UI
from PySide2.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QLineEdit, QHBoxLayout, QColorDialog

class ThreeJntChainWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Create Three Joint Chain")
        self.setGeometry(0, 0, 600, 300)

        self.masterLayout = QVBoxLayout()
        self.setLayout(self.masterLayout)

        hintLabel = QLabel("Please select the root of the joint chain")
        self.masterLayout.addWidget(hintLabel)

        autoFindBtn = QPushButton("Auto Find Joints")
        self.masterLayout.addWidget(autoFindBtn)
        autoFindBtn.clicked.connect(self.AutoFindBtnClicked)

        """radioButtons = QRadioButton("buttons")
        self.masterLayout.addWidget(radioButtons)

        radioButtons = QRadioButton("buttons")
        self.masterLayout.addWidget(radioButtons)"""

        self.selectionDisplay = QLabel()
        self.masterLayout.addWidget(self.selectionDisplay)

        rigThreeJntChainBtn = QPushButton("Rig Three Joint Chain")
        self.masterLayout.addWidget(rigThreeJntChainBtn)
        rigThreeJntChainBtn.clicked.connect(self.RigThreeJntChainBtnClicked)


        ctrlSettingLayout = QHBoxLayout()
        self.ctrlSizeLabel = QLabel("Controller Size:")
        ctrlSettingLayout.addWidget(self.ctrlSizeLabel)
        
        self.ctrlSize = QLineEdit()
        self.ctrlSize.setValidator(QDoubleValidator())
        self.ctrlSize.setText("10")
        self.ctrlSize.textChanged.connect(self.CtrlSizeValueSet)
        ctrlSettingLayout.addWidget(self.ctrlSize)


        self.ctrlColorLabel = QLabel("Controller Color: \n(Click to select color)")
        ctrlSettingLayout.addWidget(self.ctrlColorLabel)

        self.ctrlColor = QColorDialog()
        self.controlColorBtn = QPushButton("Control Color")
        self.controlColorBtn.setStyleSheet(f"background-color : rgb(0,0,0)")
        ctrlSettingLayout.addWidget(self.controlColorBtn)
        self.controlColorBtn.clicked.connect(self.CtrlColorValueSet)

        self.masterLayout.addLayout(ctrlSettingLayout)

        self.adjustSize()
        self.threeJntChain = ThreeJntChain()

    def CtrlSizeValueSet(self, valStr:str):
        size = float(valStr)
        self.threeJntChain.controllerSize = size
        """self.ctrlSize.setValidator(QDoubleValidator())
        print(f"{self.ctrlSize}")"""
        print("done typing")
    
    def CtrlColorValueSet(self):
        color = self.ctrlColor.getColor()
        if color.isValid():
            self.controlColorBtn.setAutoFillBackground(True)
            self.controlColorBtn.setStyleSheet(f"background-color : rgb({color.red()}, {color.green()}, {color.blue()})")
            self.threeJntChain.controllerColor = color

    def AutoFindBtnClicked(self):
        print("button pressed")
        self.threeJntChain.AutoFindJntsBasedOnSelf()
        self.selectionDisplay.setText(f"{self.threeJntChain.root}, {self.threeJntChain.middle}, {self.threeJntChain.end}")
    
    def RigThreeJntChainBtnClicked(self):
         size = float(self.ctrlSize.text())
         color = self.controlColorBtn.palette().button().color()
         self.threeJntChain.RigThreeJntChain(size = size, color=color)

        

threeJntChainWidget = ThreeJntChainWidget();
threeJntChainWidget.show()