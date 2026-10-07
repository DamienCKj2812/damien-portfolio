"""Replace only the stair flights with simple escalators in the saved lobby."""
import ast
import json
import math
from pathlib import Path
import random
import sys

import bpy
from mathutils import Euler, Matrix, Vector

ROOT = Path(__file__).resolve().parent
scene = bpy.data.scenes['KAZE / Monochrome Atrium']
bpy.context.window.scene = scene
collections = {c.name.split(' • ')[1][:2]:c for c in scene.collection.children
               if c.name.startswith('Lobby • ')}
black = bpy.data.materials['Lobby • Obsidian architecture']
desk_mat = bpy.data.materials['Lobby • Reception charcoal']
line_mat = bpy.data.materials['Lobby • Fine silver edges']
dot_mat = bpy.data.materials['Lobby • White surface particles']
prefixes = ('Lobby • Stair ','Lobby • Continuous stair handrail',
            'Lobby • Escalator L /','Lobby • Escalator R /')
rider_names = {'Lobby • Stair / ascending visitor','Lobby • Escalator / riding upstairs'}
retained = {o.name:o.matrix_world.copy() for o in scene.objects
            if not o.name.startswith(prefixes) and o.name not in rider_names}
for obj in list(scene.objects):
    if obj.name.startswith(prefixes) or obj.name in rider_names:
        bpy.data.objects.remove(obj,do_unlink=True)
source = ast.parse((ROOT/'build_lobby.py').read_text())
names = {'link','lines','box','particles','person','build_escalators'}
helpers = ast.Module(body=[n for n in source.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[])
exec(compile(helpers,str(ROOT/'build_lobby.py'),'exec'),globals())
assemblies = build_escalators()
random.seed(42)
person('Escalator / riding upstairs',(6.85,12.35,2.16),.98,
       angle=math.pi,pose='riding_escalator',count=.9)
bpy.context.view_layer.update()
assert len(assemblies)==2
assert sum('/ step ' in o.name and o.name.rsplit(' ',1)[-1].isdigit()
           for o in collections['02'].objects)==68
assert not any(o.name.startswith('Lobby • Stair ') for o in collections['02'].objects)
for name,matrix in retained.items():
    assert scene.objects[name].matrix_world == matrix, f'Unexpected change to {name}'
manifest = json.loads((ROOT/'lobby-manifest.json').read_text())
for key in ['stair_treads','stair_solid_treads','stair_outline_only_treads','stair_tread_thickness_m','stair_first_step_y']:
    manifest.pop(key,None)
people = list(collections['06'].objects)
manifest.update(objects=len(scene.objects),escalators=2,escalator_steps_per_flight=34,
                escalator_entry_y=8.45,clearance_behind_reception_m=3.85,
                npc_poses={p:sum(o.get('pose')==p for o in people)
                           for p in sorted({o.get('pose') for o in people})})
(ROOT/'lobby-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
scene['Design reference'] = 'KAZE monochrome particle atrium; twin escalators and reflective floor'
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
print(json.dumps({'checks':'passed','escalators':len(assemblies),'preserved_objects':len(retained)}))
