"""Widen one selected video display, preserving the completed hallway/NPCs."""
import argparse
import json
import sys
from pathlib import Path

import bpy

OUT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--id', default='agent-property')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
scene = bpy.data.scenes['PROJECT HALLWAY / Monochrome Exhibition']
bpy.context.window.scene = scene
scene.frame_set(1)
root = next(obj for obj in scene.objects if obj.get('project_id') == args.id and obj.get('hallway_display'))
project = next(item for item in json.loads((OUT / 'projects.json').read_text())['projects'] if item['id'] == args.id)
board = next(obj for obj in root.children if obj.name.endswith(' / black display'))
target = project['video']
old_width = board.dimensions.x
old_height = board.dimensions.z
sx, sz = target['width'] / old_width, target['height'] / old_height
center_z = board.location.z
parts = {root, *root.children_recursive}
preserved = [(obj, obj.matrix_world.copy(), obj.hide_render, obj.animation_data.action if obj.animation_data else None)
             for obj in scene.objects if obj not in parts]
board.scale.x *= sx
board.scale.z *= sz
for obj in root.children_recursive:
    if obj.type == 'FONT' or obj.name.endswith(' / typography rules'):
        obj.hide_render = True
    elif obj.name.endswith(' / holographic corner brackets'):
        for spline in obj.data.splines:
            points = spline.bezier_points if spline.type == 'BEZIER' else spline.points
            for point in points:
                point.co.x *= sx
                point.co.z = center_z + (point.co.z - center_z) * sz
                if spline.type == 'BEZIER':
                    for handle in [point.handle_left, point.handle_right]:
                        handle.x *= sx
                        handle.z = center_z + (handle.z - center_z) * sz
    elif obj.type == 'CURVE' and obj.name.endswith(' / black display / outline'):
        points = [point for spline in obj.data.splines for point in spline.points]
        width = max(point.co.x for point in points) - min(point.co.x for point in points)
        height = max(point.co.z for point in points) - min(point.co.z for point in points)
        for point in points:
            point.co.x *= target['width'] / width
            point.co.z = center_z + (point.co.z - center_z) * target['height'] / height
    elif obj.type == 'CURVE' and 'frustum rays' in obj.name:
        to_board = root.matrix_world.inverted() @ obj.matrix_world
        from_board = to_board.inverted()
        for spline in obj.data.splines:
            for point in spline.points:
                if point.co.z > 1:
                    position = to_board @ point.co.xyz
                    position.x *= sx
                    position.z = center_z + (position.z - center_z) * sz
                    point.co.xyz = from_board @ position
    elif obj.type == 'MESH' and obj.name.endswith(' / subtle projected light field'):
        to_board = root.matrix_world.inverted() @ obj.matrix_world
        from_board = to_board.inverted()
        for vertex in obj.data.vertices:
            if vertex.co.z > 1:
                position = to_board @ vertex.co
                position.x *= sx
                position.z = center_z + (position.z - center_z) * sz
                vertex.co = from_board @ position
root['project_metadata'] = json.dumps(project)
root['video_display'] = True
bpy.context.view_layer.update()
assert abs(board.dimensions.x - target['width']) < 1e-5
assert abs(board.dimensions.z - target['height']) < 1e-5
outline = next(obj for obj in root.children if obj.name.endswith(' / black display / outline'))
assert abs(outline.dimensions.x - target['width']) < .025
assert abs(outline.dimensions.z - target['height']) < .025
assert all(obj.hide_render for obj in root.children_recursive if obj.type == 'FONT'), 'Video board must have no printed project text'
for obj, matrix, hidden, action in preserved:
    assert obj.matrix_world == matrix and obj.hide_render == hidden, f'Unrelated room object changed: {obj.name}'
    assert (obj.animation_data.action if obj.animation_data else None) == action, f'NPC/animation changed: {obj.name}'
bpy.context.preferences.filepaths.save_version = 1
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'project-hallway.blend'))
print(f'PASS {args.id}: 16:9 video board {board.dimensions.x:.2f} × {board.dimensions.z:.4f} m; text hidden; {len(preserved)} surrounding objects/actions preserved')
