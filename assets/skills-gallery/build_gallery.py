"""Editable monochrome Skills Gallery with articulated particle visitors.

blender --background --factory-startup --python assets/skills-gallery/build_gallery.py -- --render
"""
import json
import math
from pathlib import Path
import random
import sys

import bpy
from mathutils import Euler, Vector

ROOT = Path(__file__).resolve().parent
SKILLS=json.loads((ROOT/'skills.json').read_text())['entries']
if bpy.data.filepath:
    raise RuntimeError('Generate with --factory-startup to preserve existing models.')
random.seed(63)
factory_scenes = list(bpy.data.scenes)
scene = bpy.data.scenes.new('SKILLS / Technology Gallery')
bpy.context.window.scene = scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'METERS'
scene.render.fps = 30
scene.frame_start = 1; scene.frame_end = 960
collections = {}
for label in ['01 Architecture', '02 Skill exhibits', '03 Sculpture & seating',
              '04 Lighting & atmosphere', '05 Particle visitors',
              '06 Cameras', '07 Integration anchors', '08 AT-AT centre exhibit']:
    col = bpy.data.collections.new('Gallery • '+label)
    scene.collection.children.link(col)
    collections[label[:2]] = col


def link(name,data=None,group='01'):
    obj = bpy.data.objects.new('Gallery • '+name,data)
    collections[group].objects.link(obj)
    return obj


def material(name,gray,emission=0,roughness=.5,metallic=0):
    mat = bpy.data.materials.new('Gallery • '+name)
    mat.diffuse_color = (gray,gray,gray,1)
    mat.use_nodes = True
    p = mat.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (gray,gray,gray,1)
    p.inputs['Emission Color'].default_value = (gray,gray,gray,1)
    p.inputs['Emission Strength'].default_value = emission
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Metallic'].default_value = metallic
    return mat


black = material('Black architectural backing',.002,roughness=.82)
graphite = material('Exhibit graphite',.011,roughness=.35,metallic=.25)
floor_mat = material('Polished black gallery floor',.009,roughness=.10,metallic=.70)
edge = material('Fine silver feature lines',.32,emission=1.1)
quiet = material('Secondary graphite lines',.11,emission=.8)
white = material('Luminous exhibit borders',.70,emission=3.5)
type_mat = material('Silver exhibit typography',.48,emission=1.0)
particle_mat = material('Lobby-style white surface particles',.55,emission=1.1)
dust_mat = material('Sparse ambient dust',.14,emission=.55)


def lines(name,paths,mat=edge,radius=.003,group='01'):
    data = bpy.data.curves.new('Gallery • '+name,'CURVE')
    data.dimensions = '3D'; data.resolution_u = 1
    data.bevel_depth = radius; data.bevel_resolution = 0
    for path in paths:
        spline = data.splines.new('POLY'); spline.points.add(len(path)-1)
        for point,co in zip(spline.points,path):
            point.co = (*co,1)
    obj = link(name,data,group); data.materials.append(mat)
    return obj


def box(name,center,size,mat=black,group='01',outline=True,edge_mat=edge):
    x,y,z = (s/2 for s in size)
    verts = [(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),
             (-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)]
    faces = [(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)]
    data = bpy.data.meshes.new('Gallery • '+name)
    data.from_pydata(verts,[],faces); data.materials.append(mat)
    obj = link(name,data,group); obj.location = center
    if outline:
        edges = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
        wire = lines(name+' / feature edges',[[verts[a],verts[b]] for a,b in edges],edge_mat,.003,group)
        wire.parent = obj
    return obj


def text(name,body,position,size=.14,group='02',align='CENTER',mat=type_mat,max_width=None):
    data = bpy.data.curves.new('Gallery • '+name,'FONT')
    data.body = body; data.align_x = align; data.align_y = 'CENTER'
    data.size = size; data.space_character = 1.15; data.space_line = 1.35
    obj = link(name,data,group); obj.location = position
    obj.rotation_euler = (math.pi/2,0,0); data.materials.append(mat)
    if max_width:
        bpy.context.view_layer.update()
        width=max(point[0] for point in obj.bound_box)-min(point[0] for point in obj.bound_box)
        if width>max_width:
            data.size*=max_width/width
    return obj


def circle_xz(x,y,z,r,n=48):
    return [(x+r*math.cos(i*math.tau/n),y,z+r*math.sin(i*math.tau/n)) for i in range(n+1)]


def point_display(name,vertices,mat=particle_mat,radius=.0055,group='05',shared=None):
    mesh = bpy.data.meshes.new('Gallery • '+name+' / editable point positions')
    mesh.from_pydata(vertices,[],[])
    obj = link(name,mesh,group)
    tree = shared
    if tree is None:
        tree = bpy.data.node_groups.new('Gallery • '+name+' / sphere display','GeometryNodeTree')
        tree.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
        tree.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
        inp = tree.nodes.new('NodeGroupInput'); inp.location = (-450,50)
        points = tree.nodes.new('GeometryNodeMeshToPoints'); points.mode = 'VERTICES'; points.location = (-250,50)
        ico = tree.nodes.new('GeometryNodeMeshIcoSphere'); ico.location = (-250,-140)
        ico.inputs['Radius'].default_value = radius; ico.inputs['Subdivisions'].default_value = 1
        shade = tree.nodes.new('GeometryNodeSetMaterial'); shade.location = (-30,-140)
        shade.inputs['Material'].default_value = mat
        inst = tree.nodes.new('GeometryNodeInstanceOnPoints'); inst.location = (170,50)
        out = tree.nodes.new('NodeGroupOutput'); out.location = (390,50)
        tree.links.new(inp.outputs['Geometry'],points.inputs['Mesh'])
        tree.links.new(ico.outputs['Mesh'],shade.inputs['Geometry'])
        tree.links.new(points.outputs['Points'],inst.inputs['Points'])
        tree.links.new(shade.outputs['Geometry'],inst.inputs['Instance'])
        tree.links.new(inst.outputs['Instances'],out.inputs['Geometry'])
    obj.modifiers.new('Particle rendering / editable source','NODES').node_group = tree
    obj['particle_count'] = len(vertices)
    return obj,tree


# Architecture: full room with a presentation cutaway at the entrance.
box('Reflective tiled floor',(0,1,-.10),(12,16,.20),floor_mat,outline=False)
box('Black ceiling',(0,1,5.5),(12,16,.20),black,outline=False)
for side in [-1,1]:
    box('Side gallery wall',(side*6.10,1,2.7),(.20,16,5.4),black,outline=False)
    for y in [-6.5,-3.0,.5,4,8.8]:
        box('Wall structural reveal',(side*5.985,y,2.7),(.035,.065,5.35),graphite,edge_mat=quiet)
    for z in [.12,.34,4.75,5.35]:
        lines('Side wall horizontal reveal',[[(side*5.98,-7,z),(side*5.98,9,z)]],quiet,.0025)
    lines('Gallery skirting light',[[(side*5.91,-6.9,.12),(side*5.91,8.9,.12)]],white,.009)
