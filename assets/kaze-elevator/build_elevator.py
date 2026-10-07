"""Build an isolated KAJU cabin; blender --background --factory-startup --python this_file."""
import json
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent/'branding'))
from kaju_brand import logo_paths, SPACED_BRAND
random.seed(1204)
scene = bpy.data.scenes.new('KAZE / Elevator interior')
bpy.context.window.scene = scene
scene.unit_settings.system = 'METRIC'
groups = {}
for label in ['Architecture', 'Light channels', 'Identity', 'Controls', 'Campaign', 'Surface particles', 'Doors', 'Anchors', 'Cameras and lights']:
    col = bpy.data.collections.new('Elevator / ' + label)
    scene.collection.children.link(col)
    groups[label] = col


def link(name, data, group='Architecture'):
    obj = bpy.data.objects.new('Elevator / ' + name, data)
    groups[group].objects.link(obj)
    return obj


def material(name, shade, emission=0, metallic=0, roughness=.5):
    mat = bpy.data.materials.new('Elevator / ' + name)
    mat.diffuse_color = (shade, shade, shade, 1)
    mat.use_nodes = True
    p = mat.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = mat.diffuse_color
    p.inputs['Metallic'].default_value = metallic
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Emission Color'].default_value = mat.diffuse_color
    p.inputs['Emission Strength'].default_value = emission
    return mat


black = material('Graphite wall panels', .007, metallic=.45, roughness=.32)
inset = material('Recessed black glass', .002, metallic=.35, roughness=.18)
floor = material('Reflective obsidian floor', .012, metallic=.8, roughness=.16)
silver = material('Satin chrome rails', .19, metallic=.9, roughness=.22)
edge = material('Silver hairline', .26, emission=.65, metallic=.3)
quiet = material('Subtle construction grid', .055, emission=.4)
glow = material('White perimeter lighting', .72, emission=3)
type_mat = material('Silver lettering', .58, emission=.65)
dot = material('Fine white pointwork', .27, emission=.75)


def lines(name, paths, mat=edge, radius=.0016, group='Light channels'):
    data = bpy.data.curves.new(name, 'CURVE')
    data.dimensions = '3D'
    data.bevel_depth = radius
    data.bevel_resolution = 1
    data.resolution_u = 1
    for path in paths:
        s = data.splines.new('POLY')
        s.points.add(len(path)-1)
        for p, co in zip(s.points, path):
            p.co = (*co, 1)
    obj = link(name, data, group)
    data.materials.append(mat)
    return obj


def box(name, pos, size, mat=black, group='Architecture', bevel=0):
    x,y,z = [v/2 for v in size]
    vertices = [(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),(-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)]
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], [(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)])
    data.materials.append(mat)
    obj = link(name, data, group)
    obj.location = pos
    if bevel:
        mod = obj.modifiers.new('Machined edge radius', 'BEVEL')
        mod.width = bevel
        mod.segments = 3
        obj.modifiers.new('Weighted surface normals', 'WEIGHTED_NORMAL')
    return obj


def basis(side):
    # Typography local X runs horizontally, local Y vertically, local Z into cabin.
    if side == 'rear':
        return Vector((1,0,0)), Vector((0,0,1)), Vector((0,-1,0))
    if side == 'right':
        return Vector((0,-1,0)), Vector((0,0,1)), Vector((-1,0,0))
    return Vector((0,1,0)), Vector((0,0,1)), Vector((1,0,0))


def text(name, body, pos, size=.06, side='rear', group='Identity', mat=type_mat):
    data = bpy.data.curves.new(name, 'FONT')
    data.body = body
    data.align_x = 'CENTER'
    data.align_y = 'CENTER'
    data.size = size
    data.space_character = 1.3
    data.space_line = 1.35
    data.extrude = .0002
    obj = link(name, data, group)
    obj.location = pos
    u,v,n = basis(side)
    obj.rotation_euler = Matrix((u,v,n)).transposed().to_euler()
    data.materials.append(mat)
    return obj


def wall_path(side, center, coords):
    u,v,n = basis(side)
    return [tuple(Vector(center)+u*x+v*y) for x,y in coords]


def frame(name, side, center, w,h, mat=edge, group='Identity'):
    return lines(name, [wall_path(side,center,[(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2),(-w/2,-h/2)])], mat, group=group)


