"""Match the street crowd to NPC point forms in the authored lobby reference.

Reads the lobby file without saving it. Copies suitable outdoor poses and their
props into existing city positions; the city's animation and architecture stay.
"""
import json
import math
import os
from pathlib import Path
import random
import bpy
from mathutils import Matrix, Vector

ROOT=Path('/home/damienckj/Documents/damien-portfolio')
MASTER=ROOT/'assets/cyber-city/monochrome-city-solid-tower.blend'
REFERENCE=ROOT/'assets/kaze-lobby/kaze-lobby-walkthrough.blend'
scene=bpy.context.scene
if scene.name!='MONO / Wire & Particle City':raise RuntimeError('Open the city production master.')
scene.frame_set(1);bpy.context.view_layer.update()
crowd=scene.objects['Mono • 07 Street life • particles 3']
people=json.loads(crowd['person_metadata'])
# A reference refresh first folds our moving people back into the source crowd.
# The walking stage can then be rebuilt once, without duplicate old walkers.
walkers=[o for o in scene.objects if o.get('city_role')=='walking_npc']
for walker in walkers:
    people.append(json.loads(walker['person_metadata']))
    for child in reversed(list(walker.children_recursive)):bpy.data.objects.remove(child,do_unlink=True)
    bpy.data.objects.remove(walker,do_unlink=True)
people=sorted({person['id']:person for person in people}.values(),key=lambda person:person['id'])
walking_collection=bpy.data.collections.get('City NPC • Scroll-driven walkers')
if walking_collection and not walking_collection.objects:bpy.data.collections.remove(walking_collection)
if 'walking_npc_paths' in scene:del scene['walking_npc_paths']
layout=ROOT/'assets/cyber-city/npc-layout.json'
if layout.exists():people=json.loads(layout.read_text())['people']
with bpy.data.libraries.load(str(REFERENCE),link=False) as (available,loaded):
    loaded.scenes=['KAZE / Monochrome Atrium']
reference=loaded.scenes[0];reference.frame_set(1)
allowed={'walking','carrying_bag','phone','observing','talking','listening'}
templates=[o for o in reference.objects if o.type=='MESH' and o.get('pose') in allowed]
if not templates:raise RuntimeError('No suitable NPC forms found in the lobby reference.')
by_pose={pose:[o for o in templates if o['pose']==pose] for pose in allowed}
pattern=['walking','walking','carrying_bag','phone','walking','observing','talking','listening','walking','phone','walking','observing']

def emission(name,value):
    material=bpy.data.materials.new(name);material.use_nodes=True;n=material.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');node=n.new('ShaderNodeEmission');node.inputs['Color'].default_value=(value,value,value,1);node.inputs['Strength'].default_value=1;material.node_tree.links.new(node.outputs[0],out.inputs[0]);return material

props_col=bpy.data.collections.get('City NPC • Lobby-reference accessories')
if props_col:
    for obj in list(props_col.objects):bpy.data.objects.remove(obj,do_unlink=True)
else:
    props_col=bpy.data.collections.new('City NPC • Lobby-reference accessories');scene.collection.children.link(props_col)
prop_mat=emission('City NPC • Dark activity props',.016)
edge_mat=emission('City NPC • Activity prop edges',.5)
template_group=next(g for g in bpy.data.node_groups if g.name.startswith('Mono • Wires'))
prop_edges=template_group.copy();prop_edges.name='City NPC • Thin accessory outlines';prop_edges.nodes.get('Set Material').inputs['Material'].default_value=edge_mat
def wire(name,segments):
    vertices=[];edges=[]
    for a,b in segments:k=len(vertices);vertices.extend([tuple(a),tuple(b)]);edges.append((k,k+1))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,edges,[]);mesh.update();attr=mesh.attributes.new('radius','FLOAT','POINT');attr.data.foreach_set('value',[.004]*len(vertices))
    obj=bpy.data.objects.new(name,mesh);props_col.objects.link(obj);modifier=obj.modifiers.new('Fine activity outlines','NODES');modifier.node_group=prop_edges

