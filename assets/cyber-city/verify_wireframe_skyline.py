"""Verify restored native skyline and its connected point/line browser package."""
import json
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view

ROOT = Path(__file__).resolve().parent
scene = bpy.context.scene
report = json.loads(scene['wireframe_skyline'])
assert report['buildingCount'] >= 30
assert report['silhouetteSegments'] > 500
assert report['floorBandSegments'] > 200
assert not report['denseFacadeCloud']
objects = [obj for obj in scene.objects if obj.get('city_skyline')]
assert len(objects) == 5
assert all(not obj.hide_render and not obj.hide_get() for obj in objects)
assert all(obj.type == 'MESH' and not obj.data.polygons and 'radius' in obj.data.attributes for obj in objects)
assert scene.objects['Mono • 04 Skyline • particles 0'].hide_render
assert all(obj.hide_render for obj in scene.objects if obj.name.startswith(
    ('Reference tower • Left background', 'Reference tower • Right background')))
assert all(bounds['bounds'][0][1] > -5.55 for bounds in report['buildings'])
visible_frames = []
points = [obj.matrix_world @ vertex.co for obj in objects for vertex in obj.data.vertices]
for frame in (90, 145, 180, 220, 245, 280, 310):
    scene.frame_set(frame)
    scene.view_layers[0].update()
    visible = sum(0 <= p.x <= 1 and 0 <= p.y <= 1 and p.z > 0
                  for p in (world_to_camera_view(scene, scene.camera, point) for point in points))
    assert visible > 100, f'Skyline is missing from the approach camera at {frame}'
    visible_frames.append({'frame': frame, 'projectedVertices': visible})
package = ROOT.parents[1] / 'public/models/city'
manifest = json.loads((package / 'scene.json').read_text())
assert manifest['wireframeSkyline'] == report
groups = [group for group in manifest['groups'] if group.get('role') == 'skyline']
assert {group['kind'] for group in groups} == {'points', 'lines'}
assert all(group['actor'] == 0 for group in groups)
assert sum(group['vertexCount'] // 2 for group in groups if group['kind'] == 'lines') > 900
assert sum(group['vertexCount'] for group in groups if group['kind'] == 'points') > 300
scene.frame_set(1)
print(json.dumps({'checks': 'passed', 'buildings': report['buildingCount'],
                  'visibleApproachFrames': visible_frames, 'nativePointLineSources': len(objects),
                  'connectedBrowserGroups': len(groups), 'opaqueReplacementBlocksHidden': True}))