def circle(name, side, center, radius, mat=edge, group='Controls'):
    coords = [(radius*math.cos(i*math.tau/40),radius*math.sin(i*math.tau/40)) for i in range(41)]
    return lines(name,[wall_path(side,center,coords)],mat,group=group)


def logo(name, side, center, scale):
    paths = [wall_path(side,center,[(x*scale,y*scale) for x,y in path]) for path in logo_paths()]
    lines(name,paths,type_mat,.0014,'Identity')


# Clear interior: 2.6 m across, 2.8 m deep, 3.2 m high. Entrance is at Y=0.
box('Floor slab',(0,1.4,-.065),(2.76,2.96,.13),floor)
box('Rear wall',(0,2.86,1.6),(2.76,.12,3.2))
box('Left wall',(-1.36,1.4,1.6),(.12,2.8,3.2))
box('Right wall',(1.36,1.4,1.6),(.12,2.8,3.2))
box('Ceiling',(0,1.4,3.26),(2.76,2.96,.12),inset)
box('Recessed ceiling tray',(0,1.4,3.18),(2.28,2.48,.025),black)

for x in [-1.29,1.29]:
    for y in [.04,2.76]:
        box('Corner chrome reveal',(x,y,1.6),(.025,.025,3.15),silver)
        lines('Vertical corner light', [[(x*.989,y, .08),(x*.989,y,3.13)]],glow,.0022)
    for z in [.08,3.12]:
        lines('Side perimeter strip',[[(x,.04,z),(x,2.76,z)]],glow,.0022)
for z in [.08,3.12]:
    lines('Rear perimeter strip',[[(-1.29,2.785,z),(1.29,2.785,z)]],glow,.0022)
for inset_amount in [0,.05]:
    x=1.13-inset_amount
    lines('Ceiling concentric reveal',[[(-x,.18+inset_amount,3.16),(x,.18+inset_amount,3.16),(x,2.62-inset_amount,3.16),(-x,2.62-inset_amount,3.16),(-x,.18+inset_amount,3.16)]],edge)

# Flush panel seams and floor tile joints.
paths=[]
for x in [-.86,0,.86]:
    paths.append([(x,2.791,.12),(x,2.791,3.1)])
for z in [.42,1.04,2.4,2.96]:
    paths.append([(-1.28,2.791,z),(1.28,2.791,z)])
for x in [-1.295,1.295]:
    for y in [.55,1.15,1.75,2.35]:
        paths.append([(x,y,.12),(x,y,3.1)])
    for z in [.42,1.04,2.4,2.96]:
        paths.append([(x,.05,z),(x,2.75,z)])
for x in [-.86,-.43,0,.43,.86]:
    paths.append([(x,.02,.006),(x,2.78,.006)])
for y in [.4,.8,1.2,1.6,2,2.4]:
    paths.append([(-1.29,y,.006),(1.29,y,.006)])
lines('Panel and tile joints',paths,quiet,.0009)

for side,x in [('left',-1.22),('right',1.22)]:
    box(side+' handrail',(x,1.4,1.03),(.055,2.5,.045),silver,bevel=.012)
    lines(side+' handrail highlight',[[(x,.15,1.054),(x,2.65,1.054)]],edge,.0018)
    for y in [.35,2.45]:
        box(side+' rail bracket',(x*1.025,y,1.01),(.09,.025,.05),silver,bevel=.008)
    box(side+' skirting',(x*1.055,1.4,.16),(.025,2.65,.11),silver)

# Rear corporate identity, arranged like the reference.
logo('Rear geometric KAZE mark','rear',(0,2.774,2.04),.18)
text('KAZE wordmark',SPACED_BRAND,(0,2.772,1.84),.092)
text('Industries descriptor','I N D U S T R I E S',(0,2.771,1.745),.023)
text('Brand pillars','PEOPLE\nCULTURE\nTECH\nTOMORROW',(0,2.771,1.37),.041)
text('Clean future statement','A CLEANER BRIGHTER\nHUMAN FUTURE',(0,2.771,.60),.027)
lines('Identity divider',[[(-.055,2.771,1.115),(.055,2.771,1.115)],[(-.045,2.771,.48),(.045,2.771,.48)]],edge,.0012,'Identity')

