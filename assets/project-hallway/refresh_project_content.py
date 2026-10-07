"""Refresh one project's printed title/metadata without rebuilding the hallway.

blender --background assets/project-hallway/project-hallway.blend --python-exit-code 1 --python assets/project-hallway/refresh_project_content.py -- --id Aria
"""
import argparse
import json
import sys
from pathlib import Path

import bpy

parser = argparse.ArgumentParser()
parser.add_argument('--id', required=True)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
OUT = Path(__file__).resolve().parent
scene = bpy.data.scenes['PROJECT HALLWAY / Monochrome Exhibition']
bpy.context.window.scene = scene
scene.frame_set(1)
project = next(item for item in json.loads((OUT / 'projects.json').read_text())['projects'] if item['id'] == args.id)
root = next(obj for obj in scene.objects if obj.get('project_id') == args.id and obj.get('hallway_display'))
copy = {label: next(obj for obj in root.children if obj.name.endswith(' / ' + label)) for label in ['title', 'summary', 'stack']}
preserved = [(obj, obj.matrix_world.copy(), obj.hide_render, obj.data,
              obj.animation_data.action if obj.animation_data else None,
              obj.data.body if obj.type == 'FONT' and obj not in copy.values() else None)
             for obj in scene.objects]
for label, size in [('title', .165), ('summary', .106), ('stack', .10)]:
    obj = copy[label]
    obj.data.body = '\n'.join(project['tags']) if label == 'stack' else project[label]
    obj.data.size = size
    bpy.context.view_layer.update()
    if obj.dimensions.x > 1.68:
        obj.data.size *= 1.68 / obj.dimensions.x
root['project_metadata'] = json.dumps(project)
bpy.context.view_layer.update()
assert all(obj.dimensions.x <= 1.68001 for obj in copy.values())
for obj, matrix, hidden, data, action, body in preserved:
    assert obj.matrix_world == matrix and obj.hide_render == hidden and obj.data == data, f'Unexpected room change: {obj.name}'
    assert (obj.animation_data.action if obj.animation_data else None) == action, f'Animation changed: {obj.name}'
    if body is not None:
        assert obj.data.body == body, f'Unrelated text changed: {obj.name}'
bpy.context.preferences.filepaths.save_version = 1
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'project-hallway.blend'))
print(f'PASS {project["title"]}: fitted title and metadata; {len(preserved)} room objects/transforms/actions preserved')