rng=random.Random(186)
vertices=[];radii=[];ids=[];new_metadata=[];pose_counts={};prop_count=0
for i,person in enumerate(people):
    pose=person.get('pose',pattern[i%len(pattern)]) if layout.exists() else pattern[i%len(pattern)]
    options=by_pose[pose];template=options[i%len(options)]
    origin=Vector(template['pose_origin']);angle=float(template['facing_angle_rad'])
    reference_inverse=Matrix.Rotation(-angle,4,'Z')@Matrix.Translation(-origin)
    local=[reference_inverse@(template.matrix_world@v.co) for v in template.data.vertices]
    minimum=min(v.z for v in local);height=max(v.z for v in local)-minimum
    scale=float(person.get('scale',1));normalization=2.05/height
    base=Vector(person['base'])
    if person.get('walk'):
        direction=Vector(person['walk']['offset']);facing=math.atan2(direction.x,-direction.y)
    elif 'facing' in person:facing=float(person['facing'])
    elif pose=='walking':
        direction=Vector((-1.5-base.x,-5.3-base.y,0))
        if i%3==0:direction=-direction
        facing=math.atan2(direction.x,-direction.y)
    else:facing=rng.uniform(-1.1,1.1)
    placement=Matrix.Translation(base)@Matrix.Rotation(facing,4,'Z')@Matrix.Scale(scale*normalization,4)@Matrix.Translation(Vector((0,0,-minimum)))
    count=min(len(local),max(650,int(1200*scale*scale)))
    selected=rng.sample(range(len(local)),count)
    for index in selected:
        vertices.append(tuple(placement@local[index]));radii.append(.005*scale*rng.uniform(.8,1.15));ids.append(person['id'])
    record=dict(person);record.update(points=count,height=2.05*scale,pose=pose,facing=facing,reference_npc=template.name,reference_file='assets/kaze-lobby/kaze-lobby-walkthrough.blend')
    new_metadata.append(record);pose_counts[pose]=pose_counts.get(pose,0)+1
    for prop in reference.objects:
        if prop.get('npc_owner')!=template.name:continue
        name=f'City NPC {person["id"]:02d} • {prop.name.split(" / ")[-1]}'
        if prop.type=='MESH':
            mesh=prop.data.copy()
            # Reference prop object transforms can be stale independently of
            # the point body. Anchor its copied box to the verified hand pose.
            center=Vector((0,-.345,1.40)) if pose=='phone' else Vector((.32,.01,.57))
            original_center=sum((vertex.co for vertex in mesh.vertices),Vector())/len(mesh.vertices)
            for vertex in mesh.vertices:vertex.co=placement@(vertex.co-original_center+center)
            mesh.update()
            mesh.materials.clear();mesh.materials.append(prop_mat)
            for polygon in mesh.polygons:polygon.material_index=0
            obj=bpy.data.objects.new(name,mesh);props_col.objects.link(obj);obj['city_render_kind']='solid';obj['npc_owner']=person['id'];prop_count+=1
            wire(name+' • hand-aligned edges',[tuple(mesh.vertices[index].co for index in edge.vertices) for edge in mesh.edges])
            if pose=='carrying_bag':
                points=[(.32,-.055,.72),(.32,-.055,.805),(.32,.075,.805),(.32,.075,.72)]
                wire(name+' • handle',[(placement@Vector(a),placement@Vector(b)) for a,b in zip(points,points[1:])])
        elif prop.type=='CURVE':
            # Box contours and bag handles are rebuilt above from the same
            # hand anchors, avoiding misplaced duplicate reference outlines.
            continue

mesh=bpy.data.meshes.new('City crowd • Lobby-reference articulated forms');mesh.from_pydata(vertices,[],[]);mesh.update()
radius=mesh.attributes.new('radius','FLOAT','POINT');radius.data.foreach_set('value',radii)
person_ids=mesh.attributes.new('person_id','INT','POINT');person_ids.data.foreach_set('value',ids)
crowd.data=mesh;crowd['person_metadata']=json.dumps(new_metadata);crowd['npc_reference']='assets/kaze-lobby/kaze-lobby-walkthrough.blend';crowd['npc_pose_counts']=json.dumps(pose_counts)
scene['npc_design_reference']=crowd['npc_reference']
scene.frame_set(1);scene.view_layers[0].update()
# Atomically update the production master, without making another retained snapshot.
staging=MASTER.with_name(MASTER.stem+'.pending.blend')
bpy.data.libraries.write(str(staging),{scene},fake_user=False,compress=True);os.replace(staging,MASTER)
result={'production_master':str(MASTER),'reference_read_only':str(REFERENCE),'people':len(people),'points':len(vertices),'pose_counts':pose_counts,'solid_activity_props':prop_count,'layout_source':'npc-layout.json' if layout.exists() else 'existing city positions'}
