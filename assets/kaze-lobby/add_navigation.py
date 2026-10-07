"""Navigation stage of rebuild_lobby.py: animate the freshly generated lobby.

The rebuild entrypoint runs this in memory before saving the single main file.
"""
import bisect
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parent
scene = bpy.data.scenes['KAZE / Monochrome Atrium']
bpy.context.window.scene = scene
if scene.objects.get('Lobby • Navigation / walkthrough camera'):
    raise RuntimeError('Navigation already exists. Use rebuild_lobby.py for a full intentional rebuild.')
group = bpy.data.collections.new('Lobby • 14 Navigation / entrance to elevator')
scene.collection.children.link(group)

# Positions in world-space meters. The camera remains outside the elevator.
ROUTE = [
    (1,(0,-11.6,1.735)), (60,(0,-11.6,1.735)),
    (120,(0,-8,1.735)), (190,(.2,-4.8,1.735)),
    (260,(.2,-1.7,1.735)), (320,(3.6,.7,1.70)),
    (380,(5.55,3.6,1.70)), (440,(6.1,6.35,1.70)),
    (490,(6.85,8.5,1.72)), (510,(6.85,9.3,1.88)),
    (690,(6.85,18.65,7.82)), (720,(6.85,19.5,7.82)),
    (775,(5.6,20.65,7.82)), (840,(4.05,21.45,7.82)),
    (1020,(4.05,21.45,7.82)),
]
LOOK = [
    (1,(0,6.9,9.0)), (100,(0,6.9,8.3)), (220,(0,3.7,3.8)),
    (300,(0,3.7,2.3)), (370,(6.85,10,3.5)),
    (490,(6.85,17,6.7)), (510,(6.85,20,8.0)),
    (648,(6.85,23.4,8.3)), (690,(6.2,24,8.3)),
    (775,(4.05,23.965,8.0)), (840,(4.05,23.965,7.90)),
    (1020,(4.05,23.965,7.90)),
]
LENS = [(1,(16,0)),(440,(16,0)),(510,(15,0)),(690,(15,0)),
        (840,(14,0)),(1020,(14,0))]
FPS = 30
END = 1020
DOORS_BEGIN = 900
DOORS_OPEN = 990


def pchip(keys, frame, straight_segment=None):
    """Monotone cubic interpolation: smooth travel without path overshoot."""
    times = [k[0] for k in keys]
    values = [Vector(k[1]) for k in keys]
    if frame <= times[0]:
        return values[0]
    if frame >= times[-1]:
        return values[-1]
    i = bisect.bisect_right(times,frame)-1
    h = times[i+1]-times[i]
    t = (frame-times[i])/h
    if straight_segment == (times[i],times[i+1]):
        return values[i].lerp(values[i+1],t)

    def tangent(index):
        if index in [0,len(times)-1]:
            return Vector([0]*len(values[0]))
        hp = times[index]-times[index-1]
        hn = times[index+1]-times[index]
        dp = (values[index]-values[index-1])/hp
        dn = (values[index+1]-values[index])/hn
        w1,w2 = 2*hn+hp,hn+2*hp
        return Vector([0 if a*b<=0 else (w1+w2)/(w1/a+w2/b) for a,b in zip(dp,dn)])

    m0,m1 = tangent(i),tangent(i+1)
    return ((2*t**3-3*t*t+1)*values[i] + (t**3-2*t*t+t)*h*m0
            + (-2*t**3+3*t*t)*values[i+1] + (t**3-t*t)*h*m1)


def new_object(name,data=None):
    obj = bpy.data.objects.new('Lobby • Navigation / '+name,data)
    group.objects.link(obj)
    return obj


