"""Read-only comparison of native lobby NPC poses/morphs to the browser export."""
import json
from array import array
from pathlib import Path
import bpy
from mathutils import Quaternion, Vector

ROOT = Path(__file__).resolve().parents[2]
package = ROOT/'public/models/lobby'
manifest = json.loads((package/'scene.json').read_text())
motion = array('f'); motion.frombytes((package/'animation.bin').read_bytes())
geometry = array('f'); geometry.frombytes((package/'geometry.bin').read_bytes())
scene = bpy.data.scenes['KAZE / Monochrome Atrium']
max_error = 0
for frame in [1,150,400,700,1020,2500]:
    scene.frame_set(frame); scene.view_layers[0].update()
    sampled = (frame-1)%manifest['npcLoopFrames']
    for actor in manifest['actors']:
        if not actor.get('autonomous'): continue
        obj = scene.objects[actor['name']]
        offset = (sampled*manifest['channelCount']+actor['index'])*manifest['channelStride']
        p = Vector(motion[offset:offset+3]); q = Quaternion((motion[offset+6],*motion[offset+3:offset+6]))
        scale = Vector(motion[offset+7:offset+10])
        assert (obj.matrix_world.translation-p).length < .0001
        assert abs(abs(obj.matrix_world.to_quaternion().dot(q))-1) < .00001
        keys = list(obj.data.shape_keys.key_blocks)
        weights = motion[offset+12:offset+12+len(keys)-1]
        assert all(abs(weight-key.value)<.00001 for weight,key in zip(weights,keys[1:]))
        group = next(g for g in manifest['groups'] if g['actor']==actor['index'] and g['kind']=='points')
        for vertex in range(0,len(keys[0].data),max(1,len(keys[0].data)//24)):
            expected = keys[0].data[vertex].co.copy()
            for key in keys[1:]: expected += (key.data[vertex].co-keys[0].data[vertex].co)*key.value
            expected = obj.matrix_world@expected
            start = group['byteOffset']//4+vertex*5
            baked = Vector(geometry[start:start+3])
            for morph,weight in zip(group['morphs'],weights):
                start=morph['byteOffset']//4+vertex*3; baked+=Vector(geometry[start:start+3])*weight
            baked = q@Vector((baked.x*scale.x,baked.y*scale.y,baked.z*scale.z))+p
            max_error = max(max_error,(expected-baked).length)
            assert (expected-baked).length < .0002
print(json.dumps({'checks':'passed','npc_count':18,'max_point_position_error_m':max_error,'source_modified':False}))
