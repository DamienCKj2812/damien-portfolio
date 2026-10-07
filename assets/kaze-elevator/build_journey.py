"""Blender-only entry, level-selection, door-opening, and exit choreography."""
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'kaze-elevator-interactive.blend'))
scene = bpy.context.scene
scene.name = 'KAZE / Enter - choose - exit'
scene.frame_start = 1
scene.frame_end = 180
scene.render.fps = 30
col = bpy.data.collections.new('Elevator / Journey staging')
scene.collection.children.link(col)
black = bpy.data.materials['Elevator / Graphite wall panels']
white = bpy.data.materials['Elevator / Silver lettering']
edge = bpy.data.materials['Elevator / Silver hairline']


def link(name, data, group=col):
    obj = bpy.data.objects.new('Elevator / '+name, data)
    group.objects.link(obj)
    return obj


def text(name, body, position, size, group):
    data = bpy.data.curves.new(name, 'FONT')
    data.body = body
    data.size = size
    data.align_x = 'CENTER'
    data.align_y = 'CENTER'
    data.space_character = 1.2
    data.space_line = 1.4
    data.materials.append(white)
    obj = link(name, data, group)
    obj.location = position
    obj.rotation_euler = (math.pi/2, 0, math.pi)
    return obj


def outline(name, coords, group=col):
    data = bpy.data.curves.new(name, 'CURVE')
    data.dimensions = '3D'
    data.bevel_depth = .0018
    data.bevel_resolution = 1
    spline = data.splines.new('POLY')
    spline.points.add(len(coords)-1)
    for p, xyz in zip(spline.points, coords): p.co = (*xyz, 1)
    data.materials.append(edge)
    return link(name, data, group)


# Neutral arrival landing; the selected destination's sign is revealed on exit.
mesh = bpy.data.meshes.new('Destination landing end wall')
mesh.from_pydata([(-3.5,-5.18,0),(3.5,-5.18,0),(3.5,-5.18,3.8),(-3.5,-5.18,3.8)],[],[(0,3,2,1)])
mesh.materials.append(black)
link('Destination landing end wall', mesh)
outline('Arrival wall inset',[(-2.4,-5.16,.25),(2.4,-5.16,.25),(2.4,-5.16,3.35),(-2.4,-5.16,3.35),(-2.4,-5.16,.25)])
for x in [-3,-1.2,1.2,3]:
    outline('Arrival vertical reveal',[(x,-5.16,.05),(x,-5.16,3.75)])
levels = json.loads((ROOT/'elevator-levels.json').read_text())['levels']
for level in levels:
    group = bpy.data.collections.new('Elevator / Destination / '+level['id'])
    scene.collection.children.link(group)
    text('Arrival level '+level['id'],f"LEVEL {level['number']:02} / KAJU",(0,-5.13,2.50),.075,group)
    title = level['title'].replace(' & ', ' &\n')
    text('Arrival destination '+level['id'],title,(0,-5.13,2.0),.16 if level['id']=='experience' else .22,group)
    text('Arrival welcome '+level['id'],'WELCOME / YOUR NEXT CHAPTER',(0,-5.13,1.43),.05,group)
    group.hide_viewport = True
    group.hide_render = True
light_data = bpy.data.lights.new('Arrival landing overhead', 'AREA')
light_data.energy = 45
light_data.shape = 'RECTANGLE'
light_data.size = 3
light_data.size_y = 1.5
light = link('Arrival landing overhead', light_data)
light.location = (0,-3.8,3.5)
light.rotation_euler = (Vector((0,-5.1,1.6))-light.location).to_track_quat('-Z','Y').to_euler()

camera_data = bpy.data.cameras.new('Full journey camera')
cam = link('Full journey camera', camera_data)
camera_data.lens = 21
camera_data.clip_start = .025
camera_data.clip_end = 80
cam.rotation_mode = 'XYZ'
# Euler yaw is deliberately unwrapped: a continuous right-hand turn, never a flip.
# Constant focal length avoids a zoom sensation while walking.
path = [
    (1,(-.12,-4.25,1.65),-.018,1.55),
    (24,(-.12,-3.95,1.65),-.018,1.55),
    (90,(-.10,-1.30,1.65),-.03,1.56),
    (142,(-.13,.64,1.65),-.10,1.57),
    (170,(-.18,1.53,1.65),-1.25,1.57),
    (180,(-.18,1.55,1.65),-1.25,1.57),
    (181,(-.18,1.55,1.65),-1.25,1.57),
    (220,(-.18,1.55,1.65),-1.25,1.57),
    (242,(-.18,1.55,1.65),-1.64,1.57),
    (268,(-.14,1.55,1.65),-2.56,1.57),
    (296,(-.08,1.55,1.65),-math.pi,1.57),
    (350,(-.08,1.55,1.65),-math.pi,1.57),
    (370,(-.08,1.55,1.65),-math.pi,1.57),
    (414,(-.06,-.10,1.65),-math.pi,1.57),
    (468,(0,-2.30,1.65),-math.pi,1.62),
    (500,(0,-3.01,1.65),-math.pi,1.67),
    (510,(0,-3.05,1.65),-math.pi,1.67),
]
for frame, position, yaw, pitch in path:
    cam.location = position
    cam.rotation_euler = (pitch,0,yaw)
    cam.keyframe_insert(data_path='location',frame=frame)
    cam.keyframe_insert(data_path='rotation_euler',frame=frame)


