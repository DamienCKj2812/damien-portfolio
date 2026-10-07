"""Final architectural/detail pass; run once after polish_scene.py."""
import bpy
import ast
import math
import random
from pathlib import Path
from mathutils import Vector

ROOT=Path('/home/damienckj/Documents/damien-portfolio/assets/cyber-city')
scene=bpy.context.scene
if not scene.name.startswith('NEON / Kaze Megacity'):
    raise RuntimeError('Activate the generated city scene before detailing.')
source=ast.parse((ROOT/'build_scene.py').read_text())
helpers=ast.Module(body=[node for node in source.body if isinstance(node,ast.FunctionDef)],type_ignores=[])
cyan=bpy.data.materials['City • Electric cyan']
exec(compile(helpers,str(ROOT/'build_scene.py'),'exec'),globals())
frame=bpy.data.materials['City • Facade mullions']
steel=bpy.data.materials['City • Graphite titanium']
warm=bpy.data.materials['City • Warm occupied offices']
blueglass=bpy.data.materials['City • Cobalt curtain wall']
amber=bpy.data.materials['City • Warm architectural lighting']
concrete=bpy.data.materials['City • Bridge concrete']
bark=bpy.data.materials['City • Tree bark']
leaf_meshes=[m for m in bpy.data.meshes if m.name.startswith('City • shared foliage cluster')]
random.seed(82)
# Reuse the construction helpers by restoring their active collection.
current=bpy.data.collections['03 Sky garden']
batches={}
for floor in range(49):
    z=.75+floor*.85
    batch_box((8.3,-.25,z),(5.45,.09,.075),frame)
    for col in range(6):
        x=5.98+col*.9
        batch_box((x,-.31,z+.33),(.79,.035,.58),warm if random.random()<.3 else blueglass)
for x in [5.52+i*.91 for i in range(7)]:batch_box((x,-.35,21),(.055,.05,41),frame)

# Observation-lounge furnishings: visible tables and warm ceiling pendants.
for i in range(10):
    a=i*math.tau/10
    x=8.2+3.8*math.cos(a);y=2+3.8*math.sin(a)
    cylinder('Sky lounge • cafe table',(x,y,40.9),.38,.08,frame,16)
    cylinder('Sky lounge • cafe table pedestal',(x,y,40.5),.07,.75,steel,12)
    cylinder('Sky lounge • pendant light',(x,y,42.05),.17,.08,amber,16)
    for dy in [-.55,.55]:box('Sky lounge • seat',(x,y+dy,40.55),(.42,.35,.12),steel,.03)

# Setback rooftop rail and backlit crown canopy.
for y in [-3.2,5.2]:
    tube('Crown • safety rail',[(-6.7,y,51.7),(4.1,y,51.7)],.035,frame)
    for x in [-6.7+i*1.08 for i in range(11)]:batch_box((x,y,51.2),(.04,.04,1.1),frame)
for x in [-6.7,4.1]:tube('Crown • safety rail',[(x,-3.2,51.7),(x,5.2,51.7)],.035,frame)
box('Crown • rooftop canopy',(-1.3,1,52.15),(7.5,4.7,.16),steel,.05)
tube('Crown • canopy warm edge',[(-5.05,-1.35,52.08),(2.45,-1.35,52.08)],.035,amber)
for x in [-5,2.4]:
    for y in [-1.3,3.3]:tube('Crown • canopy post',[(x,y,51),(x,y,52.1)],.04,frame)

current=bpy.data.collections['05 Elevated highways']
points=[(-32+i*2,-17+i*.34,4.2+i*.10) for i in range(33)]
for offset in [-1.15,1.15]:
    tube('Foreground skyway • deep edge girder',[(x,y+offset,z-.36) for x,y,z in points],.18,steel)
for i in range(0,32,2):
    x,y,z=points[i]
    tube('Foreground skyway • underdeck crossmember',[(x,y-1.5,z-.43),(x,y+1.5,z-.43)],.12,frame)
    tube('Foreground skyway • double guardrail',[(x,y-1.58,z+.32),(x+2,y-1.24,z+.42)],.04,frame)

# Move the foreground flying car fully inside the hero camera framing.
scene.objects['Aircar 01 • foreground commuter'].location=(-7.2,-14,13.0)
scene.objects['Aircar 02 • right approaching'].location=(11.8,-9,12)
for name,target in [('Aircar 01 • fill',(-7.2,-14,13)),('Aircar 02 • fill',(11.8,-9,12))]:
    obj=scene.objects[name];obj.location=(target[0],target[1]-3,target[2]+3);obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler();obj.data.energy=280

# More visible trees and planting beds just outside the entrance.
current=bpy.data.collections['07 Street life']
for x,y,size in [(-8.5,-7,1.3),(10.5,-7,1.25),(-9.5,-17,1.6),(13,-15,1.5)]:
    box('Plaza • raised planter',(x,y,.2),(1.4,1.2,.4),concrete,.04)
    tree(x,y,.4,size)
for x in [-5.3,-3.4,-1.5,.4,2.3]:
    for z in [.3,1.5,3.1]:batch_box((x,-5.68,z),(1.7,.06,.05),frame)
    batch_box((x+.45,-5.7,1.25),(.025,.03,.4),steel)
for (col_name,material_name),(verts,faces) in batches.items():
    current=bpy.data.collections[col_name]
    mesh_obj('Architectural refinement • '+material_name,verts,faces,bpy.data.materials[material_name])

for mesh in leaf_meshes:
    for p in mesh.polygons:p.use_smooth=True
scene.camera.data.lens=30
scene.render.resolution_x=850;scene.render.resolution_y=1250;scene.cycles.samples=64
scene.render.film_transparent=True;scene.render.image_settings.color_mode='RGBA'
scene.render.filepath=str(ROOT/'preview.png')
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'cyber-city.blend'))
result={'scene':scene.name,'objects':len(scene.objects),'transparent':scene.render.film_transparent,'detail_pass':'complete'}
