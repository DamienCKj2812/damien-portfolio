"""Replace the mistaken standing nameplate with a flat 90 x 55 mm paper card."""
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
black = bpy.data.materials['Office • Black architectural backing']
graphite = bpy.data.materials['Office • Desk and equipment graphite']
edge = bpy.data.materials['Office • Fine architectural silver']
screen_line = bpy.data.materials['Office • Screen interface silver']
type_mat = bpy.data.materials['Office • Silver lettering']
camera_names = {'Office • Contact card focus camera','Office • Name card contact zoom camera'}
scene.frame_set(1); bpy.context.view_layer.update()
old_root = scene.objects['Office • Name card / interactive assembly']
contact_name,contact_url = old_root['contact_name'],old_root['contact_url']
retained = {o.name:o.matrix_world.copy() for o in scene.objects
            if o not in collections['10'].objects[:] and o.name not in camera_names}
scene.camera = scene.objects['Office • About office presentation camera']
for obj in list(collections['10'].objects):
    bpy.data.objects.remove(obj,do_unlink=True)
for name in camera_names:
    obj = scene.objects.get(name)
    if obj:
        bpy.data.objects.remove(obj,do_unlink=True)
marker_names = {'01 / Office overview','02 / Name-card zoom preview','03 / Contact details','04 / Hold contact view'}
for marker in list(scene.timeline_markers):
    if marker.name in marker_names:
        scene.timeline_markers.remove(marker)
source = ast.parse((ROOT/'build_office.py').read_text())
names = {'material','link','lines','box','text','camera','apply_name_card_click_hint','build_name_card'}
helpers = ast.Module(body=[n for n in source.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[])
exec(compile(helpers,str(ROOT/'build_office.py'),'exec'),globals())
card = build_name_card(contact_name,contact_url)
bpy.context.view_layer.update()
for name,matrix in retained.items():
    assert scene.objects[name].matrix_world==matrix, f'Unexpected change to {name}'
paper = scene.objects['Office • Name card / paper']
local_size = [max(v.co[i] for v in paper.data.vertices)-min(v.co[i] for v in paper.data.vertices)
              for i in range(3)]
assert all(abs(a-b)<.00001 for a,b in zip(local_size,(.09,.055,.0008)))
assert not any('weighted foot' in o.name or 'front plaque' in o.name or 'rear support' in o.name
               for o in collections['10'].objects)
assert paper.parent.rotation_euler.z>.17
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
