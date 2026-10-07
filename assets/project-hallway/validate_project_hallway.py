"""Check the standalone Blender deliverable and report authored geometry costs."""
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'assets/project-hallway'
bpy.ops.wm.open_mainfile(filepath=str(OUT / 'project-hallway.blend'))
scene = bpy.context.scene
projects = json.loads((OUT / 'projects.json').read_text())['projects']
layout = json.loads((OUT / 'hallway-layout.json').read_text())
panels = [o for o in scene.objects if 'project_id' in o]
npcs = [o for o in scene.objects if 'source_person_id' in o]
assert len(bpy.data.scenes) == 1, 'Unexpected appended reference scene'
assert len(panels) == len(projects) == 16
assert {o['project_id'] for o in panels} == {p['id'] for p in projects}
assert len(npcs) == 15
thinkers = [o for o in npcs if o.get('activity') == 'thinking']
assert len(thinkers) == 1 and 'Thinking / hand to chin' in thinkers[0].data.shape_keys.key_blocks
interactive = scene.objects['Project Hallway / free-look camera']
assert scene.camera == interactive and interactive.animation_data is None
assert 'hallway_controls.py' in bpy.data.texts
windows = [o for o in scene.objects if o.get('hallway_window')]
assert len(windows) == scene['window_count'] == 0
walls = [o for o in scene.objects if o.get('hallway_solid_wall')]
assert len(walls) == 2 and {math.copysign(1, o.location.x) for o in walls} == {-1, 1}
for wall in walls:
    assert wall.dimensions.z >= 6.2 - .001
    shader = wall.data.materials[0].node_tree.nodes.get('Principled BSDF')
    assert shader.inputs['Metallic'].default_value == 0
    assert shader.inputs['Roughness'].default_value >= .9
assert not any('clear glazing' in o.name or 'Window wall' in o.name for o in scene.objects)
displays = [o for o in scene.objects if o.get('hallway_display')]
projectors = [o for o in scene.objects if o.get('holographic_projector')]
assert len(displays) == len(projectors) == len(projects) + 1
assert not scene.objects.get('Entry / exhibition guide')
assert scene.objects.get('Entry / projects directory')
directory=scene.objects['Entry / projects directory']
assert directory.get('hallway_directory')
directory_face=next(obj for obj in directory.children if obj.get('hallway_directory_face'))
assert abs(directory_face.location.z-3.575)<.001
directory_unit=next(obj for obj in directory.children if obj.get('holographic_projector'))
assert directory_unit.location.z>5.8 and abs(directory_unit.rotation_euler.x-math.pi)<.001
directory_field=next(obj for obj in directory_unit.children if obj.type=='MESH' and 'subtle projected light field' in obj.name)
projected_corners=[directory_unit.matrix_basis @ vertex.co for vertex in list(directory_field.data.vertices)[1:]]
assert abs(min(point.z for point in projected_corners)-2.0)<.001
assert abs(max(point.z for point in projected_corners)-5.15)<.001
gates = [o for o in scene.objects if o.get('hallway_category_gate')]
assert {o['hallway_category_gate'] for o in gates} == {'academic', 'personal'}
assert [category['id'] for category in layout['categories']] == ['client','academic','personal']
assert 'door' not in layout['categories'][0]
for category in layout['categories'][1:]:
    assert category['door']['revealY'] < category['door']['y'] and category['door']['automatic']
    parts = [o for o in scene.objects if o.get('hallway_category_id') == category['id']]
    assert {'categoryFrame','categoryCurtain','categoryDoorLabel'} <= {o['hallway_category_role'] for o in parts}
    assert not any(o['hallway_category_role'] in {'categoryDoorLeft','categoryDoorRight'} for o in parts)
    veil = next(o for o in parts if 'holographic veil' in o.name)
    nodes = veil.data.materials[0].node_tree.nodes
    assert any(node.type == 'BSDF_TRANSPARENT' for node in nodes)
    assert next(node for node in nodes if node.type == 'MIX_SHADER').inputs[0].default_value < .05
    assert any(o.get('hallway_render_kind') == 'points' for o in parts), 'Portal dust missing'
    title=next(o for o in parts if o.type=='FONT' and o.name.startswith('Category / number'))
    expected_title='02 ACADEMIC ASSIGNMENT PROJECTS' if category['id']=='academic' else '03 PERSONAL PROJECTS'
    assert title.data.body==expected_title
    marker=next(o for o in parts if o.get('hallway_category_wall_number'))
    assert marker['hallway_category_wall_number']==str(category['number']).zfill(2)
    assert marker.type=='CURVE' and len(marker.data.splines)==7
