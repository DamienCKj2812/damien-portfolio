"""Animate existing hover cars and create a three-car elevated maglev train.

Run once in the completed walkthrough scene. Camera animation is preserved.
"""
import ast
import math
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path('/home/damienckj/Documents/damien-portfolio/assets/cyber-city')
scene=bpy.context.scene
if 'Walkthrough • camera' not in scene.objects:
    raise RuntimeError('Open the walkthrough scene first.')
if bpy.data.objects.get('Transit • maglev train'):
    raise RuntimeError('Traffic already exists. Edit the traffic curves instead of rebuilding.')
if bpy.context.screen.is_animation_playing:
    bpy.ops.screen.animation_cancel(restore_frame=False)
if bpy.context.object and bpy.context.object.mode!='OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
cyan=bpy.data.materials['City • Electric cyan']
steel=bpy.data.materials['City • Graphite titanium']
frame=bpy.data.materials['City • Facade mullions']
ice=bpy.data.materials['City • Ice blue']
pink=bpy.data.materials['City • Hot magenta']
amber=bpy.data.materials['City • Warm architectural lighting']
source=ast.parse((ROOT/'build_scene.py').read_text())
helpers=ast.Module(body=[node for node in source.body if isinstance(node,ast.FunctionDef)],type_ignores=[])
exec(compile(helpers,str(ROOT/'build_scene.py'),'exec'),globals())

transit=bpy.data.collections.new('12 Transit • maglev & rails');scene.collection.children.link(transit)
paths=bpy.data.collections.new('13 Traffic • editable motion paths');scene.collection.children.link(paths)
current=transit
shell=mat('Maglev • satin silver blue',(.19,.28,.36),.72,.24)
windows=mat('Maglev • continuous cyan windows',(.025,.27,.45),.35,.15,.8)
interior=mat('Maglev • warm passenger compartment',(.8,.45,.18),.15,.4,1.0)

road=scene.objects['Foreground skyway • road surface']
left=(road.matrix_world@road.data.vertices[0].co+road.matrix_world@road.data.vertices[1].co)/2
right=(road.matrix_world@road.data.vertices[-2].co+road.matrix_world@road.data.vertices[-1].co)/2
tangent=(right-left).normalized()
perp=Vector((-tangent.y,tangent.x,0)).normalized()
def road_point(x,lane=.65,lift=.12):
    p=left+(right-left)*((x-left.x)/(right.x-left.x))
    return p+perp*lane+Vector((0,0,lift))

def fcurves(obj):
    action=obj.animation_data.action
    if hasattr(action,'fcurves'):return list(action.fcurves)
    return [curve for layer in action.layers for strip in layer.strips for bag in getattr(strip,'channelbags',[]) for curve in bag.fcurves]

def route(name,points):
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.resolution_u=24;data.use_path=True;data.path_duration=450
    spline=data.splines.new('BEZIER');spline.bezier_points.add(len(points)-1)
    for p,co in zip(spline.bezier_points,points):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
    obj=bpy.data.objects.new(name,data);paths.objects.link(obj);obj.hide_render=True;obj.show_in_front=True
    return obj

def follow(obj,path):
    obj.location=(0,0,0);obj.rotation_euler=(0,0,0)
    constraint=obj.constraints.new('FOLLOW_PATH');constraint.name='Traffic • constant-speed pass';constraint.target=path
    constraint.use_fixed_location=True;constraint.use_curve_follow=True;constraint.forward_axis='FORWARD_X';constraint.up_axis='UP_Z'
    for f,value in [(1,0),(450,1)]:constraint.offset_factor=value;constraint.keyframe_insert(data_path='offset_factor',frame=f)
    for curve in fcurves(obj):
        for key in curve.keyframe_points:key.interpolation='LINEAR'
    return constraint

# Two separate highway lanes: maglev on the far lane, commuter on the near lane.
for lateral in [.65-.36,.65+.36]:
    tube('Maglev • guide rail',[tuple(road_point(x,lateral,.06)) for x in range(-32,33,2)],.025,frame)
for x in range(-32,33,2):
    tube('Maglev • guideway cross tie',[tuple(road_point(x,.65-.46,.035)),tuple(road_point(x,.65+.46,.035))],.018,steel)

