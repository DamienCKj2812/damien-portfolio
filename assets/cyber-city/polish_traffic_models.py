"""Replace particle vehicles with clean solid coupe/maglev models.

Run in background on the optimized city. Animated roots/routes are preserved;
the result is saved separately from both the original city and the lobby assets.
"""
import math
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path('/home/damienckj/Documents/damien-portfolio/assets/cyber-city')
scene=bpy.context.scene
if scene.name!='MONO / Wire & Particle City':raise RuntimeError('Open the optimized city scene.')
scene.frame_set(1);bpy.context.view_layer.update()
collection=bpy.data.collections.new('Traffic • Solid bodies & bright contours');scene.collection.children.link(collection)

def material(name,value):
    mat=bpy.data.materials.new('Traffic • '+name);mat.use_nodes=True;n=mat.node_tree.nodes;n.clear()
    output=n.new('ShaderNodeOutputMaterial');emission=n.new('ShaderNodeEmission');emission.inputs['Color'].default_value=(value,value,value,1);emission.inputs['Strength'].default_value=1
    mat.node_tree.links.new(emission.outputs[0],output.inputs[0]);mat.diffuse_color=(value,value,value,1)
    return mat

body=[material('Body shadow',.012),material('Body side',.024),material('Body upper facets',.043)]
glass=material('Opaque dark cockpit glass',.002)
tire=material('Opaque tire & undercarriage',.006)
white=material('White contour',1)
detail=material('Window & mechanical contour',.62)
headlight=material('White headlight',1)
template=next(group for group in bpy.data.node_groups if group.name.startswith('Mono • Wires'))
stroke_groups={}
for name,mat in [('primary',white),('detail',detail)]:
    group=template.copy();group.name='Traffic • continuous '+name+' contours';group.nodes.get('Set Material').inputs['Material'].default_value=mat;stroke_groups[name]=group

counts={'solid_triangles':0,'outline_segments':0,'replaced_roots':0}
def mesh_object(name,vertices,faces,parent,materials=None,indices=None):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);collection.objects.link(obj);obj.parent=parent;obj['city_render_kind']='solid'
    for mat in (materials or body):mesh.materials.append(mat)
    for i,poly in enumerate(mesh.polygons):
        poly.material_index=indices[i] if indices is not None else (2 if poly.normal.z>.45 else 1 if poly.normal.y<-.25 else 0)
    mesh.calc_loop_triangles();counts['solid_triangles']+=len(mesh.loop_triangles)
    return obj

def strokes(name,segments,parent,style='primary'):
    vertices=[];edges=[]
    for a,b in segments:
        index=len(vertices);vertices.extend([tuple(a),tuple(b)]);edges.append((index,index+1))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,edges,[]);mesh.update()
    attribute=mesh.attributes.new('radius','FLOAT','POINT');attribute.data.foreach_set('value',[.022 if style=='primary' else .013]*len(vertices))
    obj=bpy.data.objects.new(name,mesh);collection.objects.link(obj);obj.parent=parent;obj['city_render_kind']='outline'
    mod=obj.modifiers.new('Continuous bright contours','NODES');mod.node_group=stroke_groups[style]
    counts['outline_segments']+=len(segments);return obj

def outline(obj,style='primary',angle=24):
    adjacency={}
    for poly in obj.data.polygons:
        for edge in poly.edge_keys:adjacency.setdefault(tuple(sorted(edge)),[]).append(poly.normal.copy())
    segments=[]
    for edge in obj.data.edges:
        normals=adjacency.get(tuple(sorted(edge.vertices)),[])
        if len(normals)==2 and normals[0].dot(normals[1])>math.cos(math.radians(angle)):continue
        segments.append(tuple(obj.data.vertices[i].co for i in edge.vertices))
    strokes(obj.name+' • contours',segments,obj.parent,style)

def rectangle(name,points,parent,mat=glass,style='detail'):
    obj=mesh_object(name,points,[(0,1,2,3)],parent,[mat],[0]);outline(obj,style);return obj

