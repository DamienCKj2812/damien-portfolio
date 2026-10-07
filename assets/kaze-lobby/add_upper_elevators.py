"""Add the upper elevator foyer to a saved lobby without rebuilding its interior."""
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
if '13' not in collections:
    collections['13'] = bpy.data.collections.new('Lobby • 13 Upper elevator foyer')
    scene.collection.children.link(collections['13'])
black = bpy.data.materials['Lobby • Obsidian architecture']
desk_mat = bpy.data.materials['Lobby • Reception charcoal']
floor_mat = bpy.data.materials['Lobby • Polished black stone']
line_mat = bpy.data.materials['Lobby • Fine silver edges']
quiet_mat = bpy.data.materials['Lobby • Secondary gray edges']
white = bpy.data.materials['Lobby • White light channels']
type_mat = bpy.data.materials['Lobby • Silver typography']
camera_names = {'Lobby • Upper elevator foyer camera','Lobby • Escalator arrival camera',
                'Lobby • Upper foyer back toward escalators camera'}
changed_names = {'Lobby • Reflective atrium floor','Lobby • Dark overhead canopy',
                 'Lobby • Side wall','Lobby • Side wall.001','Lobby • Rear atrium wall',
                 'Lobby • Rear gallery railing'}
retained = {o.name:o.matrix_world.copy() for o in scene.objects
            if o not in collections['13'].objects[:] and o.name not in changed_names|camera_names}
for obj in list(collections['13'].objects):
    bpy.data.objects.remove(obj,do_unlink=True)
for name in camera_names:
    obj = scene.objects.get(name)
    if obj:
        bpy.data.objects.remove(obj,do_unlink=True)
source = ast.parse((ROOT/'build_lobby.py').read_text())
names = {'link','lines','box','text','camera','build_upper_elevator_foyer'}
helpers = ast.Module(body=[n for n in source.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[])
exec(compile(helpers,str(ROOT/'build_lobby.py'),'exec'),globals())
build_upper_elevator_foyer()
bpy.context.view_layer.update()
lift_roots = [o for o in collections['13'].objects if o.get('type')=='Upper-floor elevator entrance']
assert len(lift_roots)==4
assert sum(o.get('side')=='left' for o in lift_roots)==2
assert sum(o.get('side')=='right' for o in lift_roots)==2
assert abs(scene.objects['Lobby • Upper foyer walking deck'].location.z+.10-6.12)<.001
for name,matrix in retained.items():
    assert scene.objects[name].matrix_world == matrix, f'Unexpected change to {name}'
manifest = json.loads((ROOT/'lobby-manifest.json').read_text())
manifest['dimensions_m']['depth'] = 36.5
manifest.update(objects=len(scene.objects),elevators=4,elevators_per_side=2,
                upper_foyer={'floor_z':6.12,'front_y':19,'rear_y':24.5},
                upper_view_cameras=sorted(camera_names))
(ROOT/'lobby-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
if '--render' in sys.argv:
    original = (scene.camera,scene.render.resolution_x,scene.render.resolution_y,
                scene.render.resolution_percentage,scene.render.filepath)
    scene.render.resolution_percentage = 100
    for camera_name,width,height,filename in [
        ('Lobby • Upper elevator foyer camera',1280,800,'upper-landing-elevators.png'),
        ('Lobby • Escalator arrival camera',1280,800,'escalator-arrival.png'),
        ('Lobby • Upper foyer back toward escalators camera',1280,800,'upper-landing-back-view.png'),
        ('Lobby • Concept portrait camera',720,1120,'lobby-concept.png'),
        ('Lobby • Wide lobby activity camera',1280,800,'lobby-wide.png')]:
        scene.camera = scene.objects[camera_name]
        scene.render.resolution_x = width; scene.render.resolution_y = height
        scene.render.filepath = str(ROOT/filename)
        bpy.ops.render.render(write_still=True)
    (scene.camera,scene.render.resolution_x,scene.render.resolution_y,
     scene.render.resolution_percentage,scene.render.filepath) = original
print(json.dumps({'checks':'passed','elevators':4,'per_side':2,'preserved_objects':len(retained)}))