spotlights = [o for o in scene.objects if o.get('gallery_spotlight')]
assert not spotlights
assert not any(o.type == 'LIGHT' and o.data.type == 'SPOT' for o in scene.objects)
assert not any('spotlight housing' in o.name or 'spotlight lens' in o.name for o in scene.objects)
assert scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value <= .0251
for display in displays:
    front = display.matrix_world.to_quaternion() @ Vector((0, -1, 0))
    angle = math.radians(45)
    expected = Vector((-display.location.x,-6.95-display.location.y,0)).normalized() if display.get('hallway_directory') else Vector((math.cos(angle) if display.location.x < 0 else -math.cos(angle), -math.sin(angle), 0))
    assert front.dot(expected) > .99999, 'Display must face inward and slightly toward the entrance'
    assert display['display_facing'] == ('entrance' if display.get('hallway_directory') else 'east-entrance' if display.location.x < 0 else 'west-entrance')
    unit = next(p for p in projectors if p.parent == display)
    assert len(unit.children) >= 10
    assert any('luminous lens' in o.name for o in unit.children)
pillars = [o for o in scene.objects if o.get('dotted_pillar')]
assert len(pillars) == scene.get('structural_pillar_pair_count', math.ceil((scene['hallway_length_m'] + 2) / 7.8)) * 2
assert all(o.dimensions.x > 1 and o.dimensions.y > 1 for o in pillars)
assert all(not o.data.polygons and not o.data.edges and o.get('hallway_render_kind') == 'points' for o in pillars)
assert not any('dot matrix collar' in o.name for o in scene.objects)
bases = [o for o in scene.objects if o.get('dotted_pillar_base')]
assert len(bases) == len(pillars) and all(not o.data.polygons for o in bases)
base_material = bpy.data.materials['Hallway / extra bright ground particles']
base_emission = next(n for n in base_material.node_tree.nodes if n.type == 'EMISSION')
assert base_emission.inputs['Strength'].default_value >= 3.5
assert abs(scene['pillar_width_m'] - 1.1) < .001
benches = [o for o in scene.objects if o.name.startswith('Bench ') and 'outline' not in o.name]
for unit in projectors:
    for part in unit.children:
        if part.type != 'MESH' or not any(label in part.name for label in ('floor anchor', 'emitter housing', 'optical head')):
            continue
        a = [part.matrix_world @ Vector(corner) for corner in part.bound_box]
        for bench in benches:
            b = [bench.matrix_world @ Vector(corner) for corner in bench.bound_box]
            separated = any(max(v[axis] for v in a) <= min(v[axis] for v in b)
                            or max(v[axis] for v in b) <= min(v[axis] for v in a) for axis in range(3))
            assert separated, f'Projector intersects furniture: {part.name}, {bench.name}'
for category in layout['categories']:
    for side in (-1, 1):
        ordered = sorted(o.location.y for o in panels if o.location.x * side > 0 and o['project_section'] == category['id'])
        assert all(abs(b - a - scene['project_bay_spacing_m']) < .001 for a, b in zip(ordered, ordered[1:]))
viewers = [o for o in npcs if o.get('activity') == 'viewing_display']
assert len(viewers) == 6
for npc in npcs:
    placement = json.loads(npc['placement'])
    direction = Vector((math.sin(placement['facing']), -math.cos(placement['facing'])))
    toward = Vector(placement['target'][:2]) - Vector(placement['position'])
    assert direction.dot(toward.normalized()) > .999
    assert abs(placement['position'][0]) > 1.8, 'NPC blocks center camera lane'
for viewer in viewers:
    placement = json.loads(viewer['placement'])
    panel = next(o for o in panels if o['project_id'] == viewer['viewing_project'])
    assert (Vector(placement['target'][:2]) - panel.location.xy).length < .001
    front = panel.matrix_world.to_quaternion() @ Vector((0, -1, 0))
    toward_viewer = Vector((*placement['position'], 0)) - panel.location
    assert front.dot(toward_viewer) > 1, 'Viewer behind inward-facing display'
groups = {}
for npc in npcs:
    if 'interaction_group' in npc:
        groups.setdefault(npc['interaction_group'], []).append(npc)
