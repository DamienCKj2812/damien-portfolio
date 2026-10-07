"""Monochrome About Us office. One editable blend, original procedural screen art.

blender --background --factory-startup --python assets/about-office/build_office.py -- --render
"""
import json
import math
from pathlib import Path
import random
import sys

import bpy
from mathutils import Euler, Vector

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from office_environment import build_environment
from contact_card_content import contact_card_lines, read_contact_details
from malaysia_screen import apply_malaysia_screen
if bpy.data.filepath:
    raise RuntimeError('Generate in a fresh --factory-startup process to preserve existing work.')
random.seed(47)
factory_scenes = list(bpy.data.scenes)
scene = bpy.data.scenes.new('ABOUT / Skyline Office')
bpy.context.window.scene = scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'METERS'
collections = {}
for label in ['01 Architecture & glazing', '02 Workstation & chair', '03 Screen & desk objects',
              '04 Skyline backdrop', '05 Botanical forms', '06 Particle figure',
              '07 Atmosphere', '08 Cameras & lighting', '09 Integration anchors',
              '10 Name card & contact', '11 Interior library & aquarium']:
    col = bpy.data.collections.new('Office • '+label)
    scene.collection.children.link(col)
    collections[label[:2]] = col


def link(name,data,group):
    obj = bpy.data.objects.new('Office • '+name,data)
    collections[group].objects.link(obj)
    return obj


def material(name,gray,emission=0,roughness=.5,metallic=0):
    mat = bpy.data.materials.new('Office • '+name)
    mat.diffuse_color = (gray,gray,gray,1)
    mat.use_nodes = True
    p = mat.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (gray,gray,gray,1)
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Metallic'].default_value = metallic
    p.inputs['Emission Color'].default_value = (gray,gray,gray,1)
    p.inputs['Emission Strength'].default_value = emission
    return mat


black = material('Black architectural backing',.002,roughness=.85)
stone = material('Polished dark floor',.009,roughness=.105,metallic=.65)
graphite = material('Desk and equipment graphite',.012,roughness=.27,metallic=.28)
cloth = material('Chair woven charcoal',.018,roughness=.85)
edge = material('Fine architectural silver',.31,emission=1.25)
quiet = material('Secondary graphite lines',.12,emission=.8)
hero = material('White architectural light',.78,emission=4)
screen_line = material('Screen interface silver',.36,emission=1.7)
type_mat = material('Silver lettering',.40,emission=1.0)
dots_mat = material('White surface particles',.50,emission=1.1)
window_dot = material('Distant illuminated windows',.26,emission=1.2)
dust_mat = material('Ambient floating dots',.13,emission=.5)


def lines(name,paths,mat=edge,radius=.003,group='01'):
    data = bpy.data.curves.new('Office • '+name,'CURVE')
    data.dimensions = '3D'; data.resolution_u = 1
    data.bevel_depth = radius; data.bevel_resolution = 0
    for path in paths:
        spline = data.splines.new('POLY'); spline.points.add(len(path)-1)
        for point,co in zip(spline.points,path):
            point.co = (*co,1)
    obj = link(name,data,group); data.materials.append(mat)
    return obj


def box(name,center,size,mat=black,group='02',outline=True,edge_mat=edge,rotation=None):
    x,y,z = (d/2 for d in size)
    verts = [(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),
             (-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)]
    faces = [(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)]
    data = bpy.data.meshes.new('Office • '+name)
    data.from_pydata(verts,[],faces); data.materials.append(mat)
    obj = link(name,data,group); obj.location = center
    if rotation:
        obj.rotation_euler = rotation
    if outline:
        edges = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
        wire = lines(name+' / feature edges',[[verts[a],verts[b]] for a,b in edges],edge_mat,.0025,group)
        wire.parent = obj
    return obj


def ellipse(center,rx,ry,plane='XY',segments=48):
    out = []
    for i in range(segments+1):
        a = i*math.tau/segments
        coords = {'XY':(rx*math.cos(a),ry*math.sin(a),0),
                  'XZ':(rx*math.cos(a),0,ry*math.sin(a)),
                  'YZ':(0,rx*math.cos(a),ry*math.sin(a))}[plane]
        out.append(tuple(Vector(center)+Vector(coords)))
    return out