# Shared panel authoring keeps full rebuilds and master-only edits consistent.
levels = [('about','ABOUT ME'),('skills','SKILLS'),('projects','PROJECTS'),
          ('experience','EXPERIENCE\n& EDUCATION')]
sys.path.insert(0, str(ROOT))
from floor_panel_design import apply_panel_design
apply_panel_design(scene, [{'id':key,'number':i+1,'title':label} for i,(key,label) in enumerate(levels)])

# Left campaign panel with a genuine 3D stippled profile silhouette.
box('Campaign black glass',(-1.282,1.45,1.92),(.025,.78,1.68),inset,'Campaign',.006)
frame('Campaign frame','left',(-1.264,1.45,1.92),.78,1.68,group='Campaign')
text('Campaign headline','HUMAN\nTOGETHER',(-1.252,1.45,2.57),.051,'left','Campaign')
text('Campaign pillars','PEOPLE\nCULTURE\nTECH\nTOMORROW',(-1.252,1.45,1.29),.031,'left','Campaign')

verts=[]
faces=[]
def point(pos,r):
    start=len(verts)
    x,y,z=pos
    verts.extend([(x+r,y,z),(x-r,y,z),(x,y+r,z),(x,y-r,z),(x,y,z+r),(x,y,z-r)])
    faces.extend([tuple(start+i for i in f) for f in [(0,2,4),(2,1,4),(1,3,4),(3,0,4),(2,0,5),(1,2,5),(3,1,5),(0,3,5)]])

for i in range(2800):
    v=random.uniform(-.43,.43)
    # Profile faces the entrance; nose/lips interrupt the right contour.
    if v > -.09:
        width=.175*math.sqrt(max(0,1-((v-.12)/.32)**2))
        left=-width
        right=width + .066*math.exp(-((v-.055)/.033)**2) + .025*math.exp(-((v+.032)/.018)**2)
    else:
        width=.085+max(0,-v-.23)*.72
        left=-width-.04
        right=width-.055
    if right<=left:
        continue
    u=random.uniform(left,right)
    if random.random()<.3+.7*abs(u)/max(.05,width):
        point((-1.248,1.45+u,1.99+v),random.uniform(.0007,.0018))
for side in ['rear','left','right','floor','ceiling']:
    for i in range(1100):
        if side=='rear':
            pos=(random.uniform(-1.25,1.25),2.787,random.uniform(.18,3.1))
        elif side=='floor' or side=='ceiling':
            pos=(random.uniform(-1.25,1.25),random.uniform(.05,2.75),.009 if side=='floor' else 3.155)
        else:
            pos=(-1.292 if side=='left' else 1.292,random.uniform(.05,2.75),random.uniform(.18,3.1))
        point(pos,random.uniform(.00045,.0011))
mesh=bpy.data.meshes.new('Stippled surfaces and human portrait')
mesh.from_pydata(verts,[],faces)
mesh.materials.append(dot)
link('Stippled surfaces and human portrait',mesh,'Surface particles')

# Open sliding entrance, tracks, jambs. Doors remain separate for runtime animation.
for x in [-1.23,1.23]:
    box('Entrance jamb',(x,-.025,1.6),(.14,.13,3.2),silver)
    lines('Entrance jamb edge',[[(x,-.1,.03),(x,-.1,3.17)]],edge)
box('Entrance header',(0,-.025,3.16),(2.6,.13,.08),silver)
box('Entrance threshold',(0,-.015,.015),(2.6,.16,.025),silver)
for y in [-.065,-.02,.025]:
    lines('Threshold track',[[(-1.2,y,.03),(1.2,y,.03)]],quiet,.001)
for label,x in [('Left',-1.77),('Right',1.77)]:
    obj=box(label+' sliding door',(x,-.035,1.6),(1.16,.035,3.04),black,'Doors',.005)
    obj['open_x']=x
    obj['closed_x']=-.58 if label=='Left' else .58
    obj['animation_axis']='X'

for name,pos in [('Entrance origin',(0,0,0)),('Standing camera',(0,.3,1.65)),('Rear wall anchor',(0,2.8,0)),('Exit direction',(0,-1,0))]:
    anchor=link(name,None,'Anchors')
    anchor.location=pos
    anchor.empty_display_type='PLAIN_AXES'
    anchor.empty_display_size=.15

