"""Remove automatic close-up playback; add an idle shine cue to the paper card."""
import ast
import json
from pathlib import Path
import sys

import bpy

ROOT = Path(__file__).resolve().parent
scene = bpy.data.scenes['ABOUT / Skyline Office']
bpy.context.window.scene = scene
collections = {c.name.split(' • ')[1][:2]:c for c in scene.collection.children
               if c.name.startswith('Office • ')}
edge = bpy.data.materials['Office • Fine architectural silver']
scene.frame_set(1); bpy.context.view_layer.update()
old_zoom_name = 'Office • Name card contact zoom camera'
retained = {o.name:o.matrix_world.copy() for o in scene.objects
            if o.name!=old_zoom_name and not any(s in o.name for s in ['clickable luminous rim','soft corner glint'])}
scene.camera = scene.objects['Office • About office presentation camera']
old_zoom = scene.objects.get(old_zoom_name)
if old_zoom:
    bpy.data.objects.remove(old_zoom,do_unlink=True)
for obj in list(collections['10'].objects):
    if 'clickable luminous rim' in obj.name or 'soft corner glint' in obj.name:
        bpy.data.objects.remove(obj,do_unlink=True)
source = ast.parse((ROOT/'build_office.py').read_text())
names = {'material','link','lines','apply_name_card_click_hint'}
helpers = ast.Module(body=[n for n in source.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[])
exec(compile(helpers,str(ROOT/'build_office.py'),'exec'),globals())
root = scene.objects['Office • Name card / interactive assembly']
face = scene.objects['Office • Name card / contact face']
settings = apply_name_card_click_hint(root,face)
bpy.context.view_layer.update()
for name,matrix in retained.items():
    assert scene.objects[name].matrix_world==matrix, f'Unexpected change to {name}'
wide = scene.camera
wide_pose = wide.matrix_world.copy()
strengths = []
for frame in [1,46,91,136,180]:
    scene.frame_set(frame); bpy.context.view_layer.update()
    assert scene.camera==wide and wide.matrix_world==wide_pose
    strengths.append(bpy.data.materials['Office • Business card clickable glow'].node_tree.nodes[
        'Principled BSDF'].inputs['Emission Strength'].default_value)
assert strengths[1]>strengths[0]*2
assert root['auto_zoom'] is False
assert scene.objects.get('Office • Contact card focus camera')
manifest_path = ROOT/'office-manifest.json'
manifest = json.loads(manifest_path.read_text())
card = manifest['contact_card']
for key in ['zoom_camera','zoom_frames','timeline_frames']:
    card.pop(key,None)
card.update(settings,interaction_status='Click-triggered contact focus prepared; website interaction planned')
manifest.update(objects=len(scene.objects),active_camera=wide.name,contact_card=card)
manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
scene.frame_set(1)
bpy.ops.object.select_all(action='DESELECT')
wide.select_set(True); bpy.context.view_layer.objects.active = wide
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
if '--render' in sys.argv:
    original = (scene.camera,scene.render.resolution_x,scene.render.resolution_y,scene.render.filepath)
    for camera_name,frame,width,height,filename in [
        (wide.name,46,1440,840,'office-preview.png'),
        ('Office • Contact card focus camera',46,1280,800,'office-name-card.png')]:
        scene.camera = scene.objects[camera_name]; scene.frame_set(frame)
        scene.render.resolution_x = width; scene.render.resolution_y = height
        scene.render.filepath = str(ROOT/filename)
        bpy.ops.render.render(write_still=True)
    scene.camera,scene.render.resolution_x,scene.render.resolution_y,scene.render.filepath = original
    scene.frame_set(1)
print(json.dumps({'checks':'passed','automatic_zoom':False,'active_camera':wide.name,
                  'glow_strengths':strengths,'focus_camera_retained':True}))
