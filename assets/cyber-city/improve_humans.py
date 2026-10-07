"""Replace column-like crowd particles with a reusable humanoid silhouette."""
import bisect
import json
import math
import random
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path('/home/damienckj/Documents/damien-portfolio/assets/cyber-city')
scene=bpy.context.scene
if not scene.name.startswith('MONO /'):
    raise RuntimeError('Activate the monochrome walkthrough first.')
source=bpy.data.scenes['NEON / Kaze Megacity']
vertices=[];faces=[]

def ring_mesh(rings,segments=20,transform=None):
    start=len(vertices)
    for z,rx,ry in rings:
        for j in range(segments):
            angle=j*math.tau/segments;p=Vector((rx*math.cos(angle),ry*math.sin(angle),z))
            if transform:p=transform(p)
            vertices.append(tuple(p))
    for i in range(len(rings)-1):
        for j in range(segments):
            a=start+i*segments+j;b=start+i*segments+(j+1)%segments
            faces.append((a,b,b+segments,a+segments))
    faces.extend([tuple(reversed(range(start,start+segments))),tuple(range(start+(len(rings)-1)*segments,start+len(rings)*segments))])

def ellipsoid(center,radii):
    rings=[]
    for i in range(13):
        angle=-math.pi/2+i*math.pi/12
        rings.append((radii[2]*math.sin(angle),radii[0]*math.cos(angle),radii[1]*math.cos(angle)))
    center=Vector(center)
    ring_mesh(rings,transform=lambda p:p+center)

def capsule(a,b,radius):
    a=Vector(a);b=Vector(b);direction=b-a;length=direction.length;rotation=direction.to_track_quat('Z','Y')
    rings=[(-radius,0,0),(-radius*.866,radius*.5,radius*.5),(-radius*.5,radius*.866,radius*.866),(0,radius,radius),(length,radius,radius),(length+radius*.5,radius*.866,radius*.866),(length+radius*.866,radius*.5,radius*.5),(length+radius,0,0)]
    ring_mesh(rings,16,lambda p:rotation@p+a)

# Taller scan-like proportions: smaller head, narrow torso, longer separated legs.
ellipsoid((0,0,1.915),(.125,.115,.135))
capsule((0,0,1.70),(0,0,1.79),.036)
ring_mesh([(.94,.13,.082),(1.04,.14,.09),(1.35,.155,.095),(1.60,.182,.095),(1.68,.18,.085),(1.73,.092,.06)])
for side in [-1,1]:
    capsule((side*.19,0,1.61),(side*.23,-.012,1.28),.050)
    capsule((side*.23,-.012,1.28),(side*.225,-.025,.94),.043)
    ellipsoid((side*.225,-.025,.88),(.045,.046,.065))
    capsule((side*.09,0,.99),(side*.095,-.015,.12),.054)
    ellipsoid((side*.095,-.05,.055),(.058,.095,.045))

mesh=bpy.data.meshes.new('Humanoid • rounded source geometry');mesh.from_pydata(vertices,[],faces);mesh.update();mesh.calc_loop_triangles()
for polygon in mesh.polygons:polygon.use_smooth=True
forms=bpy.data.collections.get('Mono • Human source forms (hidden)')
if forms is None:
    forms=bpy.data.collections.new('Mono • Human source forms (hidden)');scene.collection.children.link(forms)
forms.hide_render=True;forms.hide_viewport=True
prototype=bpy.data.objects.get('Humanoid • editable silhouette source')
if prototype:prototype.data=mesh
else:
    prototype=bpy.data.objects.new('Humanoid • editable silhouette source',mesh);forms.objects.link(prototype)
triangles=[];cumulative=[];area=0
for triangle in mesh.loop_triangles:
    coords=[mesh.vertices[i].co.copy() for i in triangle.vertices]
    value=(coords[1]-coords[0]).cross(coords[2]-coords[0]).length/2
    if value>1e-10:area+=value;triangles.append((coords,triangle.normal.copy()));cumulative.append(area)

rng=random.Random(944)
def sample(count):
    positions=[]
    for _ in range(count):
        coords,normal=triangles[bisect.bisect_left(cumulative,rng.random()*area)]
        # Sparse centers, clearer contour: favor side-facing surface samples.
        if rng.random()>.20+.80*(1-abs(normal.y))**1.2:continue
        u=math.sqrt(rng.random());v=rng.random();weights=(1-u,u*(1-v),u*v)
        positions.append(sum((co*weight for co,weight in zip(coords,weights)),Vector()))
    return positions

people=[o for o in source.objects if o.name.startswith('Pedestrian • coat')]
cloud=[];radii=[];person_ids=[];metadata=[]
for person_id,coat in enumerate(people):
    scale=coat.dimensions.z/.85
    base=coat.matrix_world.translation.copy();base.z-=.94*scale
    rotation=coat.matrix_world.to_quaternion()
    points=sample(int(area*600*scale**2))
    for point in points:
        cloud.append(tuple(rotation@(point*scale)+base));radii.append(.0048*scale*rng.uniform(.65,1.25));person_ids.append(person_id)
    metadata.append({'id':person_id,'source':coat.name,'base':list(base),'scale':scale,'height':2.05*scale,'points':len(points)})
