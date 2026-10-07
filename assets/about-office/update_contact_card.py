"""Update only printed contact copy in the existing authored office master.

blender --background assets/about-office/about-office.blend --python-exit-code 1 --python assets/about-office/update_contact_card.py
"""
import ast
import json
import math
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from contact_card_content import contact_card_lines, read_contact_details

scene = bpy.data.scenes['ABOUT / Skyline Office']
bpy.context.window.scene = scene
scene.frame_set(1)
root = scene.objects['Office • Name card / interactive assembly']
details = read_contact_details()
lines = contact_card_lines(details)
names = {'Office • Name card / ' + label for label, *_ in lines}
retained = {obj.name: (obj.matrix_world.copy(), obj.hide_render, obj.animation_data.action if obj.animation_data else None)
            for obj in scene.objects if obj.name not in names}
collections = {'10': next(col for col in scene.collection.children if col.name.startswith('Office • 10'))}
type_mat = bpy.data.materials['Office • Silver lettering']
source = ast.parse((ROOT / 'build_office.py').read_text())
helpers = ast.Module(body=[node for node in source.body if isinstance(node, ast.FunctionDef) and node.name in {'link', 'text'}], type_ignores=[])
exec(compile(helpers, str(ROOT / 'build_office.py'), 'exec'), globals())

for label, body, y, size in lines:
    obj = scene.objects.get('Office • Name card / ' + label)
    if obj is None:
        obj = text('Name card / ' + label, body, (0, y, .00060), size, '10')
        obj.parent = root
    obj.data.body = body
    obj.data.size = size
    obj.location = (0, y, .00060)
    obj.rotation_euler = (0, 0, 0)

root['contact_email'] = details['email']
root['contact_phone'] = details['phone']
root['contact_whatsapp'] = details['whatsapp']
bpy.context.view_layer.update()
for name, (matrix, hidden, action) in retained.items():
    obj = scene.objects[name]
    assert obj.matrix_world == matrix and obj.hide_render == hidden, f'Unexpected change to {name}'
    assert (obj.animation_data.action if obj.animation_data else None) == action, f'Animation changed: {name}'
for name in names:
    obj = scene.objects[name]
    assert obj.parent == root
    assert all(abs(corner[0] + obj.location.x) < .0435 and abs(corner[1] + obj.location.y) < .0265
               for corner in obj.bound_box), f'Printed text exceeds card bounds: {name}'

manifest_path = ROOT / 'office-manifest.json'
manifest = json.loads(manifest_path.read_text())
manifest['contact_card'].update(email=details['email'], phone=details['phone'], whatsapp=details['whatsapp'])
manifest['objects'] = len(scene.objects)
manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
bpy.context.preferences.filepaths.save_version = 1
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'about-office.blend'))
print(f'PASS contact card: seven printed lines fit; {len(retained)} surrounding objects/cameras/actions preserved')
