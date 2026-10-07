"""Render gallery context and an isolated dot-only dinosaur reference view."""
from pathlib import Path
import json

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
scene = bpy.data.scenes['SKILLS / Technology Gallery']
bpy.context.window.scene = scene
portrait = scene.objects.get('Gallery • T-Rex dot portrait camera')
if portrait is None:
    data = bpy.data.cameras.new('Gallery • T-Rex dot portrait camera')
    portrait = bpy.data.objects.new(data.name,data)
    bpy.data.collections['Gallery • 06 Cameras'].objects.link(portrait)
portrait.location = (-5.70,-5.0,3.10)
portrait.rotation_euler = (Vector((-.15,3.85,2.30))-portrait.location).to_track_quat('-Z','Y').to_euler()
portrait.data.lens = 55; portrait.data.clip_start = .04; portrait.data.clip_end = 100
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
manifest_path = ROOT/'gallery-manifest.json'
manifest = json.loads(manifest_path.read_text())
manifest.update(objects=len(scene.objects),dot_portrait_camera=portrait.name)
manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
original = (scene.camera,scene.frame_current,scene.render.resolution_x,
            scene.render.resolution_y,scene.render.filepath)
for camera_name,frame,width,height,filename in [
    ('Gallery • Skills gallery presentation camera',300,1440,1080,'gallery-preview.png'),
    ('Gallery • T-Rex sculpture detail camera',480,1440,960,'gallery-trex.png')]:
    scene.camera = scene.objects[camera_name]; scene.frame_set(frame)
    scene.render.resolution_x = width; scene.render.resolution_y = height
    scene.render.filepath = str(ROOT/filename)
    bpy.ops.render.render(write_still=True)
hide_state = {obj:obj.hide_render for obj in scene.objects}
try:
    for obj in scene.objects:
        obj.hide_render = not (obj.get('trex_dots') or obj==portrait)
    scene.camera = portrait
    scene.render.resolution_x = 1080; scene.render.resolution_y = 1080
    scene.render.filepath = str(ROOT/'gallery-trex-dots.png')
    bpy.ops.render.render(write_still=True)
finally:
    for obj,hidden in hide_state.items():
        obj.hide_render = hidden
    camera,frame,width,height,filepath = original
    scene.camera = camera; scene.frame_set(frame)
    scene.render.resolution_x = width; scene.render.resolution_y = height
    scene.render.filepath = filepath
