"""Check role-based deformations, planted feet, accessories, and loop seams."""
import sys
from pathlib import Path
import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from npc_motion import PERIOD, body_regions

scene = bpy.data.scenes['KAZE / Monochrome Atrium']
people = [obj for obj in scene.objects if obj.get('pose_origin') is not None]
assert len(people) == 17
assert 'Lobby • Escalator / riding upstairs' not in scene.objects
assert all(obj.get('autonomous_npc') for obj in people)
props = [obj for obj in scene.objects if obj.get('npc_owner')]
assert props and all(obj.animation_data and obj.animation_data.action for obj in props)

for obj in people:
    keys = obj.data.shape_keys.key_blocks
    assert len(keys) == 5, f'Expected four browser morph channels: {obj.name}'
    regions = body_regions(obj)
    gesture, attention = keys['Activity gesture'], keys['Attention and response']
    assert max((a.co-b.co).length for a, b in zip(keys['Basis'].data, attention.data)) > .005
    if obj['pose'] == 'greeting':
        hands = [i for i, part in enumerate(regions) if part == 'hand:1']
        assert max((gesture.data[i].co-keys['Basis'].data[i].co).length for i in hands) > .06
    if not obj.get('predefined_route'):
        for i, region in enumerate(regions):
            if region.startswith(('thigh:', 'shin:', 'foot:')):
                assert (gesture.data[i].co-keys['Basis'].data[i].co).length < 1e-6
                assert (attention.data[i].co-keys['Basis'].data[i].co).length < 1e-6
    weights = []
    for frame in [1, 75, 150, 225, 300, 450, 600, 750, 900, 1020]:
        scene.frame_set(frame)
        weights.append((gesture.value, attention.value))
    assert any(max(w[channel] for w in weights)-min(w[channel] for w in weights) > .05 for channel in range(2))
    assert max(abs(a-b) for a, b in zip(weights[0], weights[-1])) < 1e-5


def snapshot(frame):
    scene.frame_set(frame)
    scene.view_layers[0].update()
    return [tuple(value for row in obj.matrix_world for value in row) for obj in [*people, *props]]


start, end = snapshot(1), snapshot(PERIOD+1)
assert max(abs(a-b) for first, last in zip(start, end) for a, b in zip(first, last)) < 1e-5
scene.frame_set(1)
print({'npcs': len(people), 'animated_accessories': len(props),
       'role_gestures': True, 'stationary_feet_planted': True, 'seamless_loop': True})
