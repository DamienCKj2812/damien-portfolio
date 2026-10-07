"""Validate the standalone, monochrome, NPC-free observatory deliverable."""
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

OUT = Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(OUT / 'timeline-observatory.blend'))
scene = bpy.context.scene
content = json.loads((OUT / 'milestones.json').read_text())
cards = [o for o in scene.objects if 'milestone_id' in o]
assert len(bpy.data.scenes) == 1
assert scene['npc_count'] == 0
assert not any(o.type == 'ARMATURE' or 'npc' in o.name.lower() or 'person_metadata' in o for o in scene.objects)
assert len(cards) == len(content['milestones']) == 6
assert {o['milestone_id'] for o in cards} == {m['id'] for m in content['milestones']}
assert len([o for o in scene.objects if o.get('timeline_node')]) == 6
assert not any(o.get('cosmic_banner') or 'cosmic wall banner' in o.name.lower() for o in scene.objects)
windows = [o for o in scene.objects if o.get('observatory_window')]
assert len(windows) == 4 and all(o.type == 'MESH' for o in windows)
assert len([o for o in scene.objects if o.get('roof_window')]) == 1
assert len([o for o in scene.objects if o.get('exterior_starfield')]) == 1
starfield = next(o for o in scene.objects if o.get('exterior_starfield'))
assert min(v.co.length for v in starfield.data.vertices) > 70, 'Stars are not outside the observatory'
wall = scene.objects['Observatory / curved wall with actual observation openings']
assert wall['wall_thickness_m'] == .16
assert any(m.type == 'SOLIDIFY' and abs(m.thickness - .16) < 1e-6 for m in wall.modifiers)
assert not any('fine wall grid' in o.name or 'curved wall latitude' in o.name for o in scene.objects)
for pane in windows:
    a = math.radians(pane['angle_degrees'])
    direction = Vector((math.sin(a), math.cos(a), 0))
    assert not wall.ray_cast(Vector((0, 0, 4.15)), direction)[0], 'Window is backed by a solid wall'
    assert wall.ray_cast(Vector((0, 0, .25)), direction)[0], 'Missing solid window sill'
    assert wall.ray_cast(Vector((0, 0, 8.0)), direction)[0], 'Missing solid window header'
    nodes = pane.data.materials[0].node_tree.nodes
    assert any(n.type == 'BSDF_TRANSPARENT' for n in nodes), 'Window glazing is not clear'
planets = [o for o in scene.objects if o.get('external_planet')]
assert len(planets) == 5
assert {o['planet_variant'] for o in planets} == {'ringed', 'geodesic', 'banded', 'cratered'}
for planet in planets:
    body = next(o for o in planet.children if o.get('planet_body'))
    assert len(body.data.polygons) > 100, 'Planet is not a three-dimensional sphere'
    assert all(max(v.co[axis] for v in body.data.vertices) - min(v.co[axis] for v in body.data.vertices)
               > planet['planet_radius_m'] * 1.8 for axis in range(3))
    if planet['exterior_zone'] == 'roof':
        assert planet.location.z - planet['planet_radius_m'] > 8.3
    else:
        extent = planet['planet_radius_m'] * (1.7 if planet['planet_variant'] == 'ringed' else 1.05)
        assert planet.location.xy.length - extent > 12.5, 'Exterior planet intersects chamber'
pillars = [o for o in scene.objects if o.get('architectural_wall_rib')]
wall_lights = [o for o in scene.objects if o.get('architectural_wall_light')]
assert len(pillars) == 8 and len(wall_lights) == 16
assert all(o.type == 'MESH' and len(o.data.polygons) == 1 for o in pillars)
assert all(o.type == 'CURVE' for o in wall_lights)
assert not any(o.get('dotted_pillar') or 'gridded annular roof' in o.name for o in scene.objects)
assert 'Observatory / smooth curved ceiling fascia' in scene.objects
base_emission = next(n for n in bpy.data.materials['Observatory / brighter lower wall lights'].node_tree.nodes if n.type == 'EMISSION')
assert abs(base_emission.inputs['Strength'].default_value - 2.4) < 1e-6
assert len([o for o in scene.objects if o.get('future_node')]) == 16
assert not any(o.library for o in scene.objects)
assert all(image.packed_file for image in bpy.data.images if image.source == 'FILE'), 'Logo images must be packed, not external dependencies'
slabs = [o for o in scene.objects if o.get('floor_layer') == 'slab']
inlays = [o for o in scene.objects if o.get('floor_layer') == 'inlay']
assert 35 <= len(slabs) <= 70, 'Floor should use large architectural slabs'
for slab in slabs:
    assert abs(max(v.co.z for v in slab.data.vertices)) < 1e-6, 'Walking surface must stay level'
    assert abs(min(v.co.z for v in slab.data.vertices) + .07) < 1e-6
    assert slab['joint_width_m'] == .008
    assert all(v.co.xy.length <= 12.501 for v in slab.data.vertices), 'Slab extends beyond circular wall'
