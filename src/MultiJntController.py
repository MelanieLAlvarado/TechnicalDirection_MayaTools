#commandPort -name "localhost:7001" -sourceType "mel";
import maya.cmds as mc
from PySide2.QtCore import Signal, Qt
from PySide2.QtGui import QIntValidator, QDoubleValidator, QPalette, QColor, QPainter, QBrush
from PySide2.QtWidgets import QCheckBox, QLineEdit, QWidget, QPushButton, QListWidget, QAbstractItemView, QLabel, QHBoxLayout, QVBoxLayout, QMessageBox, QColorDialog

#NOTES: 
#   I still need to put toggle to include root or not
#   I should put options for override names
#   use the self.jntKey more often
def SetControllerColor(ctrlName, color:QColor):
    mc.setAttr(ctrlName + ".overrideEnabled",1)
    mc.setAttr(ctrlName + ".overrideRGBColors", 1)
    mc.setAttr(ctrlName + ".overrideColorRGB", color.redF(), color.greenF(), color.blueF())

class RigMultiJnt():
    def __init__(self):
        self.jntKey = ""
        self.rootJnt = "" #proboably add parameter to enable or disable this. (bool?)
        self.baseJnt = ""
        self.midJnt = ""
        self.endJnt = ""
        self.shouldRigRoot = True
        
        self.chainJnts = set()
        self.drvJnts = set()

        self.controllerSize = 15
        self.controllerColor = QColor(0, 0, 0)
        self.overrideNames = ["base", "mid", "end"] #set in widget next to 'include rootjnt' (maybe with names for each joint?)

    def RigMultiJointChain(self, size = 15, color = QColor(0, 0, 0)):
        self.controllerColor = color
        self.controllerSize = size

        drvJntGrp = self.CreateDriverJnts()
        if self.shouldRigRoot == True:
            rootCtrl, rootCtrlGrp = self.CreateJntController(self.baseJnt, self.controllerSize + 2, self.controllerColor)
        
        baseCtrl, baseCtrlGrp = self.CreateJntController(self.baseJnt, self.controllerSize, self.controllerColor, False, self.overrideNames[0])
        midCtrl, midCtrlGrp = self.CreateJntController(self.midJnt, self.controllerSize, self.controllerColor, True, self.overrideNames[1])        
        endCtrl, endCtrlGrp = self.CreateJntController(self.endJnt, self.controllerSize, self.controllerColor, False, self.overrideNames[2])
        
        ikHandle, ikGrp = self.CreateDriverIK(baseCtrl, endCtrl)

        rigGrp = self.jntKey + "_rig_grp"
        mc.group(drvJntGrp, n = rigGrp)
        if self.shouldRigRoot ==True:
            mc.parent(midCtrlGrp, rootCtrl)
            mc.parent(baseCtrlGrp, rootCtrl)
            mc.parent(rootCtrlGrp, rigGrp)
        else:
            nonRootGrp = "ac_" + self.jntKey + "_grp"
            mc.group(baseCtrlGrp, n = nonRootGrp)
            mc.parent(nonRootGrp, rigGrp)
        mc.parent(endCtrlGrp, midCtrl)
        mc.parent(ikGrp, rigGrp)

        if self.shouldRigRoot == True:
            mc.parentConstrain(rootCtrl, drvJntGrp)
        """start of node section. might move into separate functions"""
        #ikHandle_spine.roll = ac_hips.rotateX;
        #.O[1] = ac_hips.rotateX + ac_spine.rotateX + ac_chest.rotateX;
        mc.expression(s = ikHandle + ".roll = " + baseCtrl + ".rotateX; " + ikHandle + ".twist = " + baseCtrl + ".rotateX + " + midCtrl + ".rotateX + " + endCtrl + ".rotateX;")
        #REAL NODE WORK STARTS!
        pass

    def CreateJntController(self, jnt, size = float(10), color = QColor(0, 0, 0), orientConstraint = True, overrideName = str("")):
        if overrideName == "":
            ctrlName = "ac_" + jnt
        else:
            ctrlName = "ac_" + overrideName
        ctrlGrpName = ctrlName + "_grp"
        mc.circle(n=ctrlName, nr=(1, 0, 0), r = size)
        mc.group(ctrlName, n =ctrlGrpName)
        mc.matchTransform(ctrlGrpName, jnt)
        if orientConstraint == True:
            mc.orientConstraint(ctrlName, jnt)
        else: 
            mc.parentConstraint(ctrlName, jnt)
        SetControllerColor(ctrlName, color)
        return ctrlName, ctrlGrpName

    def CreateDriverJnts(self):
        jnts = list(self.chainJnts)
        dupJnts = mc.duplicate(jnts[0], n = "drv_" + jnts[0], rc = True)
        for dup in dupJnts:
            dup = "drv_" + dup
        drvJnts = []
        for dup in dupJnts:
            if mc.objExists(dup) and mc.objectType(dup) == "joint":
                drvJnts.append(dup)
                drvJnts = self.AddChildOfJoint(dup, drvJnts)
                break
        
        if len(drvJnts) == 0:
            return False, "No Joint Selected!"

        dupJnts.reverse()
        for dup in dupJnts:
            if dup not in drvJnts:
                mc.delete(dup)
        index = 0
        initialJntNames = list(self.chainJnts)
        renamedDrvJnt = []
        for drv in drvJnts:
            drv = mc.rename(drv, "drv_" + initialJntNames[index], ignoreShape = True)
            renamedDrvJnt.append(drv)
            index += 1

        drvJntGrp = self.jntKey + "_drv_grp"
        mc.group(renamedDrvJnt[0], n=drvJntGrp)
        self.drvJnts = set(renamedDrvJnt)
        self.drvJnts = sorted(set(renamedDrvJnt), key=renamedDrvJnt.index)
        return drvJntGrp


    def CreateDriverIK(self, baseCtrl, endCtrl):
        startDrvJnt = mc.ls(self.drvJnts, type='joint')[0]
        endDrvJnt = mc.listRelatives(self.drvJnts, ad=True, type='joint')[0]
        
        ikHandleName = "ikHandle_" + self.jntKey
        ikCurve = mc.ikHandle(n=ikHandleName, sj = startDrvJnt, ee = endDrvJnt, sol = "ikSplineSolver")[2]
        
        upperVerts = mc.ls(f"{ikCurve}.cv[2:3]")
        upperCluster = mc.cluster(upperVerts)
        mc.parent(upperCluster[1], endCtrl)
        lowerVerts = mc.ls(f"{ikCurve}.cv[0:1]")
        lowerCluster = mc.cluster(lowerVerts)
        mc.parent(lowerCluster[1], baseCtrl)
        
        ikGrp = "IK_" + self.jntKey + "_grp"
        mc.group(ikHandleName, ikCurve, n = ikGrp)

        startChainJnt = mc.ls(self.chainJnts, type='joint')[0]
        endChainJnt = mc.ls(self.chainJnts, type='joint')
        endChainJnt.reverse()
        endChainJnt = endChainJnt[0]

        tempDrvList = list(self.drvJnts)
        tempDrvList.remove(startDrvJnt)
        tempDrvList.remove(endDrvJnt)
        print(tempDrvList)

        tempChainList = list(self.chainJnts)
        tempChainList.remove(startChainJnt)
        tempChainList.remove(endChainJnt)
        print(tempChainList)
        index = 0
        for chain in tempChainList:
            mc.parentConstraint(tempDrvList[index], chain)
            index
        print(self.drvJnts)
        print(self.chainJnts)
        return ikHandleName, ikGrp

    def AddChildOfJoint(self, jnt, jnts:list):
        nextJnts = mc.listRelatives(jnt, c=True)
        for j in nextJnts:
            if mc.objectType(j) == "joint" and str(self.jntKey) in str(j):
                jnts.append(j)
                self.AddChildOfJoint(j, jnts)
                return jnts

    def AddLoopedJoints(self):
        selection = mc.ls(sl=True)
        if not selection:
            return False, "No Jnts Selected!"
        self.chainJnts.clear()
        jnts = []
        for sel in selection:
            if mc.objExists(sel) and mc.objectType(sel) == "joint":
                jnts.append(sel)
                jnts = self.AddChildOfJoint(sel, jnts)
                return jnts

    def AddSelectedJnts(self):
        jnts = self.AddLoopedJoints()
        if len(jnts) == 0:
            return False, "No Joint Selected!"
        self.chainJnts = set(jnts)
        self.chainJnts = sorted(set(jnts), key=jnts.index)
        print(f"self.chainJnts : {self.chainJnts}")
        return True, ""

    def AssignBaseJnt(self):
        tempJnt = mc.ls(sl=True, type = "joint")[0]
        if mc.objExists(tempJnt):
            self.baseJnt = tempJnt
            return True, ""
        else:
            return False, "Selected is not a joint!"

    def AssignMidJnt(self):
        tempJnt = mc.ls(sl=True, type = "joint")[0]
        if mc.objExists(tempJnt):
            self.midJnt = tempJnt
            return True, ""
        else:
            return False, "Selected is not a joint!"

    def AssignEndJnt(self):
        tempJnt = mc.ls(sl=True, type = "joint")[0]
        if mc.objExists(tempJnt):
            self.endJnt = tempJnt
            return True, ""
        else:
            return False, "Selected is not a joint!"

