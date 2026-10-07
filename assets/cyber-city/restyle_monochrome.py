"""Build a separate X-ray wire / point-cloud interpretation of the walkthrough.

Original materials and geometry are untouched. Animated rigs are copied and
constraints remapped; render geometry is replaced with fine wires and points.
"""
import bisect
import math
import random
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector

ROOT=Path('/home/damienckj/Documents/damien-portfolio/assets/cyber-city')
source=bpy.context.scene
if 'Walkthrough • camera' not in source.objects:
    raise RuntimeError('Open the city walkthrough before restyling.')
if source.name.startswith('MONO /'):
    raise RuntimeError('Activate the original neon scene to generate a new style.')
if bpy.context.screen.is_animation_playing:
    bpy.ops.screen.animation_cancel(restore_frame=False)
source.frame_set(1);bpy.context.view_layer.update()
deps=bpy.context.evaluated_depsgraph_get()
rng=random.Random(812)
scene=bpy.data.scenes.new('MONO / Wire & Particle City')
collections={}
for old in source.collection.children:
    if old.name.startswith('11 '):continue
    col=bpy.data.collections.new('Mono • '+old.name);scene.collection.children.link(col);collections[old.name]=col
dust=bpy.data.collections.new('Mono • Suspended particles');scene.collection.children.link(dust)
rig=bpy.data.collections.new('Mono • Animated rig');scene.collection.children.link(rig)

def emission(name,value):
    mat=bpy.data.materials.new('Mono • '+name);mat.use_nodes=True;n=mat.node_tree.nodes;n.clear()
    out=n.new('ShaderNodeOutputMaterial');node=n.new('ShaderNodeEmission');node.inputs['Color'].default_value=(value,value,value,1);node.inputs['Strength'].default_value=1
    mat.node_tree.links.new(node.outputs[0],out.inputs['Surface']);mat.diffuse_color=(value,value,value,1)
    return mat

levels=[.05,.15,.45,1.0]
materials=[emission(f'Gray level {i}',value) for i,value in enumerate(levels)]
wire_materials=[emission(f'Wire gray level {i}',value) for i,value in enumerate([.015,.045,.12,.25])]

def group(kind,material):
    tree=bpy.data.node_groups.new(f'Mono • {kind} • {material.name}','GeometryNodeTree')
    tree.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
    tree.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    n=tree.nodes;links=tree.links;inp=n.new('NodeGroupInput');out=n.new('NodeGroupOutput')
    attribute=n.new('GeometryNodeInputNamedAttribute');attribute.data_type='FLOAT';attribute.inputs['Name'].default_value='radius'
    if kind=='Points':
        convert=n.new('GeometryNodeMeshToPoints');convert.mode='VERTICES';links.new(inp.outputs['Geometry'],convert.inputs['Mesh']);links.new(attribute.outputs['Attribute'],convert.inputs['Radius'])
        geometry=convert.outputs['Points']
    else:
        convert=n.new('GeometryNodeMeshToCurve');links.new(inp.outputs['Geometry'],convert.inputs['Mesh'])
        radius=n.new('GeometryNodeSetCurveRadius');links.new(convert.outputs['Curve'],radius.inputs['Curve']);links.new(attribute.outputs['Attribute'],radius.inputs['Radius'])
        profile=n.new('GeometryNodeCurvePrimitiveCircle');profile.inputs['Resolution'].default_value=3;profile.inputs['Radius'].default_value=1
        tube=n.new('GeometryNodeCurveToMesh');links.new(radius.outputs['Curve'],tube.inputs['Curve']);links.new(profile.outputs['Curve'],tube.inputs['Profile Curve']);links.new(attribute.outputs['Attribute'],tube.inputs['Scale']);geometry=tube.outputs['Mesh']
    shade=n.new('GeometryNodeSetMaterial');shade.inputs['Material'].default_value=material;links.new(geometry,shade.inputs['Geometry']);links.new(shade.outputs['Geometry'],out.inputs['Geometry'])
    return tree

groups={(kind,i):group(kind,material) for kind,shades in [('Points',materials),('Wires',wire_materials)] for i,material in enumerate(shades)}

# Clone only the rig objects needed for cameras, moving actors, and sliding doors.
targets={constraint.target for obj in source.objects for constraint in obj.constraints if hasattr(constraint,'target') and constraint.target}
mapping={}
for obj in source.objects:
    if obj.type in ['EMPTY','CAMERA'] or (obj.type=='CURVE' and obj in targets):
        copy=obj.copy()
        if obj.type=='CAMERA':copy.data=obj.data.copy()
        rig.objects.link(copy);copy.name='Mono • '+obj.name;mapping[obj]=copy
for old,new in mapping.items():
    new.parent=mapping.get(old.parent)
    new.matrix_parent_inverse=old.matrix_parent_inverse.copy()
    for constraint in new.constraints:
        if hasattr(constraint,'target') and constraint.target in mapping:constraint.target=mapping[constraint.target]