assert len(groups) == 2
for pair in groups.values():
    assert len(pair) == 2 and {o['pose'] for o in pair} == {'talking', 'listening'}
    a, b = [json.loads(o['placement']) for o in pair]
    assert 1.2 < (Vector(a['position']) - Vector(b['position'])).length < 1.6
    assert (Vector(a['target'][:2]) - Vector(b['position'])).length < .001
assert not any(block.library for block in bpy.data.objects), 'External linked objects'
assert not any(image.source == 'FILE' for image in bpy.data.images), 'External image dependency'
assert scene.frame_start == 1 and scene.frame_end == 1200
assert len([g for g in bpy.data.node_groups if 'shared particle instances' in g.name]) == 3
roof = bpy.data.collections['09 / Monochrome circuit ceiling']
roof_lights = [o for o in roof.objects if o.get('ceiling_role') == 'recessed_light']
roof_rails = [o for o in roof.objects if o.get('ceiling_role') == 'light_rail']
assert len(roof_lights) == scene['ceiling_light_count'] == 0
assert not any('Ceiling / recessed light' in o.name for o in scene.objects)
assert len(roof_rails) == 7
assert not any(o.get('ceiling_role') in {'dot_panel', 'grid'} or o.get('hallway_render_kind') == 'points' for o in roof.objects)
roof_panels = [o for o in roof.objects if o.get('ceiling_role') == 'panel']
roof_junctions = [o for o in roof.objects if o.get('ceiling_role') == 'junction']
assert not roof_panels and not roof_junctions
roof_ribs = [o for o in roof.objects if o.get('ceiling_role') == 'wave_rib']
assert len(roof_ribs) == 41
assert sum(o.get('ceiling_path') == 'curved' for o in roof_rails) == 5
assert all(min(v.co.z for v in o.data.vertices) > 5.87 and max(abs(v.co.x) for v in o.data.vertices) < 4.85 * scene.get('hallway_width_m', 10.2) / 10.2 for o in roof_ribs)
assert not any('Ceiling / suspended rectangle' in o.name for o in scene.objects)
for material in bpy.data.materials:
    if not material.name.startswith('Ceiling /'):
        continue
    for node in material.node_tree.nodes:
        if node.type in {'EMISSION', 'BSDF_PRINCIPLED'}:
            color = node.inputs['Color' if node.type == 'EMISSION' else 'Base Color'].default_value
            assert max(color[:3]) - min(color[:3]) < 1e-6, 'Ceiling is not monochrome'
for obj in npcs:
    radii = [a.value for a in obj.data.attributes['radius'].data]
    assert min(radii) > 0 and max(radii) < .01
    assert len(obj.data.vertices) >= 650
    coords = [obj.matrix_world @ v.co for v in obj.data.vertices]
    assert min(v.z for v in coords) > -.02
    assert 1.7 < max(v.z for v in coords) < 2.3
positions = []
tour_camera = scene.objects['Project Hallway / walkthrough camera']
for frame in (1, 190, 600, 1160, 1200):
    scene.frame_set(frame)
    position = list(tour_camera.matrix_world.translation)
    assert abs(position[0]) < .001 and abs(position[2] - 2.45) < .001
    assert abs(interactive.location.y + 7.8) < .001, 'Timeline locks the user camera'
    positions.append(position)
assert all(a[1] < b[1] for a, b in zip(positions, positions[1:]))


def sample_person(npc):
    """Inspect native shape-key deformation without realizing particle instances."""
    keys = npc.data.shape_keys.key_blocks
    indices = range(0, len(npc.data.vertices), 1 if npc.parent.get('npc_animation') == 'walking_loop' else 9)
    result = []
    for index in indices:
        point = keys[0].data[index].co.copy()
        for key in list(keys)[1:]:
            point += (key.data[index].co - keys[0].data[index].co) * key.value
        result.append(npc.matrix_world @ point)
    return result


for npc in npcs:
    assert npc.parent and npc.parent.get('npc_animation')
    assert npc.data.shape_keys and npc.data.shape_keys.animation_data
    for action in (npc.parent.animation_data.action, npc.data.shape_keys.animation_data.action):
        curves = [curve for layer in action.layers for strip in layer.strips
                  for bag in strip.channelbags for curve in bag.fcurves]
        assert curves and all(any(m.type == 'CYCLES' for m in curve.modifiers) for curve in curves)
