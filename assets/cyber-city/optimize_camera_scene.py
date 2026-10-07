"""Prune static geometry outside the entire camera route, then write a slim blend.

Uses every camera sample with a 15% framing margin. Whole humanoids and tree
clusters are retained when visible; moving traffic and all animation rigs stay.
"""
import json
import math
from pathlib import Path
import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector
from mathutils.kdtree import KDTree

ROOT=Path('/home/damienckj/Documents/damien-portfolio/assets/cyber-city')
scene=bpy.context.scene
if scene.name!='MONO / Wire & Particle City':
    raise RuntimeError('Activate the monochrome walkthrough first.')
source=bpy.data.scenes.get('NEON / Kaze Megacity')
if not source:raise RuntimeError('Run optimization in the full editable file with its source scene.')
if bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_cancel(restore_frame=False)
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':area.spaces.active.shading.type='SOLID'
scene.frame_set(1);bpy.context.view_layer.update()
samples=json.loads((ROOT/'walkthrough-camera.json').read_text())['samples']
projection=scene.camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=scene.render.resolution_x,y=scene.render.resolution_y,scale_x=scene.render.pixel_aspect_x,scale_y=scene.render.pixel_aspect_y)
matrices=[];exterior=[]
for sample in samples:
    world=Matrix.LocRotScale(Vector(sample['position']),Quaternion(sample['quaternion_wxyz']),Vector((1,1,1)))
    matrix=np.asarray(projection@world.inverted(),dtype=np.float64);matrices.append(matrix)
    # Once inside, black lobby backings occlude the exterior ahead of the camera.
    if sample['position'][1]<=-5.3:exterior.append(matrix)
matrices=np.asarray(matrices);exterior=np.asarray(exterior);MARGIN=1.15

def planes(clip):
    x,y,z,w=np.moveaxis(clip,-1,0)
    return np.stack([MARGIN*w+x,MARGIN*w-x,MARGIN*w+y,MARGIN*w-y,w+z,w-z],axis=-1)

def point_visibility(vertices,views):
    homogeneous=np.column_stack([vertices,np.ones(len(vertices))]);visible=np.zeros(len(vertices),dtype=bool)
    for matrix in views:
        indices=np.flatnonzero(~visible)
        if not len(indices):break
        distances=planes(homogeneous[indices]@matrix.T)
        visible[indices]=np.all(distances>=-1e-6,axis=1)
    return visible

def bounds_visibility(lo,hi,views):
    corners=np.array([(x,y,z,1) for x in [lo[0],hi[0]] for y in [lo[1],hi[1]] for z in [lo[2],hi[2]]])
    clip=np.einsum('fij,vj->fvi',views,corners)
    # Conservative box/frustum test: reject only if all corners lie beyond a plane.
    outside=np.any(np.all(planes(clip)<-1e-6,axis=1),axis=1)
    return bool(np.any(~outside))

def edge_visibility(vertices,edges,views):
    homogeneous=np.column_stack([vertices,np.ones(len(vertices))]);visible=np.zeros(len(edges),dtype=bool)
    for matrix in views:
        indices=np.flatnonzero(~visible)
        if not len(indices):break
        da=planes(homogeneous[edges[indices,0]]@matrix.T);db=planes(homogeneous[edges[indices,1]]@matrix.T)
        lower=np.zeros(len(indices));upper=np.ones(len(indices));valid=np.ones(len(indices),dtype=bool)
        for plane in range(6):
            start=da[:,plane];delta=db[:,plane]-start
            parallel=np.abs(delta)<1e-12;valid&=~(parallel&(start<0))
            crossing=np.divide(-start,delta,out=np.zeros_like(start),where=~parallel)
            lower=np.where(delta>0,np.maximum(lower,crossing),lower)
            upper=np.where(delta<0,np.minimum(upper,crossing),upper)
        visible[indices]=valid&(lower<=upper)&(upper>=0)&(lower<=1)
    return visible

def mesh_arrays(obj):
    count=len(obj.data.vertices);coords=np.empty(count*3,dtype=np.float64);obj.data.vertices.foreach_get('co',coords);coords=coords.reshape(-1,3)
    world=np.asarray(obj.matrix_world);positions=coords@world[:3,:3].T+world[:3,3]
    radius=np.empty(count,dtype=np.float32);obj.data.attributes['radius'].data.foreach_get('value',radius)
    return coords,positions,radius

def replace_mesh(obj,coords,radius,keep,edges=None,person_ids=None):
    indices=np.flatnonzero(keep);mesh=bpy.data.meshes.new(obj.data.name+' • camera optimized')
    remapped=[]
    if edges is not None:remapped=np.searchsorted(indices,edges).tolist()
    mesh.from_pydata(coords[indices].tolist(),remapped,[]);mesh.update()
    attr=mesh.attributes.new('radius','FLOAT','POINT');attr.data.foreach_set('value',radius[indices])
    if person_ids is not None:
        attr=mesh.attributes.new('person_id','INT','POINT');attr.data.foreach_set('value',person_ids[indices])
    obj.data=mesh

# Identify the separate people within their aggregated particle mesh.
crowd=scene.objects['Mono • 07 Street life • particles 3']
if 'person_id' not in crowd.data.attributes or 'person_metadata' not in crowd:
    raise RuntimeError('Run improve_humans.py first to add stable person IDs.')
crowd_ids=np.empty(len(crowd.data.vertices),dtype=np.int32);crowd.data.attributes['person_id'].data.foreach_get('value',crowd_ids)
people=json.loads(crowd['person_metadata'])

