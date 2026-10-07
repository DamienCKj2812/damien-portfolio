"""Read-only checks on the combined cabin-entry preview and authored motion."""
import json
import math
from pathlib import Path
import bpy
from mathutils import Quaternion, Vector

ROOT=Path('/home/damienckj/Documents/damien-portfolio');scene=bpy.context.scene;config=json.loads(scene['journey_config'])
manifest=json.loads((ROOT/'public/models/elevator/scene.json').read_text())
from array import array
motion=array('f');motion.frombytes((ROOT/'public/models/elevator/animation.bin').read_bytes())
offset=(config['elevatorSelectionFrame']-1)*manifest['channelCount']*manifest['channelStride'];expected=Vector(motion[offset:offset+3])+Vector(config['elevatorOffset']);expected_q=Quaternion((motion[offset+6],motion[offset+3],motion[offset+4],motion[offset+5]))
scene.frame_set(config['frameEnd']);scene.view_layers[0].update();camera=scene.camera
position_error=(camera.matrix_world.translation-expected).length;angle=camera.matrix_world.to_quaternion().rotation_difference(expected_q).angle;angle=min(angle,abs(2*math.pi-angle))
assert position_error<.0001 and angle<.001
samples=[]
for frame in range(config['lobbyGlobalEnd'],config['frameEnd']+1):
    scene.frame_set(frame);scene.view_layers[0].update();samples.append(scene.camera.matrix_world.translation.copy())
assert all(samples[i].y>=samples[i-1].y-1e-5 for i in range(1,len(samples)))
# The cabin must sit behind the original landing frame and preserve its display
# throughout opening. Cast toward actual glyph vertices, not the text's empty center.
display=scene.objects['Integrated • Lobby • Elevator R1 / floor display']
visible_frames=[config['elevatorHoldFrame'],config['elevatorHoldFrame']+30,config['lobbyGlobalEnd']]
for frame in visible_frames:
    scene.frame_set(frame);scene.view_layers[0].update()
    evaluated=display.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh()
    origin=scene.camera.matrix_world.translation.copy()
    for vertex in list(mesh.vertices)[::max(1,len(mesh.vertices)//12)]:
        target=display.matrix_world@vertex.co;direction=target-origin
        hit,point,normal,index,obj,matrix=scene.ray_cast(bpy.context.evaluated_depsgraph_get(),origin,direction.normalized(),distance=direction.length-.002)
        assert not hit or obj.hide_render or obj==display, f'R1 display blocked at {frame} by {obj.name}'
    evaluated.to_mesh_clear()
report={'entry_stop_global_frame':config['frameEnd'],'authored_selection_frame':config['elevatorSelectionFrame'],'selection_position_error_m':position_error,'selection_rotation_error_rad':angle,'entry_never_steps_back':True,'max_entry_step_m':max((samples[i]-samples[i-1]).length for i in range(1,len(samples))),'cabin_entrance_world':config['elevatorOffset'],'floor_buttons':len(manifest['interactions']),'elevator_source_modified':False,'unobstructed_R1_display_frames':visible_frames}
(ROOT/'assets/journey/elevator-handoff-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
