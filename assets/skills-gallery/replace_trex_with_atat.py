"""Explicit sculpture replacement; preserve gallery architecture and animation."""
import importlib.util
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parent
scene = bpy.context.scene
assert scene.name == 'SKILLS / Technology Gallery'
spec = importlib.util.spec_from_file_location('atat_walker', ROOT / 'atat_walker.py')
module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
collection = next(col for col in scene.collection.children if col.name.startswith('Gallery • 08 '))
scene.frame_set(1);scene.view_layers[0].update()

changed_cameras = {'Gallery • T-Rex sculpture detail camera','Gallery • T-Rex dot portrait camera','Gallery • AT-AT walker detail camera'}
sculpture_objects = set(collection.all_objects)
preserved = [obj for obj in scene.objects if obj not in sculpture_objects and not obj.name.startswith('Gallery • T-Rex') and obj.name not in changed_cameras and obj.name != 'Gallery • Sculpture / anchor']


def pose_snapshot(frame):
    scene.frame_set(frame);scene.view_layers[0].update()
    return {obj.as_pointer(): tuple(value for row in obj.matrix_world for value in row) for obj in preserved}


frames = [1, 130, 480, 960, 1650, 2290, 2940]
before = {frame: pose_snapshot(frame) for frame in frames}
scene.frame_set(1);scene.view_layers[0].update()
plinth_objects = []
for obj in list(collection.all_objects):
    if any(label in obj.name.lower() for label in ['plinth','display title','display subtitle']):
        obj.name = obj.name.replace('T-Rex', 'AT-AT')
        if obj.type == 'FONT': obj.data.body = 'A T - A T   W A L K E R' if 'title' in obj.name and 'subtitle' not in obj.name else 'STAR WARS  /  MECHANICAL WALKER'
        plinth_objects.append(obj)
    else:
        bpy.data.objects.remove(obj, do_unlink=True)
for obj in list(scene.objects):
    if obj.name.startswith('Gallery • T-Rex') or obj.name == 'Gallery • AT-AT walker detail camera':
        bpy.data.objects.remove(obj, do_unlink=True)
guides = bpy.data.collections.get('Gallery • T-Rex hidden dot sources')
if guides:
    for obj in list(guides.objects): bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(guides)
collection.name = 'Gallery • 08 AT-AT centre exhibit'
exhibit = module.build_atat_exhibit(scene, collection)
assert exhibit['legs'] == 4 and exhibit['bounds_max'][2] < 5.2
assert exhibit['bounds_max'][2] < 3.85, 'The walker needs clear space beneath the gallery ceiling.'
assert exhibit['bounds_min'][0] > -3.9 and exhibit['bounds_max'][0] < 3.5
assert exhibit['bounds_min'][1] > 2.245 and exhibit['bounds_max'][1] < 5.45
for obj in preserved:
    if obj.name.startswith('Gallery • Visitor /'):
        obj.name = obj.name.replace('T-Rex', 'AT-AT').replace('dinosaur', 'walker')
assert before == {frame: pose_snapshot(frame) for frame in frames}, 'A preserved gallery/camera/visitor transform changed.'

scene.frame_set(1);scene.view_layers[0].update()
data = bpy.data.cameras.new('Gallery • AT-AT walker detail camera')
camera = bpy.data.objects.new('Gallery • AT-AT walker detail camera', data)
camera_collection = next(col for col in scene.collection.children if col.name.startswith('Gallery • 06 '))
camera_collection.objects.link(camera)
camera.location = (-5.2,-4.25,3.1)
focus_height = (exhibit['bounds_min'][2] + exhibit['bounds_max'][2]) / 2
camera.rotation_euler = (Vector((-.40,3.85,focus_height))-camera.location).to_track_quat('-Z','Y').to_euler()
data.lens = 26;data.clip_start = .04;data.clip_end = 100
scene.objects['Gallery • Sculpture / anchor'].location = (0,3.85,focus_height)
stops = json.loads(scene['Gallery tour stops'])
for stop in stops:
    if stop['index'] == 0: stop['label'] = 'AT-AT walker';stop['hint'] = 'Look ahead and around the mechanical walker'
scene['Gallery tour stops'] = json.dumps(stops)
scene['Design reference'] = 'Monochrome technology museum; AT-AT walker matching the supplied white-outline reference.'
for marker in scene.timeline_markers:
    marker.name = marker.name.replace('T-Rex', 'AT-AT').replace('Dinosaur', 'AT-AT walker')
for text in bpy.data.texts:
    body = text.as_string()
    if 'T-Rex' in body or 'dinosaur' in body:
        text.clear();text.write(body.replace('T-Rex', 'AT-AT').replace('dinosaur', 'walker'))
assert not any(obj.name.startswith('Gallery • T-Rex') for obj in scene.objects)
assert sum(bool(obj.get('atat_leg')) for obj in scene.objects) == 4
scene.camera = scene.objects['Gallery • Guided walk / free-look camera']
bpy.context.preferences.filepaths.save_version = 1
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'skills-gallery.blend'))

manifest_path = ROOT / 'gallery-manifest.json'
manifest = json.loads(manifest_path.read_text())
manifest.update(centre_exhibit=exhibit, objects=len(scene.objects), particle_count=sum(obj.get('particle_count',0) for obj in scene.objects))
manifest.pop('dot_portrait_camera', None)
manifest['sculpture_detail_camera'] = camera.name
for visitor in manifest['visitors']: visitor['root'] = visitor['root'].replace('T-Rex','AT-AT').replace('dinosaur','walker')
for stop in manifest['guided_walk']['stops']:
    if stop['index'] == 0: stop['label'] = 'AT-AT walker';stop['hint'] = 'Look ahead and around the mechanical walker'
manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
walk_path = ROOT / 'gallery-walk.json'
walk = json.loads(walk_path.read_text())
for stop in walk['stops']:
    if stop['index'] == 0: stop['label'] = 'AT-AT walker';stop['hint'] = 'Look ahead and around the mechanical walker'
walk_path.write_text(json.dumps(walk, indent=2) + '\n')
print(json.dumps({'exhibit':exhibit, 'gallery_and_visitor_poses_preserved':True, 'guided_frames':scene.frame_end}))