# Tree bounds and spatial labels keep the full cluster of any visible tree.
trees=[]
for obj in source.objects:
    if obj.type=='CURVE' and obj.name.startswith('Tree • trunk'):
        a=obj.matrix_world@Vector(obj.data.splines[0].points[0].co[:3]);b=obj.matrix_world@Vector(obj.data.splines[0].points[-1].co[:3])
        scale=(b-a).length/1.5;lo=np.array([a.x-scale,a.y-scale,a.z]);hi=np.array([a.x+scale,a.y+scale,a.z+2.8*scale])
        trees.append({'center':a+Vector((0,0,1.65*scale)),'visible':bounds_visibility(lo,hi,exterior)})
tree_kd=KDTree(len(trees))
for i,tree in enumerate(trees):tree_kd.insert(tree['center'],i)
tree_kd.balance()

# Skyline volumes provide whole-building retention for their particle clouds.
buildings=[]
for obj in source.objects:
    if obj.type=='MESH' and ((obj.name.startswith('Skyline') and '• tower' in obj.name) or obj.name.startswith('Flanking skyline • stepped shaft')):
        corners=np.asarray([obj.matrix_world@Vector(corner) for corner in obj.bound_box]);lo=corners.min(axis=0)-.3;hi=corners.max(axis=0)+.3;hi[2]+=6
        buildings.append({'name':obj.name,'center':Vector((obj.location.x,obj.location.y,0)),'visible':bounds_visibility(lo,hi,exterior)})
building_kd=KDTree(len(buildings))
for i,building in enumerate(buildings):building_kd.insert(building['center'],i)
building_kd.balance()

stats={'camera_frames_checked':len(matrices),'margin_percent':15,'people_before':len(people),'people_after':0,'trees_before':len(trees),'trees_after':sum(tree['visible'] for tree in trees),'skyline_before':len(buildings),'skyline_after':sum(building['visible'] for building in buildings),'points_before':0,'points_after':0,'segments_before':0,'segments_after':0,'unused_mesh_objects_removed':0}
remove=[]
for obj in list(scene.objects):
    if obj.type!='MESH' or obj.parent or obj.animation_data:continue
    if any(col.hide_render for col in obj.users_collection):continue
    if obj.hide_render and obj.name.startswith('Mono •'):
        remove.append(obj);continue
    if not obj.modifiers or obj.modifiers[0].type!='NODES':continue
    group=obj.modifiers[0].node_group
    if not group or 'radius' not in obj.data.attributes:continue
    coords,positions,radius=mesh_arrays(obj)
    is_exterior=any(label in obj.name for label in ['01 Megatower','02 Neon media','03 Sky garden','04 Skyline','05 Elevated highways','07 Street life','Clean outlines'])
    views=exterior if is_exterior else matrices
    if not len(obj.data.edges):
        stats['points_before']+=len(coords);keep=point_visibility(positions,views);person_ids=None
        if obj==crowd:
            person_ids=crowd_ids;retained=[]
            for person in people:
                indices=np.flatnonzero(person_ids==person['id']);points=positions[indices]
                if not len(points):continue
                visible=bounds_visibility(points.min(axis=0)-.025,points.max(axis=0)+.025,exterior)
                keep[indices]=visible;stats['people_after']+=int(visible)
                if visible:retained.append(person)
            crowd['person_metadata']=json.dumps(retained)
        elif obj.name in ['Mono • 03 Sky garden • particles 2','Mono • 07 Street life • particles 2']:
            labels=np.array([tree_kd.find(Vector(point))[1] for point in positions],dtype=np.int32)
            keep|=np.array([trees[index]['visible'] for index in labels])
        elif '04 Skyline • particles' in obj.name:
            labels=np.array([building_kd.find(Vector((point[0],point[1],0)))[1] for point in positions],dtype=np.int32)
            keep|=np.array([buildings[index]['visible'] for index in labels])
        stats['points_after']+=int(keep.sum())
        if not np.any(keep):remove.append(obj)
        elif not np.all(keep):replace_mesh(obj,coords,radius,keep,person_ids=person_ids)
    else:
        edges=np.empty(len(obj.data.edges)*2,dtype=np.int32);obj.data.edges.foreach_get('vertices',edges);edges=edges.reshape(-1,2)
        stats['segments_before']+=len(edges);keep_edges=edge_visibility(positions,edges,views);stats['segments_after']+=int(keep_edges.sum())
        if not np.any(keep_edges):remove.append(obj)
        elif not np.all(keep_edges):
            kept=edges[keep_edges];keep_vertices=np.zeros(len(coords),dtype=bool);keep_vertices[np.unique(kept)]=True
            replace_mesh(obj,coords,radius,keep_vertices,kept)
for obj in remove:
    # Only generated mono meshes are removed; original scenes are not edited.
    if len(obj.users_scene)==1:
        bpy.data.objects.remove(obj,do_unlink=True);stats['unused_mesh_objects_removed']+=1

scene['camera_optimization']=json.dumps(stats)
scene.frame_set(1);bpy.context.view_layer.update()
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':area.spaces.active.shading.type='RENDERED';area.spaces.active.overlay.show_overlays=False;area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'monochrome-city-walkthrough.blend'))
# Write just this scene and its dependencies, excluding all original source scenes.
optimized=ROOT/'monochrome-city-optimized.blend'
bpy.data.libraries.write(str(optimized),{scene},fake_user=False,compress=True)
stats['optimized_file']=str(optimized);stats['optimized_MB']=round(optimized.stat().st_size/1e6,2)
(ROOT/'camera-optimization.json').write_text(json.dumps(stats,indent=2))
result=stats
