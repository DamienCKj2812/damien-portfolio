"""Export optimized native point/line data and baked motion for the React viewer."""
import json
import hashlib
import math
import shutil
from array import array
from pathlib import Path
import bpy

ROOT=Path('/home/damienckj/Documents/damien-portfolio')
OUTPUT=ROOT/'public/models/city'
scene=bpy.context.scene
if scene.name!='MONO / Wire & Particle City':raise RuntimeError('Open the optimized monochrome scene first.')
if not OUTPUT.is_dir():raise RuntimeError('Create public/models/city before exporting.')
screen=bpy.context.screen
if screen and screen.is_animation_playing:bpy.ops.screen.animation_cancel(restore_frame=False)
for area in (screen.areas if screen else []):
    if area.type=='VIEW_3D':area.spaces.active.shading.type='SOLID'
scene.frame_set(1);bpy.context.view_layer.update()
city_camera=scene.objects.get(scene.get('journey_city_camera','')) or scene.camera
city_frame_end=int(scene.get('journey_city_frames',scene.frame_end))

def animated_root(obj):
    root=None;parent=obj.parent
    while parent:
        if parent.animation_data and parent.animation_data.action:root=parent
        parent=parent.parent
    return root

objects=[o for o in scene.objects if o.type=='MESH' and not o.hide_render and o.get('integration_zone','city')=='city' and not any(c.hide_render for c in o.users_collection)]
roots=sorted({root for o in objects if (root:=animated_root(o)) is not None},key=lambda obj:obj.name)
root_indices={obj:i+1 for i,obj in enumerate(roots)}
buffers={}
point_count=0;line_count=0;outline_count=0;glow_count=0;mask_triangles=0;solid_triangles=0;screen_triangles=0;textures=set()
deps=bpy.context.evaluated_depsgraph_get()
for obj in objects:
    root=animated_root(obj)
    transform=root.matrix_world.inverted()@obj.matrix_world if root else obj.matrix_world
    actor=root_indices.get(root,0)
    scale=max(abs(v) for v in transform.to_scale())
    modifier=next((m for m in obj.modifiers if m.type=='NODES'),None)
    if modifier and 'radius' in obj.data.attributes:
        kind=obj.get('city_browser_render_kind',obj.get('city_render_kind','lines' if len(obj.data.edges) else 'points'))
        if kind == 'points' and obj.get('city_sky_shine'):
            kind = 'skyShinePoints'
        elif kind == 'points' and (obj.name == 'Mono • quiet suspended dust' or obj.get('city_sky_points')):
            kind = 'skyPoints'
        elif obj.get('city_skyline'):
            kind = 'skylinePoints' if kind == 'points' else 'skylineLines'
        values=buffers.setdefault((actor,kind),array('f'))
        material=modifier.node_group.nodes.get('Set Material').inputs['Material'].default_value
        emission=next(n for n in material.node_tree.nodes if n.type=='EMISSION')
        color=emission.inputs['Color'].default_value
        luminance=obj.get('city_browser_luminance',(color[0]*.2126+color[1]*.7152+color[2]*.0722)*emission.inputs['Strength'].default_value)
        if kind in ['points', 'skyPoints', 'skyShinePoints', 'skylinePoints']:
            for vertex,radius in zip(obj.data.vertices,obj.data.attributes['radius'].data):
                p=transform@vertex.co;values.extend((*p,obj.get('city_shine_radius',radius.value)*scale,luminance))
            point_count+=len(obj.data.vertices)
        else:
            for edge in obj.data.edges:
                for index in edge.vertices:
                    p=transform@obj.data.vertices[index].co;values.extend((*p,luminance))
            if kind=='outline':outline_count+=len(obj.data.edges)
            elif kind=='glow':glow_count+=len(obj.data.edges)
            else:line_count+=len(obj.data.edges)
    else:
        # Keep the approved ground/lobby anchors in the browser copy. These
        # invisible backing objects were translated independently in the file;
        # correcting the export does not modify the artist's Blender scene.
        anchors={
            'Mono • dark reflective ground':(0,0,-.12),
            'Mono backing • Lobby • left wall':(-5.75,0,2.2),
            'Mono backing • Lobby • right wall':(5.75,0,2.2),
            'Mono backing • Lobby • back wall / future design area':(0,4.82,2.2),
            'Mono backing • Lobby • ceiling':(0,0,4.3),
        }
        if obj.name in anchors:
            transform=transform.copy();transform.translation=anchors[obj.name]
        kind=obj.get('city_render_kind','mask')
        texture=obj.get('city_texture') if kind=='screen' else None
        if texture:textures.add(texture)
        key=f'screen|{texture}' if texture else kind
        values=buffers.setdefault((actor,key),array('f'))
        evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh(preserve_all_data_layers=True,depsgraph=deps);mesh.calc_loop_triangles()
        for triangle in mesh.loop_triangles:
            luminance=0
            if kind=='solid':
                mat=mesh.materials[triangle.material_index]
                emission=next(node for node in mat.node_tree.nodes if node.type=='EMISSION')
                color=emission.inputs['Color'].default_value
                luminance=mat.get('city_browser_luminance',(color[0]*.2126+color[1]*.7152+color[2]*.0722)*emission.inputs['Strength'].default_value)
            for index,loop in zip(triangle.vertices,triangle.loops):
                values.extend(transform@mesh.vertices[index].co)
                if kind=='solid':values.append(luminance)
                elif kind=='screen':values.extend(mesh.uv_layers.active.data[loop].uv)
        if kind=='solid':solid_triangles+=len(mesh.loop_triangles)
        elif kind=='screen':screen_triangles+=len(mesh.loop_triangles)
        else:mask_triangles+=len(mesh.loop_triangles)
        evaluated.to_mesh_clear()

