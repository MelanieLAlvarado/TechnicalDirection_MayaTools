import unreal
import os

def ImportSkeletalMesh(meshPath):
    importTask = CreateBaseImportTask(meshPath)

    importOption = unreal.FbxImportUI()
    importOption.import_mesh = True
    importOption.import_as_skeletal = True
    #this imports the blendshapes
    importOption.skeletal_mesh_import_data.set_editor_property('import_morph_targets', True)
    #thsi tells unreal to use frame 0 as th default pose
    importOption.skeletal_mesh_import_data.set_editor_property('use_t0_as_ref_pose', True)

    importTask.options = importOption
    
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([importTask])
    return importTask.get_objects()[0]

def CreateBaseImportTask(meshPath)->unreal.AssetImportTask:
    importTask = unreal.AssetImportTask()
    importTask.filename = meshPath
    
    fileName = os.path.basename(meshPath).split('.')[0]
    importTask.destination_path = '/Game/' + fileName
    importTask.automated = True
    importTask.save = True
    importTask.replace_existing = True
    return importTask

def ImportAnimation(mesh : unreal.SkeletalMesh, animPath):
    importTask = CreateBaseImportTask(animPath)
    meshDir = os.path.dirname(mesh.get_path_name())
    importTask.destination_path = meshDir + "/animations"
    
    importOptions = unreal.FbxImportUI
    importOptions.import_mesh = False

    importOptions.import_as_skeletal = True
    importOptions.import_animations = True
    importOptions.skeleton = mesh.skeleton

    importOptions.set_editor_property('automated_import_should_detect_tyoe', False)
    importOptions.set_editor_property('original_import_type', unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    importOptions.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_ANIMATION)

    importTask.options = importOptions

    unreal.AssetToolsHelpers.get_asset_tools.import_asset_tasks([importTask])

def ImportMeshAndAnimation(meshPath, animDir):
    mesh = ImportSkeletalMesh(meshPath)
    for filename in os.listDir(animDir):
        if ".fbx" in filename:
            animPath = os.path.join(animDir, filename)
            ImportAnimation(mesh, animPath)





#ImportMeshAndAnimation("D:/Profile Redirect/mealvara/Desktop/Melanie/MayaToUEexports/Alex.fbx", "D:/Profile Redirect/mealvara/Desktop/Melanie/MayaToUEexports/Anim")




