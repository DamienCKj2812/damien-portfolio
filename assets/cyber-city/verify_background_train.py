"""Verify the independent rear train, retired interchange and exported motion."""
import json
from array import array
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parent
scene = bpy.context.scene
stats = json.loads(scene['background_train_route'])
train = scene.objects[stats['actor']]
package = ROOT.parent.parent / 'public/models/city'
manifest = json.loads((package / 'scene.json').read_text())
actor = next(actor for actor in manifest['actors'] if actor['name'] == train.name)
assert actor['autonomous'] and actor['motion'] == stats['motion']
assert manifest['backgroundTrain'] == stats
assert actor['motion']['mode'] == 'one-way'
assert actor['motion']['resetFrames'] > 0
assert stats['offscreenEndpointChecks']['cameraFrames'] == 450
assert not next(actor for actor in manifest['actors'] if actor['name'] == 'Mono • Transit • maglev train').get('autonomous')
channel = manifest['channels'].index(train.name)
motion = array('f')
motion.frombytes((package / manifest['animation']).read_bytes())
for frame in range(1, 451):
    scene.frame_set(frame)
    scene.view_layers[0].update()
    expected = -1000 + (frame - 1) / 449 * 2000
    assert abs(train.matrix_world.translation.x - expected) < .001
    assert abs(train.matrix_world.translation.y - 7) < .001
    assert abs(train.matrix_world.translation.z - 7.6) < .001
    assert train.matrix_world.to_quaternion().angle < 1e-6, frame
    for obj in train.children_recursive:
        if obj.type == 'MESH':
            ys = [(obj.matrix_world @ v.co).y for v in obj.data.vertices]
            assert min(ys) > 5.65 and max(ys) < 8.35, (obj.name, frame)
    start = ((frame - 1) * manifest['channelCount'] + channel) * manifest['channelStride']
    assert all(abs(a - b) < .001 for a, b in zip(train.matrix_world.translation, motion[start:start + 3])), frame
removed = json.loads(scene['left_transit_route'])['removedUpperInterchange']
assert removed['Clean outlines • Highway edges'] == 48
assert removed['Clean outlines • Highway supports'] == 72
for name, count in removed.items():
    obj = scene.objects.get(name)
    if obj:
        original = bpy.data.meshes[obj['left_transit_source']]
        assert len(obj.data.vertices) == len(original.vertices) - count, name
        assert any(recovery.data == original for recovery in bpy.data.collections['Left transit • Source recovery'].objects)
scene.frame_set(1)
print(json.dumps({'checks': 'passed', 'rearHighwayMotionFramesChecked': 450,
                  'autonomousRearTrain': True, 'foregroundTrainStillScrollDriven': True,
                  'upperInterchangeRemoved': True, 'nativeTrainFitsRearDeck': True,
                  'oneWayWithoutSpin': True, 'hiddenResetEndpoints': True}))
