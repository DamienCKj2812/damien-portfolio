"""Update the portal title lettering only, preserving the authored hallway."""
import importlib.util
from pathlib import Path
import bpy

OUT=Path(__file__).resolve().parent
scene=bpy.data.scenes['PROJECT HALLWAY / Monochrome Exhibition']
bpy.context.window.scene=scene;scene.frame_set(1);scene.view_layers[0].update()
titles={obj for obj in scene.objects if obj.type=='FONT' and obj.name.startswith('Category / number')}
preserved=[(obj,obj.matrix_world.copy(),obj.hide_render,obj.data,
            obj.animation_data.action if obj.animation_data else None,
            obj.data.body if obj.type=='FONT' and obj not in titles else None) for obj in scene.objects]
spec=importlib.util.spec_from_file_location('hallway_category_titles',OUT/'category_titles.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.refresh_category_titles(scene)
for obj,matrix,hidden,data,action,body in preserved:
    assert obj.matrix_world==matrix and obj.hide_render==hidden and obj.data==data
    assert (obj.animation_data.action if obj.animation_data else None)==action
    if body is not None:
        assert obj.data.body==body
bpy.context.preferences.filepaths.save_version=1
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'project-hallway.blend'),compress=True)
print('PORTAL TITLES UPDATED: 02 Academic Assignment Projects / 03 Personal Projects; all transforms and actions preserved')
