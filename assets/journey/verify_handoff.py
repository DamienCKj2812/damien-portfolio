"""Read-only continuity/entrance checks on the generated integration blend."""
import json
import math
from pathlib import Path
import bpy
from mathutils import Quaternion, Vector
from mathutils.bvhtree import BVHTree

ROOT=Path('/home/damienckj/Documents/damien-portfolio')
scene=bpy.context.scene;config=json.loads(scene['journey_config'])

def bounds(obj):
    points=[obj.matrix_world@Vector(p) for p in obj.bound_box]
    return [min(p[i] for p in points) for i in range(3)],[max(p[i] for p in points) for i in range(3)]

# Closed leaves cover the actual aperture, and fully open leaves fit entirely
# behind the pockets. This catches both light leaks and exposed moving borders.
scene.frame_set(config['lobbyHoldFrame']);scene.view_layers[0].update()
leaves=[scene.objects['Portal • tall glass leaf'+suffix] for suffix in ['', '.001']]
opening=bounds(scene.objects['Atrium • grand doorway opening'])
closed=[bounds(leaf) for leaf in leaves]
assert closed[0][0][0]<=opening[0][0] and closed[1][1][0]>=opening[1][0]
seam_overlap=closed[0][1][0]-closed[1][0][0]
assert seam_overlap>0
assert all(low[2]<=.001 and high[2]>=opening[1][2] for low,high in closed)
sealed_rays=0
if json.loads(scene.get('reference_tower_redesign','{}')).get('version',0)>=2:
    # A projected width test cannot detect a gap along the depth of a recessed
    # door. Test the actual leaves/returns from central and oblique viewpoints.
    blockers=[o for o in scene.objects if o.type=='MESH' and not o.hide_render and
              (o.name.startswith('Portal • tall glass leaf') or 'vestibule' in o.name and 'reveal' in o.name)]
    trees=[BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],
                               [tuple(p.vertices) for p in o.data.polygons]) for o in blockers]
    for eye in [Vector((-1.5,-15,1.7)),Vector((9,-14,1.7)),Vector((-10,-14,1.7)),Vector((-1.5,-7,1.7))]:
        for x in [-4.30,-3,-1.5,0,1.30]:
            for z in [.025,.10,1.7,4.0,7.48,7.56]:
                target=Vector((x,-5.98,z));direction=(target-eye).normalized()
                assert any(tree.ray_cast(eye,direction,30)[0] is not None for tree in trees),f'Closed vestibule leak toward {tuple(target)} from {tuple(eye)}'
                sealed_rays+=1
scene.frame_set(310);scene.view_layers[0].update()
for leaf,suffix in zip(leaves,['','.001']):
    low,high=bounds(leaf);pocket_low,pocket_high=bounds(scene.objects['Portal • concealed sliding pocket'+suffix])
    assert all(pocket_low[i]<=low[i] and high[i]<=pocket_high[i] for i in [0,2])
    assert pocket_low[1]<low[1], 'Sliding pocket must be in front of its leaf.'
assert bounds(leaves[0])[1][0]<opening[0][0] and bounds(leaves[1])[0][0]>opening[1][0]
concealed_rays=0
if sealed_rays:
    casings=[o for o in scene.objects if o.type=='MESH' and not o.hide_render and
             (o.name.startswith('Portal • concealed sliding pocket') or o.name.startswith('Portal • pocket '))]
    trees=[BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],
                               [tuple(p.vertices) for p in o.data.polygons]) for o in casings]
    for leaf in leaves:
        low,high=bounds(leaf)
        for eye in [Vector((-1.5,-7,1.7)),Vector((9,-14,1.7)),Vector((-10,-14,1.7)),Vector((-1.5,-4.4,1.7))]:
            for x in [low[0]+.03,(low[0]+high[0])/2,high[0]-.03]:
                for z in [.10,3.8,7.55]:
                    target=Vector((x,low[1],z));direction=(target-eye).normalized();distance=(target-eye).length
                    hits=[tree.ray_cast(eye,direction,distance+.01)[3] for tree in trees]
                    assert any(hit is not None and hit<distance for hit in hits),f'Open leaf exposed at {tuple(target)} from {tuple(eye)}'
                    concealed_rays+=1