box('Rear exhibit wall',(0,9.10,2.7),(12,.20,5.4),black,outline=False)
for x in [-5.8,-4.2,-2.1,0,2.1,4.2,5.8]:
    lines('Rear wall seam',[[(x,8.99,.08),(x,8.99,5.35)]],quiet,.0025)
lines('Rear skirting light',[[(-5.9,8.92,.12),(5.9,8.92,.12)]],white,.009)
for x in range(-6,7):
    lines('Floor longitudinal joint',[[(x,-7,.008),(x,9,.008)]],quiet,.0015)
for y in range(-7,10):
    lines('Floor transverse joint',[[(-6,y,.008),(6,y,.008)]],quiet,.0015)
for x in range(-6,7):
    lines('Ceiling longitudinal grid',[[(x,-7,5.385),(x,9,5.385)]],quiet,.0015)
for y in range(-7,10):
    lines('Ceiling transverse grid',[[(-6,y,5.385),(6,y,5.385)]],quiet,.0015)
lines('Ceiling luminous perimeter',[[(-4.3,-4.8,5.35),(4.3,-4.8,5.35),(4.3,7.2,5.35),
                                      (-4.3,7.2,5.35),(-4.3,-4.8,5.35)]],white,.015)
text('Rear gallery title','T E C H N O L O G Y   S K I L L S',(0,8.94,4.94),.185,'01')
text('Rear gallery subtitle','DISCIPLINE  /  CREATIVITY\nOPPORTUNITY',(0,8.94,4.56),.074,'01')


def exhibit(index,title,items,icon,center,angle,width=2.35):
    before = set(scene.objects)
    root = link('Exhibit %02d / %s' % (index,title),group='02')
    root['category'] = title; root['concept_items'] = ' / '.join(items)
    content=SKILLS[index-1]
    root['content_status'] = content['contentStatus']
    root['skill_id']=content['id'];root['skill_metadata']=json.dumps(content)
    height = 3.50
    box('Exhibit %02d / backing' % index,(0,0,0),(width,.09,height),graphite,'02',edge_mat=quiet)
    for inset,mat,radius in [(0,white,.005),(.055,edge,.0025)]:
        x,z = width/2-inset,height/2-inset
        lines('Exhibit %02d / illuminated border' % index,
              [[(-x,-.065,-z),(x,-.065,-z),(x,-.065,z),(-x,-.065,z),(-x,-.065,-z)]],mat,radius,'02')
    mesh = bpy.data.meshes.new('Gallery • Exhibit %02d / UV surface' % index)
    mesh.from_pydata([(-width/2+.08,0,-height/2+.08),(width/2-.08,0,-height/2+.08),
                      (width/2-.08,0,height/2-.08),(-width/2+.08,0,height/2-.08)],[],[(0,1,2,3)])
    uv = mesh.uv_layers.new(name='ExhibitUV')
    for loop,co in zip(uv.data,[(0,0),(1,0),(1,1),(0,1)]):
        loop.uv = co
    mesh.materials.append(black)
    surface = link('Exhibit %02d / content surface' % index,mesh,'02'); surface.location.y = -.055
    surface['web_role'] = 'Separate portrait skill-exhibit content surface'
    y = -.073
    text('Exhibit %02d / index' % index,'%02d' % index,(-width/2+.15,y,1.52),.08,'02',align='LEFT')
    paths = []
    if icon=='code':
        paths = [[(-.12,y,1.03),(-.31,y,1.17),(-.12,y,1.31)],
                 [(.12,y,1.03),(.31,y,1.17),(.12,y,1.31)],[(.08,y,1.36),(-.08,y,.99)]]
    elif icon=='window':
        paths = [[(-.29,y,1.0),(.29,y,1.0),(.29,y,1.34),(-.29,y,1.34),(-.29,y,1.0)],
                 [(-.29,y,1.27),(.29,y,1.27)]]
    elif icon=='gear':
        paths = [circle_xz(0,y,1.17,.23),circle_xz(0,y,1.17,.11)]
        for i in range(12):
            a = i*math.tau/12
            paths.append([(.23*math.cos(a),y,1.17+.23*math.sin(a)),
                          (.29*math.cos(a),y,1.17+.29*math.sin(a))])
    elif icon=='database':
        for z in [1.02,1.17,1.32]:
            paths.append([(.26*math.cos(i*math.tau/32),y,z+.065*math.sin(i*math.tau/32)) for i in range(33)])
        paths += [[(-.26,y,1.02),(-.26,y,1.32)],[(.26,y,1.02),(.26,y,1.32)]]
    elif icon=='brain':
        nodes = [(-.20,1.08),(-.25,1.27),(-.12,1.39),(0,1.28),(.12,1.39),(.25,1.27),(.20,1.08),(0,1.0)]
        paths = [[(x,y,z) for x,z in nodes]+[(-.20,y,1.08)],[(0,y,1.0),(0,y,1.38)]]
        for i,j in [(0,3),(1,7),(2,6),(3,5),(4,7)]:
            paths.append([(nodes[i][0],y,nodes[i][1]),(nodes[j][0],y,nodes[j][1])])
    elif icon=='shield':
        paths = [[(-.26,y,1.35),(0,y,1.42),(.26,y,1.35),(.22,y,1.12),
                  (0,y,.95),(-.22,y,1.12),(-.26,y,1.35)],
                 [(-.10,y,1.20),(-.02,y,1.10),(.13,y,1.29)]]
    elif icon=='infinity':
        paths = [[(.35*math.cos(i*math.tau/64),y,1.17+.17*math.sin(2*i*math.tau/64)) for i in range(65)]]
    elif icon=='services':
        for z in [1.0,1.15,1.3]:
            paths.append([(-.28,y,z),(.28,y,z),(.28,y,z+.09),(-.28,y,z+.09),(-.28,y,z)])
        paths += [[(-.18,y,1.03),(-.14,y,1.03)],[(-.18,y,1.18),(-.14,y,1.18)],[(-.18,y,1.33),(-.14,y,1.33)]]
    elif icon=='linux':
        paths = [circle_xz(0,y,1.29,.13),
                 [(-.10,y,1.17),(-.20,y,.97),(-.26,y,.94),(-.10,y,.91),(0,y,.95),
                  (.10,y,.91),(.26,y,.94),(.20,y,.97),(.10,y,1.17)],
                 [(-.055,y,1.24),(0,y,1.20),(.055,y,1.24)]]
    lines('Exhibit %02d / symbol' % index,paths,edge,.005,'02')
    text('Exhibit %02d / heading' % index,title.upper(),(0,y,.62),.17,'02',max_width=width*.88)
    text('Exhibit %02d / subheading' % index,'APPLIED / PROJECT EVIDENCE',(0,y,.36),.058,'02',max_width=width*.84)
    branch_x = -width*.34
    branches = [[(branch_x,y,.08),(branch_x,y,-1.27)]]
    for i,item in enumerate(items):
        z = -.13-i*.30
        branches.append([(branch_x,y,z),(branch_x+.13,y,z)])
        text('Exhibit %02d / item %02d' % (index,i),item,(branch_x+.20,y,z),.115,'02',align='LEFT',max_width=width*.66)
    lines('Exhibit %02d / taxonomy branches' % index,branches,edge,.003,'02')
    text('Exhibit %02d / footer' % index,'ABOUT + PROJECTS / %02d' % index,(0,y,-1.53),.056,'02')
    for obj in set(scene.objects)-before:
        if obj!=root and obj.parent is None:
            obj.parent = root
    root.location = center; root.rotation_euler.z = angle
    return root


