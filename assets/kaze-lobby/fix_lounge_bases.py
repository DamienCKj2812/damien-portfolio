"""Remove misplaced solid sofa bases, align remaining seating, restore stair toes."""
import ast
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parent
scene = bpy.data.scenes['KAZE / Monochrome Atrium']
bpy.context.window.scene = scene
collections = {c.name.split(' • ')[1][:2]:c for c in scene.collection.children
               if c.name.startswith('Lobby • ')}
black = bpy.data.materials['Lobby • Obsidian architecture']
desk_mat = bpy.data.materials['Lobby • Reception charcoal']
line_mat = bpy.data.materials['Lobby • Fine silver edges']
retained = {o.name:o.matrix_world.copy() for o in scene.objects
            if o not in collections['10'].objects[:]}
# Rebuild the authored furniture without either solid base. Curves and cushions
# are positioned together after a dependency-graph flush, matching seated NPCs.
for obj in list(collections['10'].objects):
    bpy.data.objects.remove(obj,do_unlink=True)
source = ast.parse((ROOT/'build_lobby.py').read_text())
names = {'link','lines','box','build_lounge_furniture'}
helpers = ast.Module(body=[n for n in source.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[])
exec(compile(helpers,str(ROOT/'build_lobby.py'),'exec'),globals())
build_lounge_furniture()
for side in [-1,1]:
    for i in range(3):
        name = 'Stair %s / tread %02d' % ('L' if side<0 else 'R',i+1)
        if not scene.objects.get('Lobby • '+name):
            z = (i+1)*.15
            box(name,(side*6.85,9.1+i*.25,z-.0175),(1.45,.25,.035),group='02',outline=False)
bpy.context.view_layer.update()
assert not any('Lounge sofa base' in o.name for o in scene.objects)
assert sum('/ tread ' in o.name for o in scene.objects)==80
for name,matrix in retained.items():
    assert scene.objects[name].matrix_world == matrix, f'Unexpected change to {name}'
for obj in collections['10'].objects:
    if obj.type=='MESH':
        assert -2.6<obj.location.y<2.0, f'Misplaced furniture: {obj.name}'
manifest = json.loads((ROOT/'lobby-manifest.json').read_text())
manifest.update(objects=len(scene.objects),lounge_sofa_bases=0,
                stair_solid_treads=80,stair_outline_only_treads=0)
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
print(json.dumps({'checks':'passed','sofa_bases_remaining':0,'restored_stair_treads':6,
                  'preserved_objects':len(retained)}))
