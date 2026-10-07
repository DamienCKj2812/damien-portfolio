"""Update only office monitor content; preserve the room and native animation."""
import json
from pathlib import Path
import sys

import bpy

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from malaysia_screen import apply_malaysia_screen, OLD_CONTENT, PREFIX

MASTER = ROOT / 'about-office.blend'
assert Path(bpy.data.filepath).resolve() == MASTER
scene = bpy.data.scenes['ABOUT / Skyline Office']
bpy.context.window.scene = scene
snapshots = {}
for frame in (1, 180, 360, 540, 720):
    scene.frame_set(frame)
    scene.view_layers[0].update()
    snapshots[frame] = {obj.name: obj.matrix_world.copy() for obj in scene.objects if not obj.name.startswith(PREFIX)}
actions = {obj.name: obj.animation_data.action if obj.animation_data else None for obj in scene.objects if not obj.name.startswith(PREFIX)}
scene.frame_set(1)
report = apply_malaysia_screen(scene)
for frame, snapshot in snapshots.items():
    scene.frame_set(frame)
    scene.view_layers[0].update()
    assert all(scene.objects[name].matrix_world == matrix for name, matrix in snapshot.items()), f'Office pose changed at {frame}'
for name, action in actions.items():
    obj = scene.objects[name]
    assert (obj.animation_data.action if obj.animation_data else None) == action
for suffix in OLD_CONTENT:
    obj = scene.objects.get('Office • ' + suffix)
    assert obj is None or obj.hide_render
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 1
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER), compress=True)
(ROOT / 'malaysia-screen.json').write_text(json.dumps(report, indent=2) + '\n')
manifest_file = ROOT / 'office-manifest.json'
manifest = json.loads(manifest_file.read_text())
manifest['screen_content'] = 'Monochrome Malaysia map / Natural Earth public-domain geography'
manifest['malaysia_map'] = report
manifest['objects'] = len(scene.objects)
manifest_file.write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps(report))
