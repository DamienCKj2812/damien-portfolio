"""Focused production-master texture update; no tower/sky/NPC rebuilding."""
import hashlib
import json
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parent
MASTER = ROOT / 'monochrome-city-solid-tower.blend'
scene = bpy.context.scene
assert scene.name == 'MONO / Wire & Particle City'
assert Path(bpy.data.filepath).resolve() == MASTER
art = json.loads((ROOT / 'reference-tower-artwork.json').read_text())
assert art['source'] == 'banner-artwork/long-banner-source.png'
assert hashlib.sha256((ROOT / art['source']).read_bytes()).hexdigest() == art['sourceSha256']
targets = {obj['tower_display_key']: obj for obj in scene.objects
           if obj.get('tower_reference_display') and obj.get('tower_display_key') in ('logo', 'portrait')}
assert set(targets) == {'logo', 'portrait'}


def poses():
    snapshot = {}
    for frame in (1, 90, 245, 383, 450):
        scene.frame_set(frame)
        scene.view_layers[0].update()
        snapshot[frame] = {obj.name: (tuple(value for row in obj.matrix_world for value in row),
                                     obj.hide_render, obj.hide_get(),
                                     obj.animation_data.action if obj.animation_data else None)
                           for obj in scene.objects}
    return snapshot


before = poses()
camera = scene.camera
geometry = {key: ([tuple(vertex.co) for vertex in obj.data.vertices],
                  [tuple(loop.uv) for loop in obj.data.uv_layers.active.data])
            for key, obj in targets.items()}
for key, obj in targets.items():
    filename = f'reference-{key}.jpg'
    texture_path = ROOT / 'textures-monochrome' / filename
    assert hashlib.sha256(texture_path.read_bytes()).hexdigest() == art['outputs'][filename]['sha256']
    image = bpy.data.images.load(str(texture_path), check_existing=False)
    image.name = f'Reference tower • SANCTUM long banner / {key}'
    image.colorspace_settings.name = 'sRGB'
    image.pack()
    material = obj.active_material.copy()
    material.name = f'Reference tower • SANCTUM long banner / {key} screen'
    node = next(node for node in material.node_tree.nodes if node.type == 'TEX_IMAGE')
    node.image = image
    obj.material_slots[0].link = 'OBJECT'
    obj.material_slots[0].material = material
    obj['city_texture'] = filename
    obj['banner_artwork_source'] = art['source']
    obj['banner_artwork_sha256'] = art['outputs'][filename]['sha256']
assert before == poses(), 'Existing city poses, visibility or animation actions changed'
for key, obj in targets.items():
    assert geometry[key] == ([tuple(vertex.co) for vertex in obj.data.vertices],
                              [tuple(loop.uv) for loop in obj.data.uv_layers.active.data])
assert scene.camera == camera
scene.frame_set(1)
scene.view_layers[0].update()
bpy.context.preferences.filepaths.save_version = 1
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER))
print(json.dumps({'checks': 'passed', 'updatedPanels': list(targets),
                  'source': art['source'], 'geometryUvCameraActorPosesPreserved': True}))
