"""Add a standalone open-door approach and walk-in shot to the existing cabin."""
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'kaze-elevator.blend'))
scene = bpy.context.scene
scene.name = 'KAZE / Open elevator entrance'
col = bpy.data.collections.new('Elevator / Entrance approach')
scene.collection.children.link(col)


def link(name, data):
    obj = bpy.data.objects.new('Elevator / ' + name, data)
    col.objects.link(obj)
    return obj


def box(name, pos, size, mat):
    x, y, z = (s/2 for s in size)
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),(-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)], [],
                      [(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)])
    mesh.materials.append(mat)
    obj = link(name, mesh)
    obj.location = pos
    return obj


def line(name, paths, mat, radius=.0015):
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'
    curve.bevel_depth = radius
    curve.bevel_resolution = 1
    for path in paths:
        s = curve.splines.new('POLY')
        s.points.add(len(path)-1)
        for p, xyz in zip(s.points, path):
            p.co = (*xyz, 1)
    curve.materials.append(mat)
    return link(name, curve)


def text(name, body, pos, size):
    curve = bpy.data.curves.new(name, 'FONT')
    curve.body = body
    curve.size = size
    curve.align_x = 'CENTER'
    curve.align_y = 'CENTER'
    curve.space_character = 1.3
    curve.materials.append(bpy.data.materials['Elevator / Silver lettering'])
    obj = link(name, curve)
    obj.location = pos
    obj.rotation_euler.x = math.pi/2
    return obj


black = bpy.data.materials['Elevator / Graphite wall panels']
floor = bpy.data.materials['Elevator / Reflective obsidian floor']
glass = bpy.data.materials['Elevator / Recessed black glass']
silver = bpy.data.materials['Elevator / Satin chrome rails']
edge = bpy.data.materials['Elevator / Silver hairline']
quiet = bpy.data.materials['Elevator / Subtle construction grid']
glow = bpy.data.materials['Elevator / White perimeter lighting']

# Full-height landing facade masks the retracted door leaves and their pockets.
box('Landing floor', (0,-2.6,-.065), (7,5.2,.13), floor)
for sign in [-1,1]:
    box('Landing facade', (sign*2.325,-.145,1.9), (2.05,.18,3.8), black)
    box('Portal outer chrome trim', (sign*1.325,-.25,1.62), (.055,.045,3.24), silver)
    line('Portal illuminated vertical', [[(sign*1.357,-.278,.04),(sign*1.357,-.278,3.25)]], glow,.002)
    for x in [1.72,2.52,3.1]:
        line('Landing vertical seam', [[(sign*x,-.24,.08),(sign*x,-.24,3.72)]], quiet,.001)
    for z in [.16,1.05,2.8]:
        line('Landing horizontal seam', [[(sign*1.38,-.24,z),(sign*3.3,-.24,z)]], quiet,.001)
box('Landing overdoor lintel',(0,-.145,3.53),(2.6,.18,.54),black)
box('Landing ceiling',(0,-2.6,3.85),(7,5.2,.1),glass)
line('Portal crown',[[(-1.357,-.278,3.25),(1.357,-.278,3.25)]],glow,.002)
line('Portal outer outline',[[(-1.41,-.245,.04),(-1.41,-.245,3.31),(1.41,-.245,3.31),(1.41,-.245,.04)]],edge,.001)
for x in [-2.6,-1.3,0,1.3,2.6]:
    line('Landing floor longitudinal joint',[[(x,-5.15,.004),(x,-.08,.004)]],quiet,.0009)
for y in [-4.8,-3.6,-2.4,-1.2]:
    line('Landing floor cross joint',[[(-3.3,y,.004),(3.3,y,.004)]],quiet,.0009)
text('Landing lift identification','K A J U   /   0 1',(0,-.246,3.57),.07)
text('Landing arrival indicator','01   /   WELCOME',(0,-.246,3.42),.046)
box('Landing call plate',(1.63,-.258,1.4),(.17,.023,.31),glass)
line('Call plate frame',[[(1.545,-.275,1.245),(1.715,-.275,1.245),(1.715,-.275,1.555),(1.545,-.275,1.555),(1.545,-.275,1.245)]],edge)
line('Landing call up arrow',[[(1.603,-.28,1.41),(1.63,-.28,1.44),(1.657,-.28,1.41)],[(1.63,-.28,1.38),(1.63,-.28,1.44)]],glow,.0014)

