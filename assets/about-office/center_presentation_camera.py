"""Explicit authoring update: center the existing presentation camera on the monitor.

Run on about-office.blend. Other objects/cameras stay intact, and Blender keeps
one previous-save backup. Browser free-look is provided by the room runtime.
"""
import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parent
scene = bpy.context.scene
scene.frame_set(1)
scene.view_layers[0].update()
camera = scene.objects['Office • About office presentation camera']
screen = scene.objects['Office • About content screen / web texture target']
assert camera.parent is None and not camera.constraints and not camera.animation_data


def signature(obj):
    return (tuple(value for row in obj.matrix_world for value in row),
            obj.data.as_pointer() if obj.data else None,
            len(obj.data.vertices) if obj.type == 'MESH' else None)


before = {obj.name: signature(obj) for obj in scene.objects if obj != camera}
target = screen.matrix_world.translation.copy()
previous = camera.matrix_world.copy()
camera.location.x = target.x
camera.rotation_mode = 'QUATERNION'
camera.rotation_quaternion = (target - camera.location).to_track_quat('-Z', 'Y')
scene.camera = camera
scene['Presentation view'] = 'Computer-centered presentation; browser drag/free-look'
scene.view_layers[0].update()
assert before == {obj.name: signature(obj) for obj in scene.objects if obj != camera}
direction = camera.matrix_world.to_quaternion() @ Vector((0, 0, -1))
assert direction.normalized().dot((target - camera.matrix_world.translation).normalized()) > .999999
assert abs(camera.matrix_world.translation.x - target.x) < 1e-6

changed = max(abs(camera.matrix_world[row][col] - previous[row][col]) for row in range(4) for col in range(4)) > 1e-6
if changed:
    bpy.context.preferences.filepaths.save_version = 1
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'about-office.blend'))

manifest_path = ROOT / 'office-manifest.json'
manifest = json.loads(manifest_path.read_text())
manifest['presentation_target'] = list(target)
manifest['presentation_view'] = scene['Presentation view']
manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps({'camera_position': list(camera.location), 'target': list(target),
                  'camera_updated': changed, 'other_objects_and_cameras_unchanged': True}))
