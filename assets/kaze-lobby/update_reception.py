"""Add reception carpet and slim stair treads without rebuilding the saved lobby."""
import ast
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
scene = bpy.data.scenes['KAZE / Monochrome Atrium']
bpy.context.window.scene = scene
collections = {c.name.split(' • ')[1][:2]:c for c in scene.collection.children
               if c.name.startswith('Lobby • ')}
if '12' not in collections:
    collections['12'] = bpy.data.collections.new('Lobby • 12 Reception carpet')
    scene.collection.children.link(collections['12'])
black = bpy.data.materials['Lobby • Obsidian architecture']
line_mat = bpy.data.materials['Lobby • Fine silver edges']
treads = [o for o in collections['02'].objects if '/ tread ' in o.name]
assert len(treads) in {74,80}
retained = {o.name:o.matrix_world.copy() for o in scene.objects
            if o not in treads and o not in collections['12'].objects[:]}
bpy.context.view_layer.update()
for obj in treads:
    top = max((obj.matrix_world @ Vector(c)).z for c in obj.bound_box)
    obj.scale.z *= .035/obj.dimensions.z
    obj.location.z = top-.0175
    obj['construction'] = 'Slim open-riser tread; no chunky base block'
for obj in list(collections['12'].objects):
    bpy.data.objects.remove(obj,do_unlink=True)
source = ast.parse((ROOT/'build_lobby.py').read_text())
names = {'material','link','lines','box','build_reception_carpet'}
helpers = ast.Module(body=[n for n in source.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[])
exec(compile(helpers,str(ROOT/'build_lobby.py'),'exec'),globals())
carpet = build_reception_carpet()
bpy.context.view_layer.update()
assert all(abs(o.dimensions.z-.035)<.001 for o in treads)
assert abs(carpet.location.y-carpet.dimensions.y/2+12)<.001
assert abs(carpet.location.y+carpet.dimensions.y/2-4.75)<.001
for name,matrix in retained.items():
    assert scene.objects[name].matrix_world == matrix, f'Unexpected change to {name}'
manifest = json.loads((ROOT/'lobby-manifest.json').read_text())
manifest.update(objects=len(scene.objects),stair_tread_thickness_m=.035,
                reception_carpet={'center':list(carpet.location),'dimensions_m':list(carpet.dimensions)})
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
print(json.dumps({'checks':'passed','slim_treads':len(treads),'preserved_objects':len(retained),**manifest}))
