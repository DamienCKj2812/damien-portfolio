"""Render example tour views; illustrative look angles are never saved or keyed."""
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
scene = bpy.data.scenes['SKILLS / Technology Gallery']
bpy.context.window.scene = scene
camera = scene.objects['Gallery • Guided walk / free-look camera']
original = (scene.camera,scene.frame_current,camera.rotation_euler.copy(),
            scene.render.resolution_x,scene.render.resolution_y,scene.render.filepath)
try:
    scene.camera = camera
    for frame,target,filename in [(1,None,'gallery-walk-start.png'),
                                  (300,(-5.94,-.3,2.65),'gallery-walk-languages.png'),
                                  (1100,(0,8.94,2.65),'gallery-walk-databases.png')]:
        scene.frame_set(frame); bpy.context.view_layer.update()
        if target:
            camera.rotation_euler = (Vector(target)-camera.matrix_world.translation).to_track_quat('-Z','Y').to_euler()
        scene.render.resolution_x = 1280; scene.render.resolution_y = 960
        scene.render.filepath = str(ROOT/filename)
        bpy.ops.render.render(write_still=True)
finally:
    previous_camera,frame,rotation,width,height,filepath = original
    camera.rotation_euler = rotation; scene.camera = previous_camera; scene.frame_set(frame)
    scene.render.resolution_x = width; scene.render.resolution_y = height
    scene.render.filepath = filepath
