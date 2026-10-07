"""Replace dense facade/road wire detail with clean, brighter outline networks."""
import math
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path('/home/damienckj/Documents/damien-portfolio/assets/cyber-city')
scene=bpy.context.scene
if scene.name!='MONO / Wire & Particle City':
    raise RuntimeError('Activate MONO / Wire & Particle City first.')
if bpy.data.collections.get('Mono • Simplified environment outlines'):
    raise RuntimeError('Simplified outlines already exist; edit that collection instead of rebuilding.')
source=bpy.data.scenes['NEON / Kaze Megacity']
if bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_cancel(restore_frame=False)

# Retain old networks, but hide them. People and moving-vehicle geometry is untouched.
hidden=[];old_segments=0
categories=['01 Megatower','02 Neon media','03 Sky garden','04 Skyline','05 Elevated highways','12 Transit • maglev & rails']
for obj in scene.objects:
    if 'fine outlines' in obj.name and any(category in obj.name for category in categories):
        old_segments+=len(obj.data.edges);obj.hide_render=True;obj.hide_set(True);hidden.append(obj.name)
    # Remove individual window specks from the curtain-wall grid.
    if obj.name in ['Mono • 01 Megatower • particles 0','Mono • 03 Sky garden • particles 0']:
        obj.hide_render=True;obj.hide_set(True)

col=bpy.data.collections.new('Mono • Simplified environment outlines');scene.collection.children.link(col)
styles={
    'Primary tower silhouette':(.32,.010),
    'Major structure':(.18,.008),
    'Skyline silhouettes':(.085,.007),
    'Highway edges':(.26,.009),
    'Highway supports':(.38,.010),
    'Billboard frames':(.25,.008),
    'Secondary guide rails':(.07,.005),
}
networks={name:{'vertices':[],'edges':[],'radii':[]} for name in styles}
def line(a,b,style='Major structure'):
    data=networks[style];k=len(data['vertices']);data['vertices'].extend([tuple(a),tuple(b)]);data['edges'].append((k,k+1));data['radii'].extend([styles[style][1]]*2)

def polygon(points,style='Major structure',close=True):
    points=list(points)
    if close and points:points.append(points[0])
    for a,b in zip(points,points[1:]):line(a,b,style)

def outline_box(obj,style='Major structure'):
    # Eight corners only: no triangulation, bevel loops, mullions or internal detail.
    corners=[obj.matrix_world@Vector(p) for p in obj.bound_box]
    for a,b in [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]:line(corners[a],corners[b],style)

def rectangle(x0,x1,y0,y1,z,style='Major structure'):
    polygon([(x0,y0,z),(x1,y0,z),(x1,y1,z),(x0,y1,z)],style)

def circle(cx,cy,z,radius,style='Major structure',segments=24):
    polygon([(cx+radius*math.cos(i*math.tau/segments),cy+radius*math.sin(i*math.tau/segments),z) for i in range(segments)],style)

def source_curve(obj,style='Major structure'):
    for spline in obj.data.splines:
        coords=[obj.matrix_world@Vector(p.co[:3]) for p in spline.points] if spline.type!='BEZIER' else [obj.matrix_world@p.co for p in spline.bezier_points]
        polygon(coords,style,close=spline.use_cyclic_u)

# Megatower: simple corner cage, sparse major floors, and a few diagonal braces.
outline_box(source.objects['Megatower • central occupied volume'],'Primary tower silhouette')
outline_box(source.objects['Crown • stepped upper block'],'Primary tower silhouette')
for z in [12,24,37,44]:
    line((-6.9,-5.28,z),(6.9,-5.28,z))
    line((6.9,-5.28,z),(6.9,5.25,z))
for x in [-4.7,4.7]:line((x,-5.28,4),(x,-5.28,48))
for obj in source.objects:
    if obj.type=='CURVE' and obj.name.startswith('Exoskeleton') and 'titanium' in obj.name:source_curve(obj,'Primary tower silhouette')

# Terraces and circular lounge: readable volume boundaries, very few ribs.
for obj in source.objects:
    if obj.type=='MESH' and obj.name.startswith(('Cantilever garden • slab','Crown • rooftop canopy')):outline_box(obj)
outline_box(source.objects['Sky lounge • supporting tower'])
for z in [14,28]:rectangle(5.65,10.95,-.2,5.2,z)
for z in [39.7,40.3,42.4,42.7]:circle(8.2,2,z,5.8,'Primary tower silhouette')
for i in range(8):
    angle=i*math.tau/8;x=8.2+5.8*math.cos(angle);y=2+5.8*math.sin(angle)
    line((x,y,40.3),(x,y,42.4))
rectangle(-6.7,4.1,-3.2,5.2,51.7)

# Distant towers: outer volumes and crowns, no individual window outlines.
for obj in source.objects:
    if obj.type=='MESH':
        if obj.name.startswith('Skyline') and ('• tower' in obj.name or '• crown' in obj.name):outline_box(obj,'Skyline silhouettes')
        elif obj.name.startswith(('Flanking skyline • stepped shaft','Flanking skyline • crown')):outline_box(obj,'Skyline silhouettes')
    elif obj.type=='CURVE' and obj.name.startswith(('Skyline • antenna','Flanking skyline • spire')):source_curve(obj,'Skyline silhouettes')

