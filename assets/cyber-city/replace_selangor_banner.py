"""Focused master-saving replacement of NEW HORIZONS with the Selangor artwork."""
import hashlib
import json
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parent
MASTER = ROOT/'monochrome-city-solid-tower.blend'
NAME = 'Hero display • Curved LED • landscape'
scene = bpy.context.scene
assert scene.name=='MONO / Wire & Particle City'
assert Path(bpy.data.filepath).resolve()==MASTER
obj = scene.objects[NAME]
assert obj.get('city_render_kind')=='screen'
path = ROOT/'textures-monochrome/selangor.jpg'
assert path.is_file()


def poses():
    snapshot = {}
    for frame in [1,90,245,383,450]:
        scene.frame_set(frame);scene.view_layers[0].update()
        snapshot[frame] = {o.name:tuple(v for row in o.matrix_world for v in row) for o in scene.objects}
    return snapshot


before = poses()
vertices = [tuple(v.co) for v in obj.data.vertices]
uvs = [tuple(loop.uv) for loop in obj.data.uv_layers.active.data]
texture = bpy.data.images.load(str(path),check_existing=False)
texture.name = 'City • Owner Selangor / curved banner'
texture.colorspace_settings.name = 'sRGB';texture.pack()
material = obj.material_slots[0].material.copy()
material.name = 'Hero display • Owner Selangor'
next(node for node in material.node_tree.nodes if node.type=='TEX_IMAGE').image = texture
obj.material_slots[0].link = 'OBJECT';obj.material_slots[0].material = material
obj['city_texture'] = 'selangor.jpg'
obj['banner_artwork_source'] = 'banner-artwork/selangor-source.png'
obj['banner_artwork_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
assert before==poses(), 'An existing scene/camera/actor transform changed'
assert vertices==[tuple(v.co) for v in obj.data.vertices]
assert uvs==[tuple(loop.uv) for loop in obj.data.uv_layers.active.data]
assert scene.objects['Hero display • KAZE • cyborg campaign • LED display'].get('city_texture')=='portrait.jpg'
assert not any(o.get('city_texture')=='night.png' for o in scene.objects)
scene.frame_set(1);scene.view_layers[0].update()
bpy.context.preferences.filepaths.save_version=1
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER))
print(json.dumps({'checks':'passed','updatedObject':NAME,'texture':'selangor.jpg',
                  'packedImageSize':list(texture.size),'geometryUvCameraActorPosesPreserved':True}))
