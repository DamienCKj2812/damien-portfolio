"""Append the authored cabin into the generated journey without saving inputs."""
import json
import math
import sys
from pathlib import Path
from array import array
import bpy
from mathutils import Matrix, Quaternion, Vector

ROOT=Path('/home/damienckj/Documents/damien-portfolio');scene=bpy.context.scene;config=json.loads(scene['journey_config'])
sys.path.insert(0,str(ROOT/'assets/journey'))
from geometry_clearance import fit_r1_doors
LOBBY_END=1403;ENTRY_START=62;SELECT=180;STOP=LOBBY_END+SELECT-ENTRY_START
# Recess the cabin behind the landing doors. Its ceiling/front trim must never
# sit in front of R1's smaller portal or its floor indicator.
offset=Vector((4.05,24.165,6.12))+Vector(config['lobbyOffset'])
with bpy.data.libraries.load(str(ROOT/'assets/kaze-elevator/kaze-elevator-journey.blend'),link=False) as (available,loaded):loaded.scenes=['KAZE / Enter - choose - exit']
source=loaded.scenes[0];source_camera=source.objects['Elevator / Full journey camera']
group=bpy.data.collections.new('Journey • Interactive elevator cabin');scene.collection.children.link(group);anchor=bpy.data.objects.new('Journey • R1 cabin alignment',None);group.objects.link(anchor);anchor.location=offset
def curves(action):return list(action.fcurves) if hasattr(action,'fcurves') else [c for layer in action.layers for strip in layer.strips for bag in getattr(strip,'channelbags',[]) for c in bag.fcurves]
mapping={}
for old in source.objects:
    if old.type=='CAMERA' or any(c.name.startswith('Elevator / Dialog / ') or c.name.startswith('Elevator / Destination / ') for c in old.users_collection):continue
    if any(c.name in ['Elevator / Entrance approach','Elevator / Journey staging'] for c in old.users_collection):continue
    new=old.copy();new.name='Integrated • '+old.name;group.objects.link(new);new['integration_zone']='elevator';mapping[old]=new
    if old.animation_data and old.animation_data.action:
        new.animation_data.action=old.animation_data.action.copy()
        for curve in curves(new.animation_data.action):
            for key in curve.keyframe_points:
                for point in [key.co,key.handle_left,key.handle_right]:point.x+=LOBBY_END-ENTRY_START
for old,new in mapping.items():
    new.parent=mapping.get(old.parent,anchor);new.matrix_parent_inverse=old.matrix_parent_inverse.copy();new.matrix_basis=old.matrix_basis.copy()
    for constraint in new.constraints:
        if hasattr(constraint,'target') and constraint.target in mapping:constraint.target=mapping[constraint.target]

# Clear the combined lobby shell, matching the separately exported opening.
backing=scene.objects.get('Integrated • Lobby • Navigation / R1 interior handoff / black backing')
if backing:bpy.data.objects.remove(backing,do_unlink=True)
mesh=bpy.data.meshes.new('Journey • Elevator aperture tool');x,y,z=4.05,25.1,7.66
verts=[tuple(Vector((x+dx*1.06,y+dy*2.25,z+dz*1.56))+Vector(config['lobbyOffset'])) for dx,dy,dz in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]];mesh.from_pydata(verts,[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);mesh.update();tool=bpy.data.objects.new('Journey • R1 portal cutter',mesh);group.objects.link(tool);tool.hide_render=True;tool.hide_set(True)
for name in ['Integrated • Lobby • Elevator R1 / wall surround','Integrated • Lobby • Rear atrium wall']:
    obj=scene.objects.get(name)
    if obj:mod=obj.modifiers.new('Journey • cabin clearance','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=tool
fit_r1_doors(scene,'Integrated • ')

camera=scene.camera;scene.frame_set(LOBBY_END);scene.view_layers[0].update();last_position=camera.matrix_world.translation.copy();last_q=camera.matrix_world.to_quaternion();last_lens=camera.data.lens
elevator_manifest=json.loads((ROOT/'public/models/elevator/scene.json').read_text());motion=array('f');motion.frombytes((ROOT/'public/models/elevator/animation.bin').read_bytes())
for frame in range(LOBBY_END+1,STOP+1):
    local=ENTRY_START+frame-LOBBY_END;index=(local-1)*elevator_manifest['channelCount']*elevator_manifest['channelStride'];position=Vector(motion[index:index+3])+offset;position.y=max(last_position.y,position.y);q=Quaternion((motion[index+6],motion[index+3],motion[index+4],motion[index+5]));lens=21
    t=min(1,(frame-LOBBY_END)/30);t=t*t*(3-2*t);position=last_position.lerp(position,t);q=last_q.slerp(q,t);lens=last_lens+(lens-last_lens)*t
    scene.frame_set(frame)
    camera.location=position;camera.rotation_quaternion=q;camera.data.lens=lens;camera.keyframe_insert(data_path='location',frame=frame);camera.keyframe_insert(data_path='rotation_quaternion',frame=frame);camera.data.keyframe_insert(data_path='lens',frame=frame)
for owner in [camera,camera.data]:
    for curve in curves(owner.animation_data.action):
        for key in curve.keyframe_points:key.interpolation='LINEAR'
config.update(frameEnd=STOP,lobbyGlobalEnd=LOBBY_END,elevatorOffset=list(offset),elevatorEntryStart=ENTRY_START,elevatorSelectionFrame=SELECT,elevatorTransitionFrames=30,elevatorRevealFrame=config['cityEnd']+900,elevatorHoldFrame=config['cityEnd']+900,elevatorPreloadFrame=config['bookmarks']['escalator'],lobbyHideFrame=LOBBY_END+142-ENTRY_START)
config['bookmarks'].update(cabin=STOP);scene['journey_config']=json.dumps(config);scene.frame_end=STOP;scene.frame_set(1);scene.view_layers[0].update()
config['rooms']=json.loads((ROOT/'assets/journey/room-destinations.json').read_text());scene['journey_config']=json.dumps(config)
output=ROOT/'assets/journey/portfolio-journey.blend';bpy.data.libraries.write(str(output),{scene},fake_user=False,compress=True)
for path in [ROOT/'public/models/journey.json',ROOT/'assets/journey/city-lobby-handoff.json']:path.write_text(json.dumps(config,indent=2))
print(json.dumps({'file':str(output),'cabin_translation':list(offset),'entry_stop_global_frame':STOP,'source_entry_start':ENTRY_START,'authored_inputs_modified':False}))
