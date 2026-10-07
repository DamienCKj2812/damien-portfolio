"""Replace the shallow rear identity panel with the freestanding reception pillar.

Historical design patch; saves the currently opened file.
"""
import ast
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
scene = bpy.data.scenes['KAZE / Monochrome Atrium']
bpy.context.window.scene = scene
collections = {c.name.split(' • ')[1][:2]:c for c in scene.collection.children
               if c.name.startswith('Lobby • ')}
black = bpy.data.materials['Lobby • Obsidian architecture']
line_mat = bpy.data.materials['Lobby • Fine silver edges']
quiet_mat = bpy.data.materials['Lobby • Secondary gray edges']
type_mat = bpy.data.materials['Lobby • Silver typography']
replaced = {'Lobby • KAZE angular crest','Lobby • KAZE wordmark',
            'Lobby • Industries subline','Lobby • Japanese-inspired subline',
            'Lobby • Values','Lobby • Numbered manifesto'}
prefixes = ('Lobby • KAZE identity monolith','Lobby • Identity wall reveals',
            'Lobby • KAZE identity pillar','Lobby • Pillar front reveal',
            'Lobby • Pillar side reveal')
retained = {o.name:o.matrix_world.copy() for o in scene.objects
            if o.name not in replaced and not o.name.startswith(prefixes)}
for obj in list(scene.objects):
    if obj.name in replaced or obj.name.startswith(prefixes):
        bpy.data.objects.remove(obj,do_unlink=True)
source = ast.parse((ROOT/'build_lobby.py').read_text())
names = {'link','lines','box','text','build_identity_pillar'}
helpers = ast.Module(body=[n for n in source.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[])
exec(compile(helpers,str(ROOT/'build_lobby.py'),'exec'),globals())
pillar = build_identity_pillar()
bpy.context.view_layer.update()
for name,matrix in retained.items():
    assert scene.objects[name].matrix_world == matrix, f'Unexpected change to {name}'
assert all(abs(a-b)<.001 for a,b in zip(pillar.dimensions,(3.5,2.2,18)))
front = min((pillar.matrix_world @ Vector(v)).y for v in pillar.bound_box)
desk = scene.objects['Lobby • Reception floating countertop']
rear = max((desk.matrix_world @ Vector(v)).y for v in desk.bound_box)
assert 1.19 < front-rear < 1.21
assert abs(pillar.location.x)<.001
wide = scene.objects['Lobby • Wide lobby activity camera']
wide.rotation_euler = (Vector((0,6,5.8))-wide.location).to_track_quat('-Z','Y').to_euler()
manifest = json.loads((ROOT/'lobby-manifest.json').read_text())
manifest.update(objects=len(scene.objects),identity_pillar={
    'center':list(pillar.location),'dimensions_m':list(pillar.dimensions),
    'front_y':round(front,3),'reception_clearance_m':round(front-rear,3)})
(ROOT/'lobby-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
if '--render' in sys.argv:
    original = (scene.camera,scene.render.resolution_x,scene.render.resolution_y,
                scene.render.resolution_percentage,scene.render.filepath)
    scene.render.resolution_percentage = 100
    for camera_name,width,height,filename in [
        ('Lobby • Concept portrait camera',720,1120,'lobby-concept.png'),
        ('Lobby • Wide lobby activity camera',1280,800,'lobby-wide.png')]:
        scene.camera = scene.objects[camera_name]
        scene.render.resolution_x = width; scene.render.resolution_y = height
        scene.render.filepath = str(ROOT/filename)
        bpy.ops.render.render(write_still=True)
    (scene.camera,scene.render.resolution_x,scene.render.resolution_y,
     scene.render.resolution_percentage,scene.render.filepath) = original
print(json.dumps({'checks':'passed','preserved_objects':len(retained),**manifest}))