scene.frame_set(1)
initial = {npc.name: sample_person(npc) for npc in npcs}
motion = {npc.name: 0 for npc in npcs}
walking_positions = {npc.name: [] for npc in npcs if npc.parent.get('npc_animation') == 'walking_loop'}
furniture_bounds = []
physical_projectors = [part for unit in projectors for part in unit.children if part.type == 'MESH'
                       and any(label in part.name for label in ('floor anchor', 'emitter housing', 'optical head'))]
door_parts = [o for o in scene.objects if o.type == 'MESH' and o.get('hallway_category_role')]
for bench in [*benches, *physical_projectors, *door_parts]:
    corners = [bench.matrix_world @ Vector(c) for c in bench.bound_box]
    furniture_bounds.append(([min(v[axis] for v in corners) for axis in range(3)],
                             [max(v[axis] for v in corners) for axis in range(3)], bench.name))
for frame in range(1, 1201, 15):
    scene.frame_set(frame)
    for npc in npcs:
        coords = sample_person(npc)
        motion[npc.name] = max(motion[npc.name], max((a - b).length for a, b in zip(coords, initial[npc.name])))
        assert min(v.z for v in coords) > -.035, f'NPC feet below floor: {npc.name}, frame {frame}'
        if npc.name in walking_positions:
            walking_positions[npc.name].append(npc.parent.location.copy())
            low = [min(v[axis] for v in coords) for axis in range(3)]
            high = [max(v[axis] for v in coords) for axis in range(3)]
            assert low[0] > 1.0 or high[0] < -1.0, 'Walker enters center camera lane'
            for a, b, name in furniture_bounds:
                assert any(high[axis] <= a[axis] or low[axis] >= b[axis] for axis in range(3)), f'Walker intersects {name} at frame {frame}'
assert all(distance > .02 for distance in motion.values()), 'NPC has no visible motion'
assert len(walking_positions) == 3
assert all(max(v.y for v in points) - min(v.y for v in points) > 4 for points in walking_positions.values())
scene.frame_set(1201)
loop_error = max((a - b).length for npc in npcs for a, b in zip(sample_person(npc), initial[npc.name]))
assert loop_error < .001, f'Global NPC loop has a visible seam: {loop_error}'
scene.frame_set(1)
report = {
    'scene': scene.name,
    'projects': len(panels),
    'categories': [category['title'] for category in layout['categories']],
    'categoryDoors': len(gates),
    'npcs': len(npcs),
    'conversationPairs': len(groups),
    'displayViewers': len(viewers),
    'thinkingVisitors': len(thinkers),
    'interactiveCamera': interactive.name,
    'windows': len(windows),
    'solidBlackWalls': len(walls),
    'gallerySpotlights': len(spotlights),
    'holographicProjectors': len(projectors),
    'displayFacing': {'left': 'east', 'right': 'west'},
    'pillarWidthMeters': scene['pillar_width_m'],
    'projectBaySpacingMeters': scene['project_bay_spacing_m'],
    'lengthMeters': scene['hallway_length_m'],
    'objects': len(scene.objects),
    'meshVerticesAuthored': sum(len(o.data.vertices) for o in scene.objects if o.type == 'MESH'),
    'meshPolygonsAuthored': sum(len(o.data.polygons) for o in scene.objects if o.type == 'MESH'),
    'particlePoints': sum(len(o.data.vertices) for o in scene.objects if o.get('hallway_render_kind') == 'points'),
    'curveSegments': sum(len(o.data.splines) for o in scene.objects if o.type == 'CURVE'),
    'sharedParticleNodeGroups': 3,
    'ceilingPlainPanels': len(roof_panels),
    'ceilingFlowingRibs': len(roof_ribs),
    'ceilingCurvedLightStrips': sum(o.get('ceiling_path') == 'curved' for o in roof_rails),
    'ceilingSquareJunctions': len(roof_junctions),
    'ceilingRecessedLights': len(roof_lights),
    'ceilingLongitudinalRails': len(roof_rails),
    'pureDotPillars': len(pillars),
    'brightDottedBases': len(bases),
    'walkingLoops': len(walking_positions),
    'walkingLoopFrames': 300,
    'animationFramesSampled': list(range(1, 1201, 15)),
    'globalLoopErrorMeters': loop_error,
    'minimumNpcMotionMeters': min(motion.values()),
    'modelBytes': (OUT / 'project-hallway.blend').stat().st_size,
    'externalDependencies': 0,
    'cameraFramesChecked': [1, 190, 600, 1160, 1200],
    'validation': 'passed',
}
(OUT / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
