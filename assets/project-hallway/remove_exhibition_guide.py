"""Remove only the Selected Work entrance board and its complete projector."""
import json
from pathlib import Path
import bpy

OUT=Path(__file__).resolve().parent
scene=bpy.data.scenes['PROJECT HALLWAY / Monochrome Exhibition']
bpy.context.window.scene=scene
scene.frame_set(1);scene.view_layers[0].update()
root=scene.objects.get('Entry / exhibition guide')
assert root and root.get('hallway_display'), 'Selected Work board not found'
removed={root,*root.children_recursive}
assert any(obj.get('holographic_projector') for obj in removed)
preserved=[(obj,obj.matrix_world.copy(),obj.hide_render,obj.data,
            obj.animation_data.action if obj.animation_data else None,
            obj.data.body if obj.type=='FONT' else None) for obj in scene.objects if obj not in removed]
names=sorted(obj.name for obj in removed)
for obj in list(removed):
    bpy.data.objects.remove(obj,do_unlink=True)
scene.view_layers[0].update()
for obj,matrix,hidden,data,action,body in preserved:
    assert obj.matrix_world==matrix and obj.hide_render==hidden and obj.data==data, f'Unrelated room change: {obj.name}'
    assert (obj.animation_data.action if obj.animation_data else None)==action, f'Animation changed: {obj.name}'
    if body is not None:
        assert obj.data.body==body, f'Unrelated text changed: {obj.name}'
assert scene.objects.get('Entry / projects directory')
assert len([obj for obj in scene.objects if obj.get('source_person_id')])==15
assert len([obj for obj in scene.objects if obj.get('project_id')])==16
layout=json.loads((OUT/'hallway-layout.json').read_text())
layout['projectorCount']=len([obj for obj in scene.objects if obj.get('holographic_projector')])
bpy.context.preferences.filepaths.save_version=1
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'project-hallway.blend'),compress=True)
(OUT/'hallway-layout.json').write_text(json.dumps(layout,indent=2)+'\n')
print(f'SELECTED WORK REMOVED: {len(names)} board/projector objects; {len(preserved)} unrelated objects and performances preserved')
