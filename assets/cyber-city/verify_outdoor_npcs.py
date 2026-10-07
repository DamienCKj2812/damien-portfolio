"""Verify restored street people, native actions and browser actor channels."""
import json
from array import array
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parent
scene = bpy.context.scene
layout = json.loads((ROOT / 'npc-layout.json').read_text())['people']
expected_ids = {person['id'] for person in layout}
crowd = scene.objects['Mono • 07 Street life • particles 3']
assert not crowd.hide_render and not crowd.hide_get()
stationary = json.loads(crowd['person_metadata'])
walkers = [obj for obj in scene.objects if obj.get('city_role') == 'walking_npc']
assert len(stationary) == 8 and len(walkers) == 10
ids = {person['id'] for person in stationary}
for root in walkers:
    assert not root.hide_render and not root.hide_get()
    assert root.animation_data and root.animation_data.action
    person = json.loads(root['person_metadata'])
    assert person['id'] not in ids
    ids.add(person['id'])
    body = next(obj for obj in root.children_recursive if obj.type == 'MESH' and 'person_id' in obj.data.attributes)
    assert not body.hide_render and len(body.data.vertices) >= 650
assert ids == expected_ids
assert all(not obj.hide_render for obj in scene.objects if obj.name.startswith('City NPC'))
manifest = json.loads((ROOT.parent.parent / 'public/models/city/scene.json').read_text())
actors = {actor['name']: actor for actor in manifest['actors']}
motion = array('f')
motion.frombytes((ROOT.parent.parent / 'public/models/city/animation.bin').read_bytes())
for frame in [1, 90, 180, 245, 310, 383, 450]:
    scene.frame_set(frame)
    scene.view_layers[0].update()
    for root in walkers:
        actor = actors[root.name]
        assert actor.get('walk') and actor['style'] == 'walking_npc'
        offset = ((frame - 1) * manifest['channelCount'] + actor['index']) * manifest['channelStride']
        assert all(abs(a - b) < .001 for a, b in zip(root.matrix_world.translation, motion[offset:offset + 3]))
scene.frame_set(1)
print(json.dumps({'checks': 'passed', 'outdoorPeople': len(ids), 'stationaryPeople': len(stationary),
                  'animatedWalkers': len(walkers), 'accessoriesVisible': True, 'nativeAndBrowserMotionMatch': True}))
