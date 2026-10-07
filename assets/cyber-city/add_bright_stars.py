"""Add optical-star companions without rebuilding any existing sky geometry."""
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from bright_star_layout import BRIGHT_STARS

scene = bpy.context.scene
assert scene.name == 'MONO / Wire & Particle City'
frame = scene.frame_current
scene.frame_set(1)
bpy.context.view_layer.update()
collection = bpy.data.collections['City • Reference orbital sky']
original = collection.objects['Orbital sky • bright star optical shine']
assert original.get('city_sky_shine') and len(original.data.vertices) == 1
meta = json.loads(scene['orbital_sky_reference'])
height = meta['distance_m'] * scene.camera.data.sensor_width / scene.camera.data.lens / (scene.render.resolution_x / scene.render.resolution_y)
width = height * meta['reference_aspect']
basis = scene.camera.matrix_world.to_3x3()
anchor = original.data.vertices[0].co.copy()
prefix = 'bright star optical shine '
for obj in list(collection.objects):
    if obj.get('city_sky_element', '').startswith(prefix):
        meta['sky_points'] -= len(obj.data.vertices)
        bpy.data.objects.remove(obj, do_unlink=True)
for index, (x, y, flare_radius) in enumerate(BRIGHT_STARS[1:], 2):
    obj = original.copy()
    obj.data = original.data.copy()
    obj.name = 'Orbital sky • ' + prefix + f'{index:02d}'
    obj.data.name = obj.name
    obj['city_sky_element'] = prefix + f'{index:02d}'
    obj['city_shine_radius'] = flare_radius
    obj.data.vertices[0].co = anchor + basis @ Vector(((x-.730)*width, (.313-y)*height, 0))
    obj.data.attributes['radius'].data[0].value = .12 * flare_radius / 9
    collection.objects.link(obj)
    meta['sky_points'] += 1
meta['brightStars'] = len(BRIGHT_STARS)
scene['orbital_sky_reference'] = json.dumps(meta)
scene.frame_set(frame)
bpy.context.preferences.filepaths.save_version = 1
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'monochrome-city-solid-tower.blend'))
(ROOT/'orbital-sky.json').write_text(scene['orbital_sky_reference'])
print({'brightStars': len(BRIGHT_STARS), 'addedCompanions': len(BRIGHT_STARS)-1, 'originalStarPreserved': True})
