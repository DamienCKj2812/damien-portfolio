"""Focused master-saving update; preserves architecture, navigation and doors."""
import sys
from pathlib import Path
import bpy

sys.path.insert(0,str(Path(__file__).resolve().parent))
from npc_motion import install_npc_motion

scene = bpy.data.scenes['KAZE / Monochrome Atrium']
protected = [obj for obj in scene.objects if obj.animation_data and obj.animation_data.action
             and obj.get('pose_origin') is None and not obj.get('npc_owner')]


def motion_samples():
    samples = []
    for frame in [1, 320, 510, 690, 840, 900, 990, 1020]:
        scene.frame_set(frame)
        scene.view_layers[0].update()
        samples.extend(tuple(value for row in obj.matrix_world for value in row) for obj in protected)
    return samples


before = motion_samples()
bases = {obj.name: tuple(tuple(point.co) for point in obj.data.shape_keys.key_blocks['Basis'].data)
         for obj in scene.objects if obj.get('autonomous_npc') and obj.data.shape_keys}
count = install_npc_motion(scene)
for name, basis in bases.items():
    assert tuple(tuple(point.co) for point in scene.objects[name].data.shape_keys.key_blocks['Basis'].data) == basis, f'Authored pose changed: {name}'
assert motion_samples() == before, 'Navigation or door animation changed.'
scene.frame_set(1)
scene.view_layers[0].update()
bpy.context.preferences.filepaths.save_version = 1
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print({'animated_npcs':count,'loop_frames':1019,'navigation_and_doors_preserved':True})
