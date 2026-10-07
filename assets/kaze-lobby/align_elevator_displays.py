"""Align landing status typography in the master without rebuilding its rig."""
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parent
scene = bpy.data.scenes['KAZE / Monochrome Atrium']
original_frame = scene.frame_current
names = [f'Lobby • Elevator {lift} / floor display' for lift in ['L1','L2','R1','R2']]
assert all(name in scene.objects for name in names)
channels = [scene.objects['Lobby • Navigation / walkthrough camera'],
            scene.objects['Lobby • Elevator R1 / left door leaf'],
            scene.objects['Lobby • Elevator R1 / right door leaf']]

def samples():
    result = []
    for frame in [1, 320, 510, 690, 840, 900, 990, 1020]:
        scene.frame_set(frame);scene.view_layers[0].update()
        result.extend(tuple(value for row in obj.matrix_world for value in row) for obj in channels)
    return result

before = samples()
for name in names:
    obj = scene.objects[name]
    obj.location.z = 9.40
    obj['landing_status_baseline'] = 9.40
assert samples() == before, 'Camera/door motion changed.'
scene.frame_set(original_frame);scene.view_layers[0].update()
heights = [scene.objects[name].matrix_world.translation.z for name in names]
assert max(heights)-min(heights) < .00001, f'Status baselines disagree: {heights}'
bpy.context.preferences.filepaths.save_version = 1
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'kaze-lobby-walkthrough.blend'))
print({'landing_status_heights': dict(zip(names,heights)), 'motion_preserved': True})
