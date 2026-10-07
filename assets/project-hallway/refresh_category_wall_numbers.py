"""Add category wall numbers without rebuilding the completed animated scene."""
import importlib.util
from pathlib import Path
import bpy

OUT=Path(__file__).resolve().parent
scene=bpy.data.scenes['PROJECT HALLWAY / Monochrome Exhibition']
bpy.context.window.scene=scene;scene.frame_set(1);scene.view_layers[0].update()
preserved=[(obj,obj.matrix_world.copy(),obj.hide_render,obj.data,obj.animation_data.action if obj.animation_data else None,obj.data.body if obj.type=='FONT' else None) for obj in scene.objects if not obj.get('hallway_category_wall_number')]
spec=importlib.util.spec_from_file_location('wall_numbers',OUT/'category_wall_numbers.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.configure_category_wall_numbers(scene)
for obj,matrix,hidden,data,action,body in preserved:
    assert obj.matrix_world==matrix and obj.hide_render==hidden and obj.data==data
    assert (obj.animation_data.action if obj.animation_data else None)==action
    if body is not None:
        assert obj.data.body==body
bpy.context.preferences.filepaths.save_version=1
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'project-hallway.blend'),compress=True)
print('CATEGORY WALL NUMBERS: luminous 02 and 03 with light accents; completed scene and performances preserved')
