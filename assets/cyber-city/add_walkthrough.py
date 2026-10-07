"""Add an editable street-to-lobby camera route to the existing city scene.

Run once in the generated city scene. Saves a separate walkthrough blend.
"""
import ast
import json
import math
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path('/home/damienckj/Documents/damien-portfolio/assets/cyber-city')
scene=bpy.context.scene
if not scene.name.startswith('NEON / Kaze Megacity'):
    raise RuntimeError('Activate the NEON / Kaze Megacity scene first.')
if bpy.data.objects.get('Walkthrough • camera'):
    raise RuntimeError('Walkthrough already exists; edit the existing path instead of rebuilding it.')
if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')

cyan=bpy.data.materials['City • Electric cyan']
source=ast.parse((ROOT/'build_scene.py').read_text())
helpers=ast.Module(body=[n for n in source.body if isinstance(n,ast.FunctionDef)],type_ignores=[])
exec(compile(helpers,str(ROOT/'build_scene.py'),'exec'),globals())
steel=bpy.data.materials['City • Graphite titanium']
frame=bpy.data.materials['City • Facade mullions']
amber=bpy.data.materials['City • Warm architectural lighting']
ice=bpy.data.materials['City • Ice blue']
hero=scene.camera
# Align a uniformly translated exterior to the construction coordinates before
# creating the lobby. Moving only the plaza leaves the entrance detached.
offset=scene.objects['Megatower • central occupied volume'].location-Vector((0,0,24))
if offset.length > .001:
    for col in scene.collection.children:
        if col.name[:2] in ['01','02','03','04','05','06','07','08']:
            for obj in col.objects:
                if obj.parent is None and obj.name!='Rain-soaked city plaza':
                    obj.location-=offset
# Approved ground alignment for the walkthrough copy of the scene.
scene.objects['Rain-soaked city plaza'].location=(0,0,-.12)

lobby=bpy.data.collections.new('09 Lobby • blockout');scene.collection.children.link(lobby)
rig=bpy.data.collections.new('10 Walkthrough • camera rig');scene.collection.children.link(rig)
cutters=bpy.data.collections.new('11 Entrance • non-destructive cutters');scene.collection.children.link(cutters)
current=cutters
room_cut=box('Lobby • room cavity cutter',(0,0,2.12),(11.8,9.9,4.5),steel)
entry_cut=box('Entrance • doorway cutter',(-1.5,-5.35,1.85),(3.4,2.0,4.1),steel)
for obj in [room_cut,entry_cut]:
    obj.display_type='WIRE';obj.hide_render=True;obj.hide_set(True)