def cylinder(name,center,radius,depth,group='03',mat=graphite):
    n = 24
    verts = [(radius*math.cos(i*math.tau/n),radius*math.sin(i*math.tau/n),z)
             for z in [-depth/2,depth/2] for i in range(n)]
    faces = [tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh = bpy.data.meshes.new('Office • '+name); mesh.from_pydata(verts,[],faces)
    mesh.materials.append(mat)
    obj = link(name,mesh,group); obj.location = center
    wire = lines(name+' / rim', [ellipse((0,0,-depth/2),radius,radius),
                                ellipse((0,0,depth/2),radius,radius)],edge,.002,group)
    wire.parent = obj
    return obj


def text(name,body,position,size=.10,group='03',align='CENTER',mat=type_mat):
    data = bpy.data.curves.new('Office • '+name,'FONT')
    data.body = body; data.align_x = align; data.align_y = 'CENTER'
    data.size = size; data.space_character = 1.15; data.space_line = 1.3
    obj = link(name,data,group); obj.location = position
    obj.rotation_euler = (math.pi/2,0,0); data.materials.append(mat)
    return obj


def particles(name,vertices,radius,group,mat=dots_mat):
    mesh = bpy.data.meshes.new('Office • '+name+' / editable positions')
    mesh.from_pydata(vertices,[],[])
    obj = link(name,mesh,group)
    tree = bpy.data.node_groups.new('Office • '+name+' / point display','GeometryNodeTree')
    tree.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
    tree.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    inp = tree.nodes.new('NodeGroupInput'); inp.location = (-450,50)
    points = tree.nodes.new('GeometryNodeMeshToPoints'); points.mode = 'VERTICES'; points.location = (-260,50)
    ico = tree.nodes.new('GeometryNodeMeshIcoSphere'); ico.location = (-260,-140)
    ico.inputs['Radius'].default_value = radius; ico.inputs['Subdivisions'].default_value = 1
    shade = tree.nodes.new('GeometryNodeSetMaterial'); shade.location = (-50,-140)
    shade.inputs['Material'].default_value = mat
    inst = tree.nodes.new('GeometryNodeInstanceOnPoints'); inst.location = (160,50)
    out = tree.nodes.new('NodeGroupOutput'); out.location = (380,50)
    tree.links.new(inp.outputs['Geometry'],points.inputs['Mesh'])
    tree.links.new(ico.outputs['Mesh'],shade.inputs['Geometry'])
    tree.links.new(points.outputs['Points'],inst.inputs['Points'])
    tree.links.new(shade.outputs['Geometry'],inst.inputs['Instance'])
    tree.links.new(inst.outputs['Instances'],out.inputs['Geometry'])
    obj.modifiers.new('Editable surface point display','NODES').node_group = tree
    obj['particle_count'] = len(vertices)
    return obj


# Full-height skyline glazing faces +Y. The other walls are authored below
# as a complete 360-degree interior, retaining the elevator opening at -Y.
box('Reflective tiled office floor',(0,-1,-.10),(12,12,.20),stone,'01',outline=False)
box('Black ceiling',(0,-1,4.68),(12,12,.16),black,'01',outline=False)
for x in [-6,-3,0,3,6]:
    box('Rear glazing mullion',(x,5.0,2.30),(.055,.075,4.60),graphite,'01',edge_mat=quiet)
for z in [.08,1.12,4.55]:
    lines('Panoramic window transom',[[(-6,5,z),(6,5,z)]],edge,.003,'01')
for x in [-4.6,-1.3,2.0,5.3]:
    lines('Ceiling panel seam',[[(x,-7,4.59),(x,5,4.59)]],quiet,.0025,'01')
for y in [-5,-1,3]:
    lines('Ceiling cross seam',[[(-6,y,4.59),(6,y,4.59)]],quiet,.0025,'01')
for x in range(-6,7):
    lines('Floor longitudinal joint',[[(x,-7,.008),(x,5,.008)]],quiet,.0015,'01')
for y in range(-7,6):
    lines('Floor transverse joint',[[(-6,y,.008),(6,y,.008)]],quiet,.0015,'01')
for x,y0,y1 in [(-2.1,-3.5,3.6),(3.8,-3.1,3.6)]:
    lines('Suspended ceiling light',[[(x,y0,4.54),(x,y1,4.54)]],hero,.009,'01')
text('Window architectural label','OFFICE  /  FLOOR 32\nABOUT US  /  WORKSPACE',(-4.8,4.92,4.10),.075,'01',align='LEFT')
text('Window manifesto','WORK\nANYWHERE\nFURTHER',(1.75,4.92,3.45),.14,'01')
text('Right window manifesto','IDEAS\nPEOPLE\nTOGETHER',(4.78,4.92,2.85),.10,'01')

# A lightweight original skyline backdrop: volumes, restrained feature lines,
# sparse illuminated windows. No city project files are opened or modified.
window_points = []
for row,y in enumerate([9.8,17.0,26.0]):
    for index in range(15):
        x = (index-7)*2.8+random.uniform(-.6,.6)
        width = random.uniform(1.05,2.3); depth = random.uniform(1.2,2.2)
        height = random.uniform(5.0,15.0)+(3 if index in [4,9] else 0)
        base = -6.0
        box('Skyline tower %02d-%02d' % (row,index),(x,y,base+height/2),
            (width,depth,height),black,'04',edge_mat=quiet)
        if index%4==0:
            box('Skyline stepped crown',(x,y,base+height+.35),(width*.65,depth*.7,.7),black,'04',edge_mat=quiet)
            lines('Skyline antenna',[[(x,y,base+height+.7),(x,y,base+height+1.4)]],quiet,.002,'04')
        cols = max(2,int(width/.18))
        for level in range(int(height/.33)):
            z = base+.18+level*.33
            for column in range(cols):
                if random.random()<.34:
                    xx = x-width*.42+column*width*.84/(cols-1)
                    window_points.append((xx,y-depth/2-.008,z))
            if level%5==0:
                lines('Skyline floor band', [[(x-width/2,y-depth/2-.008,z),
                                             (x+width/2,y-depth/2-.008,z)]],quiet,.0015,'04')
particles('Skyline window lights',window_points,.010,'04',window_dot)

# Desk with a light open frame, drawer pedestal, and an ultrawide monitor.
box('Work desk floating top',(.55,.45,.85),(4.85,1.70,.09),graphite,'02')
for x in [-1.75,2.85]:
    lines('Desk thin support frame',[[(x,-.26,.08),(x,-.26,.79),(x,1.16,.79),(x,1.16,.08)],
                                     [(x,-.26,.08),(x,1.16,.08)]],edge,.011,'02')
box('Desk storage pedestal',(2.2,.35,.38),(1.05,1.34,.70),graphite,'02')
for z in [.23,.53]:
    box('Desk drawer front',(2.2,-.328,z),(.98,.028,.265),graphite,'02',edge_mat=quiet)
    lines('Drawer recessed pull',[[(2.09,-.349,z+.06),(2.31,-.349,z+.06)]],edge,.003,'02')
monitor = box('Monitor body',(.35,1.13,1.49),(2.55,.105,1.19),graphite,'03',edge_mat=edge)
box('Monitor stand stem',(.35,1.15,.98),(.12,.12,.24),graphite,'03')
box('Monitor stand foot',(.35,1.09,.915),(.59,.36,.025),graphite,'03')
screen_mesh = bpy.data.meshes.new('Office • About display UV mesh')
screen_mesh.from_pydata([(-1.22,0,-.54),(1.22,0,-.54),(1.22,0,.54),(-1.22,0,.54)],[],[(0,1,2,3)])
uv = screen_mesh.uv_layers.new(name='ScreenUV')
for loop,co in zip(uv.data,[(0,0),(1,0),(1,1),(0,1)]):
    loop.uv = co
screen_mesh.materials.append(black)
display = link('About content screen / web texture target',screen_mesh,'03')
display.location = (.35,1.070,1.49)
display['web_role'] = 'Separate UV-mapped about-section display; replace concept graphics on the website.'
display['aspect_ratio'] = 2.44/1.08
screen_y = 1.061
text('Screen navigation','ABOUT\nWORK\nNOTES\nIDEAS\nCONTACT',(-.75,screen_y,1.66),.053,'03',align='LEFT',mat=screen_line)
text('Screen signature','DAMIEN',(-.75,screen_y,1.99),.065,'03',align='LEFT',mat=screen_line)
lines('Screen layout panels',[[(-.30,screen_y,.99),(-.30,screen_y,1.99)],
                              [(.91,screen_y,.99),(.91,screen_y,1.99)],
                              [(-.26,screen_y,1.13),(.86,screen_y,1.13)]],screen_line,.0014,'03')

# Original network artwork in the monitor, drawn directly as planar points/lines.
network = []
for _ in range(480):
    a = random.uniform(0,math.tau); r = random.random()**1.8
    network.append((.24+math.cos(a)*r*.50,screen_y-.001,1.58+math.sin(a)*r*.31))
network_paths = []
for i,point in enumerate(network):
    distances = sorted(((Vector(point)-Vector(other)).length,j) for j,other in enumerate(network) if i!=j)
    for distance,j in distances[:3]:
        if j>i and distance<.12:
            network_paths.append([point,network[j]])
for i in range(7):
    network_paths.append([(-.21+j*.14,screen_y-.002,
                           1.58+math.sin(j*.9+i)*(.10+i*.018)) for j in range(8)])
lines('Screen original idea network',network_paths,screen_line,.0009,'03')
particles('Screen network nodes',network,.0032,'03',screen_line)
text('Screen profile caption','BUILD  /  LEARN  /  CREATE',(.27,screen_y,1.055),.037,'03',mat=screen_line)
globe = []
for tilt in [0,math.pi/3,2*math.pi/3]:
    points = []
    for i in range(37):
        a = i*math.tau/36
        points.append((1.21+.17*math.cos(a)*math.cos(tilt),screen_y-.002,
                       1.78+.17*math.sin(a)))
    globe.append(points)
for z,r in [(1.70,.145),(1.78,.17),(1.86,.145)]:
    globe.append([(1.21-r,screen_y-.002,z),(1.21+r,screen_y-.002,z)])
lines('Screen globe diagram',globe,screen_line,.0014,'03')
text('Screen right caption','GLOBAL\nIDEAS\nREAL SPACES',(1.21,screen_y,1.41),.034,'03',mat=screen_line)
bars = []
for i in range(11):
    x = 1.01+i*.035
    bars.append([(x,screen_y,1.06),(x,screen_y,1.08+random.uniform(.02,.15))])
lines('Screen activity chart',bars,screen_line,.0015,'03')
malaysia_map = apply_malaysia_screen(scene)

# Keyboard, mouse, lamp, notebook, and pen holder.
box('Keyboard chassis',(.35,-.04,.927),(1.12,.39,.035),graphite,'03')
key_paths = []
for row in range(5):
    for col in range(15):
        x = -.175+col*.072; y = -.195+row*.073
        key_paths.append([(x-.028,y-.026,.948),(x+.028,y-.026,.948),
                          (x+.028,y+.026,.948),(x-.028,y+.026,.948),(x-.028,y-.026,.948)])
lines('Keyboard key contours',key_paths,edge,.0012,'03')
lines('Mouse contours',[ellipse((1.20,-.02,.946),.080,.12),
                        [(1.20,-.11,.958),(1.20,-.01,.966)]],edge,.002,'03')
box('Desk lamp weighted base',(-1.16,.79,.923),(.38,.29,.05),graphite,'03')
lines('Desk lamp stem',[[(-1.16,.79,.95),(-1.16,.79,1.57)]],edge,.011,'03')
box('Desk lamp light bar',(-1.16,.79,1.59),(.70,.085,.045),graphite,'03')
lines('Desk lamp luminous strip',[[(-1.49,.741,1.57),(-.83,.741,1.57)]],hero,.006,'03')
box('Pen holder',(-.66,.76,1.045),(.19,.19,.25),graphite,'03')
for i in range(5):
    x = -.72+i*.030
    lines('Pen',[[(x,.75,.96),(x+random.uniform(-.025,.025),.75,1.30)]],edge,.003,'03')
box('Standing notebook',(2.18,.62,1.16),(.53,.06,.48),graphite,'03',rotation=(0,0,-.12))
text('Notebook cover','IDEAS\nPLANS\nPEOPLE',(2.18,.574,1.17),.048,'03')
box('Notebook foot',(2.18,.58,.93),(.58,.27,.025),graphite,'03')

# A turned, adjustable office chair: cloth panels, open arms, five-star base.
chair_root = link('Chair / editable root',None,'02')
chair_before = set(scene.objects)
box('Chair seat',(0,0,.50),(.72,.64,.10),cloth,'02')
box('Chair angled back',(0,-.31,.98),(.73,.055,.86),cloth,'02',rotation=(.16,0,0))
for z in [.76,1.12]:
    lines('Chair back cross brace',[[(-.36,-.345,z),(.36,-.345,z)]],edge,.005,'02')
for side in [-1,1]:
    lines('Chair armrest',[[(side*.41,.21,.59),(side*.41,.21,.79),
                           (side*.41,-.32,.79),(side*.41,-.34,.64)]],edge,.010,'02')
cylinder('Chair height piston',(0,0,.29),.045,.34,'02')
for i in range(5):
    a = i*math.tau/5+.2
    x,y = math.cos(a)*.45,math.sin(a)*.45
    lines('Chair star-base spoke',[[(0,0,.17),(x,y,.085)]],edge,.014,'02')
    wheel = cylinder('Chair caster',(x,y,.064),.060,.050,'02')
    wheel.rotation_euler = (math.pi/2,0,a)
for obj in set(scene.objects)-chair_before:
    if obj.parent is None:
        obj.parent = chair_root
chair_root.location = (.20,-1.26,0)
chair_root.rotation_euler.z = -.12


def plant(name,origin,height,group='05'):
    origin = Vector(origin)
    box(name+' / planter',tuple(origin+Vector((0,0,.16))),(.39,.39,.32),graphite,group)
    paths = []
    for i in range(9):
        a = i*math.tau/9+random.uniform(-.25,.25)
        end = origin+Vector((math.cos(a)*height*.32,math.sin(a)*height*.28,
                              height*random.uniform(.64,1.0)+.25))
        base = origin+Vector((0,0,.29))
        middle = base.lerp(end,.50)
        paths.append([tuple(base),tuple(middle),tuple(end)])
        direction = (end-middle).normalized()
        width_axis = Vector((math.cos(a+math.pi/2),math.sin(a+math.pi/2),.1)).normalized()
        left,right = [],[]
        for j in range(13):
            t = j/12
            center = middle.lerp(end,t)+Vector((0,0,math.sin(t*math.pi)*height*.05))
            width = math.sin(t*math.pi)*height*.105
            left.append(tuple(center+width_axis*width)); right.append(tuple(center-width_axis*width))
        outline = left+list(reversed(right))+[left[0]]
        paths.append(outline)
        verts = left+right
        faces = [(j,j+1,13+j+1,13+j) for j in range(12)]
        mesh = bpy.data.meshes.new('Office • '+name+' / leaf')
        mesh.from_pydata(verts,[],faces); mesh.materials.append(black)
        link(name+' / leaf surface',mesh,group)
    lines(name+' / botanical contours',paths,edge,.0025,group)


box('Window-side console',(-4.55,2.3,.38),(2.9,.84,.72),graphite,'02')
for x in [-5.45,-4.55,-3.65]:
    box('Console front panel',(x,1.869,.39),(.85,.028,.62),graphite,'02',edge_mat=quiet)
plant('Window-side broad-leaf plant',(-5.45,2.27,.75),1.7)
plant('Desktop plant',(2.58,1.01,.90),.58)
for i,title in enumerate(['CODE','SYSTEMS','IDEAS']):
    box('Console book '+title,(-4.5,2.16,.78+i*.065),(1.00,.41,.06),graphite,'03')
    text('Book spine '+title,title,(-4.5,1.946,.785+i*.065),.032,'03')
box('Globe pedestal',(-3.52,2.20,.80),(.30,.30,.10),graphite,'03')
globe_paths = [ellipse((-3.52,2.20,1.095),.225,.225,'XZ'),
               ellipse((-3.52,2.20,1.095),.225,.225,'YZ')]
for z in [-.15,0,.15]:
    globe_paths.append(ellipse((-3.52,2.20,1.095+z),math.sqrt(.225**2-z*z),math.sqrt(.225**2-z*z)))
lines('Console wire globe',globe_paths,edge,.0025,'03')

# One quiet human silhouette looking out at the city, hands behind the back.
def observer(origin):
    forms = []
    def blob(center,size,n,rotation=None):
        forms.append((Vector(center),size,n,rotation))
    def limb(a,b,r,n):
        a,b = Vector(a),Vector(b)
        blob((a+b)/2,(r,r*.90,(b-a).length*.56),n,(b-a).to_track_quat('Z','Y'))
    blob((0,0,1.79),(.12,.115,.16),240)
    blob((0,0,1.44),(.235,.12,.27),600)
    blob((0,0,1.09),(.16,.105,.17),200)
    limb((0,0,1.64),(0,0,1.68),.055,60)
    for side in [-1,1]:
        limb((side*.12,0,1.05),(side*.13,0,.55),.075,350)
        limb((side*.13,0,.55),(side*.15,0,.085),.055,300)
        blob((side*.15,-.07,.055),(.073,.14,.045),110)
        limb((side*.23,0,1.52),(side*.29,.12,1.18),.059,230)
        limb((side*.29,.12,1.18),(side*.065,.19,.99),.046,210)
        blob((side*.065,.19,.99),(.048,.045,.065),75)
    dots = []
    for center,size,n,rotation in forms:
        for _ in range(n):
            u = random.uniform(-1,1); a = random.uniform(0,math.tau); r = math.sqrt(1-u*u)
            v = Vector((size[0]*r*math.cos(a),size[1]*r*math.sin(a),size[2]*u))
            if rotation:
                v = rotation @ v
            v = (center+v)*1.04
            # Facing +Y into the windows, preserving separated feet and arms.
            dots.append((origin[0]-v.x,origin[1]-v.y,origin[2]+v.z))
    obj = particles('Observer / looking out at city',dots,.0055,'06')
    obj['pose'] = 'Standing, looking through windows, hands behind back'
    return obj


observer((-3.10,1.30,0))
particles('Floating office dust',[(random.uniform(-6,6),random.uniform(-7,5),random.uniform(.1,4.5))
                                  for _ in range(750)],.003,'07',dust_mat)
particles('Outside night particles',[(random.uniform(-25,25),random.uniform(8,30),random.uniform(0,16))
                                     for _ in range(700)],.004,'07',dust_mat)

environment = build_environment(scene, box, lines, text, material, particles, ellipse)


def camera(name,position,target,lens):
    data = bpy.data.cameras.new('Office • '+name)
    obj = link(name,data,'08'); obj.location = position
    obj.rotation_euler = (Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
    data.lens = lens; data.clip_start = .04; data.clip_end = 150
    return obj


def apply_name_card_click_hint(root,face):
    """Keep the camera wide; animate only a subtle clickable-card highlight."""
    glow = bpy.data.materials.get('Office • Business card clickable glow')
    if glow is None:
        glow = material('Business card clickable glow',.8,emission=2.2,roughness=.7)
    p = glow.node_tree.nodes.get('Principled BSDF')
    strength = p.inputs['Emission Strength']
    for frame,value in [(1,2.2),(46,5.0),(91,2.2),(136,5.0),(181,2.2)]:
        strength.default_value = value
        strength.keyframe_insert(data_path='default_value',frame=frame)
    for layer in glow.node_tree.animation_data.action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:
                        key.interpolation = 'BEZIER'
                        key.handle_left_type = 'AUTO_CLAMPED'
                        key.handle_right_type = 'AUTO_CLAMPED'
                    if not any(m.type=='CYCLES' for m in curve.modifiers):
                        curve.modifiers.new('CYCLES')
    halo = lines('Name card / clickable luminous rim',
                 [[(-.047,-.0295,.0010),(.047,-.0295,.0010),(.047,.0295,.0010),
                   (-.047,.0295,.0010),(-.047,-.0295,.0010)]],glow,.00020,'10')
    halo.parent = root
    x,y,z = .0455,.0275,.0012
    spark = lines('Name card / soft corner glint',
                  [[(x-.007,y,z),(x+.007,y,z)],[(x,y-.007,z),(x,y+.007,z)],
                   [(x-.003,y-.003,z),(x+.003,y+.003,z)],
                   [(x-.003,y+.003,z),(x+.003,y-.003,z)]],glow,.00016,'10')
    spark.parent = root
    root['interaction'] = 'Click/tap only → contact focus; no automatic camera zoom'
    root['auto_zoom'] = False
    root['idle_hint'] = 'Soft repeating luminous rim and corner glint'
    face['interaction_trigger'] = 'click_or_tap'
    face['auto_zoom'] = False
    scene.camera = scene.objects['Office • About office presentation camera']
    scene.render.fps = 30
    scene.frame_start = 1; scene.frame_end = 180
    old_labels = {'01 / Office overview','02 / Name-card zoom preview','03 / Contact details','04 / Hold contact view'}
    for marker in list(scene.timeline_markers):
        if marker.name in old_labels or marker.name.startswith('Card hint /'):
            scene.timeline_markers.remove(marker)
    for frame,label in [(1,'Card hint / wide office view'),(46,'Card hint / shine peak'),
                        (91,'Card hint / soft glow'),(136,'Card hint / shine peak 2')]:
        scene.timeline_markers.new(label,frame=frame)
    scene.frame_set(1); bpy.context.view_layer.update()
    return {'auto_zoom':False,'interaction_trigger':'click_or_tap',
            'idle_hint':'Pulsing rim and corner glint','idle_frames':[1,180],
            'shine_strength_range':[2.2,5.0]}


def build_name_card(name=None,contact_url=None):
    """A flat paper card; the contact-focus camera is used only on request."""
    before = set(scene.objects)
    details = read_contact_details()
    name = name or details['name']
    contact_url = contact_url or details['github']
    details.update(name=name, github=contact_url)
    root = link('Name card / interactive assembly',None,'10')
    root['interaction'] = 'Planned website click: zoom to contact camera and show contact details'
    root['contact_name'] = name
    root['contact_url'] = contact_url
    root['contact_email'] = details['email']
    root['contact_phone'] = details['phone']
    root['contact_whatsapp'] = details['whatsapp']
    root['dimensions_m'] = [.09,.055,.0008]
    root['layout'] = 'Flat paper business card, 90 x 55 mm, slight rotation on desk'
    paper = material('Business card charcoal paper',.08,emission=.20,roughness=1)
    box('Name card / paper',(0,0,0),(.09,.055,.0008),paper,'10',outline=False)
    lines('Name card / fine printed border',[[(-.0435,-.0265,.00050),(.0435,-.0265,.00050),
                                            (.0435,.0265,.00050),(-.0435,.0265,.00050),
                                            (-.0435,-.0265,.00050)]],screen_line,.000075,'10')
    mesh = bpy.data.meshes.new('Office • Name card / UV contact face')
    mesh.from_pydata([(-.0435,-.0265,0),(.0435,-.0265,0),(.0435,.0265,0),(-.0435,.0265,0)],[],[(0,1,2,3)])
    uv = mesh.uv_layers.new(name='CardUV')
    for loop,co in zip(uv.data,[(0,0),(1,0),(1,1),(0,1)]):
        loop.uv = co
    mesh.materials.append(paper)
    face = link('Name card / contact face',mesh,'10')
    face.location = (0,0,.00048)
    face['web_role'] = 'Future click/tap contact target'
    face['contact_url'] = contact_url
    print_objects = [text('Name card / '+label,body,(0,y,.00060),size,'10',
                          mat=screen_line if label=='name' else type_mat)
                     for label,body,y,size in contact_card_lines(details)]
    for obj in print_objects:
        obj.rotation_euler = (0,0,0)
    for obj in set(scene.objects)-before:
        if obj != root and obj.parent is None:
            obj.parent = root
    root.location = (1.82,-.16,.8962)
    root.rotation_euler.z = .18
    focus = camera('Contact card focus camera',(1.832,-.26,1.0262),(1.82,-.16,.89668),45)
    root['focus_camera'] = focus.name
    face['focus_camera'] = focus.name
    hint = apply_name_card_click_hint(root,face)
    return {'name':name,'url':contact_url,'email':details['email'],'phone':details['phone'],
            'whatsapp':details['whatsapp'],'face_mesh':face.name,'focus_camera':focus.name,
            'dimensions_m':[.09,.055,.0008],'layout':'Flat on desk',
            **hint,'interaction_status':'Click-triggered contact focus prepared; website interaction planned'}


hero_camera = camera('About office presentation camera',(.35,-5.5,2.15),(.35,1.07,1.49),28)
camera('Screen detail camera',(.35,-1.7,1.64),(.35,1.07,1.49),32)
camera('Office arrival camera',(0,-6.5,1.70),(0,2.6,1.65),20)
camera('Office architectural overview camera',(5.4,-5.5,3.8),(-.4,1.4,1.3),23)
scene.camera = hero_camera
contact_card = build_name_card()
scene.frame_end = scene.get('Aquarium loop frames', scene.frame_end)
scene.frame_set(1)
for name,position in [('Entrance',(0,-6.8,0)),('About screen',(.35,1.07,1.49)),
                       ('Observer focus',(-3.10,1.30,1.5))]:
    obj = link(name+' / anchor',None,'09'); obj.location = position
    obj.empty_display_type = 'ARROWS'; obj.empty_display_size = .25
for x,y,z,energy,size in [(-2,1,4.42,75,3),(3,-1,4.42,60,3),(.35,.6,3.2,18,1.8)]:
    data = bpy.data.lights.new('Office • Soft white bounce','AREA')
    data.energy = energy; data.shape = 'DISK'; data.size = size
    obj = link('Soft white bounce',data,'08'); obj.location = (x,y,z)
world = bpy.data.worlds.new('Office • Absolute black world'); world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (0,0,0,1)
world.node_tree.nodes['Background'].inputs[1].default_value = 0
scene.world = world
scene.render.engine = 'CYCLES'
scene.cycles.samples = 48; scene.cycles.use_denoising = False
scene.cycles.max_bounces = 5; scene.cycles.diffuse_bounces = 1; scene.cycles.glossy_bounces = 3
scene.render.resolution_x = 1440; scene.render.resolution_y = 840
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'Standard'; scene.view_settings.look = 'None'
scene.render.film_transparent = False
scene.render.filepath = str(ROOT/'office-preview.png')
tree = bpy.data.node_groups.new('Office • Restrained architectural glow','CompositorNodeTree')
tree.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
render = tree.nodes.new('CompositorNodeRLayers'); render.scene = scene; render.location = (-300,0)
glow = tree.nodes.new('CompositorNodeGlare'); glow.location = (-30,0)
glow.inputs['Type'].default_value = 'Fog Glow'; glow.inputs['Quality'].default_value = 'High'
glow.inputs['Threshold'].default_value = 1.2; glow.inputs['Strength'].default_value = .15
glow.inputs['Size'].default_value = .18
output = tree.nodes.new('NodeGroupOutput'); output.location = (240,0)
tree.links.new(render.outputs['Image'],glow.inputs['Image'])
tree.links.new(glow.outputs['Image'],output.inputs['Image'])
scene.compositing_node_group = tree
for old in factory_scenes:
    bpy.data.scenes.remove(old)
bpy.context.view_layer.update()
assert scene.objects['Office • About content screen / web texture target'].data.uv_layers
assert len(collections['06'].objects)==1
assert len([o for o in collections['04'].objects if o.name.startswith('Office • Skyline tower') and o.type=='MESH'])==45
scene['Design reference'] = 'About Us office: panoramic city windows, black reflective floor, fine white outlines and particle human.'
scene['Screen note'] = 'Monochrome Malaysia geography: Peninsular Malaysia, Sabah and Sarawak; Natural Earth public-domain map data.'
scene['Entrance direction'] = '+Y inward; Z up; room entrance (0,-6.8,0)'
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective = 'CAMERA'
            area.spaces.active.region_3d.view_camera_zoom = 18
            area.spaces.active.region_3d.view_camera_offset = (0,0)
            area.spaces.active.overlay.show_overlays = False
            area.spaces.active.shading.type = 'MATERIAL'
            if hasattr(area.spaces.active.shading,'use_compositor'):
                area.spaces.active.shading.use_compositor = 'CAMERA'
bpy.ops.object.select_all(action='DESELECT')
scene.camera.select_set(True); bpy.context.view_layer.objects.active = scene.camera
bpy.context.preferences.filepaths.save_version = 1
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'about-office.blend'))
manifest = {'blend':'about-office.blend','scene':scene.name,'section':'About Us',
            'dimensions_m':{'width':12,'depth':12,'height':4.6},
            'entrance_anchor':[0,-6.8,0],'forward_axis':'+Y','up_axis':'+Z',
            'presentation_camera':hero_camera.name,'screen_mesh':display.name,
            'presentation_target':list(display.location),'presentation_view':'Computer-centered presentation; browser drag/free-look',
            'active_camera':scene.camera.name,'contact_card':contact_card,
            'environment':environment,
            'screen_aspect_ratio':display['aspect_ratio'],'skyline_towers':45,
            'objects':len(scene.objects),'particle_count':sum(o.get('particle_count',0) for o in scene.objects),
            'existing_assets_modified':False,'screen_content':'Monochrome Malaysia geography','malaysia_map':malaysia_map,
            'integration_status':'Standalone office; not yet connected to the elevator or website.'}
(ROOT/'office-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
if '--render' in sys.argv:
    for name,width,height,filename in [('About office presentation camera',1440,840,'office-preview.png'),
                                      ('Screen detail camera',1200,800,'office-screen.png'),
                                      ('Office architectural overview camera',1280,800,'office-overview.png'),
                                      ('Contact card focus camera',1280,800,'office-name-card.png')]:
        scene.camera = scene.objects['Office • '+name]
        scene.render.resolution_x = width; scene.render.resolution_y = height
        scene.render.filepath = str(ROOT/filename)
        bpy.ops.render.render(write_still=True)
    scene.camera = hero_camera
    scene.render.resolution_x = 1440; scene.render.resolution_y = 840
    scene.render.filepath = str(ROOT/'office-preview.png')
print(json.dumps({'checks':'passed',**manifest}))