light = bpy.data.lights.new('Landing soft fill','AREA')
light.energy = 30
light.shape = 'RECTANGLE'
light.size = 3
light.size_y = 2
obj = link('Landing soft fill',light)
obj.location = (0,-2.2,3.6)
obj.rotation_euler = (Vector((0,-.2,1.2))-obj.location).to_track_quat('-Z','Y').to_euler()

# Five-second eye-level movement. Leaves are open for every frame.
data = bpy.data.cameras.new('Entering elevator camera')
cam = link('Entering elevator camera',data)
data.clip_start = .025
data.clip_end = 100
data.lens = 22
scene.camera = cam
scene.render.fps = 30
scene.frame_start = 1
scene.frame_end = 150
keyframes = [
    (1,(-.16,-4.3,1.65),(0,2.3,1.55),22),
    (25,(-.14,-3.85,1.65),(0,2.3,1.55),22),
    (70,(-.07,-1.7,1.658),(0,2.4,1.57),21),
    (110,(0,-.12,1.65),(.03,2.6,1.60),20),
    (135,(.04,.57,1.65),(.04,2.8,1.62),19),
    (150,(.04,.62,1.65),(.04,2.8,1.62),19),
]
for frame,pos,target,lens in keyframes:
    cam.location = pos
    cam.rotation_euler = (Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.keyframe_insert(data_path='location',frame=frame)
    cam.keyframe_insert(data_path='rotation_euler',frame=frame)
    data.lens=lens
    data.keyframe_insert(data_path='lens',frame=frame)
for owner in [cam,data]:
    action = owner.animation_data.action
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:
                        key.interpolation='BEZIER'
                        key.handle_left_type='AUTO_CLAMPED'
                        key.handle_right_type='AUTO_CLAMPED'
for label,frame in [('OPEN DOOR / APPROACH',1),('WALK FORWARD',25),('THRESHOLD',110),('INSIDE / SETTLE',135)]:
    scene.timeline_markers.new(label,frame=frame)
scene.render.resolution_x=1440
scene.render.resolution_y=900
scene.render.resolution_percentage=100
scene.cycles.samples=48
scene.frame_set(1)
scene.render.filepath=str(ROOT/'entrance-approach.png')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'kaze-elevator-entrance.blend'))
for frame,name in [(1,'entrance-approach.png'),(110,'entrance-threshold.png'),(150,'entrance-inside.png')]:
    scene.frame_set(frame)
    scene.render.filepath=str(ROOT/name)
    bpy.ops.render.render(write_still=True)

# Export includes the walk-in camera animation; add browser scene lighting separately.
scene.frame_set(1)
bpy.ops.object.select_all(action='DESELECT')
for obj in list(scene.objects):
    if obj.type in {'CURVE','FONT'}:
        obj.select_set(True)
        bpy.context.view_layer.objects.active=obj
        bpy.ops.object.convert(target='MESH')
        obj.select_set(False)
bpy.ops.export_scene.gltf(filepath=str(ROOT/'kaze-elevator-entrance.glb'),export_format='GLB',
                          use_active_scene=True,export_cameras=True,export_lights=False,
                          export_extras=True,export_animations=True)
(ROOT/'entrance-camera.json').write_text(json.dumps({
    'source':'kaze-elevator-entrance.blend','model':'kaze-elevator-entrance.glb',
    'camera':'Elevator / Entering elevator camera','fps':30,'frames':[1,150],
    'duration_seconds':5,'door_state':'open throughout','eye_height_m':1.65,
    'keyframes':[{'frame':f,'position_blender':p,'position_gltf':[p[0],p[2],-p[1]],'target_blender':t,'lens_mm':l} for f,p,t,l in keyframes],
    'notes':['Camera transforms are baked into the GLB animation.','glTF camera FOV is static; animate focal length from this manifest to reproduce the subtle Blender lens change.','The landing is a self-contained entrance surround for later lobby placement.']
},indent=2)+'\n')
