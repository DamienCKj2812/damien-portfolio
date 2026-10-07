"""Replace timeline copy/IDs without rebuilding the completed observatory."""
import json
from pathlib import Path
import sys

import bpy

OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT))
from timeline_board_art import apply_board_art
scene = bpy.data.scenes['TIMELINE OBSERVATORY / My Journey So Far']
bpy.context.window.scene = scene
scene.frame_set(1)
content = json.loads((OUT / 'milestones.json').read_text())
roots = sorted((obj for obj in scene.objects if obj.get('milestone_id')), key=lambda obj: obj.name)
assert len(roots) == len(content['milestones']) == 6
preserved = [(obj, obj.matrix_world.copy(), obj.hide_render, obj.animation_data.action if obj.animation_data else None) for obj in scene.objects]
mapping = {}
for root, item in zip(roots, content['milestones']):
    old_id = root['milestone_id']
    old_name = root.name
    new_name = old_name.rsplit(' / ', 1)[0] + ' / ' + item['id']
    mapping[old_id] = item
    for obj in list(scene.objects):
        if obj.name == old_name or obj.name.startswith(old_name + ' / '):
            obj.name = new_name + obj.name[len(old_name):]
    root['milestone_id'] = item['id']
    root['milestone_metadata'] = json.dumps(item)
    for suffix, body, size in [('title', item['cardTitle'], .19), ('caption', item['caption'], .075)]:
        obj = next(obj for obj in root.children if obj.name.endswith(' / ' + suffix))
        obj.data.body = body
        obj.data.size = size
        bpy.context.view_layer.update()
        if obj.dimensions.x > 1.60:
            obj.data.size *= 1.60 / obj.dimensions.x
    bpy.context.view_layer.update()
    apply_board_art(scene, root, item)

stations = json.loads(scene['guided_walk_stations'])
for station in stations:
    item = mapping[station['id']]
    station.update(id=item['id'], title=item['title'], caption=item['caption'])
scene['guided_walk_stations'] = json.dumps(stations)
subtitle = scene.objects.get('Observatory / journey subtitle')
if subtitle:
    subtitle.data.body = content['subtitle']
bpy.context.view_layer.update()
for obj, matrix, hidden, action in preserved:
    assert obj.matrix_world == matrix and (obj.hide_render == hidden or obj.get('timeline_retired_icon') and obj.hide_render), f'Unexpected room change: {obj.name}'
    assert (obj.animation_data.action if obj.animation_data else None) == action, f'Animation changed: {obj.name}'
layout_path = OUT / 'observatory-layout.json'
layout = json.loads(layout_path.read_text())
def update_ids(value):
    if isinstance(value, dict):
        if value.get('id') in mapping:
            item = mapping[value['id']]
            value['id'] = item['id']
            if 'title' in value:
                value['title'] = item['title']
            if 'caption' in value:
                value['caption'] = item['caption']
        for child in value.values():
            update_ids(child)
    elif isinstance(value, list):
        for child in value:
            update_ids(child)
update_ids(layout)
layout_path.write_text(json.dumps(layout, indent=2) + '\n')
bpy.context.preferences.filepaths.save_version = 1
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'timeline-observatory.blend'))
print(f'PASS six actual timeline entries; {len(preserved)} room transforms/visibility/actions preserved')