geometry=array('f');groups=[]
for (actor,key),values in sorted(buffers.items()):
    kind,_,texture=key.partition('|')
    stride={'points':5,'skyPoints':5,'skyShinePoints':5,'skylinePoints':5,'skylineLines':4,'lines':4,'outline':4,'glow':4,'solid':4,'screen':5,'mask':3}[kind]
    render_kind={'skyPoints':'points','skyShinePoints':'points','skylinePoints':'points','skylineLines':'lines'}.get(kind,kind)
    descriptor={'actor':actor,'kind':render_kind,'byteOffset':len(geometry)*4,'floatCount':len(values),'vertexCount':len(values)//stride,'stride':stride}
    if kind == 'skyPoints':
        descriptor['role'] = 'sky'
    if kind == 'skyShinePoints':
        descriptor['role'] = 'sky-shine'
    if kind in ['skylinePoints', 'skylineLines']:
        descriptor['role'] = 'skyline'
    if texture:descriptor['texture']=f'ads/{texture}'
    groups.append(descriptor)
    geometry.extend(values)
(OUTPUT/'geometry.bin').write_bytes(geometry.tobytes())

# Frame-major layout. Each channel stores position XYZ, quaternion XYZW, scale XYZ.
channels=[city_camera,*roots];animation=array('f')
for frame in range(scene.frame_start,city_frame_end+1):
    scene.frame_set(frame);bpy.context.view_layer.update()
    for obj in channels:
        position,rotation,scale=obj.matrix_world.decompose()
        animation.extend((*position,rotation.x,rotation.y,rotation.z,rotation.w,*scale))
(OUTPUT/'animation.bin').write_bytes(animation.tobytes())
camera=city_camera.data
aspect=scene.render.resolution_x/scene.render.resolution_y
vertical_fov=math.degrees(2*math.atan(camera.sensor_width/(2*camera.lens*aspect)))
manifest={
    'version':3,'coordinateSystem':'Blender Z-up','geometry':'geometry.bin','animation':'animation.bin','preview':'preview.png',
    'assetHash':hashlib.sha256(geometry.tobytes()+animation.tobytes()).hexdigest()[:12],
    'frameStart':scene.frame_start,'frameEnd':city_frame_end,'fps':scene.render.fps,
    'channelStride':10,'channelCount':len(channels),'channels':[o.name for o in channels],
    'actors':[{'index':root_indices[o],'name':o.name,'style':o.get('city_role','particle'),**({'walk':json.loads(o['city_walk'])} if 'city_walk' in o else {}),**({'autonomous':True,'motion':json.loads(o['city_motion'])} if o.get('city_autonomous') else {})} for o in roots],
    'camera':{'verticalFov':vertical_fov,'sourceAspect':aspect,'near':camera.clip_start,'far':camera.clip_end},
    'bookmarks':{
        'start':scene.frame_start,
        'lookDown':next((m.frame for m in scene.timeline_markers if m.name.startswith('02 •')),90),
        'doors':next((m.frame for m in scene.timeline_markers if m.name.startswith('03 •')),245),
        'train':next((m.frame for m in scene.timeline_markers if m.name.startswith('Traffic • train')),145),
        'entrance':next((m.frame for m in scene.timeline_markers if m.name.startswith('04 •')),383),
        'lobby':city_frame_end,
    },
    'textures':[f'ads/{file}' for file in sorted(textures)],
    'groups':groups,'statistics':{'points':point_count,'lineSegments':line_count,'vehicleOutlineSegments':outline_count,'glowSegments':glow_count,'solidTriangles':solid_triangles,'screenTriangles':screen_triangles,'maskTriangles':mask_triangles},
}
if scene.get('orbital_sky_reference'):
    manifest['orbitalSky']=json.loads(scene['orbital_sky_reference'])
if scene.get('street_plaza_reference'):
    manifest['streetPlaza']=json.loads(scene['street_plaza_reference'])
if scene.get('reference_tower_redesign'):
    manifest['referenceTower']=json.loads(scene['reference_tower_redesign'])
if scene.get('left_transit_route'):
    manifest['trainRoute']=json.loads(scene['left_transit_route'])
if scene.get('background_train_route'):
    manifest['backgroundTrain']=json.loads(scene['background_train_route'])
if scene.get('wireframe_skyline'):
    manifest['wireframeSkyline']=json.loads(scene['wireframe_skyline'])
digest=hashlib.sha256(geometry.tobytes()+animation.tobytes())
for file in sorted(textures):
    image=ROOT/'assets/cyber-city/textures-monochrome'/file
    shutil.copyfile(image,OUTPUT/'ads'/file);digest.update(image.read_bytes())
manifest['assetHash']=digest.hexdigest()[:12]
(OUTPUT/'scene.json').write_text(json.dumps(manifest,indent=2))
preview=ROOT/'assets/cyber-city'/('restored-sky-preview.png' if scene.get('reference_tower_redesign') and scene.get('orbital_sky_reference') and (ROOT/'assets/cyber-city/restored-sky-preview.png').exists() else 'reference-tower-preview.png' if scene.get('reference_tower_redesign') else 'orbital-sky-preview.png' if scene.get('orbital_sky_reference') else 'monochrome-optimized-approach.png')
if preview.exists():shutil.copyfile(preview,OUTPUT/'preview.png')
scene.frame_set(1);bpy.context.view_layer.update()
for area in (screen.areas if screen else []):
    if area.type=='VIEW_3D':area.spaces.active.shading.type='RENDERED'
result={'output':str(OUTPUT),'groups':len(groups),'actors':len(roots),'statistics':manifest['statistics'],'geometry_bytes':len(geometry)*4,'animation_bytes':len(animation)*4}
