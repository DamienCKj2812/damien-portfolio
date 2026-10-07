"""Read-only native/browser checks for the workstation's Malaysia map."""
import json
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
scene = bpy.data.scenes['ABOUT / Skyline Office']
screen = scene.objects['Office • About content screen / web texture target']
assert screen.data.uv_layers.get('ScreenUV')
report = json.loads(scene['office_malaysia_map'])
assert report['countryCode'] == 'MYS' and report['polygons'] >= 2
assert report['triangles'] > 100 and report['sourceLicense'] == 'Natural Earth public domain'
objects = [obj for obj in scene.objects if obj.get('office_screen_map')]
assert len(objects) == report['objects']
assert all(obj.parent == screen and not obj.hide_render for obj in objects)
scene.view_layers[0].update()
for obj in objects:
    corners = [obj.matrix_local @ Vector(corner) for corner in obj.bound_box]
    assert all(abs(point.x) < 1.22 and abs(point.z) < .54 for point in corners), f'Map content outside display: {obj.name}'
    for material in obj.data.materials:
        shader = next(node for node in material.node_tree.nodes if node.type == 'EMISSION')
        color = shader.inputs['Color'].default_value
        assert max(color[:3]) - min(color[:3]) < 1e-6
for name in ['Screen navigation', 'Screen signature', 'Screen original idea network', 'Screen network nodes', 'Screen globe diagram']:
    obj = scene.objects.get('Office • ' + name)
    assert obj is None or obj.hide_render
land = scene.objects['Office • Malaysia screen / Malaysia filled geography']
assert any(vertex.co.x < -.4 for vertex in land.data.vertices), 'Missing Peninsular Malaysia'
assert any(vertex.co.x > .4 for vertex in land.data.vertices), 'Missing Sabah/Sarawak'
package = ROOT.parents[1] / 'public/models/rooms/about'
manifest = json.loads((package / 'scene.json').read_text())
assert manifest['officeScreen'] == report
groups = [group for group in manifest['groups'] if group.get('role') == 'officeScreenMap']
assert groups and {group['kind'] for group in groups} >= {'solid', 'lines'}
assert all(group['actor'] == 0 and group['id'] == 'malaysia' for group in groups)
print(json.dumps({'checks': 'passed', 'country': 'Malaysia', 'regions': 2, 'monochrome': True,
                  'nativeMapObjects': len(objects), 'browserMapGroups': len(groups), 'screenUVPreserved': True}))