assert not any(o.get('hud_partial_arc') for o in inlays)
dot_panels = [o for o in inlays if o.get('dotted_floor_panel')]
assert len(dot_panels) == 24
assert any(max(v.co.y for v in o.data.vertices) > 11 for o in dot_panels), 'Rear floor lacks dots'
assert sum(any(abs(v.co.y) < 3 for v in o.data.vertices) for o in dot_panels) >= 6, 'Central aisles lack dots'
assert all(len(o.data.vertices) == 169 for o in dot_panels)
assert all(abs(v.value - .003) < 1e-6 for o in dot_panels for v in o.data.attributes['radius'].data)
assert len([o for o in scene.objects if o.get('floor_layer') == 'seam']) == 14
for slab in slabs:
    if all(v.co.xy.length < 12.49 for v in slab.data.vertices):
        assert abs(slab.dimensions.x - 2.992) < .001 and abs(slab.dimensions.y - 2.992) < .001
assert not any('concentric floor orbit' in o.name or 'fine floor and wall grid' in o.name for o in scene.objects)
for obj in inlays:
    if obj.type == 'CURVE':
        assert obj.data.bevel_depth <= .001201, 'Floor inlays have become thick physical bars'
        assert all(abs(p.co.z - .0012) < 1e-6 for s in obj.data.splines for p in s.points)
glass = bpy.data.materials['Floor / polished smoked black glass'].node_tree.nodes.get('Principled BSDF')
assert glass.inputs['Roughness'].default_value < .11
assert glass.inputs['Coat Weight'].default_value > .6
for mat in bpy.data.materials:
    for node in mat.node_tree.nodes:
        if node.type in {'EMISSION', 'BSDF_PRINCIPLED'}:
            color = node.inputs['Color' if node.type == 'EMISSION' else 'Base Color'].default_value
            assert max(color[:3]) - min(color[:3]) < 1e-6, 'Non-monochrome material'
for card in cards:
    assert abs(card.location.xy.length - 8) < .001
    metadata = json.loads(card['milestone_metadata'])
    assert len([o for o in card.children if o.type == 'FONT']) == (3 if metadata.get('cardSpecialism') else 2)
globe = next(o for o in scene.objects if o.get('observatory_globe'))
scene.frame_set(1)
start = globe.matrix_world.copy()
scene.frame_set(301)
assert abs(globe.rotation_euler.z) > 1
scene.frame_set(1201)
assert max(abs(start[i][j] - globe.matrix_world[i][j]) for i in range(4) for j in range(4)) < .001
scene.frame_set(1)
planet_start = {p.name: p.matrix_world.copy() for p in planets}
scene.frame_set(2401)
assert all(max(abs(planet_start[p.name][i][j] - p.matrix_world[i][j]) for i in range(4) for j in range(4)) < .001
           for p in planets), 'Planet rotation loops are not seamless'
scene.frame_set(1)
report = {
    'scene': scene.name, 'npcCount': 0, 'milestones': len(cards), 'cosmicBanners': 0,
    'observationWindows': len(windows), 'roofWindows': 1, 'exteriorPlanets': len(planets),
    'planetVariants': sorted({p['planet_variant'] for p in planets}), 'architecturalWallRibs': len(pillars),
    'recessedWallLights': len(wall_lights),
    'diameterMeters': 25, 'oculusRadiusMeters': 6.6, 'globeLoopFrames': 1200,
    'objects': len(scene.objects), 'floorSlabs': len(slabs), 'floorInlays': len(inlays),
    'floorJointWidthMeters': .008, 'floorHUDSystems': 0, 'dottedFloorPanels': len(dot_panels),
    'authoredMeshVertices': sum(len(o.data.vertices) for o in scene.objects if o.type == 'MESH'),
    'authoredMeshPolygons': sum(len(o.data.polygons) for o in scene.objects if o.type == 'MESH'),
    'instancedPoints': sum(len(o.data.vertices) for o in scene.objects if o.get('render_kind') == 'points'),
    'curveSegments': sum(len(o.data.splines) for o in scene.objects if o.type == 'CURVE'),
    'modelBytes': (OUT / 'timeline-observatory.blend').stat().st_size,
    'externalDependencies': 0, 'validation': 'passed',
}
(OUT / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
