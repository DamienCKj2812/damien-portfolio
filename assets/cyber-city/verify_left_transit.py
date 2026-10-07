"""Read-only full-route envelope and connected browser-motion verification."""
import json
from array import array
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
scene = bpy.context.scene
assert scene.name == 'MONO / Wire & Particle City'
stats = json.loads(scene['left_transit_route'])
assert stats['routeFramesChecked'] == 450
train = scene.objects['Mono • Transit • maglev train']
scene.frame_set(1)
scene.view_layers[0].update()
points = []
for obj in scene.objects:
    parent = obj.parent
    while parent and parent != train:
        parent = parent.parent
    if parent != train or obj.type != 'MESH':
        continue
    basis = train.matrix_world.inverted() @ obj.matrix_world
    points.extend(basis @ v.co for v in obj.data.vertices)
low = Vector(tuple(min(p[i] for p in points) for i in range(3)))
high = Vector(tuple(max(p[i] for p in points) for i in range(3)))
corners = [Vector((x, y, z)) for x in (low.x, high.x) for y in (low.y, high.y) for z in (low.z, high.z)]
rails = scene.objects['Clean outlines • Secondary guide rails']
assert all(-15.02 <= (rails.matrix_world @ v.co).x <= -14.28 for v in rails.data.vertices)
constraint = next(c for c in train.constraints if c.type == 'FOLLOW_PATH')
assert constraint.target.name == 'Mono • Traffic path • maglev highway pass'
package = ROOT.parent.parent / 'public/models/city'
manifest = json.loads((package / 'scene.json').read_text())
assert manifest['trainRoute'] == stats
channel = manifest['channels'].index(train.name)
motion = array('f')
motion.frombytes((package / manifest['animation']).read_bytes())
max_x = float('-inf')
for frame in range(1, 451):
    scene.frame_set(frame)
    scene.view_layers[0].update()
    max_x = max(max_x, max((train.matrix_world @ p).x for p in corners))
    assert max_x < -12
    assert abs(train.matrix_world.translation.x - stats['railCenterX']) < .001
    if frame <= manifest['frameEnd']:
        start = ((frame - manifest['frameStart']) * manifest['channelCount'] + channel) * manifest['channelStride']
        position, rotation, scale = train.matrix_world.decompose()
        expected = (*position, rotation.x, rotation.y, rotation.z, rotation.w, *scale)
        assert all(abs(a - b) < .001 for a, b in zip(expected, motion[start:start + 10])), frame
    if frame in (1, 450):
        assert abs(constraint.offset_factor - (frame - 1) / 449) < 1e-6
scene.frame_set(1)
print(json.dumps({'checks': 'passed', 'routeFramesChecked': 450,
                  'connectedMotionFramesChecked': manifest['frameEnd'], 'trainRightmostX': max_x,
                  'minimumTowerLateralClearanceMeters': stats['minimumTowerLateralClearanceMeters'],
                  'followPathTimingPreserved': True}))