class ColorPicker(QWidget):
    colorChanged = Signal(QColor)
    def __init__(self, width = 80, height = 20):
        super().__init__()
        self.setFixedSize(width, height)
        self.color = QColor(128, 128, 128)

    def mousePressEvent(self, event):
        color = QColorDialog().getColor(self.color)
        if color.isValid():
            self.color = color
            self.colorChanged.emit(self.color)
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setBrush(QBrush(self.color))
        painter.drawRect(0, 0, self.width(), self.height())

class MultiJntWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Create Multiple Joint Chain")
        self.setGeometry(0, 0, 600, 300)
        self.rigMultiJnt = RigMultiJnt()

        self.masterLayout = QHBoxLayout()
        self.setLayout(self.masterLayout)

        self.jointSelectionLayout = QVBoxLayout()
        self.CreateJntSelection()
        self.masterLayout.addLayout(self.jointSelectionLayout)

        jointCustomizationLayout = QVBoxLayout()
        hintLabel = QLabel("Select each of the corresponding joints \nof the chain and confirm")
        jointCustomizationLayout.addWidget(hintLabel)

        self.selectedBaseLabel = QLabel()
        jointCustomizationLayout.addWidget(self.selectedBaseLabel)
        confirmBaseBtn = QPushButton("Confirm as Base Joint")
        confirmBaseBtn.clicked.connect(self.BaseJntBtnClicked)
        jointCustomizationLayout.addWidget(confirmBaseBtn)

        self.selectedMidLabel = QLabel()
        jointCustomizationLayout.addWidget(self.selectedMidLabel)
        confirmMidBtn = QPushButton("Confirm as Middle Joint")
        confirmMidBtn.clicked.connect(self.MidJntBtnClicked)
        jointCustomizationLayout.addWidget(confirmMidBtn)

        self.selectedEndLabel = QLabel()
        jointCustomizationLayout.addWidget(self.selectedEndLabel)
        confirmEndBtn = QPushButton("Confirm as End Joint")
        confirmEndBtn.clicked.connect(self.EndJntBtnClicked)
        jointCustomizationLayout.addWidget(confirmEndBtn)

        #enableRootCtrl = QCheckBox()
        #enableRootCtrl.setChecked(self.rigMultiJnt.shouldRigRoot)
        #self.additionalOptionsLayout.addWidget(enableRootCtrl)
        #enableRootCtrl.toggled.connect(self.EnableCheckboxToggled)

        #suffixLabel = QLabel("Create Root Ctrl")
        #self.additionalOptionsLayout.addWidget(suffixLabel)

        self.masterLayout.addLayout(jointCustomizationLayout)

        self.additionalOptionsLayout = QHBoxLayout()
        self.ctrlSize = QLineEdit()
        self.CreateCntrlSettingSection()
        jointCustomizationLayout.addLayout(self.additionalOptionsLayout)

        rigButton = QPushButton("Rig Multi-Chain")
        rigButton.clicked.connect(self.RigMultiChainBtnClicked)
        jointCustomizationLayout.addWidget(rigButton)

    def ChainKeyNameSet(self, valStr:str):
        key = valStr
        self.rigMultiJnt.jntKey = key

    def BaseJntBtnClicked(self):
        self.rigMultiJnt.AssignBaseJnt()
        self.selectedBaseLabel.setText(f"{self.rigMultiJnt.baseJnt}")
        pass
    
    def MidJntBtnClicked(self):
        self.rigMultiJnt.AssignMidJnt()
        self.selectedMidLabel.setText(f"{self.rigMultiJnt.midJnt}")
        pass

    def EndJntBtnClicked(self):
        self.rigMultiJnt.AssignEndJnt()
        self.selectedEndLabel.setText(f"{self.rigMultiJnt.endJnt}")
        pass

    def RigMultiChainBtnClicked(self):
        size = float(self.ctrlSize.text())
        color = self.ctrlColorPicker.color
        self.rigMultiJnt.RigMultiJointChain(size = size, color = color)

    def EnableCheckboxToggled(self):
        self.rigMultiJnt.shouldRigRoot = not self.rigMultiJnt.shouldRigRoot
        pass

    def CtrlSizeValueSet(self, valStr:str):
        size = float(valStr)
        self.rigMultiJnt.controllerSize = size

    def CtrlColorPickerColorChanged(self, newColor:QColor):
        self.rigMultiJnt.controllerColor = QColor(newColor)
        pass

    def AddJointsBtnClicked(self):
        success, msg = self.rigMultiJnt.AddSelectedJnts()
        if not success:
            QMessageBox().Warning(self, "Warning", str(msg))
            return
        self.jntList.clear()
        self.jntList.addItems(self.rigMultiJnt.chainJnts)

    def OnJntListSelectionChanged(self):
        mc.select(cl=True)
        for item in self.jntList.selectedItems():
            mc.select(item.text(), add=True)

    def CreateJntSelection(self):
        findJointHint = QLabel("Select the highest hierachial joint in the chain then \ntype a keyword that matches the chain")
        self.jointSelectionLayout.addWidget(findJointHint)

        self.jntList = QListWidget()
        self.jntList.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.jntList.itemSelectionChanged.connect(self.OnJntListSelectionChanged)
        self.jointSelectionLayout.addWidget(self.jntList)


        keyLayout = QHBoxLayout()
        keyNameLabel = QLabel("Joint Keyname:")
        keyLayout.addWidget(keyNameLabel)

        self.chainKeyName = QLineEdit()
        self.chainKeyName.setValidator(QDoubleValidator())
        self.chainKeyName.setText("(spine, neck, etc.)")
        self.chainKeyName.textChanged.connect(self.ChainKeyNameSet)
        keyLayout.addWidget(self.chainKeyName)
        self.jointSelectionLayout.addLayout(keyLayout)

        setSelectedJntsBtn = QPushButton("Auto Find Joints")
        setSelectedJntsBtn.clicked.connect(self.AddJointsBtnClicked)
        self.jointSelectionLayout.addWidget(setSelectedJntsBtn)
        self.jntList.addItems(self.rigMultiJnt.chainJnts)

    def CreateCntrlSettingSection(self): # (Toggle Root Ctrl rig?)
        sizeLabel = QLabel("CtrlSize")
        self.additionalOptionsLayout.addWidget(sizeLabel)

        self.ctrlSize.setValidator(QDoubleValidator())
        self.ctrlSize.setText("15")
        self.ctrlSize.textChanged.connect(self.CtrlSizeValueSet)
        self.additionalOptionsLayout.addWidget(self.ctrlSize)

        self.ctrlColorPicker = ColorPicker()
        self.ctrlColorPicker.colorChanged.connect(self.CtrlColorPickerColorChanged)
        self.additionalOptionsLayout.addWidget(self.ctrlColorPicker)
        pass


multiJntWidget = MultiJntWidget()
multiJntWidget.show()