# Advertising frames: one clean rectangle or low-resolution arc, no housing cage.
for obj in source.objects:
    if obj.type!='MESH':continue
    if obj.name.startswith('THE NIGHT LIVES ON •'):continue
    if obj.name.endswith('• LED display') or '• LED display.' in obj.name:
        corners=[obj.matrix_world@v.co for v in obj.data.vertices]
        if len(corners)==4:polygon(corners,'Billboard frames')
for z,height in [(30,8),(22.7,5.3),(16.5,5),(10.8,5.6)]:
    for zz in [z-height/2,z+height/2]:
        points=[(5.4+2.91*math.sin(-1.05+2.1*i/12),-5.35-2.91*math.cos(-1.05+2.1*i/12),zz) for i in range(13)]
        polygon(points,'Billboard frames',close=False)
    for angle in [-1.05,1.05]:
        x=5.4+2.91*math.sin(angle);y=-5.35-2.91*math.cos(angle)
        line((x,y,z-height/2),(x,y,z+height/2),'Billboard frames')
for z in [2.6,34]:circle(5.4,-5.35,z,2.85,'Major structure',20)
for angle in [-1.2,1.2]:
    x=5.4+2.85*math.sin(angle);y=-5.35-2.85*math.cos(angle)
    line((x,y,2.6),(x,y,34))

# Roads: deck boundary, one guardrail per side, sparse posts, and main piers only.
for road_name in ['Foreground skyway','Left interchange','Background transit route']:
    road=source.objects[road_name+' • road surface']
    vertices=[road.matrix_world@v.co for v in road.data.vertices]
    near=[vertices[i] for i in range(0,len(vertices),2)]
    far=[vertices[i] for i in range(1,len(vertices),2)]
    # These roads are straight; endpoint segments express them without 30 subdivisions.
    a,b,c,d=near[0],near[-1],far[-1],far[0]
    polygon([a,b,c,d],'Highway edges')
    lower=[v-Vector((0,0,.35)) for v in [a,b,c,d]];polygon(lower,'Highway edges')
    for upper,below in zip([a,b,c,d],lower):line(upper,below,'Highway edges')
    for side in [near,far]:
        line(side[0]+Vector((0,0,.65)),side[-1]+Vector((0,0,.65)),'Highway edges')
        for index in sorted(set([0,len(side)//4,len(side)//2,3*len(side)//4,len(side)-1])):
            line(side[index],side[index]+Vector((0,0,.65)),'Highway edges')
    piers=sorted([obj for obj in source.objects if obj.name.startswith(road_name+' • support pier')],key=lambda obj:obj.location.x)
    for pier in piers[::2]:outline_box(pier,'Highway supports')

# Two simple rail lines are enough to connect the train visually to the skyway.
road=source.objects['Foreground skyway • road surface']
start=(road.matrix_world@road.data.vertices[0].co+road.matrix_world@road.data.vertices[1].co)/2
end=(road.matrix_world@road.data.vertices[-2].co+road.matrix_world@road.data.vertices[-1].co)/2
tangent=(end-start).normalized();perp=Vector((-tangent.y,tangent.x,0)).normalized()
for lane in [.29,1.01]:line(start+perp*lane+Vector((0,0,.06)),end+perp*lane+Vector((0,0,.06)),'Secondary guide rails')

template=next(group for group in bpy.data.node_groups if group.name.startswith('Mono • Wires'))
new_segments=0
for name,data in networks.items():
    if not data['edges']:continue
    value,width=styles[name]
    material=bpy.data.materials.new('Mono • Clean '+name);material.use_nodes=True;n=material.node_tree.nodes;n.clear()
    out=n.new('ShaderNodeOutputMaterial');emission=n.new('ShaderNodeEmission');emission.inputs['Color'].default_value=(value,value,value,1);emission.inputs['Strength'].default_value=1
    material.node_tree.links.new(emission.outputs[0],out.inputs[0]);material.diffuse_color=(value,value,value,1)
    group=template.copy();group.name='Mono • Clean outline network • '+name;group.nodes.get('Set Material').inputs['Material'].default_value=material
    mesh=bpy.data.meshes.new('Clean outlines • '+name);mesh.from_pydata(data['vertices'],data['edges'],[]);mesh.update()
    attribute=mesh.attributes.new('radius','FLOAT','POINT');attribute.data.foreach_set('value',data['radii'])
    obj=bpy.data.objects.new('Clean outlines • '+name,mesh);col.objects.link(obj);mod=obj.modifiers.new('Bright structural outlines','NODES');mod.node_group=group
    new_segments+=len(data['edges'])
scene.frame_set(145);bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'monochrome-city-walkthrough.blend'))
result={'hidden_old_line_groups':len(hidden),'old_environment_segments':old_segments,'new_environment_segments':new_segments,'reduction_percent':round((1-new_segments/old_segments)*100,1),'networks':{name:len(data['edges']) for name,data in networks.items()},'preserved':'people, particles, camera, doors, and traffic animation'}