def key_interpolation(owner,mode):
    action = owner.animation_data.action
    curves = []
    if hasattr(action,'layers'):
        for layer in action.layers:
            for strip in layer.strips:
                if hasattr(strip,'channelbags'):
                    for bag in strip.channelbags:
                        curves.extend(bag.fcurves)
    elif hasattr(action,'fcurves'):
        curves.extend(action.fcurves)
    for curve in curves:
        for key in curve.keyframe_points:
            key.interpolation = mode
            if mode=='BEZIER':
                key.handle_left_type = 'AUTO_CLAMPED'
                key.handle_right_type = 'AUTO_CLAMPED'


def black_box(name,center,size):
    x,y,z = (s/2 for s in size)
    verts = [(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),
             (-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)]
    faces = [(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)]
    mesh = bpy.data.meshes.new('Lobby • Navigation / '+name)
    mesh.from_pydata(verts,[],faces)
    mesh.materials.append(bpy.data.materials['Lobby • Obsidian architecture'])
    obj = new_object(name,mesh); obj.location = center
    return obj


camera_data = bpy.data.cameras.new('Lobby • Navigation / camera data')
camera = new_object('walkthrough camera',camera_data)
camera_data.clip_start = .06; camera_data.clip_end = 120
camera_data.dof.use_dof = False
target = new_object('animated look target')
target.empty_display_type = 'SPHERE'; target.empty_display_size = .12
track = camera.constraints.new('TRACK_TO')
track.target = target; track.track_axis = 'TRACK_NEGATIVE_Z'; track.up_axis = 'UP_Y'
track.name = 'Navigation / follow animated look target'

positions = []
for frame in range(1,END+1):
    pos = pchip(ROUTE,frame,straight_segment=(510,690))
    camera.location = pos
    target.location = pchip(LOOK,frame)
    camera_data.lens = pchip(LENS,frame)[0]
    camera.keyframe_insert(data_path='location',frame=frame,group='Eye-level route')
    target.keyframe_insert(data_path='location',frame=frame,group='Look direction')
    camera_data.keyframe_insert(data_path='lens',frame=frame)
    positions.append(pos.copy())
for owner in [camera,target,camera_data]:
    key_interpolation(owner,'LINEAR')

# A non-rendering route guide and timed waypoint markers make inspection easy.
curve = bpy.data.curves.new('Lobby • Navigation / route guide','CURVE')
curve.dimensions = '3D'
spline = curve.splines.new('POLY'); spline.points.add(len(positions[::10])-1)
for point,pos in zip(spline.points,positions[::10]):
    point.co = (*pos,1)
guide = new_object('route guide',curve); guide.hide_render = True
guide.show_in_front = True
for index,(frame,pos) in enumerate(ROUTE):
    waypoint = new_object('waypoint %02d / frame %04d' % (index+1,frame))
    waypoint.location = pos; waypoint.empty_display_type = 'PLAIN_AXES'
    waypoint.empty_display_size = .25; waypoint['frame'] = frame

# R1 door edges are separate curve objects; parent them to the sliding leaves so
# their outlines move with the solid door geometry.
doors = []
for side,label in [(-1,'left'),(1,'right')]:
    door = scene.objects['Lobby • Elevator R1 / '+label+' door leaf']
    edge = scene.objects['Lobby • Elevator R1 / '+label+' door leaf / feature edges']
    bpy.context.view_layer.update()
    edge_world = edge.matrix_world.copy()
    edge.parent = door
    edge.matrix_parent_inverse = door.matrix_world.inverted()
    edge.matrix_world = edge_world
    closed = door.location.copy()
    for frame,slide in [(1,0),(DOORS_BEGIN,0),(DOORS_OPEN,1.08),(END,1.08)]:
        door.location = closed+Vector((side*slide,0,0))
        door.keyframe_insert(data_path='location',frame=frame,group='R1 / sliding door')
    key_interpolation(door,'BEZIER')
    door['navigation_closed_position'] = list(closed)
    doors.append(door)

# Front pockets conceal the leaves after they slide out of the aperture.
# Black backing deliberately leaves the future interior undefined.
for side in [-1,1]:
    black_box('R1 door pocket '+('left' if side<0 else 'right'),
              (4.05+side*1.61,23.89,7.66),(1.14,.055,3.10))
