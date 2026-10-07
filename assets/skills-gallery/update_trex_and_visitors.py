"""Replace the globe and update visitor motion in the existing main gallery file."""
import ast
import json
import math
from pathlib import Path
import random
import sys

import bpy
from mathutils import Euler, Vector

ROOT = Path(__file__).resolve().parent
scene = bpy.data.scenes['SKILLS / Technology Gallery']
bpy.context.window.scene = scene
collections = {c.name.split(' • ')[1][:2]:c for c in scene.collection.children
               if c.name.startswith('Gallery • ')}
if scene.objects.get('Gallery • T-Rex / centre sculpture'):
    raise RuntimeError('The updated sculpture already exists; edit the main file or intentionally rebuild.')
if '08' not in collections:
    collections['08'] = bpy.data.collections.new('Gallery • 08 T-Rex centre exhibit')
    scene.collection.children.link(collections['08'])
black = bpy.data.materials['Gallery • Black architectural backing']
graphite = bpy.data.materials['Gallery • Exhibit graphite']
edge = bpy.data.materials['Gallery • Fine silver feature lines']
white = bpy.data.materials['Gallery • Luminous exhibit borders']
type_mat = bpy.data.materials['Gallery • Silver exhibit typography']
particle_mat = bpy.data.materials['Gallery • Lobby-style white surface particles']
old_prefixes = ('Gallery • Central skill pedestal','Gallery • Pedestal luminous base',
                'Gallery • Pedestal manifesto','Gallery • Central globe /','Gallery • Triangulated wire globe')
changed_cameras = {'Gallery • Visitor activity camera'}
roots = sorted([o for o in collections['05'].objects if o.get('activity')],key=lambda o:o.name)
assert len(roots)==6
scene.frame_set(1); bpy.context.view_layer.update()
retained = {o.name:o.matrix_world.copy() for o in scene.objects
            if o not in collections['05'].objects[:] and not o.name.startswith(old_prefixes)
            and o.name not in changed_cameras and o.name!='Gallery • Sculpture / anchor'}
for obj in list(scene.objects):
    if obj.name.startswith(old_prefixes):
        bpy.data.objects.remove(obj,do_unlink=True)
source = ast.parse((ROOT/'build_gallery.py').read_text())
names = {'material','link','lines','box','text','circle_xz','point_display','build_legacy_wire_trex','build_trex_exhibit',
         'smooth_keys','configure_gallery_visitors','gaze_target','solve_knee','set_segment',
         'gait_foot','pose_visitor','bake_gallery_visitors','validate_gallery_visitors','camera'}
helpers = ast.Module(body=[n for n in source.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[])
exec(compile(helpers,str(ROOT/'build_gallery.py'),'exec'),globals())
trex = build_trex_exhibit()
visitors = []
for root,phase in zip(roots,[.11,.47,.27,.61,.83,.39]):
    parts = {o['joint']:o for o in root.children if o.get('joint')}
    assert len(parts)==15
    visitors.append({'root':root,'parts':parts,'activity':root['activity'],'phase':phase})
configure_gallery_visitors(visitors)
scene.frame_start = 1; scene.frame_end = 960; scene.render.fps = 30
positions = bake_gallery_visitors(visitors)
validate_gallery_visitors(visitors,positions)
reader_camera = scene.objects['Gallery • Visitor activity camera']
reader_camera.location = (-2.7,7.5,2.3)
reader_camera.rotation_euler = (Vector((-5.4,5.9,1.40))-reader_camera.location).to_track_quat('-Z','Y').to_euler()
reader_camera.data.lens = 30
camera('T-Rex sculpture detail camera',(-.70,-1.80,2.85),(-.15,3.85,2.45),24)
scene.objects['Gallery • Sculpture / anchor'].location = (0,3.85,2.45)
old_marker_labels = {'01 / Enter the skills gallery','02 / Visitors exploring',
                     '03 / Walking visitors pause to inspect','04 / Left visitor resumes',
                     '05 / Right visitor resumes','06 / Turn at route ends',
                     '07 / Visitors return','08 / Seamless activity loop'}
for marker in list(scene.timeline_markers):
    if marker.name in old_marker_labels:
        scene.timeline_markers.remove(marker)
for frame,label in [(1,'01 / Enter the T-Rex skills gallery'),(130,'02 / Pause at wall art'),
                    (300,'03 / Visitors circulate'),(425,'04 / Dinosaur viewing'),
                    (685,'05 / Exhibit readers return'),(880,'06 / Walkers return'),
                    (960,'07 / Seamless activity loop')]:
    scene.timeline_markers.new(label,frame=frame)
scene.frame_set(1); bpy.context.view_layer.update()
for name,matrix in retained.items():
    assert scene.objects[name].matrix_world==matrix, f'Unexpected change to {name}'
assert not any('globe' in o.name.lower() for o in scene.objects)
assert sum(bool(v['route']) for v in visitors)==4
scene['Design reference'] = 'Monochrome technology museum; illuminated skill panels, large T-Rex sculpture, reflective floor.'
manifest_path = ROOT/'gallery-manifest.json'
manifest = json.loads(manifest_path.read_text())
manifest.update(objects=len(scene.objects),centre_exhibit=trex,moving_people=4,
                frames=[1,960],duration_s=32,saved_frame=300,
                particle_count=sum(o.get('particle_count',0) for o in scene.objects),
                visitors=[{'root':v['root'].name,'activity':v['root']['activity'],
                           'idle_pose':v['idle_activity'],'route_frames':list(v['root']['route_frames'])} for v in visitors])
manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
scene.camera = scene.objects['Gallery • Skills gallery presentation camera']
scene.frame_set(300)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
if '--render' in sys.argv:
    original = (scene.camera,scene.render.resolution_x,scene.render.resolution_y,scene.render.filepath)
    for camera_name,frame,width,height,filename in [
        ('Gallery • Skills gallery presentation camera',300,1440,1080,'gallery-preview.png'),
        ('Gallery • T-Rex sculpture detail camera',480,1440,960,'gallery-trex.png'),
        ('Gallery • Gallery architectural overview camera',300,1440,960,'gallery-overview.png'),
        ('Gallery • Visitor activity camera',300,1200,900,'gallery-visitors.png')]:
        scene.camera = scene.objects[camera_name]; scene.frame_set(frame)
        scene.render.resolution_x = width; scene.render.resolution_y = height
        scene.render.filepath = str(ROOT/filename)
        bpy.ops.render.render(write_still=True)
    scene.camera,scene.render.resolution_x,scene.render.resolution_y,scene.render.filepath = original
    scene.frame_set(300)
print(json.dumps({'checks':'passed','trex':trex,'moving_visitors':4,'frames':[1,960],
                  'preserved_objects':len(retained)}))