assert config['cityHideFrame']==config['cityEnd']
atrium_sightlines=0
if sealed_rays:
    # The front cylinder wraps around the lobby sides as well as its doorway.
    # Head-clearance checks miss these more distant, view-blocking triangles.
    deps=bpy.context.evaluated_depsgraph_get()
    skins=[o for o in scene.objects if o.get('tower_portal_clearance') or o.get('tower_atrium_clearance')]
    for obj in skins:
        tree=BVHTree.FromObject(obj,deps)
        inverse=obj.matrix_world.inverted()
        for eye in [Vector((-1.5,-5,1.7)),Vector((-1.5,-3,1.7))]:
            for target in [Vector((x,y,z)) for x in [-10.8,7.8] for y in [6,12] for z in [2.5,6.2]]:
                start=inverse@eye;end=inverse@target;direction=end-start
                assert tree.ray_cast(start,direction.normalized(),direction.length)[0] is None,f'Tower skin blocks atrium sightline: {obj.name} toward {tuple(target)}'
                atrium_sightlines+=1
samples=json.loads((ROOT/'assets/kaze-lobby/navigation-camera.json').read_text())['samples']
positions=[];rotations=[];close=[]
for frame in range(1,config['frameEnd']+1):
    scene.frame_set(frame);scene.view_layers[0].update();camera=scene.camera
    positions.append(camera.matrix_world.translation.copy());rotations.append(camera.matrix_world.to_quaternion())
    if frame in [383,400,420,443,500,893,1073,1403]:
        for direction in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:
            hit,p,n,index,obj,matrix=scene.ray_cast(bpy.context.evaluated_depsgraph_get(),positions[-1],Vector(direction),distance=.08)
            if hit and obj.type=='MESH' and not obj.hide_render and not any(mod.type=='NODES' for mod in obj.modifiers):close.append({'frame':frame,'object':obj.name})
city_end=config['cityEnd'];bridge_end=city_end+config['transitionFrames'];native=samples[config['transitionFrames']-1]
expected=Vector(native['position'])+Vector(config['lobbyOffset'])
position_error=(positions[bridge_end-1]-expected).length
rotation_error=rotations[bridge_end-1].rotation_difference(Quaternion(native['quaternion_wxyz'])).angle
rotation_error=min(rotation_error,abs(2*math.pi-rotation_error))
assert position_error<.0001 and rotation_error<.001
assert not close,f'Camera obstruction: {close}'
max_bridge_step=max((positions[i]-positions[i-1]).length for i in range(city_end,bridge_end))
max_bridge_turn=max(min(rotations[i].rotation_difference(rotations[i-1]).angle,abs(2*math.pi-rotations[i].rotation_difference(rotations[i-1]).angle)) for i in range(city_end,bridge_end))
report={'frames':config['frameEnd'],'handoff_position_error_m':position_error,'handoff_rotation_error_rad':rotation_error,'max_transition_step_m':max_bridge_step,'max_transition_turn_degrees':math.degrees(max_bridge_turn),'sampled_head_obstructions':close,'door_height_m':config['portal']['height'],'lobby_threshold_world':list(Vector((0,-12,0))+Vector(config['lobbyOffset'])),'closed_entrance_seam_overlap_m':seam_overlap,'closed_vestibule_sealing_rays':sealed_rays,'open_leaves_concealed':True,'cleared_city_sources':len(json.loads(scene['journey_clearance']))}
report['open_leaf_casing_occlusion_rays']=concealed_rays
report['clear_atrium_skin_sightlines']=atrium_sightlines
(ROOT/'assets/journey/handoff-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