new_mesh=bpy.data.meshes.new('Humanoid • recognizable crowd particles');new_mesh.from_pydata(cloud,[],[]);new_mesh.update()
attribute=new_mesh.attributes.new('radius','FLOAT','POINT');attribute.data.foreach_set('value',radii)
attribute=new_mesh.attributes.new('person_id','INT','POINT');attribute.data.foreach_set('value',person_ids)
crowd=scene.objects['Mono • 07 Street life • particles 3'];crowd.data=new_mesh
crowd['person_metadata']=json.dumps(metadata)

# Remove the old short stick limbs from the mixed street wire batch.
def segment_key(a,b):
    return tuple(sorted([tuple(round(float(v),4) for v in a),tuple(round(float(v),4) for v in b)]))
obsolete=set()
for obj in source.objects:
    if obj.type=='CURVE' and obj.name.startswith('Pedestrian •'):
        for spline in obj.data.splines:
            pts=[obj.matrix_world@Vector(point.co[:3]) for point in spline.points]
            obsolete.update(segment_key(a,b) for a,b in zip(pts,pts[1:]))
wire=scene.objects.get('Mono • 07 Street life • fine outlines 1')
if wire:
    old=wire.data;verts=[];edges=[];radius=[]
    for edge in old.edges:
        a,b=edge.vertices
        if segment_key(old.vertices[a].co,old.vertices[b].co) in obsolete:continue
        k=len(verts);verts.extend([tuple(old.vertices[a].co),tuple(old.vertices[b].co)]);edges.append((k,k+1));radius.extend([old.attributes['radius'].data[a].value,old.attributes['radius'].data[b].value])
    clean=bpy.data.meshes.new('Street outlines • no obsolete human sticks');clean.from_pydata(verts,edges,[]);clean.update()
    attribute=clean.attributes.new('radius','FLOAT','POINT');attribute.data.foreach_set('value',radius);wire.data=clean

# Dedicated single-figure proof scene makes the silhouette easy to inspect.
proof=bpy.data.scenes.get('MONO / Humanoid silhouette preview') or bpy.data.scenes.new('MONO / Humanoid silhouette preview')
proof.world=scene.world
points=sample(int(area*600));point_mesh=bpy.data.meshes.new('Humanoid • isolated particle preview');point_mesh.from_pydata(points,[],[]);point_mesh.update()
attribute=point_mesh.attributes.new('radius','FLOAT','POINT');attribute.data.foreach_set('value',[.0048*rng.uniform(.65,1.25) for _ in points])
figure=proof.objects.get('Humanoid • particle silhouette')
if figure:figure.data=point_mesh
else:
    figure=bpy.data.objects.new('Humanoid • particle silhouette',point_mesh);proof.collection.objects.link(figure)
figure.location=(-.43,0,0)
mod=figure.modifiers.get('Human particle style') or figure.modifiers.new('Human particle style','NODES');mod.node_group=crowd.modifiers[0].node_group
second=proof.objects.get('Humanoid • particle silhouette comparison')
if second:second.data=point_mesh
else:
    second=bpy.data.objects.new('Humanoid • particle silhouette comparison',point_mesh);proof.collection.objects.link(second)
second.location=(.43,.12,0);second.scale=(.97,.97,.97);second.rotation_euler.z=math.radians(12)
mod=second.modifiers.get('Human particle style') or second.modifiers.new('Human particle style','NODES');mod.node_group=crowd.modifiers[0].node_group
camera=proof.camera
if camera is None:
    camera_data=bpy.data.cameras.new('Humanoid • inspection camera');camera=bpy.data.objects.new(camera_data.name,camera_data);proof.collection.objects.link(camera)
camera_data=camera.data
camera.location=(0,-4,1.03);camera.rotation_euler=(Vector((0,0,1.03))-camera.location).to_track_quat('-Z','Y').to_euler();camera_data.type='ORTHO';camera_data.ortho_scale=2.35;proof.camera=camera
proof.render.engine='CYCLES';proof.cycles.samples=64;proof.cycles.use_denoising=False
proof.render.resolution_x=480;proof.render.resolution_y=640;proof.render.resolution_percentage=100
proof.view_settings.view_transform='Standard';proof.view_settings.look='None';proof.render.filepath=str(ROOT/'humanoid-preview.png')
bpy.context.view_layer.update()
result={'people_rebuilt':len(people),'crowd_points':len(cloud),'prototype_surface_area':area,'prototype_height':2.05,'proof_scene':proof.name,'features':['smaller head','slender torso','longer arms and legs','sparse centers','clearer particle silhouette']}
