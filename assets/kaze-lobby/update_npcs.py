"""Refresh only the authored crowd in an existing lobby, preserving scene edits.

Historical design patch; saves the currently opened file.
"""
import ast
import json
from pathlib import Path
import random
import math
import sys

import bpy
from mathutils import Euler, Matrix, Vector

ROOT = Path(__file__).resolve().parent
scene = bpy.data.scenes['KAZE / Monochrome Atrium']
bpy.context.window.scene = scene
collections = {c.name.split(' • ')[1][:2]:c for c in scene.collection.children
               if c.name.startswith('Lobby • ')}
if '11' not in collections:
    collections['11'] = bpy.data.collections.new('Lobby • 11 NPC accessories')
    scene.collection.children.link(collections['11'])
dot_mat = bpy.data.materials['Lobby • White surface particles']
line_mat = bpy.data.materials['Lobby • Fine silver edges']
desk_mat = bpy.data.materials['Lobby • Reception charcoal']
black = bpy.data.materials['Lobby • Obsidian architecture']

# Architecture, furnishings, materials, cameras and lights are retained in place.
retained = {o.name:o.matrix_world.copy() for o in scene.objects
            if o not in collections['06'].objects[:] and o not in collections['11'].objects[:]}
for obj in list(collections['06'].objects):
    if obj.get('pose'):
        mesh = obj.data
        groups = [mod.node_group for mod in obj.modifiers if mod.type=='NODES' and mod.node_group]
        bpy.data.objects.remove(obj,do_unlink=True)
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
        for group in groups:
            if group.users == 0:
                bpy.data.node_groups.remove(group)
for obj in list(collections['11'].objects):
    if obj.get('npc_owner'):
        bpy.data.objects.remove(obj,do_unlink=True)

source = ast.parse((ROOT/'build_lobby.py').read_text())
names = {'link','lines','box','particles','person','populate_people'}
helpers = ast.Module(body=[n for n in source.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[])
exec(compile(helpers,str(ROOT/'build_lobby.py'),'exec'),globals())
populate_people()
bpy.context.view_layer.update()
for name,matrix in retained.items():
    assert scene.objects[name].matrix_world == matrix, f'Unexpected change to {name}'
people = list(collections['06'].objects)
assert len(people)==18
assert len({o.get('pose') for o in people})==15
assert sum(o.get('pose')=='leaning' for o in people)==1
for obj in people:
    if obj.get('pose','').startswith('seated_'):
        facing = obj['facing_angle_rad']
        assert abs(facing-(math.pi/2 if obj['pose_origin'][0]<0 else -math.pi/2))<.001

manifest = json.loads((ROOT/'lobby-manifest.json').read_text())
manifest.update(objects=len(scene.objects),people=len(people),
                npc_poses={pose:sum(o.get('pose')==pose for o in people)
                           for pose in sorted({o.get('pose') for o in people})},
                particle_count=sum(o.get('particle_count',0) for o in scene.objects))
(ROOT/'lobby-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
if '--render' in sys.argv:
    original = (scene.camera,scene.render.resolution_x,scene.render.resolution_y,
                scene.render.resolution_percentage,scene.render.filepath)
    scene.render.resolution_percentage = 100
    scene.camera = scene.objects['Lobby • Concept portrait camera']
    scene.render.resolution_x = 720; scene.render.resolution_y = 1120
    scene.render.filepath = str(ROOT/'lobby-concept.png')
    bpy.ops.render.render(write_still=True)
    scene.camera = scene.objects['Lobby • Wide lobby activity camera']
    scene.render.resolution_x = 1280; scene.render.resolution_y = 800
    scene.render.filepath = str(ROOT/'lobby-wide.png')
    bpy.ops.render.render(write_still=True)
    (scene.camera,scene.render.resolution_x,scene.render.resolution_y,
     scene.render.resolution_percentage,scene.render.filepath) = original
print(json.dumps({'checks':'passed','preserved_objects':len(retained),**manifest}))