train=bpy.data.objects.new('Transit • maglev train',None);transit.objects.link(train)
def attach(obj,parent=train):obj.parent=parent;return obj
for index,cx in enumerate([-3.45,0,3.45]):
    car=bpy.data.objects.new(f'Maglev • carriage {index+1}',None);transit.objects.link(car);car.parent=train;car.location=(cx,0,0)
    def part(obj):return attach(obj,car)
    part(box(f'Carriage {index+1} • streamlined body',(0,0,.78),(3.15,1.12,1.38),shell,.2))
    part(box(f'Carriage {index+1} • roof',(0,0,1.47),(2.83,1.0,.16),steel,.07))
    part(box(f'Carriage {index+1} • magnetic skirt',(0,0,.14),(2.85,.95,.22),steel,.06))
    for side in [-1,1]:
        part(box('Maglev • panoramic window band',(0,side*.567,1.02),(2.7,.025,.53),windows,.03))
        for wx in [-1.03,-.55,-.07,.41,.89]:
            part(box('Maglev • window mullion',(wx,side*.586,1.02),(.035,.025,.55),frame,.006))
        part(tube('Maglev • lower cyan running light',[(-1.35,side*.57,.38),(1.35,side*.57,.38)],.024,cyan))
        part(tube('Maglev • roof edge accent',[(-1.3,side*.5,1.5),(1.3,side*.5,1.5)],.015,ice))
        part(box('Maglev • passenger door',(-.1,side*.589,.73),(.38,.02,1.07),frame,.025))
        part(box('Maglev • door glass',(-.1,side*.607,1.04),(.29,.02,.42),windows,.015))
        part(box('Maglev • warm doorway marker',(-.1,side*.61,1.31),(.26,.02,.035),interior,.008))
    if index==2:
        part(box('Maglev • forward cockpit',(1.39,0,1.05),(.26,.9,.56),windows,.08))
        for y in [-.36,.36]:part(box('Maglev • headlights',(1.59,y,.5),(.035,.18,.07),ice,.018))
        part(box('Maglev • nose',(1.53,0,.52),(.25,1.0,.37),shell,.12))
    if index==0:
        for y in [-.36,.36]:part(box('Maglev • tail lights',(-1.59,y,.6),(.025,.15,.065),pink,.012))
for x in [-1.725,1.725]:attach(box('Maglev • flexible carriage connector',(x,0,.76),(.3,.82,1.12),steel,.05))
train_path=route('Traffic path • maglev highway pass',[tuple(road_point(x,.65,.1)) for x in [-80,-40,0,40,90,170]])
follow(train,train_path)

# Existing cars retain their detailed meshes/materials and gain editable flight routes.
car_routes=[
    ('Aircar 01 • foreground commuter', [(-30,-20,10),(-10,-16,10.4),(12,-13,10.1),(38,-9,11)]),
    ('Aircar 02 • right approaching', [(36,-7,12),(12,-10,12.5),(-12,-13,12.1),(-34,-16,11.6)]),
    ('Aircar 03 • upper transit', [(28,10,31),(12,10,31.4),(-12,10,31.1),(-30,10,32)]),
    ('Aircar 04 • distant', [(-35,23,24),(-12,23,25),(15,23,24.6),(38,23,25.5)]),
]
for name,points in car_routes:
    obj=scene.objects[name]
    path=route('Traffic path • '+name,points);follow(obj,path)
commuter=scene.objects['Skyway vehicle']
path=route('Traffic path • highway commuter',[tuple(road_point(x,-.67,.43)) for x in [52,28,0,-28,-48]])
follow(commuter,path)

# Fill lights follow the two close aircraft without changing the city lighting.
for name,car_name in [('Aircar 01 • fill','Aircar 01 • foreground commuter'),('Aircar 02 • fill','Aircar 02 • right approaching')]:
    lamp=scene.objects.get(name)
    if lamp:
        lamp.parent=scene.objects[car_name];lamp.location=(0,-2,2.5)
        lamp.rotation_euler=(Vector((0,0,.2))-lamp.location).to_track_quat('-Z','Y').to_euler()
scene.timeline_markers.new('Traffic • train crossing foreground',frame=145)
scene.timeline_markers.new('Traffic • hover cars passing',frame=190)
scene.frame_set(1);bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'cyber-city-walkthrough.blend'))
result={'train':train.name,'carriages':3,'animated_vehicles':6,'traffic_paths':len(paths.objects),'train_center_crossing_frame':145,'saved':bpy.data.filepath}
