"""Read-only checks for the native swimming rig, attachments and journey isolation."""
import json
from pathlib import Path
import sys

import bpy
from mathutils import Quaternion, Vector

ROOT = Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from fish_motion import FISH_PARTS
from npc_motion import PERIOD

scene = bpy.data.scenes['KAZE / Monochrome Atrium']
assert scene.get('autonomous_fish_period')==PERIOD
roots = [obj for obj in scene.objects if obj.get('fish_part')]
assert len(roots)==7 and all(obj.get('autonomous_lobby') for obj in roots)
assert all(obj.get('loop_frames')==PERIOD for obj in roots)


def frame_at(frame):
    scene.frame_set(frame)
    scene.view_layers[0].update()


def snapshot(frame):
    frame_at(frame)
    return [tuple(value for row in obj.matrix_world for value in row) for obj in roots]


start,end = snapshot(1),snapshot(PERIOD+1)
assert max(abs(a-b) for first,last in zip(start,end) for a,b in zip(first,last))<1e-5

tail = scene.objects['Lobby • Exhibit / lower tail translucent membrane']
tip = min(tail.data.vertices,key=lambda v:v.co.x).co.copy()
eye = scene.objects['Lobby • Exhibit / fish eye and gill']
eye_point = Vector(eye.data.splines[0].points[0].co[:3])
tail_positions,head_positions = [],[]
for frame in range(1,171,4):
    frame_at(frame)
    tail_positions.append(tail.matrix_world@tip)
    head_positions.append(eye.matrix_world@eye_point)
    for part,names in FISH_PARTS.items():
        objects = [scene.objects['Lobby • Exhibit / '+name] for name in names]
        assert all(obj.parent.get('fish_part')==part for obj in objects)
        first = objects[0].matrix_world
        assert all(max(abs(a-b) for ra,rb in zip(first,obj.matrix_world) for a,b in zip(ra,rb))<1e-5
                   for obj in objects[1:]), f'Point/outline separation: {part}'
assert max(p.y for p in tail_positions)-min(p.y for p in tail_positions)>.8
assert max((p-head_positions[0]).length for p in head_positions)>.08

# Compare one-sided velocities at the shared loop boundary to catch a visible
# snap even when endpoint positions happen to be identical.
seam = []
for frame in [1,2,PERIOD,PERIOD+1]:
    frame_at(frame)
    seam.append(tail.matrix_world@tip)
assert ((seam[1]-seam[0])-(seam[3]-seam[2])).length<.025

assert not any('Exhibit / bridge-connected canopy' in obj.name or 'Exhibit / canopy front light' in obj.name for obj in scene.objects)
for name in ['circular projection pedestal','ceiling projection halo','floating lower halos',
             'rear display wall']:
    obj = scene.objects['Lobby • Exhibit / '+name]
    assert not obj.parent and not obj.animation_data

# The camera and R1 door leaves must still reproduce their journey samples.
navigation = json.loads((ROOT/'navigation-camera.json').read_text())
camera = scene.objects[navigation['camera']]
doors = [scene.objects[f'Lobby • Elevator R1 / {side} door leaf'] for side in ['left','right']]
for frame in [1,120,320,420,510,690,840,900,990,1020]:
    frame_at(frame)
    sample = navigation['samples'][frame-1]
    assert (camera.matrix_world.translation-Vector(sample['position'])).length<1e-4
    assert abs(camera.matrix_world.to_quaternion().dot(Quaternion(sample['quaternion_wxyz'])))>1-1e-6
    assert max(abs(obj.location.x-x) for obj,x in zip(doors,sample['R1_door_local_x']))<1e-4
frame_at(1)
print({'fish_parts':len(FISH_PARTS),'tail_swing_m':max(p.y for p in tail_positions)-min(p.y for p in tail_positions),
       'points_and_outlines_attached':True,'seamless_loop':True,'projector_static':True,
       'camera_and_doors_unchanged':True})
