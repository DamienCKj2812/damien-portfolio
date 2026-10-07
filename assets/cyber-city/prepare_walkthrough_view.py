"""Save the production master in camera view without changing authored motion.

blender --background assets/cyber-city/monochrome-city-solid-tower.blend \
    --python-exit-code 1 --python assets/cyber-city/prepare_walkthrough_view.py
"""
import json
from pathlib import Path

import bpy


MODEL = Path(__file__).resolve().parent / 'monochrome-city-solid-tower.blend'
scene = bpy.context.scene
assert Path(bpy.data.filepath).resolve() == MODEL, 'Open the production city master.'
assert scene.name == 'MONO / Wire & Particle City'
camera = scene.objects['Mono • Walkthrough • camera']


def poses():
    samples = []
    for frame in range(1, 451):
        scene.frame_set(frame)
        scene.view_layers[0].update()
        samples.append((tuple(value for row in camera.matrix_world for value in row), camera.data.lens))
    return samples


before = poses()
assert before[0][0] != before[-1][0], 'The walkthrough camera must have evaluated motion.'
scene.camera = camera
scene.frame_start, scene.frame_end = 1, 450
scene.render.fps = 30
scene.sync_mode = 'FRAME_DROP'
prepared = 0
for screen in bpy.data.screens:
    if screen.name != 'Layout':
        continue
    for area in screen.areas:
        if area.type != 'VIEW_3D':
            continue
        view = area.spaces.active
        view.use_local_camera = False
        view.camera = camera
        view.region_3d.view_perspective = 'CAMERA'
        view.overlay.show_overlays = False
        prepared += 1
assert prepared, 'The saved file needs a Layout viewport.'
assert poses() == before, 'Preparing playback must not change camera motion or lens.'
scene.frame_set(1)
scene.view_layers[0].update()
for obj in scene.objects:
    obj.select_set(False)
camera.select_set(True)
scene.view_layers[0].objects.active = camera
for window in bpy.context.window_manager.windows:
    window.scene = scene
    layout = bpy.data.workspaces.get('Layout')
    if layout:
        window.workspace = layout
bpy.context.preferences.filepaths.save_version = 0
# A scene-only library write omits the saved UI. A normal .blend save retains
# the camera-view Layout needed for Space to visibly play the walkthrough.
bpy.ops.wm.save_as_mainfile(filepath=str(MODEL), compress=True)
print(json.dumps({'model': MODEL.name, 'camera': camera.name, 'cameraViewports': prepared,
                  'motionFramesUnchanged': 450, 'startFrame': 1, 'playback': 'Space in camera view'}))