def smooth(obj):
    for layer in obj.animation_data.action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:
                        key.interpolation = 'BEZIER'
                        key.handle_left_type = 'AUTO_CLAMPED'
                        key.handle_right_type = 'AUTO_CLAMPED'


smooth(cam)
for door in [bpy.data.objects['Elevator / Left sliding door'],bpy.data.objects['Elevator / Right sliding door']]:
    for frame, state in [(1,'open'),(181,'open'),(220,'closed'),(296,'closed'),(300,'closed'),(350,'open'),(510,'open')]:
        door.location.x = door[state+'_x']
        door.keyframe_insert(data_path='location',index=0,frame=frame)
    smooth(door)
    # Internal stainless leading-edge reveal, parented to each moving leaf.
    sign = 1 if door['closed_x'] < 0 else -1
    rail = outline('Moving door leading edge',[(sign*.575,.023,-1.50),(sign*.575,.023,1.50)])
    rail.parent = door

# Direct departure mode: retain old dialog geometry but keep it out of the shot.
for level in levels:
    group = bpy.data.collections['Elevator / Dialog / '+level['id']]
    for obj in group.objects:
        if 'Selected floor highlight' in obj.name:
            obj['level_id'] = level['id']
            continue
        for frame, hidden in [(1,True),(510,True)]:
            obj.hide_render = hidden
            obj.hide_viewport = hidden
            obj.keyframe_insert(data_path='hide_render',frame=frame)
            obj.keyframe_insert(data_path='hide_viewport',frame=frame)

scene.timeline_markers.clear()
for name,frame in [('ENTER / OPEN DOORS',1),('THRESHOLD IN',116),('CHOOSE A LEVEL / WAIT',180),('SELECTION / DOORS CLOSE',181),('TURN TO EXIT',221),('DOORS OPEN',300),('WALK OUT',370),('THRESHOLD OUT',414),('ARRIVE / STOP',510)]:
    scene.timeline_markers.new(name, frame=frame)
controls = (ROOT/'elevator_controls.py').read_text()
embedded = bpy.data.texts['KAZE_Elevator_Controls.py']
embedded.clear()
embedded.write(controls)
ns = {'__name__':'__main__'}
exec(compile(controls,'KAZE_Elevator_Controls.py','exec'),ns)
ns['show_level'](scene,None)
scene.camera = cam
scene['floor_picking_enabled'] = False
scene['journey_entry_range'] = [1,180]
scene['journey_exit_range'] = [181,510]
scene['review_instructions'] = 'Run embedded controls. Replay entry stops at frame 180. Select any floor to play its departure: turn, doors open, walk out.'
scene.frame_set(1)
scene.render.resolution_x = 1440
scene.render.resolution_y = 900
scene.cycles.samples = 24
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
scene.render.filepath = str(ROOT/'journey-entry.png')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'kaze-elevator-journey.blend'))
ns['show_level'](scene,'projects')
scene.camera = cam
for frame,filename in [(180,'journey-selection.png'),(296,'journey-facing-doors.png'),(350,'journey-doors-open.png'),(414,'journey-walkout.png'),(510,'journey-arrival.png')]:
    scene.frame_set(frame)
    scene.render.filepath = str(ROOT/filename)
    bpy.ops.render.render(write_still=True)
(ROOT/'journey-camera.json').write_text(json.dumps({
    'source':'kaze-elevator-journey.blend','camera':cam.name,'fps':30,
    'entry_frames':[1,180],'departure_frames':[181,510],
    'door_close_frames':[181,220],'turn_frames':[221,296],'door_open_frames':[300,350],
    'walkout_frames':[370,510],'eye_height_m':1.65,'lens_mm':21,
    'level_ids':[level['id'] for level in levels],
    'keyframes':[{'frame':f,'position_blender':p,'rotation_euler_blender':[pitch,0,yaw]} for f,p,yaw,pitch in path],
    'notes':['Standalone Blender review; the browser connects the four authored room packages.','Entry pauses at the selection frame. Selecting any floor starts the same smooth exit choreography with its own arrival sign.','Neutral destination landing is a review staging area.']
},indent=2)+'\n')
