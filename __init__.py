import os
import sys


initFilePath = os.path.abspath(__file__)       #__file__ means this file
pluginDir = os.path.dirname(initFilePath)      #
srcDir = os.path.join(pluginDir, "src")        #
unrealLibDir = os.path.join(pluginDir, "vendor", "Unreal")  #

def AddDirToPath(dir):
    if dir not in sys.path:
        sys.path.append(dir)
        print(f"add {dir} to system path")
    
AddDirToPath(pluginDir)
AddDirToPath(srcDir)
AddDirToPath(unrealLibDir)