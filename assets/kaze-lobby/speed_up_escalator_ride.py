"""Compress only the escalator ride in an existing navigation animation."""
import json
import math
from pathlib import Path
import sys

import bpy

ROOT = Path(__file__).resolve().parent
scene = bpy.data.scenes['KAZE / Monochrome Atrium']
bpy.context.window.scene = scene
payload = json.loads((ROOT/'navigation-camera.json').read_text())
assert scene.frame_end==1350, 'This speed pass expects the original 45-second walkthrough.'


def retime(frame):
    if frame<=510:
        return frame
    if frame<=1020:
        return 510+(frame-510)*180/510
    return frame-330


owners = [scene.objects['Lobby • Navigation / walkthrough camera'],
          scene.objects['Lobby • Navigation / animated look target'],
          scene.objects['Lobby • Navigation / walkthrough camera'].data,
          scene.objects['Lobby • Elevator R1 / left door leaf'],
          scene.objects['Lobby • Elevator R1 / right door leaf'],
          scene.objects['Lobby • Elevator R1 / center door seam']]
visited = set()
for owner in owners:
    action = owner.animation_data.action
    if action in visited:
        continue
    visited.add(action)
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:
                        left,right = key.handle_left.x,key.handle_right.x
                        key.co.x = retime(key.co.x)
                        key.handle_left.x = retime(left)
                        key.handle_right.x = retime(right)
                    curve.update()
for marker in scene.timeline_markers:
    marker.frame = round(retime(marker.frame))
for obj in scene.objects:
    if obj.name.startswith('Lobby • Navigation / waypoint '):
        old = obj['frame']; new = round(retime(old))
        obj['frame'] = new
        obj.name = obj.name.replace('frame %04d' % old,'frame %04d' % new)
scene.frame_end = 1020
scene['Navigation handoff'] = 'Frame 1020; R1 open; no interior or threshold crossing.'
camera = scene.objects['Lobby • Navigation / walkthrough camera']
doors = [scene.objects['Lobby • Elevator R1 / '+side+' door leaf'] for side in ['left','right']]
samples = []
for frame in range(1,1021):
    scene.frame_set(frame); bpy.context.view_layer.update()
    matrix = camera.matrix_world
    samples.append({'frame':frame,'time_s':round((frame-1)/30,6),
                    'position':list(matrix.translation),'quaternion_wxyz':list(matrix.to_quaternion()),
                    'lens_mm':camera.data.lens,'R1_door_local_x':[d.location.x for d in doors]})
assert abs(samples[509]['position'][1]-9.3)<.001
assert abs(samples[689]['position'][1]-18.65)<.001
assert abs(samples[-1]['position'][1]-21.45)<.001
assert samples[989]['R1_door_local_x'][1]-samples[989]['R1_door_local_x'][0]>3.18
angles = [2*math.acos(min(1,abs(sum(a*b for a,b in zip(p['quaternion_wxyz'],q['quaternion_wxyz'])))))
          for p,q in zip(samples,samples[1:])]
assert max(angles)<math.radians(5)
payload.update(frame_end=1020,duration_s=34,escalator_ride_frames=[510,690],
               escalator_ride_duration_s=6,camera_stop_frame=840,door_opening_frames=[900,990],
               samples=samples,max_rotation_degrees_per_frame=math.degrees(max(angles)))
for waypoint in payload['route_waypoints']:
    waypoint['frame'] = round(retime(waypoint['frame']))
payload['handoff'].update(frame=1020,camera=samples[-1])
(ROOT/'navigation-camera.json').write_text(json.dumps(payload,indent=2)+'\n')
(ROOT/'navigation-handoff.json').write_text(json.dumps({k:v for k,v in payload.items() if k!='samples'},indent=2)+'\n')
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'kaze-lobby-walkthrough.blend'))
if '--render' in sys.argv:
    scene.frame_set(600)
    scene.render.filepath = str(ROOT/'navigation-escalator.png')
    bpy.ops.render.render(write_still=True)
print(json.dumps({'checks':'passed','escalator_ride_seconds':6,'timeline_frames':[1,1020],
                  'total_seconds':34,'door_opening_frames':[900,990]}))
