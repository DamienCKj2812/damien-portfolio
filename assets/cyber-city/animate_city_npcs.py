"""Give configured street walkers scroll-synchronized paths in the city master."""
import json
import math
import os
from pathlib import Path
import bpy
from mathutils import Matrix, Vector

ROOT=Path('/home/damienckj/Documents/damien-portfolio/assets/cyber-city')
scene=bpy.context.scene
if scene.name!='MONO / Wire & Particle City':raise RuntimeError('Open the production city.')
if any(o.get('city_role')=='walking_npc' for o in scene.objects):raise RuntimeError('Walking NPC rigs already exist; edit their existing paths.')
crowd=scene.objects['Mono • 07 Street life • particles 3'];metadata=json.loads(crowd['person_metadata'])
ids=[value.value for value in crowd.data.attributes['person_id'].data]
plans=[(p['id'],p['walk']['offset'],p['walk']['startFrame'],p['walk']['endFrame']) for p in metadata if p.get('walk')]
if not plans:raise RuntimeError('No walking paths are configured in npc-layout.json.')
collection=bpy.data.collections.new('City NPC • Scroll-driven walkers');scene.collection.children.link(collection)
walking=[]
for person_id,offset,start,end in plans:
    person=next(p for p in metadata if p['id']==person_id)
    if person.get('pose')!='walking':raise RuntimeError(f'NPC {person_id} is not a walking pose.')
    base=Vector(person['base']);scale=float(person['scale']);movement=Vector(offset)
    inverse=Matrix.Rotation(-person['facing'],4,'Z')@Matrix.Translation(-base)
    indices=[i for i,id in enumerate(ids) if id==person_id]
    points=[tuple((inverse@crowd.data.vertices[i].co)/scale) for i in indices]
    radius=[crowd.data.attributes['radius'].data[i].value/scale for i in indices]
    mesh=bpy.data.meshes.new(f'Walker {person_id:02d} • local articulated points');mesh.from_pydata(points,[],[]);mesh.update()
    attr=mesh.attributes.new('radius','FLOAT','POINT');attr.data.foreach_set('value',radius)
    attr=mesh.attributes.new('person_id','INT','POINT');attr.data.foreach_set('value',[person_id]*len(points))
    root=bpy.data.objects.new(f'City NPC • Walker {person_id:02d}',None);collection.objects.link(root)
    root.location=base;root.scale=(scale,scale,scale);root.rotation_euler.z=math.atan2(movement.x,-movement.y)
    root['city_role']='walking_npc';root['person_metadata']=json.dumps(person)
    root['city_walk']=json.dumps({'startFrame':start,'endFrame':end,'distance':movement.length,'stride':1.3,'phase':person_id*.67})
    for frame,position in [(1,base),(start,base),(end,base+movement),(450,base+movement)]:
        root.location=position;root.keyframe_insert(data_path='location',frame=frame)
    action=root.animation_data.action
    curves=list(action.fcurves) if hasattr(action,'fcurves') else [curve for layer in action.layers for strip in layer.strips for bag in getattr(strip,'channelbags',[]) for curve in bag.fcurves]
    for curve in curves:
        for key in curve.keyframe_points:key.interpolation='LINEAR'
    obj=bpy.data.objects.new(f'City NPC • Walker {person_id:02d} particles',mesh);collection.objects.link(obj);obj.parent=root
    modifier=obj.modifiers.new('Reference particle body','NODES');modifier.node_group=crowd.modifiers[0].node_group
    walking.append({'id':person_id,'actor':root.name,'startFrame':start,'endFrame':end,'distance':movement.length,'base':list(base),'end':list(base+movement)})

# Remove those people from the stationary batch so there are no duplicate figures.
moving_ids={plan[0] for plan in plans};keep=[i for i,id in enumerate(ids) if id not in moving_ids]
mesh=bpy.data.meshes.new('City crowd • stationary reference poses');mesh.from_pydata([tuple(crowd.data.vertices[i].co) for i in keep],[],[]);mesh.update()
attr=mesh.attributes.new('radius','FLOAT','POINT');attr.data.foreach_set('value',[crowd.data.attributes['radius'].data[i].value for i in keep])
attr=mesh.attributes.new('person_id','INT','POINT');attr.data.foreach_set('value',[ids[i] for i in keep])
crowd.data=mesh;crowd['person_metadata']=json.dumps([p for p in metadata if p['id'] not in moving_ids])
scene['walking_npc_paths']=json.dumps(walking)
scene.timeline_markers.new('NPC • Street walkers moving',frame=180)
scene.frame_set(1);scene.view_layers[0].update()
master=ROOT/'monochrome-city-solid-tower.blend';staging=master.with_name(master.stem+'.pending.blend')
bpy.data.libraries.write(str(staging),{scene},fake_user=False,compress=True);os.replace(staging,master)
(ROOT/'npc-walking-paths.json').write_text(json.dumps(walking,indent=2))
result={'walking_people':len(walking),'stationary_people':len(metadata)-len(walking),'paths':walking,'animation':'translation baked in Blender; distance-driven stepping rendered in the browser'}
