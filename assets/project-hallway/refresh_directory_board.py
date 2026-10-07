"""Update only the entrance directory and its projector in the authored master."""
import importlib.util
from pathlib import Path
import bpy

OUT=Path(__file__).resolve().parent
scene=bpy.data.scenes['PROJECT HALLWAY / Monochrome Exhibition']
bpy.context.window.scene=scene
scene.frame_set(1);scene.view_layers[0].update()
root=scene.objects['Entry / projects directory']
changed={root,*root.children_recursive}
preserved=[(obj,obj.matrix_world.copy(),obj.hide_render,obj.data,
            obj.animation_data.action if obj.animation_data else None,
            obj.data.body if obj.type=='FONT' else None) for obj in scene.objects if obj not in changed]
spec=importlib.util.spec_from_file_location('hallway_directory',OUT/'directory_board.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.configure_directory_board(scene)
for obj,matrix,hidden,data,action,body in preserved:
    assert obj.matrix_world==matrix and obj.hide_render==hidden and obj.data==data, f'Unrelated room change: {obj.name}'
    assert (obj.animation_data.action if obj.animation_data else None)==action, f'Animation changed: {obj.name}'
    if body is not None:
        assert obj.data.body==body
assert len([obj for obj in scene.objects if obj.get('project_id')])==16
assert len([obj for obj in scene.objects if obj.get('source_person_id')])==15
bpy.context.preferences.filepaths.save_version=1
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'project-hallway.blend'),compress=True)
print(f'ENTRANCE DIRECTORY UPDATED: raised card and downward top projector; {len(preserved)} unrelated objects and animations preserved')
