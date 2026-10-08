"""Remove only the long banner's right-edge glitch strip, retaining recovery data."""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from reference_tower_spec import CENTER
MASTER = ROOT / 'monochrome-city-solid-tower.blend'
scene = bpy.context.scene
assert scene.name == 'MONO / Wire & Particle City'
assert Path(bpy.data.filepath).resolve() == MASTER
scene.frame_set(1)
scene.view_layers[0].update()
targets = []
for obj in scene.objects:
    if obj.type != 'MESH' or not obj.name.startswith('Reference tower • Scattered glitch block'):
        continue
    center = sum((obj.matrix_world @ vertex.co for vertex in obj.data.vertices), Vector()) / len(obj.data.vertices)
    angle = math.degrees(math.atan2(center.x - CENTER[0], CENTER[1] - center.y))
    if 2.49 <= angle <= 8.51:
        targets.append(obj)
assert targets, 'No long-banner border blocks found'


def poses():
    snapshot = {}
    for frame in (1, 90, 245, 383, 450):
        scene.frame_set(frame)
        scene.view_layers[0].update()
        snapshot[frame] = {obj.name: (tuple(value for row in obj.matrix_world for value in row),
                                     obj.animation_data.action if obj.animation_data else None)
                           for obj in scene.objects}
    return snapshot


before = poses()
camera = scene.camera
visibility = {obj.name: (obj.hide_render, obj.hide_get()) for obj in scene.objects if obj not in targets}
for obj in targets:
    obj.hide_render = True
    obj.hide_set(True)
    obj['long_banner_glitch_border'] = True
layout = json.loads(scene['reference_tower_redesign'])
layout['longBannerGlitchBorderRemoved'] = True
layout['hiddenBannerGlitchBlocks'] = len(targets)
scene['reference_tower_redesign'] = json.dumps(layout)
assert before == poses(), 'Existing city/camera/actor poses or actions changed'
assert visibility == {obj.name: (obj.hide_render, obj.hide_get()) for obj in scene.objects if obj not in targets}
assert scene.camera == camera
scene.frame_set(1)
scene.view_layers[0].update()
bpy.context.preferences.filepaths.save_version = 1
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER))
(ROOT / 'reference-tower.json').write_text(json.dumps(layout, indent=2) + '\n')
print(json.dumps({'checks': 'passed', 'hiddenBannerGlitchBlocks': len(targets),
                  'unrelatedVisibilityCameraAndActorPosesPreserved': True}))
