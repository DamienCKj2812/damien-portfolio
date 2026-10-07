"""Build a grand portal, larger atrium cavity, and continuous integration camera.

Input: city production master. Lobby master is appended read-only. The combined
file is a generated integration asset; neither authored input is overwritten.
"""
import json
import math
import sys
from pathlib import Path
import bpy
from mathutils import Matrix, Quaternion, Vector

ROOT=Path('/home/damienckj/Documents/damien-portfolio')
sys.path.insert(0,str(ROOT/'assets/journey'))
from geometry_clearance import clear_city_sources
scene=bpy.context.scene
if scene.name!='MONO / Wire & Particle City':raise RuntimeError('Open the city production master.')
CITY_END=383;BRIDGE=60;LOBBY_END=1020;END=CITY_END+LOBBY_END
OFFSET=Vector((-1.5,6.45,0))
scene.frame_set(1);bpy.context.view_layer.update()
reference_tower=json.loads(scene.get('reference_tower_redesign','{}'))
cylindrical_reference=reference_tower.get('version',0)>=2
city_camera=scene.camera
scene.objects['Mono • dark reflective ground'].location=(0,0,-.12)
for obj in scene.objects:obj['integration_zone']='city'
city_sources=[obj.name for obj in scene.objects]
entry=bpy.data.collections.new('Journey • Grand entrance');scene.collection.children.link(entry)
cutters=bpy.data.collections.new('Journey • Atrium shell cutters');scene.collection.children.link(cutters)

def material(name,value):
    mat=bpy.data.materials.new('Journey • '+name);mat.use_nodes=True;nodes=mat.node_tree.nodes;nodes.clear();out=nodes.new('ShaderNodeOutputMaterial');em=nodes.new('ShaderNodeEmission');em.inputs['Color'].default_value=(value,value,value,1);em.inputs['Strength'].default_value=1;mat.node_tree.links.new(em.outputs[0],out.inputs[0]);mat.diffuse_color=(value,value,value,1);return mat
wall=material('Podium graphite',.0015 if scene.get('reference_tower_redesign') else .012);metal=material('Doorframe silver facets',.04);glass=material('Dark sliding glass',.016);light=material('Portal white light',1)
template=next(g for g in bpy.data.node_groups if g.name.startswith('Mono • Wires'));stroke=template.copy();stroke.name='Journey • Illuminated entrance contours';stroke.nodes.get('Set Material').inputs['Material'].default_value=light

def box(name,center,size,mat=wall,col=entry,parent=None):
    x,y,z=center;a,b,c=[v/2 for v in size];vertices=[(x+dx*a,y+dy*b,z+dz*c) for dx,dy,dz in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)];mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],faces);mesh.materials.append(mat);mesh.update();obj=bpy.data.objects.new(name,mesh);col.objects.link(obj);obj.parent=parent;obj['city_render_kind']='solid';obj['integration_zone']='city';return obj
def lines(name,paths,parent=None):
    vertices=[];edges=[]
    for path in paths:
        for a,b in zip(path,path[1:]):i=len(vertices);vertices.extend([tuple(a),tuple(b)]);edges.append((i,i+1))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,edges,[]);mesh.update();attr=mesh.attributes.new('radius','FLOAT','POINT');attr.data.foreach_set('value',[.018]*len(vertices));obj=bpy.data.objects.new(name,mesh);entry.objects.link(obj);obj.parent=parent;obj['city_render_kind']='glow';obj['integration_zone']='city';m=obj.modifiers.new('Grand portal lighting','NODES');m.node_group=stroke;return obj