exhibits = [
    (1,'code',(-5.94,-.3,2.65),math.pi/2,3.30),
    (2,'window',(-5.94,5.0,2.65),math.pi/2,3.30),
    (3,'gear',(-3.30,8.94,2.65),0,2.75),
    (4,'database',(0,8.94,2.65),0,2.75),
    (5,'brain',(3.30,8.94,2.65),0,2.75),
    (6,'shield',(5.94,6.9,2.65),-math.pi/2,2.35),
    (7,'infinity',(5.94,3.7,2.65),-math.pi/2,2.35),
    (8,'services',(5.94,.5,2.65),-math.pi/2,2.35),
    (9,'linux',(5.94,-2.7,2.65),-math.pi/2,2.35),
]
for params in exhibits:
    content=SKILLS[params[0]-1]
    exhibit(params[0],content['title'],content['displayItems'],*params[1:])

def build_legacy_wire_trex():
    """Original reconstructed T-Rex silhouette with scanner lines and particles."""
    rng = random.Random(927)
    scanner = material('T-Rex scanner silver',.45,emission=1.8)
    teeth_mat = material('T-Rex pale teeth and claws',.30,emission=1.2,roughness=.6)
    box('T-Rex / low display plinth',(-.20,3.85,.16),(7.40,3.20,.32),graphite,'08')
    lines('T-Rex / plinth light',[ [(-3.9,2.245,.06),(3.5,2.245,.06),(3.5,5.45,.06),
                                  (-3.9,5.45,.06),(-3.9,2.245,.06)] ],white,.010,'08')
    text('T-Rex / display title','T Y R A N N O S A U R U S   R E X',(-.20,2.235,.22),.10,'08')
    text('T-Rex / display subtitle','SCULPTURE 01  /  GENERATIVE FORMS',(-.20,2.235,.105),.045,'08')
    root = link('T-Rex / centre sculpture',group='08')
    root['exhibit_role'] = 'Static original wire-and-particle T-Rex reconstruction'
    root['plinth_rect'] = [-.20,3.85,7.40,3.20]
    surface_points = []

    def sample_surface(mesh,count):
        mesh.calc_loop_triangles()
        triangles = list(mesh.loop_triangles)
        choices = rng.choices(triangles,weights=[max(t.area,.000001) for t in triangles],k=count)
        for tri in choices:
            a,b,c = [mesh.vertices[i].co.copy() for i in tri.vertices]
            u,v = rng.random(),rng.random()
            if u+v>1:
                u,v = 1-u,1-v
            normal = (b-a).cross(c-a).normalized()
            surface_points.append(tuple(a+u*(b-a)+v*(c-a)+normal*.004))

    def loft(name,rings,count=200,n=20,mat=black):
        """Swept elliptical sections, with a few silhouette lines rather than a cage."""
        centres = [Vector(r[0]) for r in rings]
        verts = []
        for i,(center,ry,rz) in enumerate(rings):
            axis = (centres[min(i+1,len(rings)-1)]-centres[max(0,i-1)]).normalized()
            first = Vector((0,1,0)); first -= axis*first.dot(axis)
            if first.length<.1:
                first = Vector((1,0,0)); first -= axis*first.dot(axis)
            first.normalize(); second = axis.cross(first).normalized()
            for j in range(n):
                a = j*math.tau/n
                verts.append(tuple(Vector(center)+first*ry*math.cos(a)+second*rz*math.sin(a)))
        faces = [tuple(range(n-1,-1,-1)),tuple(range((len(rings)-1)*n,len(rings)*n))]
        faces += [(i*n+j,i*n+(j+1)%n,(i+1)*n+(j+1)%n,(i+1)*n+j)
                  for i in range(len(rings)-1) for j in range(n)]
        mesh = bpy.data.meshes.new('Gallery • T-Rex / '+name)
        mesh.from_pydata(verts,[],faces); mesh.materials.append(mat)
        obj = link('T-Rex / '+name,mesh,'08'); obj.parent = root
        obj['trex_surface'] = True
        paths = [[verts[i*n+j] for i in range(len(rings))] for j in [0,n//4,n//2,3*n//4]]
        paths += [[verts[i*n+j] for j in range(n)]+[verts[i*n]] for i in range(1,len(rings)-1)]
        wire = lines('T-Rex / '+name+' contours',paths,scanner,.0035,'08'); wire.parent = root
        sample_surface(mesh,count)
        return obj

    def cone(name,start,end,radius,mat=teeth_mat):
        start,end = Vector(start),Vector(end)
        axis = (end-start).normalized()
        first = Vector((0,1,0)); first -= axis*first.dot(axis)
        first.normalize(); second = axis.cross(first).normalized()
        verts = [tuple(start+radius*(first*math.cos(i*math.tau/7)+second*math.sin(i*math.tau/7)))
                 for i in range(7)]+[tuple(end)]
        faces = [tuple(range(6,-1,-1))]+[(i,(i+1)%7,7) for i in range(7)]
        mesh = bpy.data.meshes.new('Gallery • T-Rex / '+name)
        mesh.from_pydata(verts,[],faces); mesh.materials.append(mat)
        obj = link('T-Rex / '+name,mesh,'08'); obj.parent = root

    loft('torso and hips', [((-1.45,0,1.95),.28,.35),((-1.05,0,2.12),.61,.65),
                           ((-.35,0,2.26),.68,.73),((.32,0,2.43),.55,.62),
                           ((.70,0,2.65),.28,.40)],1400)
    loft('raised neck',[((.55,0,2.56),.29,.38),((.82,0,3.02),.27,.35),
                        ((1.20,0,3.33),.30,.34)],500)
    loft('long tapering tail',[((-1.28,0,2.03),.40,.39),((-1.82,.025,1.97),.32,.30),
                               ((-2.48,.08,1.60),.19,.20),((-3.15,.17,1.30),.085,.095),
                               ((-3.75,.24,1.43),.012,.018)],850)
    loft('large skull',[((1.13,0,3.40),.31,.36),((1.48,0,3.54),.46,.40),
                        ((2.05,0,3.49),.42,.29),((2.70,0,3.40),.31,.22)],1300)
    loft('open lower jaw',[((1.22,0,3.16),.27,.10),((1.73,0,3.02),.36,.09),
                            ((2.18,0,2.94),.34,.07),((2.70,0,2.91),.27,.065)],550)
    # Eye sockets and nostrils are feature rings on both sides of the dark skull.
    for side in [-1,1]:
        socket = lines('T-Rex / eye socket', [circle_xz(1.49,side*.466,3.62,.128),
                                              circle_xz(1.49,side*.470,3.62,.067)],scanner,.003,'08')
        socket.parent = root
        nostril = lines('T-Rex / nostril',[circle_xz(2.46,side*.346,3.43,.038)],edge,.002,'08')
        nostril.parent = root
        cheek = lines('T-Rex / cheek fenestra', [[(1.14,side*.336,3.48),(1.22,side*.414,3.26),
                                                (1.47,side*.447,3.23),(1.37,side*.452,3.48),
                                                (1.14,side*.336,3.48)]],edge,.003,'08')
        cheek.parent = root
        for i in range(11):
            x = 1.48+i*.11; y = side*(.34-.045*i/10)
            upper_z = 3.16+.025*i/10
            cone('upper tooth %s %02d' % (side,i),(x,y,upper_z),(x+.022,y,upper_z-.105-.025*math.sin(i)),.023)
            lower_z = 3.075-.12*i/10
            cone('lower tooth %s %02d' % (side,i),(x,y,lower_z),(x+.018,y,lower_z+.085),.020)
        # Characteristic short arms and two claws per hand.
        loft('short upper arm %s' % side,[((.53,side*.52,2.44),.09,.095),
                                        ((.88,side*.65,2.13),.067,.072)],200,n=12)
        loft('short forearm %s' % side,[((.88,side*.65,2.13),.067,.067),
                                       ((1.10,side*.61,2.27),.045,.05)],160,n=12)
        for finger in [-1,1]:
            y = side*.61+finger*.065
            loft('two-finger hand %s %s' % (side,finger),
                 [((1.08,y,2.27),.024,.025),((1.31,y,2.22),.015,.018)],65,n=10)
            cone('hand claw %s %s' % (side,finger),(1.31,y,2.22),(1.43,y,2.15),.018)
        # Muscular hind legs, bent ankles, broad feet, and three forward toes.
        loft('powerful thigh %s' % side,[((-.64,side*.50,2.12),.30,.32),
                                        ((-.22,side*.60,1.66),.28,.30),
                                        ((.02,side*.65,1.28),.20,.22)],600)
        loft('shin %s' % side,[((.02,side*.65,1.28),.16,.19),
                               ((-.27,side*.69,.55),.11,.12),
                               ((-.19,side*.70,.24),.078,.085)],400)
        loft('heel and foot %s' % side,[((-.19,side*.70,.24),.09,.10),
                                       ((.08,side*.70,.06),.18,.06),
                                       ((.33,side*.70,.05),.19,.05)],220,n=16)
        for toe in [-1,0,1]:
            y = side*.70+toe*.14
            loft('toe %s %s' % (side,toe),[((.22,y,.065),.060,.050),
                                          ((.54,y+toe*.04,.060),.030,.030)],60,n=10)
            cone('foot claw %s %s' % (side,toe),(.54,y+toe*.04,.060),(.73,y+toe*.05,.018),.032)
    cloud,_ = point_display('T-Rex / scanner particles',surface_points,particle_mat,.0045,'08')
    cloud.parent = root
    root.location = (0,3.85,.32); root.rotation_euler.z = -.18
    root['style'] = 'Dark occluding surfaces, fine scanner contours, sparse surface particles'
    bpy.context.view_layer.update()
    vertices = [obj.matrix_world @ vertex.co for obj in collections['08'].objects
                if obj.type=='MESH' and obj.get('trex_surface') for vertex in obj.data.vertices]
    lo = [min(v[i] for v in vertices) for i in range(3)]
    hi = [max(v[i] for v in vertices) for i in range(3)]
    root['bounds_min'] = lo; root['bounds_max'] = hi
    assert hi[2]<5.2 and lo[0]>-4.0 and hi[0]<3.5
    return {'root':root.name,'bounds_min':lo,'bounds_max':hi,
            'dimensions_m':[hi[i]-lo[i] for i in range(3)],
            'plinth_rect':[-.20,3.85,7.40,3.20],'particle_count':len(surface_points)}


def build_centre_exhibit():
    """Build the outlined AT-AT from the supplied reference."""
    import importlib.util
    box('AT-AT / low display plinth',(-.20,3.85,.16),(7.40,3.20,.32),graphite,'08')
    lines('AT-AT / plinth light',[[(-3.9,2.245,.06),(3.5,2.245,.06),(3.5,5.45,.06),(-3.9,5.45,.06),(-3.9,2.245,.06)]],white,.004,'08')
    text('AT-AT / display title','A T - A T   W A L K E R',(-.20,2.235,.22),.10,'08')
    text('AT-AT / display subtitle','STAR WARS  /  MECHANICAL WALKER',(-.20,2.235,.105),.045,'08')
    spec = importlib.util.spec_from_file_location('gallery_atat',ROOT/'atat_walker.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module.build_atat_exhibit(scene,collections['08'])


centre_exhibit = build_centre_exhibit()
# Quiet museum seating remains around the larger centre exhibit.
box('Foreground museum bench',(0,-3.65,.44),(3.45,.70,.17),graphite,'03')
for x in [-1.5,1.5]:
    box('Foreground bench leg',(x,-3.65,.19),(.055,.61,.38),graphite,'03',edge_mat=quiet)
for side in [-1,1]:
    box('Side viewing bench',(side*4.65,-1.10,.44),(.72,2.15,.17),graphite,'03')
    for y in [-1.9,-.3]:
        box('Side bench support',(side*4.65,y,.20),(.63,.055,.40),graphite,'03',edge_mat=quiet)
text('Bench floor caption','A  M O R E  C A P A B L E  T O M O R R O W',(0,-4.20,.015),.065,'03').rotation_euler = (0,0,0)


def smooth_keys(owner,mode='BEZIER'):
    if not owner.animation_data or not owner.animation_data.action:
        return
    for layer in owner.animation_data.action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:
                        key.interpolation = mode
                        if mode=='BEZIER':
                            key.handle_left_type = 'AUTO_CLAMPED'; key.handle_right_type = 'AUTO_CLAMPED'


def blob_points(size,count,center=(0,0,0)):
    out = []
    for _ in range(count):
        u = random.uniform(-1,1); a = random.uniform(0,math.tau); r = math.sqrt(1-u*u)
        out.append((center[0]+size[0]*r*math.cos(a),center[1]+size[1]*r*math.sin(a),center[2]+size[2]*u))
    return out


visitor_tree = None
visitors = []


def visitor(label,origin,heading,activity,scale=1,phase=0,route=None):
    """Lobby proportions and particles, split into editable articulated parts."""
    global visitor_tree
    root = link('Visitor / '+label,group='05')
    root.location = origin; root.rotation_euler.z = heading; root.scale = (scale,scale,scale)
    root['activity'] = activity; root['style_reference'] = 'KAZE lobby articulated surface particles'
    if route:
        root['route_frames'] = [f for f,_ in route]
        for frame,y in route:
            root.location.y = y; root.keyframe_insert(data_path='location',frame=frame)
        turn_end = 390 if heading>2 else 395
        return_end = 660 if heading>2 else 665
        for frame,value in [(1,heading),(360,heading),(turn_end,heading+math.pi),
                            (return_end,heading+math.pi),(return_end+30,heading+math.tau),
                            (720,heading+math.tau)]:
            root.rotation_euler.z = value
            root.keyframe_insert(data_path='rotation_euler',frame=frame)
        smooth_keys(root)
    parts = {}
    def part(name,size,count,center=(0,0,0),nominal=0):
        global visitor_tree
        obj,visitor_tree = point_display(label+' / '+name,blob_points(size,count,center),shared=visitor_tree)
        obj.parent = root; obj.rotation_mode = 'QUATERNION'
        obj['joint'] = name; obj['nominal_length'] = nominal
        parts[name] = obj
        return obj
    part('pelvis',(.16,.105,.16),190)
    part('torso',(.23,.12,.26),470)
    head = part('head',(.115,.11,.155),230)
    nose = blob_points((.03,.045,.040),35,(0,-.107,-.016))
    head.data.clear_geometry(); head.data.from_pydata(blob_points((.115,.11,.155),230)+nose,[],[])
    head['particle_count'] = 265
    for side in ['L','R']:
        part('thigh_'+side,(.075,.069,.265),240,(0,0,.25),.50)
        part('shin_'+side,(.055,.055,.258),220,(0,0,.245),.49)
        part('foot_'+side,(.073,.145,.045),95)
        part('upper_arm_'+side,(.057,.056,.193),180,(0,0,.18),.36)
        part('forearm_'+side,(.043,.045,.162),145,(0,0,.15),.30)
        part('hand_'+side,(.042,.045,.062),65)
    info = {'root':root,'parts':parts,'phase':phase,'activity':activity,'route':route,
            'start_y':route[0][1] if route else origin[1],'previous_y':None,'travel_distance':0}
    visitors.append(info)
    return info


visitor('01 / walking then reading',(-2.60,-2.20,0),math.pi,'walk_pause_inspect',1.02,.11,
        [(1,-2.20),(30,-2.20),(155,1.25),(220,1.25),(360,4.85),
         (390,4.85),(660,-2.20),(720,-2.20)])
visitor('02 / strolling back toward entrance',(2.60,7.0,0),0,'walk_pause_inspect',.97,.47,
        [(1,7.0),(20,7.0),(140,4.0),(225,4.0),(360,.40),
         (395,.40),(665,7.0),(720,7.0)])
visitor('03 / studying frameworks',(-4.55,3.90,0),-2.18,'observing',1.04,.27)
visitor('04 / considering service diagrams',(4.55,4.90,0),.88,'thinking',.99,.61)
visitor('05 / explaining an exhibit',(-2.55,7.05,0),1.91,'explaining',1.01,.83)
visitor('06 / listening and looking',(-1.40,7.45,0),-1.235,'listening',.96,.39)


def configure_gallery_visitors(people):
    """Four two-dimensional tours and a conversational pair around the centre exhibit."""
    dino = (-2.20,3.35,3.60)
    plans = [
        {'label':'01 / exploring exhibits and AT-AT','idle':'standing',
         'route':[(1,(-2.6,-2.2,0)),(30,(-2.6,-2.2,0)),(130,(-3.7,.7,0)),
                  (205,(-3.7,.7,0)),(260,(-4.6,1.8,0)),(360,(-4.6,5.9,0)),
                  (400,(-3.6,6.55,0)),(450,(-3.6,6.55,0)),(495,(-4.6,5.9,0)),
                  (605,(-4.6,1.8,0)),(650,(-3.7,.7,0)),(800,(-2.6,-2.2,0)),
                  (960,(-2.6,-2.2,0))],
         'look':[(1,(-5.90,-.3,2.4)),(205,(-5.90,-.3,2.4)),(350,dino),
                 (450,dino),(560,(-5.90,5,2.4)),(730,(-5.90,-.3,2.4)),(960,(-5.90,-.3,2.4))]},
        {'label':'02 / circling the walker','idle':'standing',
         'route':[(1,(2.6,7,0)),(30,(2.6,7,0)),(75,(3.6,6.55,0)),(145,(3.6,6.55,0)),
                  (200,(4.55,5.9,0)),(320,(4.55,1.8,0)),(365,(3.6,.65,0)),(450,(3.6,.65,0)),
                  (510,(2.6,-2.1,0)),(565,(2.6,-2.1,0)),(620,(3.6,.65,0)),
                  (675,(4.55,1.8,0)),(815,(4.55,5.9,0)),(880,(2.6,7,0)),(960,(2.6,7,0))],
         'look':[(1,dino),(145,dino),(230,(5.90,3.7,2.4)),(450,(5.90,.5,2.4)),
                 (565,(5.90,-2.7,2.4)),(690,dino),(960,dino)]},
        {'label':'03 / strolling between left exhibits','idle':'observing',
         'route':[(1,(-5.4,.3,0)),(60,(-5.4,.3,0)),(240,(-5.4,5.9,0)),
                  (400,(-5.4,5.9,0)),(620,(-5.4,.3,0)),(960,(-5.4,.3,0))],
         'look':[(1,(-5.9,-.3,2.35)),(60,(-5.9,-.3,2.35)),(240,(-5.9,5,2.35)),
                 (400,(-5.9,5,2.35)),(620,(-5.9,-.3,2.35)),(960,(-5.9,-.3,2.35))]},
        {'label':'04 / strolling between right exhibits','idle':'thinking',
         'route':[(1,(5.4,-2.6,0)),(90,(5.4,-2.6,0)),(285,(5.4,3.8,0)),
                  (465,(5.4,3.8,0)),(685,(5.4,-2.6,0)),(960,(5.4,-2.6,0))],
         'look':[(1,(5.9,-2.7,2.35)),(90,(5.9,-2.7,2.35)),(285,(5.9,3.7,2.35)),
                 (465,(5.9,3.7,2.35)),(685,(5.9,-2.7,2.35)),(960,(5.9,-2.7,2.35))]},
        {'label':'05 / discussing the AT-AT','idle':'explaining','position':(-2.55,7.05,0),'heading':.95,
         'look':[(1,dino),(150,dino),(240,(-1.4,7.45,1.8)),(330,(-1.4,7.45,1.8)),
                 (440,dino),(640,dino),(760,(-1.4,7.45,1.8)),(870,dino),(960,dino)]},
        {'label':'06 / listening beside the sculpture','idle':'listening','position':(-1.4,7.45,0),'heading':-.25,
         'look':[(1,dino),(130,dino),(250,(-2.55,7.05,1.8)),(360,(-2.55,7.05,1.8)),
                 (500,dino),(730,(-2.55,7.05,1.8)),(875,dino),(960,dino)]},
    ]
    for info,plan in zip(people,plans):
        # Reserve front-left and rear-right lanes for the explorers. The player
        # can stop/jump anywhere without depending on a timed NPC phase offset.
        number = int(plan['label'][:2])
        if number == 1:
            plan['route'] = [(1,(-5.25,-5.5,0)),(90,(-5.25,-5.5,0)),
                             (360,(-5.25,-2.65,0)),(510,(-5.25,-2.65,0)),
                             (800,(-5.25,-5.5,0)),(960,(-5.25,-5.5,0))]
            plan['look'] = [(1,(-5.9,-2.7,2.35)),(960,(-5.9,-2.7,2.35))]
        elif number == 2:
            plan['route'] = [(1,(5.25,6.4,0)),(90,(5.25,6.4,0)),
                             (360,(5.25,8,0)),(510,(5.25,8,0)),
                             (800,(5.25,6.4,0)),(960,(5.25,6.4,0))]
            plan['look'] = [(1,(5.9,6.9,2.35)),(960,(5.9,6.9,2.35))]
        root = info['root']; root.animation_data_clear()
        for obj in info['parts'].values():
            obj.animation_data_clear()
        root.name = 'Gallery • Visitor / '+plan['label']
        for name,obj in info['parts'].items():
            obj.name = 'Gallery • '+plan['label']+' / '+name
        route = plan.get('route')
        root['activity'] = 'explore_walk_pause' if route else plan['idle']
        root['route_frames'] = [f for f,_ in route] if route else []
        root['look_schedule'] = json.dumps(plan['look'])
        if route:
            for frame,position in route:
                root.location = position; root.keyframe_insert(data_path='location',frame=frame)
            root.location = route[0][1]
            toward = Vector(plan['look'][0][1])-root.location
            heading = math.atan2(toward.x,-toward.y)
            root.rotation_euler.z = heading
            smooth_keys(root)
        else:
            root.location = plan['position']; root.rotation_euler.z = plan['heading']
            heading = plan['heading']
        info.update(route=route,idle_activity=plan['idle'],look_keys=plan['look'],
                    previous_position=None,travel_distance=0,gait_distance=0,
                    heading_value=heading,start_y=root.location.y)
    return plans


def gaze_target(keys,frame):
    if frame<=keys[0][0]:
        return Vector(keys[0][1])
    for (first,a),(last,b) in zip(keys,keys[1:]):
        if frame<=last:
            t = (frame-first)/(last-first)
            t = t*t*(3-2*t)
            return Vector(a).lerp(Vector(b),t)
    return Vector(keys[-1][1])


visitor_plans = configure_gallery_visitors(visitors)


def solve_knee(hip,ankle):
    axis = ankle-hip; distance = max(.001,axis.length)
    direction = axis.normalized()
    d = min(distance,.9899)
    a = (.50**2-.49**2+d*d)/(2*d)
    height = math.sqrt(max(0,.50**2-a*a))
    forward = Vector((0,direction.z,-direction.y)).normalized()
    return hip+direction*a+forward*height


def set_segment(obj,start,end):
    obj.location = start
    axis = end-start
    obj.rotation_quaternion = axis.to_track_quat('Z','Y')
    obj.scale.z = axis.length/obj['nominal_length']


def gait_foot(cycle):
    t = cycle%1
    if t<.60:
        return -.21+.42*(t/.60),.070,0
    swing = (t-.60)/.40
    ease = swing*swing*(3-2*swing)
    return .21-.42*ease,.070+.10*math.sin(math.pi*swing),swing


def pose_visitor(info,frame,speed):
    root,parts = info['root'],info['parts']
    seconds = (frame-1)/30
    offset = info['phase']*math.tau
    distance = info['gait_distance']
    cycle = distance/.70+info['phase']
    amp = min(1,speed/.60) if info['route'] else 0
    bob = .005*amp*math.cos(cycle*math.tau*2)+.003*math.sin(seconds*math.tau/4+offset)
    parts['pelvis'].location = (0,0,1.035+bob)
    parts['torso'].location = (0,-.010*amp,1.43+bob)
    parts['head'].location = (0,-.01,1.77+bob)
    activity = info.get('idle_activity',info['activity'])
    target = gaze_target(info['look_keys'],frame)
    toward = target-root.location
    desired = math.atan2(toward.x,-toward.y)
    relative = (desired-root.rotation_euler.z+math.pi)%math.tau-math.pi
    attention = max(.35,1-amp)
    yaw = max(-1.05,min(1.05,relative))*attention+.04*math.sin(seconds*math.tau/16+offset)
    pitch = -math.atan2(target.z-1.77*root.scale.z,max(.2,math.hypot(toward.x,toward.y)))
    pitch = max(-.50,min(.20,pitch))*attention-.025*math.sin(seconds*math.tau/8+offset)
    parts['head'].rotation_quaternion = Euler((pitch,0,yaw)).to_quaternion()
    for side,sign in [('L',-1),('R',1)]:
        foot_y,foot_z,swing = gait_foot(cycle+(0 if side=='L' else .5))
        foot_y *= amp; foot_z = .070+(foot_z-.070)*amp
        hip = Vector((sign*.12,0,1.035+bob))
        ankle = Vector((sign*.13,foot_y,foot_z))
        knee = solve_knee(hip,ankle)
        set_segment(parts['thigh_'+side],hip,knee)
        set_segment(parts['shin_'+side],knee,ankle)
        parts['foot_'+side].location = (ankle.x,ankle.y-.055,ankle.z-.025)
        shoulder = Vector((sign*.23,0,1.49+bob))
        if activity=='observing':
            elbow = Vector((sign*.28,.14,1.18+bob))
            hand = Vector((sign*.06,.22,.98+bob))
        elif activity=='thinking' and side=='R':
            elbow = Vector((.27,-.14,1.28+bob))
            hand = Vector((.06,-.21,1.62+bob))
        elif activity=='explaining' and side=='R':
            gesture = .5+.5*math.sin(seconds*math.tau/8+offset)
            elbow = Vector((.34,-.12,1.23+bob))
            hand = Vector((.15,-.42-gesture*.08,1.43+gesture*.12+bob))
        elif activity=='listening':
            elbow = Vector((sign*.28,.02,1.17+bob))
            hand = Vector((sign*.13,-.12,1.10+bob))
        else:
            elbow = Vector((sign*.29,.01,1.12+bob))
            hand = Vector((sign*.30,-.025,.79+bob))
        if info['route']:
            counter = -foot_y*.65
            upper_dir = Vector((sign*.05,counter,-.34)).normalized()
            walk_elbow = shoulder+upper_dir*.36
            walk_hand = walk_elbow+Vector((0,counter*.65-.025,-.285)).normalized()*.30
            blend = amp*amp*(3-2*amp)
            elbow = elbow.lerp(walk_elbow,blend)
            hand = hand.lerp(walk_hand,blend)
        set_segment(parts['upper_arm_'+side],shoulder,elbow)
        set_segment(parts['forearm_'+side],elbow,hand)
        parts['hand_'+side].location = hand
    for name,obj in parts.items():
        obj.keyframe_insert(data_path='location',frame=frame)
        if name not in ['pelvis','torso','foot_L','foot_R','hand_L','hand_R']:
            obj.keyframe_insert(data_path='rotation_quaternion',frame=frame)
        if obj['nominal_length']:
            obj.keyframe_insert(data_path='scale',index=2,frame=frame)


# Bake the authored motions: root routes remain editable and articulation is
# lightweight object-transform animation rather than dense per-frame point data.
def bake_gallery_visitors(people,end=960):
    positions = {v['root'].name:[] for v in people}
    initial = {}
    for frame in range(1,end+1):
        scene.frame_set(frame); bpy.context.view_layer.update()
        for info in people:
            root = info['root']
            target = gaze_target(info['look_keys'],frame)
            speed = 0
            if info['route']:
                position = root.location.copy(); previous = info['previous_position']
                delta = position-previous if previous is not None else Vector((0,0,0))
                distance = delta.length; speed = distance*30
                info['travel_distance'] += distance
                amp = min(1,speed/.60)
                info['gait_distance'] += distance/max(.35,amp)
                info['previous_position'] = position
                toward = delta if speed>.035 else target-position
                desired = math.atan2(toward.x,-toward.y)
                turn = (desired-info['heading_value']+math.pi)%math.tau-math.pi
                info['heading_value'] += max(-.07,min(.07,turn*.20))
                root.rotation_euler.z = info['heading_value']
                root.keyframe_insert(data_path='rotation_euler',frame=frame)
            pose_visitor(info,frame,speed)
            if frame == 1:
                for obj in [root,*info['parts'].values()]:
                    initial[obj] = (obj.location.copy(),obj.rotation_euler.copy(),
                                    obj.rotation_quaternion.copy(),obj.scale.copy())
            positions[root.name].append(list(root.location))
    # Close every articulated channel, including head attention and gait, rather
    # than wrapping the 98-second player tour at an arbitrary visitor pose.
    for obj,(location,euler,quaternion,scale) in initial.items():
        obj.location=location;obj.rotation_euler=euler;obj.rotation_quaternion=quaternion;obj.scale=scale
        for path in ['location','rotation_quaternion' if obj.rotation_mode=='QUATERNION' else 'rotation_euler','scale']:
            obj.keyframe_insert(data_path=path,frame=end)
    for info in people:
        for obj in info['parts'].values():
            smooth_keys(obj,'LINEAR')
    scene['autonomous_npc_period'] = end-1
    return positions


def validate_gallery_visitors(people,positions):
    obstacles = [(-.20,3.85,7.40,3.20),(0,-3.65,3.45,.70),
                 (-4.65,-1.10,.72,2.15),(4.65,-1.10,.72,2.15)]
    for name,path in positions.items():
        for p in path:
            assert abs(p[0])<5.60 and -6.4<p[1]<8.3
            for x,y,w,d in obstacles:
                assert not (abs(p[0]-x)<w/2+.28 and abs(p[1]-y)<d/2+.28), f'Obstacle collision: {name} {p}'
        assert (Vector(path[0])-Vector(path[-1])).length<.001
    for i,first in enumerate(people):
        for second in people[i+1:]:
            for a,b in zip(positions[first['root'].name],positions[second['root'].name]):
                assert math.hypot(a[0]-b[0],a[1]-b[1])>.70, f'Visitor routes overlap: {first["root"].name}, {second["root"].name}'
    return True


positions = bake_gallery_visitors(visitors)
validate_gallery_visitors(visitors,positions)

for frame,label in [(1,'01 / Enter the AT-AT skills gallery'),(130,'02 / Pause at wall art'),
                    (300,'03 / Visitors circulate'),(425,'04 / AT-AT viewing'),
                    (685,'05 / Exhibit readers return'),(880,'06 / Walkers return'),
                    (960,'07 / Seamless activity loop')]:
    scene.timeline_markers.new(label,frame=frame)

point_display('Sparse gallery dust',[(random.uniform(-5.8,5.8),random.uniform(-6.8,8.8),
                                     random.uniform(.1,5.3)) for _ in range(1400)],dust_mat,.003,'04')
for x,y in [(-3,-1),(3,3),(0,7.0)]:
    data = bpy.data.lights.new('Gallery • Soft architectural bounce','AREA')
    data.energy = 80; data.shape = 'DISK'; data.size = 4
    data.specular_factor = .15
    obj = link('Soft architectural bounce',data,'04'); obj.location = (x,y,5.18)
    obj.visible_glossy = False


def camera(name,position,target,lens):
    data = bpy.data.cameras.new('Gallery • '+name)
    obj = link(name,data,'06'); obj.location = position
    obj.rotation_euler = (Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
    data.lens = lens; data.clip_start = .04; data.clip_end = 100
    return obj


hero = camera('Skills gallery presentation camera',(0,-10.3,2.05),(0,5.5,2.60),20)
camera('Gallery architectural overview camera',(0,-5.8,4.1),(0,4,1.5),18)
camera('Visitor activity camera',(-2.7,7.5,2.3),(-5.4,5.9,1.40),30)
camera('Backend exhibit detail camera',(-3.3,5.5,2.65),(-3.3,8.85,2.65),28)
camera('Gallery arrival camera',(0,-6.6,1.70),(0,4.85,1.70),18)
sculpture_focus_height = (centre_exhibit['bounds_min'][2] + centre_exhibit['bounds_max'][2]) / 2
camera('AT-AT walker detail camera',(-5.2,-4.25,3.1),(-.40,3.85,sculpture_focus_height),26)
scene.camera = hero
for name,position in [('Entrance',(0,-7,0)),('Sculpture',(0,3.85,sculpture_focus_height)),('Rear exhibits',(0,8.8,2.65))]:
    obj = link(name+' / anchor',group='07'); obj.location = position
    obj.empty_display_type = 'ARROWS'; obj.empty_display_size = .3
world = bpy.data.worlds.new('Gallery • Absolute black world'); world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (0,0,0,1)
world.node_tree.nodes['Background'].inputs[1].default_value = 0
scene.world = world
scene.render.engine = 'CYCLES'
scene.cycles.samples = 40; scene.cycles.use_denoising = False
scene.cycles.max_bounces = 5; scene.cycles.diffuse_bounces = 1; scene.cycles.glossy_bounces = 3
scene.render.resolution_x = 1440; scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'Standard'; scene.view_settings.look = 'None'
scene.render.film_transparent = False
scene.render.filepath = str(ROOT/'gallery-preview.png')
tree = bpy.data.node_groups.new('Gallery • Restrained white glow','CompositorNodeTree')
tree.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
render = tree.nodes.new('CompositorNodeRLayers'); render.scene = scene; render.location = (-300,0)
glow = tree.nodes.new('CompositorNodeGlare'); glow.location = (-30,0)
glow.inputs['Type'].default_value = 'Fog Glow'; glow.inputs['Quality'].default_value = 'High'
glow.inputs['Threshold'].default_value = 1.3; glow.inputs['Strength'].default_value = .18
glow.inputs['Size'].default_value = .18
out = tree.nodes.new('NodeGroupOutput'); out.location = (240,0)
tree.links.new(render.outputs['Image'],glow.inputs['Image'])
tree.links.new(glow.outputs['Image'],out.inputs['Image'])
scene.compositing_node_group = tree
for old in factory_scenes:
    bpy.data.scenes.remove(old)

validate_gallery_visitors(visitors,positions)
assert len([o for o in collections['02'].objects if o.get('category')])==9
scene['Design reference'] = 'Monochrome technology museum; luminous skill panels, reference-led outlined AT-AT walker, reflective floor.'
scene['Visitor style'] = 'KAZE lobby-inspired slim surface-particle humans with natural varied activity.'
scene['Skill content'] = 'Concept exhibit labels; confirm personal skills before website integration.'
import importlib.util
walk_spec = importlib.util.spec_from_file_location('gallery_walk',ROOT/'gallery_walk.py')
walk_module = importlib.util.module_from_spec(walk_spec); walk_spec.loader.exec_module(walk_module)
guided_walk = walk_module.install_guided_walk(scene,ROOT)
guided_checks = walk_module.validate_guided_walk(scene,guided_walk)
scene.frame_set(1); bpy.context.view_layer.update()
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
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'skills-gallery.blend'))
manifest = {'blend':'skills-gallery.blend','scene':scene.name,'section':'Skills Gallery',
            'dimensions_m':{'width':12,'depth':16,'height':5.4},'entrance_anchor':[0,-7,0],
            'forward_axis':'+Y','up_axis':'+Z','exhibits':9,
            'categories':[entry['title'] for entry in SKILLS],'people':6,
            'visitors':[{'root':v['root'].name,'activity':v['root']['activity'],'idle_pose':v['idle_activity'],
                         'route_frames':list(v['root'].get('route_frames',[]))} for v in visitors],
            'frames':guided_walk['frames'],'fps':30,'duration_s':guided_walk['duration_s'],'saved_frame':1,'activity_loop':True,
            'npc_clip_frames':[1,960],'npc_clip_loops_during_tour':True,
            'active_camera':guided_walk['camera'],
            'guided_walk':{k:v for k,v in guided_walk.items() if k!='positions'},
            'moving_people':4,'centre_exhibit':centre_exhibit,
            'sculpture_detail_camera':'Gallery • AT-AT walker detail camera',
            'presentation_camera':hero.name,'objects':len(scene.objects),
            'particle_count':sum(o.get('particle_count',0) for o in scene.objects),
            'existing_assets_modified':False,'visitor_clearance_checks':'passed',
            'integration_status':'Standalone Blender gallery; website integration deferred.'}
(ROOT/'gallery-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(ROOT/'gallery-walk.json').write_text(json.dumps(guided_walk,indent=2)+'\n')
if '--render' in sys.argv:
    for name,frame,width,height,filename in [
        ('Skills gallery presentation camera',300,1440,1080,'gallery-preview.png'),
        ('AT-AT walker detail camera',480,1440,960,'gallery-atat.png'),
        ('Gallery architectural overview camera',300,1440,960,'gallery-overview.png'),
        ('Visitor activity camera',300,1200,900,'gallery-visitors.png'),
        ('Backend exhibit detail camera',300,900,1100,'gallery-exhibit.png')]:
        scene.camera = scene.objects['Gallery • '+name]; scene.frame_set(frame)
        scene.render.resolution_x = width; scene.render.resolution_y = height
        scene.render.filepath = str(ROOT/filename)
        bpy.ops.render.render(write_still=True)
    scene.camera = scene.objects[guided_walk['camera']]; scene.frame_set(1)
    scene.render.resolution_x = 1440; scene.render.resolution_y = 1080
    scene.render.filepath = str(ROOT/'gallery-preview.png')
print(json.dumps({'checks':'passed',**manifest}))
