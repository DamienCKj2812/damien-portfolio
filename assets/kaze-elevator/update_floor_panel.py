"""Apply the requested panel edit to the elevator master, preserving its motion."""
import json
from pathlib import Path
import bpy
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from floor_panel_design import apply_panel_design
scene = bpy.context.scene
assert scene.objects.get('Elevator / Full journey camera'), 'Open the elevator journey master.'
frame = scene.frame_current
scene.frame_set(1)
levels = json.loads((ROOT / 'assets/kaze-elevator/elevator-levels.json').read_text())['levels']
rooms = json.loads((ROOT / 'assets/journey/room-destinations.json').read_text())
removed = []
for obj in list(scene.objects):
    if obj.name.startswith(('Elevator / Door operation ring', 'Elevator / Door operation icon')) or obj.get('level_id') == 'contact' or any(c.name in ['Elevator / Dialog / contact', 'Elevator / Destination / contact'] for c in obj.users_collection):
        removed.append(obj.name)
        bpy.data.objects.remove(obj, do_unlink=True)
for name in ['Elevator / Dialog / contact', 'Elevator / Destination / contact']:
    collection = bpy.data.collections.get(name)
    if collection: bpy.data.collections.remove(collection)
channels = [scene.objects['Elevator / Full journey camera'],scene.objects['Elevator / Left sliding door'],scene.objects['Elevator / Right sliding door']]
def motion_samples():
    result = []
    for sample in [1,62,180,181,220,296,300,350,414,510]:
        scene.frame_set(sample);bpy.context.view_layer.update()
        result.extend(tuple(value for row in obj.matrix_world for value in row) for obj in channels)
    return result
before = motion_samples()
scene.frame_set(1)
apply_panel_design(scene, levels)
for level in levels:
    scene.objects[level['button']]['destination_room'] = rooms.get(level['id'], {}).get('source', '')
assert motion_samples() == before, 'Panel edit changed camera or door motion.'
scene['floor_panel_order'] = 'Level 1 at bottom; Level 4 at top'
text = bpy.data.texts.get('KAZE_Elevator_Controls.py')
if text:
    text.clear();text.write((ROOT/'assets/kaze-elevator/elevator_controls.py').read_text())
scene.frame_set(frame)
bpy.context.view_layer.update()
assert len(levels) == 4 and not scene.objects.get('Elevator / Level button contact')
assert all(scene.objects[levels[i]['button']].location.z < scene.objects[levels[i+1]['button']].location.z for i in range(len(levels)-1))
bpy.context.preferences.filepaths.save_version = 1
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'assets/kaze-elevator/kaze-elevator-journey.blend'))
print(json.dumps({'removed': removed, 'floor_button_heights': {level['id']: scene.objects[level['button']].location.z for level in levels}, 'camera_and_door_motion_preserved': True}))
