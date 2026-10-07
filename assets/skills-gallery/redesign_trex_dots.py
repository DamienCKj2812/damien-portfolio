"""Redesign the existing sculpture as dots, preserving scale and visitor paths."""
import ast
import importlib.util
import json
import math
from pathlib import Path

import bpy
from mathutils import Euler, Vector

ROOT = Path(__file__).resolve().parent
scene = bpy.data.scenes['SKILLS / Technology Gallery']
bpy.context.window.scene = scene
collections = {c.name.split(' • ')[1][:2]:c for c in scene.collection.children
               if c.name.startswith('Gallery • ')}
black = bpy.data.materials['Gallery • Black architectural backing']
edge = bpy.data.materials['Gallery • Fine silver feature lines']
type_mat = bpy.data.materials['Gallery • Silver exhibit typography']
particle_mat = bpy.data.materials['Gallery • Lobby-style white surface particles']
source = ast.parse((ROOT/'build_gallery.py').read_text())
names = {'material','link','point_display','smooth_keys','gaze_target','solve_knee',
         'set_segment','gait_foot','pose_visitor','bake_gallery_visitors','validate_gallery_visitors'}
helpers = ast.Module(body=[n for n in source.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[])
exec(compile(helpers,str(ROOT/'build_gallery.py'),'exec'),globals())
manifest_path = ROOT/'gallery-manifest.json'
manifest = json.loads(manifest_path.read_text())
sculpture = scene.objects[manifest['centre_exhibit']['root']]
if sculpture.get('dots_only') and not sculpture.get('approved_dimensions_m'):
    # Compatibility with the first dot conversion, before dimensions were stored.
    sculpture['approved_dimensions_m'] = [6.37,1.91,3.938059628009796]
roots = sorted([o for o in collections['05'].objects if o.get('activity')],key=lambda o:o.name)
scene.frame_set(1); bpy.context.view_layer.update()
before = {root.name:[] for root in roots}
for frame in range(1,961):
    scene.frame_set(frame)
    for root in roots:
        before[root.name].append(root.location.copy())
spec = importlib.util.spec_from_file_location('gallery_trex_dots',ROOT/'trex_dots.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
trex = module.convert_to_dots(scene,collections,material,point_display,manifest['centre_exhibit'])
visitors = []
for root,phase,saved in zip(roots,[.11,.47,.27,.61,.83,.39],manifest['visitors']):
    keys = json.loads(root['look_schedule'])
    for entry in keys:
        if abs(entry[1][0]-2.2)<.01 and abs(entry[1][1]-3.35)<.01:
            entry[1][0] = -2.2
    root['look_schedule'] = json.dumps(keys)
    moving = bool(root.get('route_frames'))
    if moving:
        action = root.animation_data.action
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in list(bag.fcurves):
                        if curve.data_path=='rotation_euler':
                            bag.fcurves.remove(curve)
    parts = {o['joint']:o for o in root.children if o.get('joint')}
    for obj in parts.values():
        obj.animation_data_clear()
    scene.frame_set(1)
    toward = Vector(keys[0][1])-root.location
    heading = math.atan2(toward.x,-toward.y) if moving else root.rotation_euler.z
    if moving:
        root.rotation_euler.z = heading
    visitors.append({'root':root,'parts':parts,'activity':root['activity'],
                     'idle_activity':saved['idle_pose'],'phase':phase,'route':moving,
                     'look_keys':keys,'previous_position':None,'travel_distance':0,
                     'gait_distance':0,'heading_value':heading})
positions = bake_gallery_visitors(visitors)
validate_gallery_visitors(visitors,positions)
for name,path in positions.items():
    assert max((Vector(p)-old).length for p,old in zip(path,before[name]))<.001
manifest.update(centre_exhibit=trex,objects=len(scene.objects),
                particle_count=sum(o.get('particle_count',0) for o in scene.objects if not o.hide_render))
manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
scene['Design reference'] = 'Monochrome skills gallery; organic dot-only T-Rex, no visible dinosaur wire or solid surfaces.'
scene.frame_set(300); scene.camera = scene.objects['Gallery • Skills gallery presentation camera']
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print(json.dumps({'checks':'passed','dot_sculpture':trex,'visitor_paths_preserved':True}))