scene.objects['Lobby • Elevator R1 / portal'].location.y -= .06
backing = black_box('R1 interior handoff / black backing',(4.05,23.999,7.66),(2.12,.001,3.08))
void_material = bpy.data.materials.new('Lobby • Navigation / undefined interior black')
void_material.use_nodes = True
nodes = void_material.node_tree.nodes; nodes.clear()
output = nodes.new('ShaderNodeOutputMaterial')
emission = nodes.new('ShaderNodeEmission')
emission.inputs['Color'].default_value = (0,0,0,1)
void_material.node_tree.links.new(emission.outputs['Emission'],output.inputs['Surface'])
backing.data.materials.clear(); backing.data.materials.append(void_material)
# Remove the decorative static seam when the actual leaves separate.
seam = scene.objects['Lobby • Elevator R1 / center door seam']
for frame,hidden in [(1,False),(DOORS_BEGIN,False),(DOORS_BEGIN+1,True),(END,True)]:
    seam.hide_render = hidden; seam.hide_viewport = hidden
    seam.keyframe_insert(data_path='hide_render',frame=frame)
    seam.keyframe_insert(data_path='hide_viewport',frame=frame)
# All landing indicators share a baseline above the portal, including the R1
# handoff entrance. Raising only R1 made it visibly disagree with its neighbours.
for lift in ['L1', 'L2', 'R1', 'R2']:
    scene.objects[f'Lobby • Elevator {lift} / floor display'].location.z = 9.40

scene.camera = camera
scene.render.fps = FPS
scene.frame_start = 1; scene.frame_end = END
scene.render.resolution_x = 1280; scene.render.resolution_y = 800
scene.render.resolution_percentage = 100
for frame,label in [(1,'01 / Entrance view'),(60,'02 / Begin walking'),
                    (320,'03 / Pass reception on right'),(510,'04 / Board right escalator'),
                    (690,'05 / Upper landing'),(840,'06 / Stop outside R1'),
                    (DOORS_BEGIN,'07 / R1 doors opening'),(DOORS_OPEN,'08 / R1 doors fully open'),
                    (END,'09 / Interior-agent handoff')]:
    scene.timeline_markers.new(label,frame=frame)

# Clearance validation against solid meshes, with broad-phase bounds to avoid
# unnecessary geometry tests. Curves and particle point sources are decorative.
scene.frame_set(1); bpy.context.view_layer.update()
obstacles = []
for obj in scene.objects:
    if obj.type!='MESH' or not obj.data.polygons or obj in doors:
        continue
    verts = [obj.matrix_world @ v.co for v in obj.data.vertices]
    lo = Vector([min(v[i] for v in verts) for i in range(3)])
    hi = Vector([max(v[i] for v in verts) for i in range(3)])
    polygons = [list(p.vertices) for p in obj.data.polygons]
    obstacles.append((obj.name,lo,hi,BVHTree.FromPolygons(verts,polygons)))
clearance_issues = []
radius = .10
for frame,pos in enumerate(positions,1):
    for name,lo,hi,tree in obstacles:
        if all(lo[i]-radius<=pos[i]<=hi[i]+radius for i in range(3)):
            nearest,normal,_,distance = tree.find_nearest(pos)
            if nearest is not None and (distance<radius or (pos-nearest).dot(normal)<-.0001):
                clearance_issues.append({'frame':frame,'object':name,'distance':distance})
                break
assert not clearance_issues, f'Camera clearance failure: {clearance_issues[:5]}'
assert positions[-1].y<23.90-1.5
assert all(abs(p.x-6.85)<.001 for p in positions[509:690])
assert all((p-positions[839]).length<.001 for p in positions[839:])

