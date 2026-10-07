"""Apply the same cyber lighting accents to either static or animated lobby."""
import ast
import json
from pathlib import Path
import sys

import bpy

ROOT = Path(__file__).resolve().parent
scene = bpy.data.scenes['KAZE / Monochrome Atrium']
bpy.context.window.scene = scene
collections = {c.name.split(' • ')[1][:2]:c for c in scene.collection.children
               if c.name.startswith('Lobby • ')}
line_mat = bpy.data.materials['Lobby • Fine silver edges']
bpy.context.view_layer.update()
before = {o.name:o.matrix_world.copy() for o in scene.objects
          if 'Cyber /' not in o.name}
old_end = scene.frame_end
source = ast.parse((ROOT/'build_lobby.py').read_text())
names = {'material','link','lines','apply_cyber_lighting'}
helpers = ast.Module(body=[n for n in source.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[])
exec(compile(helpers,str(ROOT/'build_lobby.py'),'exec'),globals())
settings = apply_cyber_lighting()
bpy.context.view_layer.update()
for name,matrix in before.items():
    assert scene.objects[name].matrix_world == matrix, f'Unexpected transform change to {name}'
assert scene.frame_end==old_end
assert scene.compositing_node_group is not None
animated = scene.objects.get('Lobby • Navigation / walkthrough camera') is not None
if animated:
    scene.frame_set(1020); bpy.context.view_layer.update()
    left = scene.objects['Lobby • Elevator R1 / left door leaf']
    right = scene.objects['Lobby • Elevator R1 / right door leaf']
    assert abs(left.location.x-2.455)<.001 and abs(right.location.x-5.645)<.001
    scene.frame_set(1)
path = bpy.data.filepath
bpy.ops.wm.save_as_mainfile(filepath=path)
if not animated:
    manifest = json.loads((ROOT/'lobby-manifest.json').read_text())
    manifest.update(objects=len(scene.objects),cyber_lighting=settings)
    (ROOT/'lobby-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
if '--render' in sys.argv:
    original = (scene.camera,scene.frame_current,scene.render.resolution_x,
                scene.render.resolution_y,scene.render.resolution_percentage,scene.render.filepath)
    scene.render.resolution_percentage = 100
    if animated:
        views = [(scene.camera.name,1,1280,800,'navigation-start.png'),
                 (scene.camera.name,600,1280,800,'navigation-escalator.png'),
                 (scene.camera.name,840,1280,800,'navigation-elevator-arrival.png'),
                 (scene.camera.name,1020,1280,800,'navigation-elevator-open.png')]
    else:
        views = [('Lobby • Wide lobby activity camera',1,1280,800,'lobby-wide.png'),
                 ('Lobby • Upper elevator foyer camera',1,1280,800,'upper-landing-elevators.png'),
                 ('Lobby • Concept portrait camera',1,720,1120,'lobby-concept.png')]
    for camera_name,frame,width,height,filename in views:
        scene.camera = scene.objects[camera_name]
        scene.frame_set(frame)
        scene.render.resolution_x = width; scene.render.resolution_y = height
        scene.render.filepath = str(ROOT/filename)
        bpy.ops.render.render(write_still=True)
    camera,frame,rx,ry,percentage,filepath = original
    scene.camera = camera; scene.frame_set(frame)
    scene.render.resolution_x = rx; scene.render.resolution_y = ry
    scene.render.resolution_percentage = percentage; scene.render.filepath = filepath
print(json.dumps({'checks':'passed','file':path,'navigation_preserved':animated,
                  'preserved_objects':len(before),**settings}))
