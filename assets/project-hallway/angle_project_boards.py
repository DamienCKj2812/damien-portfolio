"""Angle the project assemblies while preserving their locations and the room."""
import sys
from pathlib import Path

import bpy
from mathutils import Vector

OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT))
from board_orientation import orient_project_board, stabilize_projector

scene = bpy.data.scenes['PROJECT HALLWAY / Monochrome Exhibition']
bpy.context.window.scene = scene
scene.frame_set(1)
roots = [obj for obj in scene.objects if obj.get('project_id') and obj.get('hallway_display')]
assert len(roots) == 16
parts = {obj for root in roots for obj in [root, *root.children_recursive]}
retained = [(obj, obj.matrix_world.copy(), obj.hide_render,
             obj.animation_data.action if obj.animation_data else None) for obj in scene.objects if obj not in parts]
positions = {root: root.location.copy() for root in roots}
for root in roots:
    orient_project_board(root)
    stabilize_projector(root)
bpy.context.view_layer.update()
for root in roots:
    assert root.location == positions[root]
    normal = root.matrix_world.to_quaternion() @ Vector((0, -1, 0))
    assert normal.y < -.3 and normal.x * (-1 if root.location.x > 0 else 1) > .9
for obj, matrix, hidden, action in retained:
    assert obj.matrix_world == matrix and obj.hide_render == hidden, f'Unrelated room change: {obj.name}'
    assert (obj.animation_data.action if obj.animation_data else None) == action, f'Animation changed: {obj.name}'
bpy.context.preferences.filepaths.save_version = 1
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'project-hallway.blend'))
print(f'PASS 16 project assemblies angled 20 degrees toward the entrance; {len(retained)} surroundings/cameras/NPC actions preserved')
