"""Read-only elevator export, including level buttons and destination variants."""
import ast
import hashlib
import json
import math
from array import array
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path('/home/damienckj/Documents/damien-portfolio')
OUTPUT=ROOT/'public/models/elevator'
scene=bpy.context.scene;camera=scene.objects['Elevator / Full journey camera']
scene.frame_set(1);scene.view_layers[0].update()
# Bake every destination sign even though the authored review keeps unselected
# collections hidden. Runtime variants decide which one is drawn in Three.js.
for collection in scene.collection.children:
    if collection.name.startswith('Elevator / Destination / '):
        collection.hide_render=False;collection.hide_viewport=False
        for obj in collection.objects:obj.hide_render=False;obj.hide_viewport=False;obj.hide_set(False)
scene.view_layers[0].update()
helpers=ast.parse((ROOT/'assets/journey/export_browser_lobby.py').read_text())
exec(compile(ast.Module(body=[n for n in helpers.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'lobby-export-helpers','exec'),globals())
levels=json.loads((ROOT/'assets/kaze-elevator/elevator-levels.json').read_text())['levels']
rooms=json.loads((ROOT/'assets/journey/room-destinations.json').read_text())
levels=[{**level,'available':level['id'] in rooms,'room':rooms.get(level['id'])} for level in levels]
roots=[scene.objects['Elevator / Left sliding door'],scene.objects['Elevator / Right sliding door']];indices={o:i+1 for i,o in enumerate(roots)}
buffers={};interactions=[];statistics={'points':0,'lineSegments':0,'glowSegments':0,'solidTriangles':0};deps=bpy.context.evaluated_depsgraph_get()
def moving_root(obj):
    if obj in indices:return obj
    parent=obj.parent
    while parent:
        if parent in indices:return parent
        parent=parent.parent
    return None
for obj in scene.objects:
    if obj.type not in ['MESH','CURVE','FONT']:continue
    collections=[c.name for c in obj.users_collection]
    dialog=next((c for c in collections if c.startswith('Elevator / Dialog / ')),None)
    destination=next((c for c in collections if c.startswith('Elevator / Destination / ')),None)
    # Old description cards are intentionally hidden by the direct-departure design.
    if dialog:continue
    if obj.hide_render and not destination:continue
    stage='exit' if any(c in ['Elevator / Entrance approach','Elevator / Journey staging'] for c in collections) and not moving_root(obj) else 'all'
    level=destination.rsplit(' / ',1)[-1] if destination else ''
    role='destination' if destination else ''
    if obj.name=='Elevator / Current floor display':role='displayDefault'
    button=obj.get('level_id') if obj.type=='MESH' and obj.name.startswith('Elevator / Level button ') else None
    if button:level=button;role='button'
    elif obj.get('level_id') and 'Elevator / Controls' in collections:
        # Move the printed lettering and border with their physical switch.
        level=obj['level_id'];role='buttonDetail'
    root=moving_root(obj);actor=indices.get(root,0);transform=root.matrix_world.inverted()@obj.matrix_world if root else obj.matrix_world
    modifier=next((m for m in obj.modifiers if m.type=='NODES'),None)
    if obj.name=='Elevator / Stippled surfaces and human portrait':
        # The author built each dot as a six-vertex octahedron. Export one GPU
        # point per dot instead of tens of thousands of tiny solid triangles.
        values=buffers.setdefault((actor,'points',level,role,stage),array('f'));luminance,_=shade(obj.data.materials[0])
        if len(obj.data.vertices)%6:raise RuntimeError('Unexpected elevator stipple topology.')
        for i in range(0,len(obj.data.vertices),6):
            verts=[obj.data.vertices[i+j].co for j in range(6)];center=sum(verts,Vector())/6;radius=max((v-center).length for v in verts)
            values.extend((*(transform@center),radius,luminance));statistics['points']+=1
    elif obj.type=='MESH' and not obj.data.polygons and obj.data.vertices:
        radius=.005;material=None
        if modifier:
            node=next((n for n in modifier.node_group.nodes if n.bl_idname=='GeometryNodeMeshIcoSphere'),None)
            if node:radius=node.inputs['Radius'].default_value
            mat_node=next((n for n in modifier.node_group.nodes if n.bl_idname=='GeometryNodeSetMaterial'),None)
            if mat_node:material=mat_node.inputs['Material'].default_value
        luminance,_=shade(material);values=buffers.setdefault((actor,'points',level,role,stage),array('f'));scale=max(abs(v) for v in transform.to_scale())
        for vertex in obj.data.vertices:values.extend((*(transform@vertex.co),radius*scale,luminance))
        statistics['points']+=len(obj.data.vertices)
    elif obj.type=='CURVE':
        luminance,glow=shade(obj.data.materials[0] if obj.data.materials else None);kind='glow' if glow else 'lines';values=buffers.setdefault((actor,kind,level,role,stage),array('f'))
        for spline in obj.data.splines:
            points=[Vector(p.co[:3]) for p in spline.points] if spline.type!='BEZIER' else [p.co for p in spline.bezier_points]
            if spline.use_cyclic_u and points:points.append(points[0])
            for a,b in zip(points,points[1:]):
                for p in [a,b]:values.extend((*(transform@p),luminance))
                statistics['glowSegments' if glow else 'lineSegments']+=1
    else:
        evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh(preserve_all_data_layers=True,depsgraph=deps)
        if not mesh:continue
        mesh.calc_loop_triangles();values=buffers.setdefault((actor,'solid',level,role,stage),array('f'))
        for triangle in mesh.loop_triangles:
            luminance,_=shade(mesh.materials[triangle.material_index] if mesh.materials else None)
            for index in triangle.vertices:values.extend((*(transform@mesh.vertices[index].co),luminance))
        statistics['solidTriangles']+=len(mesh.loop_triangles);evaluated.to_mesh_clear()
    if button:
        center=obj.matrix_world.translation;interactions.append({'id':button,'button':obj.name,'position':list(center),'dimensions':list(obj.dimensions)})

# Five ready-made numeric display variants; no browser font dependency is needed.
display=scene.objects['Elevator / Current floor display']
for level in levels:
    obj=display.copy();obj.data=display.data.copy();obj.data.body=f'{level["number"]:02}';scene.collection.objects.link(obj);scene.view_layers[0].update()
    evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh();mesh.calc_loop_triangles();values=buffers.setdefault((0,'solid',level['id'],'display','all'),array('f'))
    for triangle in mesh.loop_triangles:
        for index in triangle.vertices:values.extend((*(obj.matrix_world@mesh.vertices[index].co),.85))
    evaluated.to_mesh_clear();bpy.data.objects.remove(obj,do_unlink=True)

geometry=array('f');groups=[]
for (actor,kind,level,role,stage),values in sorted(buffers.items()):
    stride=5 if kind=='points' else 4;groups.append({'actor':actor,'kind':kind,'byteOffset':len(geometry)*4,'floatCount':len(values),'vertexCount':len(values)//stride,'stride':stride,'level':level or None,'role':role or None,'stage':stage,'available':level in rooms if role=='button' else True});geometry.extend(values)
(OUTPUT/'geometry.bin').write_bytes(geometry.tobytes());animation=array('f');channels=[camera,*roots]
for frame in range(1,511):
    scene.frame_set(frame);scene.view_layers[0].update()
    for i,obj in enumerate(channels):
        p,q,s=obj.matrix_world.decompose();fov=math.degrees(2*math.atan(camera.data.sensor_width/(2*camera.data.lens*1.6))) if i==0 else 0
        animation.extend((*p,q.x,q.y,q.z,q.w,*s,fov,1))
(OUTPUT/'animation.bin').write_bytes(animation.tobytes())
manifest={'version':3,'geometry':'geometry.bin','animation':'animation.bin','assetHash':hashlib.sha256(geometry.tobytes()+animation.tobytes()).hexdigest()[:12],'frameStart':1,'frameEnd':510,'fps':30,'channelStride':12,'channelCount':len(channels),'channels':[o.name for o in channels],'actors':[{'index':indices[o],'name':o.name,'style':'elevator'} for o in roots],'camera':{'verticalFov':56.14,'sourceAspect':1.6,'near':.025,'far':250,'fovOffset':10},'textures':[],'groups':groups,'levels':levels,'interactions':interactions,'statistics':statistics,'flow':{'entryStart':62,'selectionFrame':180,'departureStart':181,'arrivalFrame':510,'doorsClose':[181,220],'doorsOpen':[300,350],'walkout':[370,510]}}
(OUTPUT/'scene.json').write_text(json.dumps(manifest,indent=2));print(json.dumps({'output':str(OUTPUT),'groups':len(groups),'buttons':len(interactions),'geometry_bytes':len(geometry)*4,'animation_bytes':len(animation)*4,'statistics':statistics,'authored_source_modified':False}))