# Bake evaluated transforms for portable navigation and the next agent's handoff.
samples = []
for frame in range(1,END+1):
    scene.frame_set(frame); bpy.context.view_layer.update()
    matrix = camera.matrix_world
    samples.append({'frame':frame,'time_s':round((frame-1)/FPS,6),
                    'position':list(matrix.translation),'quaternion_wxyz':list(matrix.to_quaternion()),
                    'lens_mm':camera_data.lens,
                    'R1_door_local_x':[door.location.x for door in doors]})
scene.frame_set(END); bpy.context.view_layer.update()
left_edge = doors[0].location.x+.51
right_edge = doors[1].location.x-.51
assert right_edge-left_edge>2.1
final_camera = samples[-1]
angular_steps = []
for previous,current in zip(samples,samples[1:]):
    dot = abs(sum(a*b for a,b in zip(previous['quaternion_wxyz'],current['quaternion_wxyz'])))
    angular_steps.append(2*math.acos(min(1,max(-1,dot))))
assert max(angular_steps)<math.radians(5), 'Abrupt camera rotation detected.'
scene['Navigation route'] = 'Entrance → right of reception → right escalator → R1; stop outside as doors open.'
scene['Navigation handoff'] = 'Frame 1020; R1 open; no interior or threshold crossing.'
payload = {'blend':'kaze-lobby-walkthrough.blend','scene':scene.name,
           'camera':camera.name,'coordinate_system':'Blender meters, +Z up, camera -Z forward / +Y up',
           'fps':FPS,'frame_start':1,'frame_end':END,'duration_s':34,
           'escalator_ride_frames':[510,690],'escalator_ride_duration_s':6,
           'route_waypoints':[{'frame':f,'position':p} for f,p in ROUTE],
           'elevator':'R1','door_opening_frames':[DOORS_BEGIN,DOORS_OPEN],
           'camera_stop_frame':840,'camera_clearance_check':'passed; 0.10m head clearance against solid meshes',
           'max_rotation_degrees_per_frame':math.degrees(max(angular_steps)),
           'handoff':{'frame':END,'camera':final_camera,'door_center':[4.05,23.965,7.66],
                      'threshold_y':23.75,'upper_floor_z':6.12,'interior_designed':False,
                      'note':'Camera stops 2.3m in front of the threshold; continue forward only after adding the interior.'},
           'samples':samples}
(ROOT/'navigation-camera.json').write_text(json.dumps(payload,indent=2)+'\n')
(ROOT/'navigation-handoff.json').write_text(json.dumps({k:v for k,v in payload.items() if k!='samples'},indent=2)+'\n')
manifest_path = ROOT/'lobby-manifest.json'
if manifest_path.exists():
    manifest = json.loads(manifest_path.read_text())
    manifest.update(blend='kaze-lobby-walkthrough.blend',objects=len(scene.objects),
                    camera=camera.name,frames=[1,END],fps=FPS,duration_s=END/FPS)
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
scene.frame_set(1); bpy.context.view_layer.update()
scene.render.filepath = str(ROOT/'navigation-start.png')
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective = 'CAMERA'
            area.spaces.active.region_3d.view_camera_zoom = 18
            area.spaces.active.region_3d.view_camera_offset = (0,0)
            area.spaces.active.overlay.show_overlays = False
bpy.ops.object.select_all(action='DESELECT')
camera.select_set(True); bpy.context.view_layer.objects.active = camera
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'kaze-lobby-walkthrough.blend'))
if '--render' in sys.argv:
    for frame,filename in [(1,'navigation-start.png'),(420,'holographic-fish-walkthrough.png'),
                           (600,'navigation-escalator.png'),
                           (840,'navigation-elevator-arrival.png'),(END,'navigation-elevator-open.png')]:
        scene.frame_set(frame)
        scene.render.filepath = str(ROOT/filename)
        bpy.ops.render.render(write_still=True)
    scene.frame_set(1)
print(json.dumps({'checks':'passed','blend':payload['blend'],'frames':[1,END],
                  'fps':FPS,'door_opening_frames':[DOORS_BEGIN,DOORS_OPEN],
                  'camera_stop_frame':840,'final_position':final_camera['position']}))
