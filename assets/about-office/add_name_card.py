"""Add the desk name card and Blender zoom preview to the existing office file."""
import ast
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
scene = bpy.data.scenes['ABOUT / Skyline Office']
bpy.context.window.scene = scene
collections = {c.name.split(' • ')[1][:2]:c for c in scene.collection.children
               if c.name.startswith('Office • ')}
if '10' not in collections:
    collections['10'] = bpy.data.collections.new('Office • 10 Name card & contact')
    scene.collection.children.link(collections['10'])
if scene.objects.get('Office • Name card / interactive assembly'):
    raise RuntimeError('The name card already exists; edit it in the main office file.')
black = bpy.data.materials['Office • Black architectural backing']
graphite = bpy.data.materials['Office • Desk and equipment graphite']
edge = bpy.data.materials['Office • Fine architectural silver']
screen_line = bpy.data.materials['Office • Screen interface silver']
type_mat = bpy.data.materials['Office • Silver lettering']
bpy.context.view_layer.update()
retained = {o.name:o.matrix_world.copy() for o in scene.objects}
source = ast.parse((ROOT/'build_office.py').read_text())
names = {'material','link','lines','box','text','camera','apply_name_card_click_hint','build_name_card'}
helpers = ast.Module(body=[n for n in source.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[])
exec(compile(helpers,str(ROOT/'build_office.py'),'exec'),globals())
card = build_name_card()
bpy.context.view_layer.update()
for name,matrix in retained.items():
    assert scene.objects[name].matrix_world==matrix, f'Unexpected change to {name}'
assert scene.objects[card['face_mesh']].data.uv_layers.active.name=='CardUV'
assert scene.frame_end==180 and scene.render.fps==30
manifest_path = ROOT/'office-manifest.json'
manifest = json.loads(manifest_path.read_text())
manifest.update(objects=len(scene.objects),active_camera=scene.camera.name,contact_card=card)
manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
scene.frame_set(1)
bpy.ops.object.select_all(action='DESELECT')
scene.camera.select_set(True); bpy.context.view_layer.objects.active = scene.camera
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
if '--render' in sys.argv:
    original = (scene.camera,scene.render.resolution_x,scene.render.resolution_y,scene.render.filepath)
    for camera_name,width,height,filename in [
        ('Office • About office presentation camera',1440,840,'office-preview.png'),
        ('Office • Contact card focus camera',1280,800,'office-name-card.png'),
        ('Office • Office architectural overview camera',1280,800,'office-overview.png')]:
        scene.camera = scene.objects[camera_name]
        scene.render.resolution_x = width; scene.render.resolution_y = height
        scene.render.filepath = str(ROOT/filename)
        bpy.ops.render.render(write_still=True)
    scene.camera,scene.render.resolution_x,scene.render.resolution_y,scene.render.filepath = original
print(json.dumps({'checks':'passed','preserved_objects':len(retained),'contact_card':card}))