def rectangle(x0,x1,z0,z1,y):return [(x0,y,z0),(x1,y,z0),(x1,y,z1),(x0,y,z1),(x0,y,z0)]
def boolean(obj,cutter,name):m=obj.modifiers.new(name,'BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=cutter
def curves(action):return list(action.fcurves) if hasattr(action,'fcurves') else [f for layer in action.layers for strip in layer.strips for bag in getattr(strip,'channelbags',[]) for f in bag.fcurves]

# Replace the tiny placeholder room and leave the original sliding-root timing.
door_names=['Mono • Entrance • left sliding door','Mono • Entrance • right sliding door']
for side,name in [(-1,door_names[0]),(1,door_names[1])]:
    root=scene.objects[name]
    for child in reversed(list(root.children_recursive)):bpy.data.objects.remove(child,do_unlink=True)
    for col in list(root.users_collection):col.objects.unlink(root)
    entry.objects.link(root);root.animation_data.action=root.animation_data.action.copy()
    for curve in curves(root.animation_data.action):
        if curve.data_path=='location' and curve.array_index==0:
            old=-1.5+side*.81
            for key in curve.keyframe_points:
                for point in [key.co,key.handle_left,key.handle_right]:point.y=-1.5+side*1.50+(point.y-old)/1.65*3.15
    # Opaque leaves overlap at the seam and extend behind both jambs/header.
    box('Portal • tall glass leaf',(0,0,3.80),(3.12,.08,7.76),glass,parent=root)
    for x in [-1.50,1.50]:box('Portal • brushed vertical leaf frame',(x,-.05,3.80),(.055,.10,7.62),metal,parent=root)
    for z in [.03,3.75,7.57]:box('Portal • glass transom',(0,-.05,z),(3.06,.10,.045),metal,parent=root)
    lines('Portal • luminous moving leaf border',[rectangle(-1.50,1.50,.05,7.55,-.10)],root)
    for z in [1.0,1.07]:lines('Portal • etched safety stripe',[[(-1.33,-.105,z),(1.33,-.105,z)]],root)
    box('Portal • long vertical pull',(-side*1.24,-.14,2.60),(.055,.10,1.35),metal,parent=root)
for obj in list(scene.objects):
    if any(c.name=='Mono • 09 Lobby • blockout' for c in obj.users_collection) or obj.name.startswith('Mono backing • Lobby'):
        bpy.data.objects.remove(obj,do_unlink=True)
# Relocate the foreground pier that visually blocks the center of the grand
# entrance. The deck stays on its original path; the new support remains under it.
for obj in scene.objects:
    if obj.type=='MESH' and (obj.name=='Clean outlines • Highway supports' or '05 Elevated highways • particles' in obj.name):
        for vertex in obj.data.vertices:
            p=vertex.co
            if -.34<=p.x<=.34 and -11.95<=p.y<=-11.17 and -.1<=p.z<=6.0:p.x+=4;p.y+=.68
        obj.data.update()

# Enlarge the actual interior void; preserve the street-facing facade skin.
void=box('Atrium • full-height cavity',(-1.5,12.95,9.0),(20.4,36.2,18.15),col=cutters)
portal=box('Atrium • grand doorway opening',(-1.5,-5.42,3.75),(5.75,2.2,7.65),col=cutters)
for obj in [void,portal]:obj.hide_render=True;obj.display_type='WIRE';obj.hide_set(True)
bpy.context.view_layer.update()
# Boolean solids alone leave their separate point/line sources in the opening.
scene['journey_clearance']=json.dumps(clear_city_sources([scene.objects[name] for name in city_sources if scene.objects.get(name)],[void,portal]))
for obj in list(scene.objects):
    if obj.type=='MESH' and obj.get('tower_atrium_clearance'):
        boolean(obj,void,'Integration • clear reference tower from atrium')
    if obj.type=='MESH' and obj.get('tower_portal_clearance'):
        boolean(obj,portal,'Integration • working portal through cylindrical skin')
        # The curved front skin also wraps around both sides of the atrium.
        # Preserve its street-facing band, but remove the portion behind that
        # band so it cannot cover the lobby balconies/trees during the handoff.
        boolean(obj,void,'Integration • clear front skin from atrium interior')
    if obj.type=='MESH' and obj.name.startswith('Hero solid •'):
        if 'central occupied volume' in obj.name or 'supporting tower' in obj.name or 'Media cylinder' in obj.name or 'Cantilever garden' in obj.name:boolean(obj,void,'Integration • clear full atrium')
        if 'central occupied volume' in obj.name:boolean(obj,portal,'Integration • grand entrance opening')
front=box('Podium • full-width frontage',(-1.5,-5.35,9),(20.5,.30,18));boolean(front,portal,'Podium • doorway')
for x in [-11.85,8.85]:box('Podium • side envelope',(x,12.95,9),(.30,36.3,18))
box('Podium • roof',( -1.5,12.95,18.16),(20.7,36.3,.20))
if cylindrical_reference:
    for obj in entry.objects:
        if obj.name.startswith('Podium •'):
            obj.hide_render=True;obj.hide_set(True)
pocket_centers=[-6.15,3.15] if cylindrical_reference else [-7.15,4.15]
pocket_width=3.36 if cylindrical_reference else 5.2
for x in pocket_centers:box('Portal • concealed sliding pocket',(x,-5.69,3.80),(pocket_width,.15,8.04))
for x in [-4.45,1.45]:
    box('Portal • monumental pier',(x,-5.73,3.75),(.32,.42,7.50),metal)
    lines('Portal • vertical white trim',[[(x,-5.96,.08),(x,-5.96,7.63)]])
box('Portal • deep projecting canopy',(-1.5,-6.15,7.65),(6.5,1.70,.28),metal)
text_data=bpy.data.curves.new('Portal • KAZE atrium lettering','FONT');text_data.body='K A J U  /  A T R I U M';text_data.size=.23;text_data.align_x='CENTER';text_data.align_y='CENTER';text_data.materials.append(light)
text=bpy.data.objects.new(text_data.name,text_data);entry.objects.link(text);text.location=(-1.5,-7.012,7.66);text.rotation_euler=(math.pi/2,0,0);text['city_render_kind']='solid';text['integration_zone']='city'
bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();text_mesh=bpy.data.meshes.new_from_object(text.evaluated_get(deps),depsgraph=deps);lettering=bpy.data.objects.new('Portal • solid KAZE lettering',text_mesh);entry.objects.link(lettering);lettering.matrix_world=text.matrix_world;lettering['city_render_kind']='solid';lettering['integration_zone']='city';bpy.data.objects.remove(text,do_unlink=True)
if scene.get('reference_tower_redesign'):lettering.hide_render=True
lines('Portal • canopy perimeter',[[(-4.75,-6.99,7.51),(1.75,-6.99,7.51),(1.75,-5.31,7.51),(-4.75,-5.31,7.51),(-4.75,-6.99,7.51)]])
box('Portal • threshold',(-1.5,-5.55,.05),(5.8,1.4,.08),metal)
lines('Portal • threshold guides',[[(-4.25,-6.35,.10),(-4.25,-4.9,.10)],[(1.25,-6.35,.10),(1.25,-4.9,.10)]])
for x in [-4.60,1.60]:box('Portal • access panel',(x,-5.98,1.52),(.20,.035,.43),glass)
if cylindrical_reference:
    recess=bpy.data.objects.new('Portal • recessed cylindrical vestibule',None);entry.objects.link(recess)
    recess.location=(0,1.8,0)
    for name in door_names:
        root=scene.objects[name];root.parent=recess;root.matrix_parent_inverse=Matrix.Identity(4)
    for obj in entry.objects:
        if obj.name.startswith('Portal • concealed sliding pocket'):obj.location.y+=1.8
    # A fixed, closed casing hides each moving leaf from exterior side angles.
    # Fit to the fully-open leaf envelope instead of the former broad planar
    # screens, which cut across the neighboring curved storefront in close-up.
    for x in pocket_centers:
        box('Portal • pocket rear enclosure',(x,-3.49,3.80),(pocket_width,.12,8.04),wall)
        for end in [x-pocket_width/2,x+pocket_width/2]:
            box('Portal • pocket side enclosure',(end,-3.69,3.80),(.12,.52,8.04),wall)
        for z in [-.17,7.77]:
            box('Portal • pocket top bottom enclosure',(x,-3.69,z),(pocket_width,.52,.10),wall)
    # Enclose the depth between the street jamb and recessed leaves. Without
    # these returns, oblique rays bypass a closed leaf through the side/header.
    for side,x in [('left',-4.39),('right',1.39)]:
        box('Portal • vestibule '+side+' reveal',(x,-4.77,3.91),(.30,2.42,7.98),wall)
    box('Portal • vestibule header reveal',(-1.5,-4.77,7.73),(6.08,2.42,.38),wall)
    box('Portal • vestibule floor reveal',(-1.5,-4.77,.015),(6.08,2.42,.10),metal)
# Raise the low mobility campaign clear of the seven-meter doorway.
for obj in scene.objects:
    if obj.name.startswith('Hero display • Clean mobility campaign') or obj.name.startswith('Hero glow • Clean mobility campaign'):obj.location.z+=4
old_frame=scene.objects.get('Clean outlines • Billboard frames')
if old_frame:
    original=old_frame.data;vertices=[];edges=[];radii=[]
    for edge in original.edges:
        points=[original.vertices[index].co for index in edge.vertices]
        obsolete=all(-6.15<=p.x<=2.35 and abs(p.y+6.12)<.04 and 4.0<=p.z<=10.60 for p in points)
        if obsolete:continue
        k=len(vertices);vertices.extend([tuple(p) for p in points]);edges.append((k,k+1));radii.extend([original.attributes['radius'].data[index].value for index in edge.vertices])
    mesh=bpy.data.meshes.new('Billboard frames • Raised entrance campaign');mesh.from_pydata(vertices,edges,[]);mesh.update();attr=mesh.attributes.new('radius','FLOAT','POINT');attr.data.foreach_set('value',radii);old_frame.data=mesh

city_samples=json.loads((ROOT/'assets/cyber-city/walkthrough-camera.json').read_text())['samples']
lobby_data=json.loads((ROOT/'assets/kaze-lobby/navigation-camera.json').read_text())
lobby_samples=lobby_data['samples']
with bpy.data.libraries.load(str(ROOT/'assets/kaze-lobby/kaze-lobby-walkthrough.blend'),link=False) as (available,loaded):loaded.scenes=['KAZE / Monochrome Atrium']
source=loaded.scenes[0]
integration=bpy.data.collections.new('Journey • Authored KAZE atrium');scene.collection.children.link(integration)
anchor=bpy.data.objects.new('Journey • Lobby entrance alignment',None);integration.objects.link(anchor);anchor.location=OFFSET
mapping={}
for old in source.objects:
    if old.type=='CAMERA':continue
    new=old.copy();new.name='Integrated • '+old.name;integration.objects.link(new);new['integration_zone']='lobby';mapping[old]=new
    if old.animation_data and old.animation_data.action:
        new.animation_data.action=old.animation_data.action.copy()
        for curve in curves(new.animation_data.action):
            for key in curve.keyframe_points:
                for point in [key.co,key.handle_left,key.handle_right]:point.x+=CITY_END
for old,new in mapping.items():
    new.parent=mapping.get(old.parent,anchor);new.matrix_parent_inverse=old.matrix_parent_inverse.copy();new.matrix_basis=old.matrix_basis.copy()
    for constraint in new.constraints:
        if hasattr(constraint,'target') and constraint.target in mapping:constraint.target=mapping[constraint.target]

data=bpy.data.cameras.new('Journey • Continuous city-to-lobby camera');camera=bpy.data.objects.new(data.name,data);entry.objects.link(camera);camera.rotation_mode='QUATERNION';data.clip_start=.05;data.clip_end=250
city_end=city_samples[CITY_END-1];start_q=Quaternion(city_end['quaternion_wxyz'])
for f in range(1,END+1):
    if f<=CITY_END:
        sample=city_samples[f-1];position=Vector(sample['position']);q=Quaternion(sample['quaternion_wxyz']);lens=sample['lens_mm']
    else:
        local=f-CITY_END;sample=lobby_samples[local-1];position=Vector(sample['position'])+OFFSET;q=Quaternion(sample['quaternion_wxyz']);lens=sample['lens_mm']
        if local<=BRIDGE:
            t=local/BRIDGE;t=t*t*(3-2*t);position=Vector(city_end['position']).lerp(position,t);q=start_q.slerp(q,t);lens=city_end['lens_mm']+(lens-city_end['lens_mm'])*t
    camera.location=position;camera.rotation_quaternion=q;data.lens=lens;camera.keyframe_insert(data_path='location',frame=f);camera.keyframe_insert(data_path='rotation_quaternion',frame=f);data.keyframe_insert(data_path='lens',frame=f)
for owner in [camera,data]:
    for curve in curves(owner.animation_data.action):
        for key in curve.keyframe_points:key.interpolation='LINEAR'
scene.camera=camera;scene.frame_start=1;scene.frame_end=END;scene.render.fps=30;scene.render.resolution_x=1280;scene.render.resolution_y=800
scene['journey_city_camera']=city_camera.name;scene['journey_city_frames']=450
config={'version':1,'cityEnd':CITY_END,'cityHideFrame':CITY_END,'transitionFrames':BRIDGE,'lobbyEnd':LOBBY_END,'frameEnd':END,'fps':30,'lobbyOffset':list(OFFSET),'lobbyRevealFrame':245,'lobbyHoldFrame':245,'preloadFrame':100,'bookmarks':{'start':1,'lookDown':90,'doors':245,'train':145,'entrance':CITY_END,'lobby':CITY_END+BRIDGE,'reception':CITY_END+320,'escalator':CITY_END+510,'landing':CITY_END+690,'elevator':CITY_END+840,'elevatorOpen':END},'portal':{'center':[-1.5,-5.55,0],'width':5.75,'height':7.65},'lobbyPortal':{'center':[-1.5,-5.98,3.825],'width':5.48,'height':7.45},'lobbyAssetBase':'models/lobby/'}
scene['journey_config']=json.dumps(config)
scene.frame_set(1);scene.view_layers[0].update()
output=ROOT/'assets/journey/city-lobby-walkthrough.blend';bpy.data.libraries.write(str(output),{scene},fake_user=False,compress=True)
(ROOT/'assets/journey/city-lobby-handoff.json').write_text(json.dumps(config,indent=2))
(ROOT/'public/models/journey.json').write_text(json.dumps(config,indent=2))
result={'combined_file':str(output),'city_endpoint_frame':CITY_END,'lobby_start_global_frame':CITY_END+1,'final_frame':END,'entrance_height':7.65,'lobby_translation':list(OFFSET),'authored_inputs_modified':False}
print(json.dumps(result))
