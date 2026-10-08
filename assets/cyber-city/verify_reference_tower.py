"""Read-only checks of reference geometry, packed art and full-route clearance."""
import hashlib
import json
import math
import sys
from pathlib import Path
import bpy
from mathutils.bvhtree import BVHTree
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from reference_tower_spec import CENTER
scene = bpy.context.scene
assert scene.name == 'MONO / Wire & Particle City'
assert scene.get('reference_tower_redesign')
art = json.loads((ROOT / 'reference-tower-artwork.json').read_text())
layout = json.loads(scene['reference_tower_redesign'])
assert layout.get('longBannerGlitchBorderRemoved'), 'Long-banner glitch border removal must survive rebuilds'
for obj in scene.objects:
    if obj.type == 'MESH' and not obj.hide_render and obj.name.startswith('Reference tower • Scattered glitch block'):
        center = sum((obj.matrix_world @ vertex.co for vertex in obj.data.vertices), Vector()) / len(obj.data.vertices)
        angle = math.degrees(math.atan2(center.x - CENTER[0], CENTER[1] - center.y))
        assert not 2.49 <= angle <= 8.51, f'Visible glitch block on the long-banner edge: {obj.name}'
assert hashlib.sha256((ROOT / art['source']).read_bytes()).hexdigest() == art['sourceSha256']
screens = [o for o in scene.objects if o.get('tower_reference_display') and not o.hide_render]
assert len(screens) == 5
for obj in screens:
    filename = obj['city_texture']
    assert filename in art['outputs']
    assert hashlib.sha256((ROOT / 'textures-monochrome' / filename).read_bytes()).hexdigest() == art['outputs'][filename]['sha256']
    assert obj.data.uv_layers.active
    image = next(n.image for n in obj.active_material.node_tree.nodes if n.type == 'TEX_IMAGE')
    assert image.packed_file and list(image.size) == art['outputs'][filename]['size']
    assert hashlib.sha256(bytes(image.packed_file.data)).hexdigest() == art['outputs'][filename]['sha256'], f'Stale packed artwork: {filename}'
    if obj['tower_display_key'] in ('logo', 'portrait') and art.get('longBanner'):
        assert obj.get('banner_artwork_source') == art['source']
        assert obj.get('banner_artwork_sha256') == art['outputs'][filename]['sha256']
    spec = layout['screens'][obj['tower_display_key']]
    assert abs(image.size[0] / image.size[1] - spec['aspect']) < 1 / image.size[1]
    assert all(math.isfinite(v) for loop in obj.data.uv_layers.active.data for v in loop.uv)
assert scene.objects['Hero display • Curved LED • arasaka'].hide_render
assert scene.objects['Hero display • Clean mobility campaign • LED display'].hide_render
assert not any(not o.hide_render and 'THE NIGHT LIVES ON' in o.name for o in scene.objects)
collection = bpy.data.collections['Reference tower • Architectural redesign']
assert all(not o.animation_data for o in collection.objects)
assert 'Reference tower • Orbital globe shaded spherical surface' in scene.objects
assert not any(o.name.startswith(('Reference tower • Right spine fine glazing seams',
                                 'Reference tower • Right spine muted glazing')) for o in collection.objects)
surface = scene.objects['Reference tower • Orbital globe shaded spherical surface']
assert len(surface.data.polygons) > 16000 and surface.data.uv_layers.active
assert surface.get('reference_earth_detail') and surface.get('city_texture') == 'reference-earth.jpg'
earth_report = json.loads((ROOT / 'earth-detail.json').read_text())
assert hashlib.sha256((ROOT / earth_report['source']).read_bytes()).hexdigest() == earth_report['sourceSha256']
assert hashlib.sha256((ROOT / earth_report['output']).read_bytes()).hexdigest() == earth_report['outputSha256']
earth_image = next(n.image for n in surface.active_material.node_tree.nodes if n.type == 'TEX_IMAGE')
assert earth_image.packed_file and list(earth_image.size) == earth_report['size']
assert 'Reference tower • L1 lower balcony rounded slab' in scene.objects
assert 'Reference tower • L2 upper balcony rounded slab' in scene.objects
assert 'Reference tower • L1 downward crescent fin' in scene.objects
assert sum(o.name.startswith('Reference tower • Paired antenna dark mast') for o in collection.objects) == 4
assert all(not o.hide_render for o in scene.objects if o.name.startswith('City NPC'))
walkers = [o for o in scene.objects if o.get('city_role') == 'walking_npc']
assert len(walkers) == 10 and all(o.animation_data and o.animation_data.action for o in walkers)
crowd = scene.objects['Mono • 07 Street life • particles 3']
assert not crowd.hide_render and len(json.loads(crowd['person_metadata'])) == 8
scene.frame_set(1)
scene.view_layers[0].update()
integrated = bool(scene.get('journey_config'))
route_camera = scene.objects.get(scene.get('journey_city_camera', '')) or scene.camera
deps = bpy.context.evaluated_depsgraph_get()
surfaces = []
for obj in [*collection.objects, *screens]:
    if obj.type != 'MESH' or not obj.data.polygons:
        continue
    if not integrated and (obj.get('tower_portal_clearance') or obj.get('tower_atrium_clearance')):
        continue  # The working doorway is carved only in the generated copy.
    evaluated = obj.evaluated_get(deps)
    data = evaluated.to_mesh()
    vertices = [obj.matrix_world @ v.co for v in data.vertices]
    assert all(math.isfinite(v) for point in vertices for v in point)
    polygons = [tuple(p.vertices) for p in data.polygons]
    surfaces.append((obj.name, BVHTree.FromPolygons(vertices, polygons)))
    evaluated.to_mesh_clear()
minimum = (float('inf'), None, None)
for frame in range(1, 451):
    scene.frame_set(frame)
    scene.view_layers[0].update()
    eye = route_camera.matrix_world.translation
    for name, tree in surfaces:
        _, _, _, distance = tree.find_nearest(eye)
        if distance is not None and distance < minimum[0]:
            minimum = (distance, frame, name)
        assert distance is None or distance > .22, f'Camera intersects {name} at frame {frame}: {distance}'
scene.frame_set(1)
print(json.dumps({'checks': 'passed', 'packedDisplays': len(screens), 'routeFramesChecked': 450,
                  'minimumNewGeometryCameraClearanceMeters': minimum[0],
                  'closestFrame': minimum[1], 'closestObject': minimum[2],
                  'nativeStaticDetailObjects': len(collection.objects)}))