def carve(obj,tool,name):
    mod=obj.modifiers.new(name,'BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=tool
carve(scene.objects['Megatower • central occupied volume'],room_cut,'Walkthrough • hollow lobby (editable)')
carve(scene.objects['Megatower • central occupied volume'],entry_cut,'Walkthrough • entrance opening (editable)')
# Clear the doorway through batched facade panes, trims and original lobby lights.
affected=[]
for col_name in ['01 Megatower','07 Street life']:
    for obj in bpy.data.collections[col_name].objects:
        if obj.type=='MESH' and obj.name.startswith(('Batched details','Architectural refinement')):
            carve(obj,entry_cut,'Walkthrough • clear entrance');affected.append(obj.name)

current=lobby
floor_mat=mat('Lobby • honed graphite floor',(.09,.105,.13),.25,.28)
wall_mat=mat('Lobby • placeholder wall',(.11,.13,.17),.12,.5)
ceiling_mat=mat('Lobby • acoustic ceiling',(.04,.055,.08),.1,.6)
door_mat=mat('Lobby • transparent sliding glass',(.18,.3,.37),.05,.08)
p=door_mat.node_tree.nodes.get('Principled BSDF');p.inputs['Transmission Weight'].default_value=.88;p.inputs['IOR'].default_value=1.45
box('Lobby • floor',(0,0,.065),(11.7,9.8,.12),floor_mat,.015)
box('Lobby • ceiling',(0,0,4.3),(11.7,9.8,.12),ceiling_mat,.02)
box('Lobby • left wall',(-5.75,0,2.2),(.15,9.8,4.2),wall_mat,.02)
box('Lobby • right wall',(5.75,0,2.2),(.15,9.8,4.2),wall_mat,.02)
box('Lobby • back wall / future design area',(0,4.82,2.2),(11.7,.15,4.2),wall_mat,.02)
for x in [-4.8,4.8]:
    tube('Lobby • recessed floor guide',[(x,-4.7,.135),(x,4.5,.135)],.012,ice)
    tube('Lobby • ceiling light channel',[(x,-4.65,4.2),(x,4.6,4.2)],.025,amber)
for y in [-3.5,0,3.4]:
    for x in [-3.5,3.5]:
        box('Lobby • ceiling panel',(x,y,4.2),(1.2,.55,.04),amber,.015)
        data=bpy.data.lights.new('Lobby • soft ceiling illumination','AREA');data.energy=110;data.color=(1,.77,.55);data.shape='RECTANGLE';data.size=2;data.size_y=1
        obj=bpy.data.objects.new(data.name,data);lobby.objects.link(obj);obj.location=(x,y,4.1)
for x in [-5.1,5.1]:
    for y in [-3.5,3.5]:box('Lobby • structural column',(x,y,2.1),(.26,.26,4.15),frame,.03)
for x in [-3.24,.24]:box('Entrance • jamb',(x,-5.5,1.8),(.15,.25,3.6),frame,.025)
box('Entrance • header',(-1.5,-5.5,3.6),(3.65,.28,.18),frame,.025)
tube('Entrance • cyan portal outline',[(-3.22,-5.68,.16),(-3.22,-5.68,3.64),(.22,-5.68,3.64),(.22,-5.68,.16)],.025,cyan)
box('Entrance • threshold',(-1.5,-5.4,.08),(3.5,1.2,.08),floor_mat,.015)

# Doors slide sideways before the camera crosses the threshold.
doors=[]
for side in [-1,1]:
    root=bpy.data.objects.new('Entrance • '+('left' if side<0 else 'right')+' sliding door',None);lobby.objects.link(root)
    root.location=(-1.5+side*.81,-5.55,0)
    pane=box('Entrance • glass leaf',(0,0,1.8),(1.6,.04,3.45),door_mat,.012);pane.parent=root
    for x in [-.8,.8]:
        rail=box('Entrance • door edge',(x,0,1.8),(.04,.065,3.5),frame,.008);rail.parent=root
    for z in [.08,3.53]:
        rail=box('Entrance • door edge',(0,0,z),(1.6,.065,.045),frame,.008);rail.parent=root
    for f,slide in [(1,0),(245,0),(300,1.65),(450,1.65)]:
        root.location.x=-1.5+side*(.81+slide);root.keyframe_insert(data_path='location',frame=f)
    doors.append(root)

# Editable Bezier travel path, with a separately animated look target.
points=[(12,-35,1.7),(5,-22,1.7),(-1.5,-14,1.7),(-1.5,-8,1.7),(-1.5,-5.3,1.7),(-1.5,-4.3,1.7),(-.5,-3,1.7)]
data=bpy.data.curves.new('Walkthrough • travel path','CURVE');data.dimensions='3D';data.resolution_u=32;data.path_duration=450;data.use_path=True
spline=data.splines.new('BEZIER');spline.bezier_points.add(len(points)-1)
for point,co in zip(spline.bezier_points,points):
    point.co=co;point.handle_left_type='AUTO';point.handle_right_type='AUTO'
path=bpy.data.objects.new('Walkthrough • editable travel path',data);rig.objects.link(path);path.show_in_front=True;path.hide_render=True
target=bpy.data.objects.new('Walkthrough • look target',None);rig.objects.link(target);target.empty_display_type='SPHERE';target.empty_display_size=.25
for f,loc in [(1,(0,0,50)),(90,(-1.5,-5.3,1.7)),(180,(-1.5,-3,1.7)),(300,(-1.5,-1,1.7)),(380,(0,4.6,1.6)),(450,(0,4.6,1.6))]:
    target.location=loc;target.keyframe_insert(data_path='location',frame=f)
data=bpy.data.cameras.new('Walkthrough • camera');camera=bpy.data.objects.new('Walkthrough • camera',data);rig.objects.link(camera)
data.lens=24;data.clip_start=.05;data.clip_end=250
travel=camera.constraints.new('FOLLOW_PATH');travel.name='Travel • follow editable Bezier route';travel.target=path;travel.use_fixed_location=True;travel.use_curve_follow=False
for f,progress in [(1,0),(90,0),(180,.30),(245,.55),(300,.70),(350,.84),(450,1)]:
    travel.offset_factor=progress;travel.keyframe_insert(data_path='offset_factor',frame=f)
look=camera.constraints.new('TRACK_TO');look.name='Look • animated focus';look.target=target;look.track_axis='TRACK_NEGATIVE_Z';look.up_axis='UP_Y'
scene.render.fps=30;scene.frame_start=1;scene.frame_end=450
for name,f in [('01 • Stationary rooftop view',1),('02 • Looking down / begin walking',90),('03 • Doors opening',245),('04 • Entrance',380),('05 • Inside lobby',410),('06 • Future lobby screen',450)]:
    marker=scene.timeline_markers.new(name,frame=f)
scene.camera=camera

# Bake sampled evaluated camera transforms to portable data for future web use.
samples=[]
crossing=None
for f in range(1,451):
    scene.frame_set(f);bpy.context.view_layer.update();matrix=camera.matrix_world
    samples.append({'frame':f,'position':list(matrix.translation),'quaternion_wxyz':list(matrix.to_quaternion()),'lens_mm':data.lens})
    if crossing is None and matrix.translation.y>=-5.55:crossing=f
for marker in scene.timeline_markers:
    if marker.name.startswith('04 •'):marker.frame=crossing
(ROOT/'walkthrough-camera.json').write_text(json.dumps({'coordinate_system':'Blender Z-up, camera local -Z forward / +Y up','fps':30,'frame_start':1,'frame_end':450,'samples':samples},indent=2))
scene.frame_set(1)
for a in bpy.context.screen.areas:
    if a.type=='VIEW_3D':
        a.spaces.active.region_3d.view_perspective='CAMERA';a.spaces.active.overlay.show_overlays=False;a.spaces.active.shading.type='SOLID'
bpy.ops.object.select_all(action='DESELECT');camera.select_set(True);bpy.context.view_layer.objects.active=camera
scene.render.resolution_x=960;scene.render.resolution_y=600;scene.cycles.samples=24
scene.render.filepath=str(ROOT/'walkthrough-preview.png')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'cyber-city-walkthrough.blend'))
result={'file':bpy.data.filepath,'camera':camera.name,'frames':[1,450],'seconds':15,'stationary_look_phase':[1,90],'path_points':len(points),'original_hero_camera':hero.name,'lobby':'basic shell; screens not designed','carved_facade_objects':len(affected)}
