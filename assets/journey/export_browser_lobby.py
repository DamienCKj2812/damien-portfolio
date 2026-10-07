"""Export the authored lobby's point sources, feature curves, solids, and route.

Read-only export: no lobby Blender data is saved or rebuilt.
"""
import hashlib
import json
import math
import shutil
import sys
from array import array
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path('/home/damienckj/Documents/damien-portfolio')
sys.path.insert(0,str(ROOT/'assets/journey'))
from geometry_clearance import fit_r1_doors
OUTPUT=ROOT/'public/models/lobby'
scene=bpy.data.scenes['KAZE / Monochrome Atrium']
camera=scene.objects['Lobby • Navigation / walkthrough camera']
scene.frame_set(1);scene.view_layers[0].update()
fit_r1_doors(scene)
# Clear the authored interior placeholder in the export copy only. The original
# lobby remains unchanged, and its R1 doors still cover this opening until ready.
# Fit the cut to R1's existing jambs/header, rather than the wider cabin shell.
cut_mesh=bpy.data.meshes.new('Browser • R1 cabin aperture');x,y,z=4.05,25.1,7.66;a,b,c=1.06,2.25,1.56
cut_mesh.from_pydata([(x+dx*a,y+dy*b,z+dz*c) for dx,dy,dz in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]],[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);cut_mesh.update()
cutter=bpy.data.objects.new('Browser • R1 cavity cutter',cut_mesh);scene.collection.objects.link(cutter);cutter.hide_render=True
for name in ['Lobby • Elevator R1 / wall surround','Lobby • Rear atrium wall']:
    obj=scene.objects.get(name)
    if obj:mod=obj.modifiers.new('Browser • fitted cabin opening','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
scene.view_layers[0].update()

def root_for(obj):
    # Bake the closest animated ancestor's world pose. Choosing an outer root
    # would freeze the fish's nested tail/fin actions at the export rest frame.
    if obj.animation_data and obj.animation_data.action:
        return obj
    parent=obj.parent
    while parent:
        if parent.animation_data and parent.animation_data.action:return parent
        parent=parent.parent
    return None
objects=[o for o in scene.objects if o.type in ['MESH','CURVE','FONT'] and not o.hide_render and o.name!='Lobby • Navigation / R1 interior handoff / black backing' and not any(c.hide_render for c in o.users_collection)]
roots=sorted({root_for(o) for o in objects if root_for(o)},key=lambda o:o.name)
indices={root:i+1 for i,root in enumerate(roots)}
buffers={};morph_buffers={};shapes={};statistics={'points':0,'lineSegments':0,'glowSegments':0,'solidTriangles':0}
deps=bpy.context.evaluated_depsgraph_get()
def shade(material):
    if not material:return .25,False
    for node in material.node_tree.nodes if material.use_nodes else []:
        if node.type=='EMISSION':return sum(node.inputs['Color'].default_value[:3])/3*node.inputs['Strength'].default_value,True
        if node.type=='BSDF_PRINCIPLED':
            color=node.inputs['Base Color'].default_value;emission=node.inputs['Emission Strength'].default_value
            value=sum(color[:3])/3
            return min(1.5,value*max(1,emission)),emission>=2
    return sum(material.diffuse_color[:3])/3,False
for obj in objects:
    root=root_for(obj);actor=indices.get(root,0);transform=root.matrix_world.inverted()@obj.matrix_world if root else obj.matrix_world
    modifier=next((m for m in obj.modifiers if m.type=='NODES'),None)
    if obj.type=='MESH' and not obj.data.polygons and len(obj.data.vertices):
        radius_node=next((n for n in modifier.node_group.nodes if n.bl_idname=='GeometryNodeMeshIcoSphere'),None)
        mat_node=next((n for n in modifier.node_group.nodes if n.bl_idname=='GeometryNodeSetMaterial'),None)
        radius=radius_node.inputs['Radius'].default_value if radius_node else .005
        luminance,_=shade(mat_node.inputs['Material'].default_value if mat_node else None)
        values=buffers.setdefault((actor,'points'),array('f'));scale=max(abs(v) for v in transform.to_scale())
        basis=obj.data.shape_keys.key_blocks[0].data if obj.data.shape_keys else obj.data.vertices
        for vertex in basis:values.extend((*(transform@vertex.co),radius*scale,luminance))
        if obj.data.shape_keys:
            shapes[root]=obj
            morph_buffers[(actor,'points')]=[]
            for shape in list(obj.data.shape_keys.key_blocks)[1:]:
                delta=array('f')
                for a,b in zip(basis,shape.data):delta.extend(transform.to_3x3()@(b.co-a.co))
                morph_buffers[(actor,'points')].append(delta)
        statistics['points']+=len(obj.data.vertices)
    elif obj.type=='CURVE':
        luminance,glow=shade(obj.data.materials[0] if obj.data.materials else None)
        kind='glow' if glow else 'lines';values=buffers.setdefault((actor,kind),array('f'))
        for spline in obj.data.splines:
            points=[Vector(p.co[:3]) for p in spline.points] if spline.type!='BEZIER' else [p.co for p in spline.bezier_points]
            if spline.use_cyclic_u and points:points.append(points[0])
            for a,b in zip(points,points[1:]):
                for point in [a,b]:values.extend((*(transform@point),luminance))
                statistics['glowSegments' if glow else 'lineSegments']+=1
    else:
        evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh(preserve_all_data_layers=True,depsgraph=deps)
        if not mesh:continue
        mesh.calc_loop_triangles();values=buffers.setdefault((actor,'solid'),array('f'))
        for triangle in mesh.loop_triangles:
            luminance,_=shade(mesh.materials[triangle.material_index] if mesh.materials else None)
            # Large black architecture should occlude, not acquire diffuse fill.
            if luminance<.006:luminance=0
            for index in triangle.vertices:values.extend((*(transform@mesh.vertices[index].co),luminance))
        statistics['solidTriangles']+=len(mesh.loop_triangles);evaluated.to_mesh_clear()

geometry=array('f');groups=[]
for (actor,kind),values in sorted(buffers.items()):
    stride=5 if kind=='points' else 4
    group={'actor':actor,'kind':kind,'byteOffset':len(geometry)*4,'floatCount':len(values),'vertexCount':len(values)//stride,'stride':stride};geometry.extend(values)
    if (actor,kind) in morph_buffers:
        group['morphs']=[]
        for delta in morph_buffers[(actor,kind)]:
            group['morphs'].append({'byteOffset':len(geometry)*4,'floatCount':len(delta)});geometry.extend(delta)
    groups.append(group)
(OUTPUT/'geometry.bin').write_bytes(geometry.tobytes())
animation=array('f');channels=[camera,*roots];FRAME_END=1020
for frame in range(1,FRAME_END+1):
    scene.frame_set(frame);scene.view_layers[0].update()
    for channel,obj in enumerate(channels):
        position,q,scale=obj.matrix_world.decompose()
        fov=math.degrees(2*math.atan(camera.data.sensor_width/(2*camera.data.lens*1.6))) if channel==0 else 0
        animation.extend((*position,q.x,q.y,q.z,q.w,*scale,fov,0 if obj.hide_render else 1))
        weights=[key.value for key in list(shapes[obj].data.shape_keys.key_blocks)[1:]] if obj in shapes else []
        animation.extend(weights+[0]*(4-len(weights)))
(OUTPUT/'animation.bin').write_bytes(animation.tobytes())
scene.frame_set(1);scene.view_layers[0].update()
manifest={'version':3,'coordinateSystem':'Blender Z-up','geometry':'geometry.bin','animation':'animation.bin','preview':'preview.png','assetHash':hashlib.sha256(geometry.tobytes()+animation.tobytes()).hexdigest()[:12],'frameStart':1,'frameEnd':FRAME_END,'fps':30,'channelStride':12,'channelCount':len(channels),'channels':[o.name for o in channels],'actors':[{'index':indices[o],'name':o.name,'style':'lobby','visibilityOffset':11} for o in roots],'camera':{'verticalFov':math.degrees(2*math.atan(camera.data.sensor_width/(2*camera.data.lens*1.6))),'sourceAspect':1.6,'near':.05,'far':250,'fovOffset':10},'textures':[],'groups':groups,'statistics':statistics,'bookmarks':{'start':1,'reception':320,'escalator':510,'landing':690,'elevator':840,'elevatorOpen':1020}}
manifest['channelStride']=16
manifest['npcLoopFrames']=scene.get('autonomous_npc_period',1019)
manifest['autonomousLoopFrames']=manifest['npcLoopFrames']
if scene.get('autonomous_fish_period'):
    manifest['fishLoopFrames']=scene['autonomous_fish_period']
for actor,root in zip(manifest['actors'],roots):
    actor['autonomous']=bool(root.get('autonomous_npc') or root.get('autonomous_lobby'))
    actor['morphCount']=len(shapes[root].data.shape_keys.key_blocks)-1 if root in shapes else 0
    if root.get('activity_loop'):actor['activity']=root['activity_loop']
    if root.get('npc_owner'):actor['autonomous']=True
    if root.get('fish_part'):
        actor['motionType']='holographicFish'
        actor['part']=root['fish_part']
        actor['loopFrames']=root['loop_frames']
(OUTPUT/'scene.json').write_text(json.dumps(manifest,indent=2))
shutil.copyfile(ROOT/'assets/kaze-lobby/navigation-start.png',OUTPUT/'preview.png')
result={'output':str(OUTPUT),'geometry_bytes':len(geometry)*4,'animation_bytes':len(animation)*4,'groups':len(groups),'animated_geometry_roots':len(roots),'statistics':statistics,'lobby_master_modified':False}
print(json.dumps(result))
