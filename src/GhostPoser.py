import maya.cmds as mc
from PySide2.QtCore import Signal, Qt
from PySide2.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget, QAbstractItemView, QColorDialog, QSlider
from PySide2.QtGui import QColor, QPainter, QBrush


def GetCurrentFrame():
    return int(mc.currentTime(q=True))

class Ghost():
    def __init__(self):
        self.srcMeshs = set()
        self.InitGhostGrpIfNotExist()
        self.InitSrcMeshFromGhostGrp()
        self.ghostColor = [0, 0, 0]
        self.baseTransparency = 0.0
        self.transparencyRange = 60.0
        self.InitPreviousSettings()
        self.timeJob = mc.scriptJob(e=["timeChanged", self.CurrentTimeChanged])

    def CurrentTimeChanged(self):
        self.UpdateGhostTransparency()

    def UpdateTransparencyRange(self, newRange):
        print(f"New Transparent Range is : {newRange}")
        self.transparencyRange = newRange
        mc.setAttr(self.GetGhostGrpName() + "." + self.GetTransRangeAttr(), self.transparencyRange, self.transparencyRange, self.transparencyRange, type = "double3")
        self.UpdateGhostTransparency()

    def UpdateBaseTransparency(self, newTransparency):
        print(f"New Transparent Base is : {newTransparency}")
        self.baseTransparency = newTransparency
        mc.setAttr(self.GetGhostGrpName() + "." + self.GetBaseTransAttr(), self.baseTransparency, self.baseTransparency, self.baseTransparency, type = "double3")
        self.UpdateGhostTransparency()

    def UpdateSingleGhostTransparency(self, ghost):
        ghostFrame = mc.getAttr(ghost + "." + self.GetFrameAttr())
        currentFrame = GetCurrentFrame()
        distance = abs(currentFrame - ghostFrame)

        ghostMat = self.GetShaderNameForGhost(ghost)

        if distance > self.transparencyRange or self.transparencyRange == 0:
            mc.setAttr(ghostMat + ".transparency", 1, 1, 1, type = "double3")
            return

        normalizeDist = distance/self.transparencyRange
        transAmt = normalizeDist - (self.baseTransparency/2)
        #print(f"Total Transparency is : {transAmt}")
        mc.setAttr(ghostMat + ".transparency", transAmt, transAmt, transAmt, type = "double3")

    def UpdateGhostTransparency(self): #<-- in class (I split into 2 functions)
        if not mc.objExists(self.GetGhostGrpName()):
            return
        ghosts = mc.listRelatives(self.GetGhostGrpName(), c=True)
        if not ghosts:
            return
        for ghost in ghosts:
            self.UpdateSingleGhostTransparency(ghost)
            #"""ghostFrame = mc.getAttr(ghost + "." + self.GetFrameAttr())
            #currentFrame = GetCurrentFrame()
            #distance = abs(currentFrame - ghostFrame)

            #ghostMat = self.GetShaderNameForGhost(ghost)

            #if distance > self.transparencyRange:
            #    mc.setAttr(ghostMat + ".transparency", 1, 1, 1, type = "double3")
            #    continue

            #if self.transparencyRange == 0:
            #    mc.setAttr(ghostMat + ".transparency", 0, 0, 0, type = "double3")
            #    continue

            #normalizeDist = distance/(self.transparencyRange + self.baseTransparency)
            #mc.setAttr(ghostMat + ".transparency", normalizeDist, normalizeDist, normalizeDist, type = "double3")"""

    def UpdateGhostColors(self, r, g, b):
        self.ghostColor[0] = r
        self.ghostColor[1] = g
        self.ghostColor[2] = b
        ghosts = mc.listRelatives(self.GetGhostGrpName(), c=True)
        mc.setAttr(self.GetGhostGrpName() + "." + self.GetGhostColorAttr(), r, g, b, type = "double3")
        currentColor = mc.getAttr(self.GetGhostGrpName() + "." + self.GetGhostColorAttr())
        print(f"Ghost Color is :----{currentColor}")
        for ghost in ghosts:
            self.SetGhostColor(ghost, r, g, b)

    def SetGhostColor(self, ghost, r, g, b):
        ghostMat = self.GetShaderNameForGhost(ghost)
        mc.setAttr(ghostMat + ".color", r, g, b, type = "double3")

    def DeleteGhost(self, ghostName):
        ghostSg = self.GetShaderEngineForGhost(ghostName)
        if mc.objExists(ghostSg):
            mc.delete(ghostSg)

        ghostMat = self.GetShaderNameForGhost(ghostName)
        if mc.objExists(ghostMat):
            mc.delete(ghostMat)

        if mc.objExists(ghostName):
            mc.delete(ghostName)

    def DeleteCurrentGhost(self):
        for srcMesh in self.srcMeshs:
            currentGhostName = srcMesh + self.GetGhostNameSuffix() + str(GetCurrentFrame())
            self.DeleteGhost(currentGhostName)

    def DeleteAllGhosts(self):
        ghosts = mc.listRelatives(self.GetGhostGrpName(), c=True)
        if not ghosts:
            return
        for ghost in ghosts:
            self.DeleteGhost(ghost)

    def InitPreviousSettings(self): #<-- throwing error
        ghosts = mc.listRelatives(self.GetGhostGrpName(), c=True)
        if not ghosts:
            return
        self.baseTransparency = mc.getAttr(self.GetGhostGrpName() + "." + self.GetBaseTransAttr())[0][0]
        self.transparencyRange = mc.getAttr(self.GetGhostGrpName() + "." + self.GetTransRangeAttr())[0][0]
        currentColor = mc.getAttr(self.GetGhostGrpName() + "." + self.GetGhostColorAttr())
        print(f"saved base val : {self.baseTransparency}")
        print(f"saved range val : {self.transparencyRange}")
        print(f"saved color val : {currentColor}")
        self.ghostColor[0] = currentColor[0][0]
        self.ghostColor[1] = currentColor[0][1]
        self.ghostColor[2] = currentColor[0][2]

    def InitSrcMeshFromGhostGrp(self):
        srcMeshAttr = mc.getAttr(self.GetGhostGrpName() + "." + self.GetSrcMeshAttr())
        if not srcMeshAttr:
            return
        
        meshes = srcMeshAttr.split(",")
        self.srcMeshs = set(meshes)

    def InitGhostGrpIfNotExist(self):
        if not mc.objExists(self.GetGhostGrpName()):
            mc.createNode("transform", n = self.GetGhostGrpName())
            mc.addAttr(self.GetGhostGrpName(), ln = self.GetSrcMeshAttr(), dt = "string")
            mc.addAttr(self.GetGhostGrpName(), ln = self.GetBaseTransAttr(), dt = "double3")
            mc.addAttr(self.GetGhostGrpName(), ln = self.GetTransRangeAttr(), dt = "double3")
            mc.addAttr(self.GetGhostGrpName(), ln = self.GetGhostColorAttr(), dt = "double3")
            return

    def GetBaseTransAttr(self):
        return "baseTrans"
    
    def GetTransRangeAttr(self):
        return "transRange"

    def GetGhostColorAttr(self):
        return "ghostColor"
    
    def GetSrcMeshAttr(self):
        return "src"

    def GetGhostGrpName(self):
        return "Ghost_Grp"
    
    def GoToNextGhost(self):
        currentFrame = GetCurrentFrame()
        frames = self.GetGhostFramesSorted()
        nextFrame = frames[0]
        for frame in frames:
            if frame > currentFrame:
                nextFrame = frame
                break

        mc.currentTime(nextFrame, e=True)  

    def GoToPrevGhost(self):
        currentFrame = GetCurrentFrame()
        frames = self.GetGhostFramesSorted()
        prevFrame = frames[-1]
        frames.reverse()
        for frame in frames:
            if frame < currentFrame:
                prevFrame = frame
                break

        mc.currentTime(prevFrame, e=True)   

    def GetGhostFramesSorted(self):
        ghosts = mc.listRelatives(self.GetGhostGrpName(), c=True)
        frames = set()
        for ghost in ghosts:
            frame = mc.getAttr(ghost + "." + self.GetFrameAttr())
            frames.add(frame)

        frames = list(frames)
        frames.sort()
        return frames

    def GetGhostNameSuffix(self):
        return "_ghost_"

    def AddGhost(self):
        for srcMesh in self.srcMeshs:
            ghostName = srcMesh+ self.GetGhostNameSuffix() + str(GetCurrentFrame())
            if mc.objExists(ghostName):
                mc.delete(ghostName)
            mc.duplicate(srcMesh, n=ghostName)
            mc.addAttr(ghostName, ln=self.GetFrameAttr(), dv=GetCurrentFrame())
            
            mc.parent(ghostName, self.GetGhostGrpName())
            self.CreateMaterialForGhost(ghostName)

            self.SetGhostColor(ghostName, self.ghostColor[0], self.ghostColor[1],  self.ghostColor[2])
            self.UpdateSingleGhostTransparency(ghostName)

    def GetFrameAttr(self):
        return "frame"

    def InitSrcMeshesWithSel(self):
        selection = mc.ls(sl=True)
        self.srcMeshs.clear()
        for sel in selection:
            shapes = mc.listRelatives(sel, s=True)
            for s in shapes:
                if mc.objectType(s) == "mesh":
                    self.srcMeshs.add(sel)

        mc.setAttr(self.GetGhostGrpName() + "." + self.GetSrcMeshAttr(), ",".join(self.srcMeshs), typ = "string")
    
    def CreateMaterialForGhost(self, ghost):
        matName = self.GetShaderNameForGhost(ghost)
        if not mc.objExists(matName):
            mc.shadingNode("lambert", asShader = True, name = matName)

        setName = self.GetShaderEngineForGhost(ghost)
        if not mc.objExists(setName):
            mc.sets(name = setName, renderable = True, empty = True)

        mc.connectAttr(matName + ".outColor", setName + ".surfaceShader", force = True)
        mc.sets(ghost, edit=True, forceElement = setName)


    def GetShaderEngineForGhost(self, ghost):
        return ghost + "_sg"
        
    def GetShaderNameForGhost(self, ghost):
        return ghost + "_mat"


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

class GhostWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ghoster")
        self.ghost = Ghost()
        self.masterLayout = QVBoxLayout()
        self.setLayout(self.masterLayout)
        self.CreateMeshSelection()
        self.CreateMatCtrlSection()
        self.CreateCtrlSection()

    def RefreshPreviousUIVisuals(self, colorPicker:ColorPicker, transSlider:QSlider, rangeSlider:QSlider):
        if not mc.objExists(self.ghost.GetGhostGrpName()):
            print(f"Group not found!")
            return;
        
        grpColor =QColor(self.ghost.ghostColor[0]*255, self.ghost.ghostColor[1]*255, self.ghost.ghostColor[2]*255)
        colorPicker.color = grpColor
        transSlider.setValue(self.ghost.baseTransparency * 100)
        rangeSlider.setValue(self.ghost.transparencyRange)
            



    def CreateMatCtrlSection(self):
        layout = QHBoxLayout()
        self.masterLayout.addLayout(layout)

        self.ghostColorPicker = ColorPicker()
        self.ghostColorPicker.colorChanged.connect(self.GhostColorPickerColorChanged)
        layout.addWidget(self.ghostColorPicker)

        transSlider = QSlider()
        transSlider.setOrientation(Qt.Horizontal)
        transSlider.setMinimum(0)
        transSlider.setMaximum(100)
        transSlider.valueChanged.connect(self.BaseTransparencyChanged)
        layout.addWidget(transSlider)

        visCtrlLayout = QHBoxLayout()
        self.masterLayout.addLayout(visCtrlLayout)

        rangeLabel = QLabel("Transparency Range")
        visCtrlLayout.addWidget(rangeLabel)

        rangeSlider = QSlider()
        rangeSlider.setOrientation(Qt.Horizontal)
        rangeSlider.setMinimum(0)
        rangeSlider.setMaximum(60)
        rangeSlider.valueChanged.connect(self.TransparencyRangeChanged)
        visCtrlLayout.addWidget(rangeSlider)
        self.RefreshPreviousUIVisuals(self.ghostColorPicker, transSlider, rangeSlider)

    def BaseTransparencyChanged(self, value):
        self.ghost.UpdateBaseTransparency(value/100)

    def TransparencyRangeChanged(self, value):
        self.ghost.UpdateTransparencyRange(value)

    def GhostColorPickerColorChanged(self, newColor:QColor):
        print(f"New color is now: {newColor.red()}, {newColor.green()}, {newColor.blue()}")
        self.ghost.UpdateGhostColors(newColor.redF(), newColor.greenF(), newColor.blueF())


    def CreateCtrlSection(self):
        layout = QHBoxLayout()
        self.masterLayout.addLayout(layout)

        addGhostBtn = QPushButton("Add")
        addGhostBtn.clicked.connect(self.ghost.AddGhost)
        layout.addWidget(addGhostBtn)

        prevBtn = QPushButton("<<<")
        prevBtn.clicked.connect(self.ghost.GoToPrevGhost)
        layout.addWidget(prevBtn)

        nextBtn = QPushButton(">>>")
        nextBtn.clicked.connect(self.ghost.GoToNextGhost)
        layout.addWidget(nextBtn)
        
        delFrameBtn = QPushButton("Delete")
        delFrameBtn.clicked.connect(self.ghost.DeleteCurrentGhost)
        layout.addWidget(delFrameBtn)
        
        delAllBtn = QPushButton("Delete All")
        delAllBtn.clicked.connect(self.ghost.DeleteAllGhosts)
        layout.addWidget(delAllBtn)

    def CreateMeshSelection(self):
        self.srcMeshList = QListWidget()
        self.srcMeshList.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.srcMeshList.itemSelectionChanged.connect(self.SrcMeshListSelectionChanged)
        self.masterLayout.addWidget(self.srcMeshList)
        setSrcMeshBtn = QPushButton("Set Selected as Source")
        setSrcMeshBtn.clicked.connect(self.SetSrcMeshBtnClicked)
        self.masterLayout.addWidget(setSrcMeshBtn)
        self.srcMeshList.addItems(self.ghost.srcMeshs)

    def SetSrcMeshBtnClicked(self):
        self.ghost.InitSrcMeshesWithSel()
        self.srcMeshList.clear()
        self.srcMeshList.addItems(self.ghost.srcMeshs)

    def SrcMeshListSelectionChanged(self):
        mc.select(cl=True)
        for item in self.srcMeshList.selectedItems():
            mc.select(item.text(), add=True)



ghostWidget = GhostWidget()
ghostWidget.show()