def box(name,center,size,parent,mat=None,style='primary'):
    x,y,z=center;a,b,c=[value/2 for value in size]
    vertices=[(x+dx*a,y+dy*b,z+dz*c) for dx,dy,dz in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    obj=mesh_object(name,vertices,faces,parent,[mat] if mat else None,[0]*6 if mat else None);outline(obj,style);return obj

def loft(name,stations,parent):
    vertices=[]
    for x,width,low,high in stations:
        half=width/2
        vertices.extend([(x,-half,low),(x,-half,low+.13),(x,-half*.94,high-.12),(x,-half*.72,high),(x,half*.72,high),(x,half*.94,high-.12),(x,half,low+.13),(x,half,low)])
    faces=[tuple(reversed(range(8))),tuple(range((len(stations)-1)*8,len(stations)*8))]
    for ring in range(len(stations)-1):
        for i in range(8):j=(i+1)%8;faces.append((ring*8+i,ring*8+j,(ring+1)*8+j,(ring+1)*8+i))
    obj=mesh_object(name,vertices,faces,parent);outline(obj,angle=18);return obj

def wheel(name,x,y,z,parent):
    n=20;radius=.29;depth=.16
    vertices=[(x+radius*math.cos(i*math.tau/n),yy,z+radius*math.sin(i*math.tau/n)) for yy in [y-depth/2,y+depth/2] for i in range(n)]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh_object(name,vertices,faces,parent,[tire],[0]*len(faces))
    outer=y+math.copysign(depth/2+.003,y)
    segments=[]
    for r in [.235,.10]:
        pts=[(x+r*math.cos(i*math.tau/n),outer,z+r*math.sin(i*math.tau/n)) for i in range(n)]
        segments.extend(zip(pts,pts[1:]+pts[:1]))
    for i in range(3):
        a=i*math.tau/3;segments.append(((x+.10*math.cos(a),outer,z+.10*math.sin(a)),(x+.235*math.cos(a),outer,z+.235*math.sin(a))))
    strokes(name+' • rim',segments,parent)

def clear_vehicle(root):
    for obj in reversed(list(root.children_recursive)):bpy.data.objects.remove(obj,do_unlink=True)
    root['city_role']='outlined_vehicle';counts['replaced_roots']+=1

def coupe(root):
    clear_vehicle(root)
    loft('Coupe • chamfered chassis',[(-2.05,1.18,.16,.46),(-1.5,1.58,.10,.62),(.9,1.50,.12,.58),(1.92,1.18,.20,.44),(2.08,1.12,.22,.43)],root)
    vertices=[(-1.15,-.49,.61),(.65,-.46,.59),(.65,.46,.59),(-1.15,.49,.61),(-.82,-.42,1.08),(-.10,-.42,1.10),(-.10,.42,1.10),(-.82,.42,1.08)]
    faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    canopy=mesh_object('Coupe • roof and sloped cockpit',vertices,faces,root,[glass,body[2]],[0,1,0,0,0,0]);outline(canopy)
    for side in [-1,1]:
        y=side*.78
        strokes('Coupe • door and shoulder seam',[((-1.30,y,.52),(.60,y,.50)),((.60,y,.50),(.60,y,.22)),((.60,y,.22),(-1.30,y,.22)),((-1.30,y,.22),(-1.30,y,.52))],root,'detail')
        strokes('Coupe • side window pillar',[((-.40,side*.47,.60),(-.40,side*.424,1.09))],root,'detail')
        for x in [-1.28,1.24]:wheel('Coupe • hover wheel',x,side*.79,.23,root)
        box('Coupe • wing mirror',(.22,side*.62,.65),(.22,.18,.09),root,body[1],'detail')
    for y in [-.35,.35]:
        box('Coupe • headlamp',(2.085,y,.35),(.025,.25,.055),root,headlight)
        box('Coupe • tail lamp',(-2.055,y,.35),(.025,.23,.035),root,body[2],'detail')
    box('Coupe • front grille',(2.09,0,.275),(.02,.44,.055),root,tire,'detail')
    box('Coupe • visible underbody',(0,0,.075),(2.7,.95,.10),root,tire,'detail')

car_names=['Mono • Aircar 01 • foreground commuter','Mono • Aircar 02 • right approaching','Mono • Aircar 03 • upper transit','Mono • Aircar 04 • distant','Mono • Skyway vehicle']
for name in car_names:coupe(scene.objects[name])

train=scene.objects['Mono • Transit • maglev train'];clear_vehicle(train)
for index,cx in enumerate([-6,0,6]):
    coach=bpy.data.objects.new(f'Maglev • polished carriage {index+1}',None);collection.objects.link(coach);coach.parent=train;coach.location=(cx,0,0)
    stations=[(-2.8,1.18,.18,1.86),(-2.55,1.24,.15,1.94),(2.55,1.24,.15,1.94),(2.8,1.18,.18,1.86)]
    if index==2:stations=[(-2.8,1.18,.18,1.86),(-2.55,1.24,.15,1.94),(2.4,1.24,.15,1.94),(3.45,.94,.25,1.27),(3.65,.84,.29,1.14)]
    loft('Maglev • solid chamfered carriage',stations,coach)
    for side in [-1,1]:
        y=side*.624
        for x in [-2.05,-1.38,-.03,.63,1.29,1.95]:
            rectangle('Maglev • clear passenger window',[(x-.245,y,1.06),(x+.245,y,1.06),(x+.245,y,1.60),(x-.245,y,1.60)],coach)
        rectangle('Maglev • passenger door',[(-1.03,y,.30),(-.37,y,.30),(-.37,y,1.68),(-1.03,y,1.68)],coach,body[0])
        rectangle('Maglev • door window',[(-.94,y+side*.002,1.05),(-.46,y+side*.002,1.05),(-.46,y+side*.002,1.58),(-.94,y+side*.002,1.58)],coach)
        strokes('Maglev • continuous running stripe',[((-2.48,y,.62),(2.45,y,.62))],coach)
        for x in [-1.7,1.7]:box('Maglev • levitation bogie',(x,0,.15),(.62,.94,.24),coach,tire,'detail')
    if index==2:
        rectangle('Maglev • sloped driver windshield',[(2.42,-.50,1.951),(3.44,-.38,1.281),(3.44,.38,1.281),(2.42,.50,1.951)],coach)
        for side in [-1,1]:
            rectangle('Maglev • driver side glass',[(2.47,side*.626,1.15),(3.30,side*.50,.89),(3.39,side*.49,1.20),(2.47,side*.626,1.74)],coach)
            box('Maglev • forward lamp',(3.66,side*.26,.70),(.025,.16,.085),coach,headlight)
    if index==0:
        for y in [-.35,.35]:box('Maglev • rear marker',(-2.81,y,.75),(.025,.12,.06),coach,body[2],'detail')
for x in [-3,3]:box('Maglev • articulated connector',(x,0,1.02),(.40,.96,1.53),train,tire,'detail')

scene.frame_set(1);bpy.context.view_layer.update()
output=ROOT/'monochrome-city-traffic-polished.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(output),compress=True)
result={'file':str(output),'models':'five solid hover coupes and a three-car streamlined maglev','counts':counts,'preserved':'all camera, door, and traffic-root animation'}