def copy_transform(old,new):
    new.parent=mapping.get(old.parent)
    new.matrix_parent_inverse=old.matrix_parent_inverse.copy()
    new.rotation_mode=old.rotation_mode;new.matrix_basis=old.matrix_basis.copy()

static_points={};static_wires={};counts={'points':0,'wire_segments':0,'source_objects':0,'animated_objects':0}
def payload(store,key):return store.setdefault(key,{'vertices':[],'edges':[],'radii':[]})

def build(name,col,data,kind,level,original=None):
    if not data['vertices']:return None
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(data['vertices'],data['edges'],[]);mesh.update()
    attr=mesh.attributes.new('radius','FLOAT','POINT');attr.data.foreach_set('value',data['radii'])
    obj=bpy.data.objects.new(name,mesh);col.objects.link(obj)
    mod=obj.modifiers.new('Monochrome '+kind,'NODES');mod.node_group=groups[(kind,level)]
    if original:copy_transform(original,obj)
    return obj

image_cache={}
def pixels(image):
    if image.name not in image_cache:
        width,height=image.size;data=np.empty(width*height*4,dtype=np.float32);image.pixels.foreach_get(data)
        image_cache[image.name]=(data.reshape(height,width,4),width,height)
    return image_cache[image.name]

def classification(obj,col_name,dynamic):
    name=obj.name
    if 'Tree •' in name:return 35,2,False,.012
    if 'Pedestrian •' in name:return 190,3,False,.018
    if dynamic:return 28,2,True,.023
    if 'Lobby' in name or 'Entrance' in name:return 2.5,1,True,.019
    if 'Batched details' in name or 'Architectural refinement' in name:return .6,0,True,.018
    if col_name.startswith('04'):return .45,0,True,.023
    return .75,1,True,.022

for obj in list(source.objects):
    if obj.type not in ['MESH','CURVE'] or obj.hide_render or obj in mapping:continue
    col_name=next((c.name for c in obj.users_collection if c.name in collections),None)
    if not col_name:continue
    col=collections[col_name];dynamic=obj.parent in mapping
    if obj.name=='Rain-soaked city plaza':
        # An unlit black ground keeps the view clean rather than filling it with glow.
        floor=obj.copy();floor.data=obj.data.copy();floor.name='Mono • dark reflective ground';col.objects.link(floor)
        dark=emission('obsidian floor',0)
        floor.data.materials.clear();floor.data.materials.append(dark)
        continue
    density,level,with_edges,dot_radius=classification(obj,col_name,dynamic)
    own_points={};own_wires={}
    transform=(lambda v:v.copy()) if dynamic else (lambda v:obj.matrix_world@v)
    def add_point(position,point_level,radius):
        key=point_level if dynamic else (col_name,point_level)
        store=own_points if dynamic else static_points;data=payload(store,key)
        data['vertices'].append(tuple(transform(position)));data['radii'].append(radius);counts['points']+=1
    def add_edge(a,b,line_level,width=.006):
        key=line_level if dynamic else (col_name,line_level)
        store=own_wires if dynamic else static_wires;data=payload(store,key);k=len(data['vertices'])
        data['vertices'].extend([tuple(transform(a)),tuple(transform(b))]);data['edges'].append((k,k+1));data['radii'].extend([width,width]);counts['wire_segments']+=1

    if obj.type=='CURVE':
        # Use clean centerlines rather than the dense bevel tessellation of neon tubes.
        curve_level=2 if any(s in obj.name for s in ['Exoskeleton','perimeter','portal','Maglev']) else 1
        width=.008 if curve_level==2 else .0045
        if 'Tree •' in obj.name or 'Pedestrian •' in obj.name:curve_level=1;width=.004
        for spline in obj.data.splines:
            coords=[Vector(p.co[:3]) for p in spline.points] if spline.type!='BEZIER' else [p.co.copy() for p in spline.bezier_points]
            if spline.use_cyclic_u and coords:coords.append(coords[0])
            for a,b in zip(coords,coords[1:]):add_edge(a,b,curve_level,width)
        counts['source_objects']+=1
    else:
        evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh(preserve_all_data_layers=True,depsgraph=deps)
        if mesh is None:continue
        try:
            mesh.calc_loop_triangles();triangles=[];cumulative=[];area=0
            image=None
            for material in mesh.materials:
                if material and material.name.startswith('Billboard') and material.use_nodes:
                    image=next((n.image for n in material.node_tree.nodes if n.type=='TEX_IMAGE' and n.image),None)
                    if image:break
            if image:density=75;with_edges=True;level=2;dot_radius=.025
            for triangle in mesh.loop_triangles:
                vertices=[mesh.vertices[i].co.copy() for i in triangle.vertices]
                world=[obj.matrix_world@v for v in vertices]
                tri_area=(world[1]-world[0]).cross(world[2]-world[0]).length/2
                if tri_area>1e-9:area+=tri_area;triangles.append((triangle,vertices));cumulative.append(area)
            number=min(16000,int(area*density+rng.random()))
            uv_layer=mesh.uv_layers.active
            texture=pixels(image) if image else None
            for _ in range(number):
                tri,vertices=triangles[bisect.bisect_left(cumulative,rng.random()*area)]
                u=math.sqrt(rng.random());v=rng.random();weights=(1-u,u*(1-v),u*v)
                pos=sum((vertex*weight for vertex,weight in zip(vertices,weights)),Vector())
                point_level=level
                if texture and uv_layer:
                    uv=sum((uv_layer.data[index].uv*weight for index,weight in zip(tri.loops,weights)),Vector((0,0)))
                    data,width,height=texture;ix=min(width-1,max(0,int(uv.x*width)));iy=min(height-1,max(0,int(uv.y*height)))
                    rgb=data[iy,ix,:3];lum=float(rgb[0]*.2126+rgb[1]*.7152+rgb[2]*.0722)
                    if lum<.14 or rng.random()>lum**.75:continue
                    point_level=3 if lum>.65 else 2 if lum>.35 else 1
                add_point(pos,point_level,dot_radius*rng.uniform(.72,1.25))
            if with_edges:
                adjacency={}
                for polygon in mesh.polygons:
                    for edge in polygon.edge_keys:adjacency.setdefault(tuple(sorted(edge)),[]).append(polygon.normal.copy())
                for edge in mesh.edges:
                    a,b=[mesh.vertices[i].co for i in edge.vertices]
                    if (obj.matrix_world.to_3x3()@(b-a)).length<.075:continue
                    normals=adjacency.get(tuple(sorted(edge.vertices)),[])
                    if len(normals)==2 and normals[0].dot(normals[1])>math.cos(math.radians(14)):continue
                    add_edge(a,b,level,.008 if dynamic else .006)
            counts['source_objects']+=1
        finally:evaluated.to_mesh_clear()
    if dynamic:
        for point_level,data in own_points.items():build('Mono points • '+obj.name,col,data,'Points',point_level,obj)
        for line_level,data in own_wires.items():build('Mono wires • '+obj.name,col,data,'Wires',line_level,obj)
        counts['animated_objects']+=1

