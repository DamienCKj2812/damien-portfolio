"""Validate the reference sky's native/exported geometry and motion boundary."""
import json
import sys
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from bright_star_layout import BRIGHT_STARS
scene = bpy.context.scene
collection = bpy.data.collections['City • Reference orbital sky']
meta = json.loads(scene['orbital_sky_reference'])
assert meta['planets'] == 2 and meta['labels'] == 3
assert meta['line_segments'] == 894 and meta['sky_points'] == 2445 + len(BRIGHT_STARS) - 1
assert meta['brightStars'] == len(BRIGHT_STARS)
annotations = {'orbital grid annotation', 'earth distance annotation',
               'synchronization annotation', 'annotation ticks and distance bracket'}
if meta.get('showAnnotations') is False:
    assert meta['visibleLabels'] == 0
    assert all(o.hide_render for o in collection.objects if o.get('city_sky_element') in annotations)
assert all(not o.hide_render for o in collection.objects if o.get('city_sky_element') not in annotations)
assert not any('construction grid' in obj.name or 'crosshair' in obj.name or 'fine cross' in obj.name for obj in collection.objects)
assert all(obj.type == 'MESH' and not obj.animation_data and not obj.parent for obj in collection.objects)
assert all(obj.get('integration_zone', 'city') == 'city' for obj in collection.objects)
planets = [obj for obj in collection.objects if 'crescent' in obj.get('city_sky_element', '')]
assert len(planets) == 2
for planet in planets:
    assert planet.get('city_render_kind') == 'solid'
    assert len(planet.data.polygons) > 9000
    assert any(poly.material_index == 0 for poly in planet.data.polygons)
    assert any(poly.material_index > 32 for poly in planet.data.polygons)
points = [obj for obj in collection.objects if obj.get('city_sky_points')]
assert sum(len(obj.data.vertices) for obj in points) == meta['sky_points']
assert all('radius' in obj.data.attributes for obj in points)
orbit = next(obj for obj in collection.objects if obj.get('city_sky_element') == 'diagonal orbital trajectory')
tracking = next(obj for obj in collection.objects if obj.get('city_sky_element') == 'orbital tracking stars')
assert len(tracking.data.vertices) == 3
for star in tracking.data.vertices:
    assert min((star.co-point.co).length for point in orbit.data.vertices) < .001, 'Tracking star must lie on the orbit'
inverse = scene.camera.matrix_world.inverted()
projected = [inverse @ vertex.co for vertex in orbit.data.vertices]
turns = []
for i in [100, 300]:
    a, b, c = [projected[j] for j in [i-20, i, i+20]]
    turns.append((b.x-a.x)*(c.y-b.y)-(b.y-a.y)*(c.x-b.x))
assert turns[0]*turns[1] < 0, 'Orbit must bend in opposite directions'

base = ROOT.parent.parent/'public/models/city'
manifest = json.loads((base/'scene.json').read_text())
assert manifest['orbitalSky'] == meta
assert manifest['frameEnd'] == 450, 'Preserve the full authored city route'
sky = [group for group in manifest['groups'] if group.get('role') in ['sky', 'sky-shine']]
assert sky and all(group['kind'] == 'points' and group['actor'] == 0 for group in sky)
assert sum(group['vertexCount'] for group in sky) >= meta['sky_points']
shine = [group for group in sky if group.get('role') == 'sky-shine']
assert sum(group['vertexCount'] for group in shine) == len(BRIGHT_STARS)
native_shine = [obj for obj in points if obj.get('city_sky_shine')]
assert len(native_shine) == len(BRIGHT_STARS)
assert sorted(obj['city_shine_radius'] for obj in native_shine) == sorted(star[2] for star in BRIGHT_STARS)
assert (base/'animation.bin').stat().st_size == manifest['frameEnd']*manifest['channelCount']*manifest['channelStride']*4
print({'reference_sky': True, 'world_fixed': True, 'crescent_planets': len(planets),
       'orbital_points': meta['sky_points'], 'connected_export': True})