def camera(name,pos,target,lens):
    data=bpy.data.cameras.new(name)
    obj=link(name,data,'Cameras and lights')
    obj.location=pos
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
    data.lens=lens
    data.clip_start=.025
    return obj

hero=camera('Reference portrait camera',(0,-2.7,1.65),(0,1.65,1.64),32)
inside=camera('Inside cabin camera',(0,.28,1.65),(0,2.8,1.62),19)
detail=camera('Control panel detail camera',(-.8,.30,1.85),(1.26,1.42,1.91),43)
for name,pos,power,size,target in [('Ceiling softbox',(0,1.25,3.08),35,2,(0,1.3,0)),('Entrance fill',(0,-1.2,2.4),20,2,(0,2.8,1.4))]:
    data=bpy.data.lights.new(name,'AREA')
    data.energy=power
    data.shape='DISK'
    data.size=size
    obj=link(name,data,'Cameras and lights')
    obj.location=pos
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
for x in [-.78,.78]:
    lines('Ceiling downlight trim', [[(x+.044*math.cos(i*math.tau/40),.52+.044*math.sin(i*math.tau/40),3.145) for i in range(41)]],glow,.0018)

world=bpy.data.worlds.new('Elevator / Black studio')
world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.015,.015,.015,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.18
scene.world=world
scene.render.engine='CYCLES'
scene.cycles.samples=48
scene.cycles.use_denoising=True
scene.render.resolution_x=900
scene.render.resolution_y=1280
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
transforms = scene.view_settings.bl_rna.properties['view_transform'].enum_items.keys()
scene.view_settings.view_transform='AgX' if 'AgX' in transforms else 'Standard'
scene.view_settings.exposure=0
scene.render.film_transparent=False
scene.render.image_settings.color_mode='RGB'
scene.render.image_settings.color_depth='8'
scene.render.fps=30
scene.camera=hero
scene.render.filepath=str(ROOT/'elevator-reference.png')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'kaze-elevator.blend'))
bpy.ops.render.render(write_still=True)
scene.camera=inside
scene.render.resolution_x=1200
scene.render.resolution_y=1000
scene.render.filepath=str(ROOT/'elevator-interior.png')
bpy.ops.render.render(write_still=True)
scene.camera=detail
scene.render.resolution_x=900
scene.render.resolution_y=1100
scene.render.filepath=str(ROOT/'elevator-controls.png')
bpy.ops.render.render(write_still=True)

# Convert only the isolated export scene; the saved source retains editable curves/text.
bpy.ops.object.select_all(action='DESELECT')
for obj in list(scene.objects):
    if obj.type in {'CURVE','FONT'}:
        obj.select_set(True)
        bpy.context.view_layer.objects.active=obj
        bpy.ops.object.convert(target='MESH')
        obj.select_set(False)
bpy.ops.export_scene.gltf(filepath=str(ROOT/'kaze-elevator.glb'),export_format='GLB',use_active_scene=True,export_cameras=False,export_lights=False,export_extras=True)
(ROOT/'elevator-manifest.json').write_text(json.dumps({
    'name':'KAJU Elevator Interior','units':'meters','axes':{'up':'+Z (Blender), +Y (glTF)','entrance':'Blender Y=0','rear':'+Y (Blender)'},
    'clear_interior':{'width':2.6,'depth':2.8,'height':3.2},
    'files':{'source':'kaze-elevator.blend','browser':'kaze-elevator.glb','portrait':'elevator-reference.png','interior':'elevator-interior.png','controls':'elevator-controls.png'},
    'doors':{'left':{'open_x':-1.77,'closed_x':-.58},'right':{'open_x':1.77,'closed_x':.58}},
    'levels':[{'id':level_id,'number':i+1,'label':label.replace('\n',' '),'button':'Elevator / Level button '+level_id} for i,(level_id,label) in enumerate(levels)],
    'notes':['Static open doors with runtime transform metadata.','Four named portfolio levels; separate meshes include interaction metadata.','All text and portrait pointwork are geometry; no external textures or fonts.']
},indent=2)+'\n')
