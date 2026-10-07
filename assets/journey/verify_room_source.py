"""Compare browser transforms, morphs, and routes to authored rooms, read-only."""
import argparse
import json
import sys
from array import array
from pathlib import Path
import bpy
from mathutils import Quaternion, Vector

ROOT = Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser();parser.add_argument('--level',choices=['projects','skills','experience'],default='projects')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
level=args.level;config=json.loads((ROOT/'assets/journey/room-destinations.json').read_text())[level]
assert bpy.context.scene.objects.get(config['mainCamera'])
scene = bpy.context.scene
package=ROOT/'public'/config['assetBase']
manifest = json.loads((package/'scene.json').read_text())
motion = array('f');motion.frombytes((package/'animation.bin').read_bytes())
geometry = array('f');geometry.frombytes((package/'geometry.bin').read_bytes())
max_error = 0
frames=sorted({1,46,151,296,510,701,manifest['frameEnd'],manifest['frameEnd']+1,2700})
for frame in frames:
    source_frame=frame if manifest['loop'] else min(frame,manifest['frameEnd'])
    scene.frame_set(source_frame);scene.view_layers[0].update()
    for actor in manifest['actors']:
        rig = scene.objects[actor['name']]
        sampled=(frame-1)%manifest['frameEnd'] if manifest['loop'] else min(frame-1,manifest['frameEnd']-1)
        offset = (sampled*manifest['channelCount']+actor['index'])*manifest['channelStride']
        p = Vector(motion[offset:offset+3]);q = Quaternion((motion[offset+6],*motion[offset+3:offset+6]))
        assert (rig.matrix_world.translation-p).length < .0001, f'{rig.name} at frame {frame}: source {list(rig.matrix_world.translation)}, baked {list(p)}'
        assert abs(abs(rig.matrix_world.to_quaternion().dot(q))-1) < .00001
        scale=Vector(motion[offset+7:offset+10])
        assert (rig.matrix_world.to_scale()-scale).length < .0001
        if level!='projects':
            if rig.type=='MESH' and not rig.data.polygons:
                group=next(g for g in manifest['groups'] if g['actor']==actor['index'] and g['kind']=='points')
                for vertex in range(0,len(rig.data.vertices),max(1,len(rig.data.vertices)//20)):
                    expected=rig.matrix_world@rig.data.vertices[vertex].co
                    start=group['byteOffset']//4+vertex*5;baked=Vector(geometry[start:start+3])
                    baked=q@Vector((baked.x*scale.x,baked.y*scale.y,baked.z*scale.z))+p
                    max_error=max(max_error,(expected-baked).length)
                    assert (expected-baked).length < .0002
            continue
        npc = next(obj for obj in rig.children if obj.type=='MESH' and obj.data.shape_keys)
        keys = list(npc.data.shape_keys.key_blocks)
        weights = motion[offset+12:offset+12+len(keys)-1]
        assert all(abs(weight-key.value)<.00001 for weight,key in zip(weights,keys[1:]))
        group = next(g for g in manifest['groups'] if g['actor']==actor['index'] and g['kind']=='points')
        for vertex in range(0,len(keys[0].data),max(1,len(keys[0].data)//20)):
            expected = keys[0].data[vertex].co.copy()
            for key in keys[1:]: expected += (key.data[vertex].co-keys[0].data[vertex].co)*key.value
            expected = npc.matrix_world@expected
            start = group['byteOffset']//4+vertex*5
            baked = Vector(geometry[start:start+3])
            for morph,weight in zip(group['morphs'],weights):
                start=morph['byteOffset']//4+vertex*3;baked+=Vector(geometry[start:start+3])*weight
            baked = q@baked+p
            max_error = max(max_error,(expected-baked).length)
            assert (expected-baked).length < .0002
route_error=0
if manifest['navigation'].get('route'):
    descriptor=manifest['navigation']['route'];route=array('f');route.frombytes((package/descriptor['file']).read_bytes())
    camera=scene.objects[config['mainCamera']]
    assert not camera.animation_data and not camera.constraints
    route_frames=sorted({1,descriptor['frameEnd'],*[item['start'] for item in manifest['exhibits']],*range(1,descriptor['frameEnd']+1,53)})
    for frame in route_frames:
        scene.frame_set(frame);scene.view_layers[0].update()
        offset=(frame-1)*3;error=(camera.matrix_world.translation-Vector(route[offset:offset+3])).length
        route_error=max(route_error,error);assert error<.0001
report = {'level':level,'actors':len(manifest['actors']),'sampled_frames':frames,'max_point_position_error_m':max_error,'max_route_position_error_m':route_error,'source_modified':False}
name='room-motion-verification.json' if level=='projects' else f'room-{level}-verification.json'
(ROOT/'assets/journey'/name).write_text(json.dumps(report,indent=2))
print(json.dumps(report))