for (col_name,level),data in static_points.items():build(f'Mono • {col_name} • particles {level}',collections[col_name],data,'Points',level)
for (col_name,level),data in static_wires.items():build(f'Mono • {col_name} • fine outlines {level}',collections[col_name],data,'Wires',level)

# Invisible black wall backings keep the interior from showing the entire city
# through every wall. They occlude geometry without introducing shaded surfaces.
black=emission('interior black backing',0)
for name in ['Lobby • left wall','Lobby • right wall','Lobby • back wall / future design area','Lobby • ceiling']:
    old=source.objects.get(name)
    if old:
        backing=old.copy();backing.data=old.data.copy();backing.name='Mono backing • '+name
        collections['09 Lobby • blockout'].objects.link(backing);backing.data.materials.clear();backing.data.materials.append(black);backing.scale*=.998

# Spatial dust gives the rooms and approach subtle depth, without a sky backdrop.
data={'vertices':[],'edges':[],'radii':[]}
for _ in range(1600):
    data['vertices'].append((rng.uniform(-18,18),rng.uniform(-35,6),rng.uniform(.3,22)));data['radii'].append(rng.uniform(.007,.019))
for _ in range(450):
    data['vertices'].append((rng.uniform(-5.5,5.5),rng.uniform(-4.5,4.5),rng.uniform(.3,4)));data['radii'].append(rng.uniform(.007,.013))
build('Mono • quiet suspended dust',dust,data,'Points',0)

world=bpy.data.worlds.new('Mono • black void');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(0,0,0,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=0;scene.world=world
scene.camera=mapping[source.camera];scene.frame_start=source.frame_start;scene.frame_end=source.frame_end;scene.render.fps=source.render.fps
for marker in source.timeline_markers:scene.timeline_markers.new(marker.name,frame=marker.frame)
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=False
scene.render.preview_pixel_size='1';scene.cycles.preview_samples=64;scene.cycles.preview_adaptive_threshold=.03;scene.cycles.preview_adaptive_min_samples=16;scene.cycles.use_preview_denoising=False
scene.render.resolution_x=960;scene.render.resolution_y=600;scene.render.resolution_percentage=100;scene.render.film_transparent=False
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.filepath=str(ROOT/'monochrome-preview.png')
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0
bpy.context.window.scene=scene;scene.frame_set(1);bpy.context.view_layer.update()
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='SOLID';area.spaces.active.overlay.show_overlays=False
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'monochrome-city-walkthrough.blend'))
result={'scene':scene.name,'file':bpy.data.filepath,'counts':counts,'render_objects':len(scene.objects),'original_scene_preserved':source.name,'frames':[scene.frame_start,scene.frame_end]}
