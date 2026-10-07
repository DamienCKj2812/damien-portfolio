"""Render the updated master read-only; -- --isolated creates the reference view."""
from pathlib import Path
import sys

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
scene = bpy.context.scene
scene.frame_set(1)
scene.camera = scene.objects['Gallery • AT-AT walker detail camera']
scene.render.resolution_x = 1200;scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.cycles.samples = 24
scene.render.filepath = str(ROOT / 'gallery-atat.png')
if '--isolated' in sys.argv:
    for obj in scene.objects:
        obj.hide_render = not (obj.name.startswith('Gallery • AT-AT /') and not any(label in obj.name.lower() for label in ['plinth','display title','display subtitle']))
    scene.camera.hide_render = False
    scene.camera.location = (-5.65,-5.6,3.4)
    scene.camera.rotation_euler = (Vector((-.55,3.85,2.77))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
    scene.camera.data.lens = 39
    scene.render.filepath = str(ROOT / 'gallery-atat-reference.png')
bpy.ops.render.render(write_still=True)
