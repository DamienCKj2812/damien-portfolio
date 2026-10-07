"""Build the self-contained, NPC-free Timeline Observatory Blender master.

blender --background --python-exit-code 1 --python assets/timeline-observatory/build_timeline_observatory.py -- --all-previews
Use --no-render for geometry only; --preview-only renders the existing master.
"""
import json
import math
from pathlib import Path
import random
import sys

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'assets/timeline-observatory'
sys.path.insert(0, str(OUT))
from timeline_board_art import apply_board_art
MODEL = OUT / 'timeline-observatory.blend'
CONTENT = json.loads((OUT / 'milestones.json').read_text())
RNG = random.Random(4104)
RADIUS = 12.5
HEIGHT = 8.3
WINDOW_ANGLES = (-68, -33, 33, 68)
WINDOW_HALF_ANGLE = 8
WINDOW_BOTTOM, WINDOW_TOP = .55, 7.75


def window_at(angle):
    degrees = math.degrees(angle)
    return next((i for i, center in enumerate(WINDOW_ANGLES)
                 if abs((degrees - center + 180) % 360 - 180) < WINDOW_HALF_ANGLE - 1e-5), None)


def material(name, value, emission=False, strength=1, metallic=0, roughness=.4):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    if emission:
        nodes = mat.node_tree.nodes
        nodes.clear()
        output = nodes.new('ShaderNodeOutputMaterial')
        shader = nodes.new('ShaderNodeEmission')
        shader.inputs['Color'].default_value = (value, value, value, 1)
        shader.inputs['Strength'].default_value = strength
        mat.node_tree.links.new(shader.outputs[0], output.inputs['Surface'])
    else:
        shader = mat.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Base Color'].default_value = (value, value, value, 1)
        shader.inputs['Metallic'].default_value = metallic
        shader.inputs['Roughness'].default_value = roughness
    return mat


def collection(name):
    col = bpy.data.collections.new(name)
    scene.collection.children.link(col)
    return col


def mesh_object(name, vertices, faces, mat, col):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    col.objects.link(obj)
    if mat:
        data.materials.append(mat)
    return obj


def move_to(obj, col):
    for current in list(obj.users_collection):
        current.objects.unlink(obj)
    col.objects.link(obj)
    return obj


def box(name, center, dimensions, mat, col):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    obj = bpy.context.object
    obj.name = name
    obj.scale = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    return move_to(obj, col)


def lines(name, segments, mat, col, radius=.004):
    data = bpy.data.curves.new(name, 'CURVE')
    data.dimensions = '3D'
    data.bevel_depth = radius
    data.bevel_resolution = 0
    data.resolution_u = 1
    for a, b in segments:
        spline = data.splines.new('POLY')
        spline.points.add(1)
        spline.points[0].co = (*a, 1)
        spline.points[1].co = (*b, 1)
    data.materials.append(mat)
    obj = bpy.data.objects.new(name, data)
    col.objects.link(obj)
    return obj


def path(name, coordinates, mat, col, radius=.004, closed=False):
    values = list(coordinates)
    return lines(name, list(zip(values, values[1:] + ([values[0]] if closed else []))), mat, col, radius)


def circle(name, center, radius, mat, col, thickness=.004, count=128):
    x, y, z = center
    return path(name, [(x + radius * math.cos(i * math.tau / count),
                        y + radius * math.sin(i * math.tau / count), z) for i in range(count)],
                mat, col, thickness, closed=True)


def outline(obj, mat, col, radius=.004):
    bpy.context.view_layer.update()
    return lines(obj.name + ' / outline', [(obj.matrix_world @ obj.data.vertices[e.vertices[0]].co,
                                         obj.matrix_world @ obj.data.vertices[e.vertices[1]].co)
                                        for e in obj.data.edges], mat, col, radius)


def points(name, vertices, radii, mat, col):
    obj = mesh_object(name, vertices, [], None, col)
    obj.data.attributes.new('radius', 'FLOAT', 'POINT').data.foreach_set('value', radii)
    obj['render_kind'] = 'points'
    group_name = mat.name + ' / shared dot instances'
    group = bpy.data.node_groups.get(group_name)
    if not group:
        group = bpy.data.node_groups.new(group_name, 'GeometryNodeTree')
        group.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
        group.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
        nodes, links = group.nodes, group.links
        source = nodes.new('NodeGroupInput')
        output = nodes.new('NodeGroupOutput')
        convert = nodes.new('GeometryNodeMeshToPoints')
        attr = nodes.new('GeometryNodeInputNamedAttribute')
        attr.data_type = 'FLOAT'
        attr.inputs['Name'].default_value = 'radius'
        ico = nodes.new('GeometryNodeMeshIcoSphere')
        ico.inputs['Radius'].default_value = 1
        ico.inputs['Subdivisions'].default_value = 1
        paint = nodes.new('GeometryNodeSetMaterial')
        paint.inputs['Material'].default_value = mat
        instances = nodes.new('GeometryNodeInstanceOnPoints')
        links.new(source.outputs['Geometry'], convert.inputs['Mesh'])
        links.new(attr.outputs['Attribute'], convert.inputs['Radius'])
        links.new(convert.outputs['Points'], instances.inputs['Points'])
        links.new(ico.outputs['Mesh'], paint.inputs['Geometry'])
        links.new(paint.outputs['Geometry'], instances.inputs['Instance'])
        links.new(attr.outputs['Attribute'], instances.inputs['Scale'])
        links.new(instances.outputs['Instances'], output.inputs['Geometry'])
    obj.modifiers.new('Instanced celestial dots', 'NODES').node_group = group
    return obj


def text(name, body, position, size, col, mat=None, parent=None, rotation=(math.pi / 2, 0, 0), spacing=1.15):
    data = bpy.data.curves.new(name, 'FONT')
    data.body = body
    data.align_x = 'CENTER'
    data.size = size
    data.space_character = spacing
    data.space_line = 1.6
    data.materials.append(mat or TYPE)
    obj = bpy.data.objects.new(name, data)
    col.objects.link(obj)
    obj.parent = parent
    obj.location = position
    obj.rotation_euler = rotation
    return obj


def wire_sphere(name, center, radius, mat, col, subdivisions=2, thickness=.003):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=radius)
    source = bpy.context.object
    data = source.data
    segments = [(data.vertices[e.vertices[0]].co.copy(), data.vertices[e.vertices[1]].co.copy()) for e in data.edges]
    bpy.data.objects.remove(source, do_unlink=True)
    bpy.data.meshes.remove(data)
    obj = lines(name, segments, mat, col, thickness)
    obj.location = center
    return obj


def icon(kind, parent):
    def stroke(name, coords, closed=False):
        obj = path('Milestone icon / ' + name, [(x, -.047, 2.45 + z) for x, z in coords], TYPE, timeline, .003, closed)
        obj.parent = parent
    if kind == 'mountains':
        stroke('mountains', [(-.72, -.35), (-.35, -.08), (-.15, -.21), (.03, .14), (.37, -.26), (.59, -.15), (.76, -.35)])
        stroke('horizon', [(-.75, -.38), (.75, -.38)])
        stroke('sun', [(.48 + .085 * math.cos(i * math.tau / 32), .34 + .085 * math.sin(i * math.tau / 32)) for i in range(32)], True)
    elif kind == 'cube':
        top, left, right, low = (0, .35), (-.29, .19), (.29, .19), (0, .03)
        stroke('cube top', [top, left, low, right], True)
        stroke('cube left', [left, (-.29, -.21), (0, -.38), low])
        stroke('cube right', [right, (.29, -.21), (0, -.38)])
        stroke('cube vertical', [low, (0, -.38)])
    elif kind == 'graduation':
        stroke('cap', [(0, .25), (-.38, .09), (0, -.07), (.38, .09)], True)
        stroke('cap band', [(-.24, -.04), (-.24, -.21), (0, -.29), (.24, -.21), (.24, -.04)])
        stroke('tassel', [(.34, .08), (.34, -.22), (.40, -.27)])
    elif kind == 'buildings':
        for x, top in ((-.30, .02), (-.09, .31), (.14, .11)):
            stroke('tower', [(x, -.35), (x, top), (x + .18, top + .07), (x + .18, -.35)])
            for row in range(3):
                for dx in (.055, .12):
                    z = -.23 + row * .12
                    if z < top:
                        stroke('window', [(x + dx, z), (x + dx, z + .045)])
        stroke('building ground', [(-.43, -.37), (.43, -.37)])
    elif kind == 'gears':
        for cx, cz, radius in ((-.20, -.12, .18), (.22, .19, .22)):
            stroke('gear teeth', [(cx + radius * (1 if i % 4 in (1, 2) else .78) * math.cos(i * math.tau / 40),
                                   cz + radius * (1 if i % 4 in (1, 2) else .78) * math.sin(i * math.tau / 40)) for i in range(40)], True)
            stroke('gear hub', [(cx + radius * .45 * math.cos(i * math.tau / 24),
                                 cz + radius * .45 * math.sin(i * math.tau / 24)) for i in range(24)], True)
    else:
        stroke('globe rim', [(.52 * math.cos(i * math.tau / 64), .52 * math.sin(i * math.tau / 64)) for i in range(64)], True)
        for width in (.23, .42):
            stroke('globe meridian', [(width * math.cos(i * math.tau / 64), .52 * math.sin(i * math.tau / 64)) for i in range(64)], True)
        for height in (.20, .38):
            stroke('globe latitude', [(.52 * math.cos(i * math.tau / 64), height * math.sin(i * math.tau / 64)) for i in range(64)], True)


def milestone(item, angle, index):
    x, y = 8 * math.sin(angle), 8 * math.cos(angle)
    root = bpy.data.objects.new(f'Milestone {index + 1:02d} / {item["id"]}', None)
    timeline.objects.link(root)
    root.location = (x, y, 0)
    root.rotation_euler.z = math.atan2(-x, y + 11.6)
    root['milestone_id'] = item['id']
    root['milestone_metadata'] = json.dumps(item)
    board = box(root.name + ' / black floating card', (0, 0, 2.75), (1.90, .05, 2.40), SCREEN, timeline)
    edge = outline(board, WHITE, timeline, .005)
    board.parent = root
    edge.parent = root
    title = text(root.name + ' / title', item.get('cardTitle', item['title']), (0, -.033, 3.66), .19, timeline, parent=root, spacing=1.3)
    bpy.context.view_layer.update()
    if title.dimensions.x > 1.60:
        title.data.size *= 1.60 / title.dimensions.x
    caption = text(root.name + ' / caption', item['caption'], (0, -.033, 1.79), .075, timeline, MUTED, root, spacing=1.3)
    bpy.context.view_layer.update()
    if caption.dimensions.x > 1.60:
        caption.data.size *= 1.60 / caption.dimensions.x
    icon(item['icon'], root)
    apply_board_art(scene, root, item)
    stems = lines(root.name + ' / projection and upper tether', [((0, 0, .06), (0, 0, 1.55)),
                                                               ((0, 0, 3.95), (0, 0, 4.72))], WHITE, timeline, .005)
    stems.parent = root
    orb = wire_sphere(root.name + ' / glowing timeline node', (x, y, .65), .19, BRIGHT, timeline, 2, .0035)
    orb['timeline_node'] = True
    circle(root.name + ' / ground halo', (x, y, .024), .29, TYPE, timeline, .003, 48)
    return {'id': item['id'], 'position': [x, y, 0], 'angleDegrees': math.degrees(angle)}


def observation_windows(windows):
    glass = bpy.data.materials.new('Observatory / clear observation glass')
    glass.use_nodes = True
    nodes, links = glass.node_tree.nodes, glass.node_tree.links
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    clear = nodes.new('ShaderNodeBsdfTransparent')
    reflective = nodes.new('ShaderNodeBsdfPrincipled')
    reflective.inputs['Base Color'].default_value = (.6, .6, .6, 1)
    reflective.inputs['Metallic'].default_value = 1
    reflective.inputs['Roughness'].default_value = .06
    mix = nodes.new('ShaderNodeMixShader')
    mix.inputs[0].default_value = .025
    links.new(clear.outputs[0], mix.inputs[1])
    links.new(reflective.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], output.inputs['Surface'])
    specs = []
    for index, degrees in enumerate(WINDOW_ANGLES):
        start, end = [math.radians(degrees + sign * WINDOW_HALF_ANGLE) for sign in (-1, 1)]
        angles = [start + i * (end - start) / 12 for i in range(13)]
        vertices = [(12.48 * math.sin(a), 12.48 * math.cos(a), z)
                    for a in angles for z in (WINDOW_BOTTOM, WINDOW_TOP)]
        pane = mesh_object(f'Observation window {index + 1:02d} / curved clear glazing', vertices,
                           [(2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1) for i in range(12)], glass, windows)
        pane['observatory_window'] = True
        pane['angle_degrees'] = degrees
        for a in (start, end):
            jamb = box('Observation window / black structural jamb',
                       (12.49 * math.sin(a), 12.49 * math.cos(a), 4.15), (.095, .18, 7.20), BLACK, windows)
            jamb.rotation_euler.z = -a
            outline(jamb, WHITE, windows, .0035)
        for z in (WINDOW_BOTTOM, WINDOW_TOP):
            path('Observation window / curved luminous sill or header',
                 [(12.41 * math.sin(a), 12.41 * math.cos(a), z) for a in angles], WHITE, windows, .005)
        for z in (WINDOW_BOTTOM + .08, WINDOW_TOP - .08):
            path('Observation window / fine inset trim',
                 [(12.405 * math.sin(a), 12.405 * math.cos(a), z) for a in angles], MUTED, windows, .002)
        specs.append({'angleDegrees': degrees, 'halfAngleDegrees': WINDOW_HALF_ANGLE,
                      'bottomMeters': WINDOW_BOTTOM, 'topMeters': WINDOW_TOP})
    vertices = [(6.58 * math.cos(i * math.tau / 128), 6.58 * math.sin(i * math.tau / 128), 8.285) for i in range(128)]
    skylight = mesh_object('Observation roof / circular clear space window', vertices, [tuple(range(128))], glass, windows)
    skylight['roof_window'] = True
    return specs


def exterior_planet(name, center, radius, variant, tilt=(0, 0, 0)):
    root = bpy.data.objects.new('Exterior planet / ' + name, None)
    cosmos.objects.link(root)
    root.location = center
    root.rotation_euler = tilt
    root['external_planet'] = True
    root['planet_variant'] = variant
    root['planet_radius_m'] = radius
    root['exterior_zone'] = 'roof' if name == 'Overhead world' else 'wall'
    core_mat = material('Planet / ' + name + ' / dark opaque body', .006, emission=True)
    edge_mat = material('Planet / ' + name + ' / white surface contours', .34, emission=True)
    if variant == 'geodesic':
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=radius)
    else:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=radius)
    core = bpy.context.object
    core.name = root.name + ' / spherical body'
    move_to(core, cosmos)
    core.data.materials.append(core_mat)
    core['planet_body'] = True
    # Shallow physical terrain on the rocky moon, not a picture on a plane.
    if variant == 'cratered':
        for vertex in core.data.vertices:
            n = vertex.co.normalized()
            vertex.co *= 1 + .014 * math.sin(n.x * 19) * math.sin(n.y * 17) * math.cos(n.z * 13)
        core.data.update()
    core.parent = root
    if variant in {'geodesic', 'cratered'}:
        contours = lines(root.name + ' / three-dimensional wire terrain',
                         [(core.data.vertices[e.vertices[0]].co * 1.004, core.data.vertices[e.vertices[1]].co * 1.004)
                          for e in core.data.edges], edge_mat, cosmos, radius * .0008)
        contours.parent = root
    else:
        for latitude in range(-10, 11):
            a = latitude * math.pi / 24
            r, z = radius * math.cos(a) * 1.004, radius * math.sin(a) * 1.004
            ring = circle(root.name + ' / atmospheric latitude', (0, 0, z), r, edge_mat, cosmos,
                          radius * (.0014 if variant == 'banded' and latitude % 3 == 0 else .0007), 96)
            ring.parent = root
        for longitude in range(8):
            a = longitude * math.pi / 8
            curve = path(root.name + ' / meridian',
                         [(radius * 1.004 * math.cos(t) * math.cos(a), radius * 1.004 * math.cos(t) * math.sin(a),
                           radius * 1.004 * math.sin(t)) for t in [-math.pi / 2 + i * math.pi / 64 for i in range(65)]],
                         MUTED, cosmos, radius * .0006)
            curve.parent = root
    if variant == 'ringed':
        ring_root = bpy.data.objects.new(root.name + ' / tilted orbital rings', None)
        cosmos.objects.link(ring_root)
        ring_root.parent = root
        ring_root.rotation_euler = (.55, .12, .15)
        for scale in (1.30, 1.38, 1.45, 1.58, 1.64):
            ring = circle(root.name + ' / orbital ring', (0, 0, 0), radius * scale, TYPE, cosmos, radius * .001, 128)
            ring.parent = ring_root
        annulus_vertices = [(r * math.cos(i * math.tau / 96), r * math.sin(i * math.tau / 96), 0)
                            for i in range(96) for r in (radius * 1.38, radius * 1.45)]
        band_mat = material('Planet / soft white orbital dust', .055, emission=True)
        band = mesh_object(root.name + ' / orbital dust band', annulus_vertices,
                           [(2 * i, 2 * ((i + 1) % 96), 2 * ((i + 1) % 96) + 1, 2 * i + 1) for i in range(96)],
                           band_mat, cosmos)
        band.parent = ring_root
        root['ringed_planet'] = True
    if variant == 'cratered':
        for index in range(9):
            normal = Vector((math.sin(index * 2.4), -1.2, math.cos(index * 1.7))).normalized()
            tangent = normal.cross(Vector((0, 0, 1))).normalized()
            up = normal.cross(tangent).normalized()
            angular_radius = .09 + (index % 3) * .035
            rim = path(root.name + ' / crater rim',
                       [(normal * math.cos(angular_radius) + (tangent * math.cos(t) + up * math.sin(t))
                         * math.sin(angular_radius)) * radius * 1.023 for t in [i * math.tau / 48 for i in range(48)]],
                       TYPE, cosmos, radius * .0009, closed=True)
            rim.parent = root
    if variant == 'banded':
        band_mat = material('Planet / faint atmospheric bands', .012, emission=True)
        core.data.materials.append(band_mat)
        for polygon in core.data.polygons:
            z = sum(core.data.vertices[i].co.z for i in polygon.vertices) / len(polygon.vertices)
            polygon.material_index = int(math.sin(z / radius * 22) > .25)
    for frame, angle in ((1, tilt[2]), (2401, tilt[2] + math.tau)):
        root.rotation_euler.z = angle
        root.keyframe_insert(data_path='rotation_euler', index=2, frame=frame)
    for layer in root.animation_data.action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:
                        key.interpolation = 'LINEAR'
                    curve.modifiers.new('CYCLES')
    return {'name': name, 'center': list(center), 'radiusMeters': radius, 'variant': variant,
            'zone': root['exterior_zone'], 'loopFrames': 2400}


def exterior_space():
    stars, sizes = [], []
    for _ in range(4800):
        z = RNG.uniform(-1, 1)
        angle, radius = RNG.uniform(0, math.tau), RNG.uniform(72, 86)
        horizontal = math.sqrt(1 - z * z)
        stars.append((radius * horizontal * math.cos(angle), radius * horizontal * math.sin(angle), radius * z))
        sizes.append(RNG.uniform(.025, .10))
    points('Exterior space / surrounding three-dimensional starfield', stars, sizes, STAR, cosmos)['exterior_starfield'] = True
    specs = []
    eye = Vector((0, -11.6, 3.7))
    for index, (degrees, variant, radius) in enumerate(zip(WINDOW_ANGLES, ('ringed', 'geodesic', 'banded', 'cratered'), (4.0, 4.8, 5.0, 4.3))):
        a = math.radians(degrees)
        window = Vector((RADIUS * math.sin(a), RADIUS * math.cos(a), 4.8))
        center = window + (window - eye).normalized() * 12
        specs.append(exterior_planet(f'Window world {index + 1:02d}', center, radius, variant,
                                     (.16 * index, .08 * index, .2 * index)))
    specs.append(exterior_planet('Overhead world', (0, 8, 19.5), 8.0, 'geodesic', (.22, .10, 0)))
    return specs


def architectural_wall_lights(col, wall_mat):
    strip_mat = material('Observatory / recessed vertical white wall lights', .65, emission=True, strength=2)
    base_mat = material('Observatory / brighter lower wall lights', .75, emission=True, strength=2.4)
    specs = []
    for index, degrees in enumerate((-128, -94, -51, -20, 20, 51, 94, 128)):
        a = math.radians(degrees)
        center = Vector((12.34 * math.sin(a), 12.34 * math.cos(a), 0))
        tangent = Vector((math.cos(a), -math.sin(a), 0))
        vertices = [center + tangent * x + Vector((0, 0, z)) for z in (.04, 7.88) for x in (-.25, .25)]
        rib = mesh_object(f'Wall rib {index + 1:02d} / satin black architectural panel',
                          vertices, [(0, 1, 3, 2)], wall_mat, col)
        rib['architectural_wall_rib'] = True
        for side in (-1, 1):
            p = center + tangent * (side * .29)
            light = lines(f'Wall rib {index + 1:02d} / recessed vertical LED',
                          [(p + Vector((0, 0, 2.15)), p + Vector((0, 0, 7.75)))], strip_mat, col, .009)
            light['architectural_wall_light'] = True
            lines(f'Wall rib {index + 1:02d} / lower LED',
                  [(p + Vector((0, 0, .13)), p + Vector((0, 0, 1.35)))], base_mat, col, .009)
        specs.append({'angleDegrees': degrees, 'center': list(center), 'widthMeters': .5,
                      'heightMeters': 7.84, 'design': 'satin black rib / recessed white LEDs'})
    return specs


def create_guided_walk(cameras, positions):
    """Animate position only; leave camera yaw/pitch entirely user-controlled."""
    root = bpy.data.objects.new('Timeline Observatory / guided movement rig', None)
    cameras.objects.link(root)
    entrance = (0, -8.7, 0)
    def waypoint(degrees, radius):
        angle = math.radians(degrees)
        return (radius * math.sin(angle), radius * math.cos(angle), 0)
    keys = [(1, entrance), (91, entrance), (271, waypoint(-135, 4.1)),
            (331, waypoint(-110, 6.1)), (391, waypoint(-88, 6.1))]
    stations = []
    for index, (item, position) in enumerate(zip(CONTENT['milestones'], positions)):
        x, y, _ = position['position']
        heading = math.atan2(-x, y + 11.6)
        view = (x + 2.8 * math.sin(heading), y - 2.8 * math.cos(heading), 0)
        arrival = 451 + index * 270
        leave = arrival + 180
        keys.extend([(arrival, view), (leave, view)])
        stations.append({'id': item['id'], 'title': item['title'], 'arrivalFrame': arrival,
                         'leaveFrame': leave, 'viewPosition': list(view)})
        scene.timeline_markers.new(f'{index + 1:02d} / {item["title"]}', frame=arrival)
    end = stations[-1]['leaveFrame']
    home = end + 360
    period = 1200 * math.ceil((home - 1 + 60) / 1200)
    keys.extend([(end + 60, waypoint(88, 6.1)), (end + 120, waypoint(110, 6.1)),
                 (end + 180, waypoint(135, 4.1)), (home, entrance), (period + 1, entrance)])
    for frame, position in sorted(keys):
        root.location = position
        root.keyframe_insert(data_path='location', frame=frame)
    for layer in root.animation_data.action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:
                        key.interpolation = 'BEZIER'
                        key.handle_left_type = key.handle_right_type = 'AUTO_CLAMPED'
                    curve.modifiers.new('CYCLES')
    root['guided_movement_only'] = True
    data = bpy.data.cameras.new('Timeline Observatory / guided free-look camera')
    data.lens = 19.5
    data.clip_start, data.clip_end = .05, 100
    camera = bpy.data.objects.new(data.name, data)
    cameras.objects.link(camera)
    camera.parent = root
    camera.location = (0, 0, 2.45)
    camera.rotation_mode = 'QUATERNION'
    camera.rotation_quaternion = Vector((0, 1, .08)).to_track_quat('-Z', 'Y')
    scene.camera = camera
    scene['guided_walk_stations'] = json.dumps(stations)
    scene['guided_walk_period'] = period
    controls = bpy.data.texts.new('observatory_controls.py')
    controls.write((OUT / 'observatory_controls.py').read_text())
    help_text = bpy.data.texts.new('START HERE / Observatory Guided Walk')
    help_text.write('TIMELINE OBSERVATORY / MOVEMENT-ONLY GUIDED JOURNEY\n\n'
                    'Space plays the native walking route through every milestone in order.\n'
                    'The camera has no orientation animation or auto-aim constraint.\n\n'
                    'For interactive mouse-look: open Scripting, select observatory_controls.py,\n'
                    'Run Script (Alt+P), return to the 3D viewport, then F3:\n'
                    'Timeline Observatory: Guided Walk.\n\n'
                    'Mouse: free look. Space: pause/resume walking. Tab: release mouse.\n'
                    'Left/Right arrows: previous/next node. Home: restart. Esc: exit.\n'
                    'The route pauses six seconds at each node. The globe keeps rotating\n'
                    'when interactive walking is paused. No NPCs are included.\n')
    return {'periodFrames': period, 'fps': 30, 'eyeHeightMeters': 2.45, 'nodeDwellFrames': 180,
            'movementOnly': True, 'stations': stations, 'keyframes': [{'frame': f, 'position': list(p)} for f, p in sorted(keys)]}


def interface_floor():
    """Level architectural slabs and millimetre-scale, glass-embedded HUD inlays."""
    base_col = collection('10 / Interface floor / recessed foundation')
    slabs_col = collection('11 / Interface floor / smoked glass slabs')
    hud_col = collection('12 / Interface floor / embedded white interface')
    base_mat = material('Floor / recessed charcoal joints', .002, metallic=.35, roughness=.3)
    glass = material('Floor / polished smoked black glass', .004, metallic=.65, roughness=.095)
    shader = glass.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Coat Weight'].default_value = .65
    shader.inputs['Coat Roughness'].default_value = .065
    shader.inputs['IOR'].default_value = 1.48
    dim = material('Floor / dim white subsurface inlay', .24, emission=True, strength=.65)
    lit = material('Floor / selected white LED joints', .7, emission=True, strength=1.15)
    bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=RADIUS, depth=.11, location=(0, 0, -.125))
    base = move_to(bpy.context.object, base_col)
    base.name = 'Observatory / circular reflective floor'
    base.data.materials.append(base_mat)
    base['floor_layer'] = 'foundation'

    # Clip only perimeter slabs to the circular architecture. Interior slabs stay
    # rectangular/square; no boolean modifiers, tiny tiles or raised walking edges.
    footprint = [(RADIUS * math.cos(i * math.tau / 128),
                  RADIUS * math.sin(i * math.tau / 128)) for i in range(128)]

    def clipped_slab(x0, x1, y0, y1):
        polygon = footprint[:]
        for axis, limit, sign in ((0, x0, 1), (0, x1, -1), (1, y0, 1), (1, y1, -1)):
            result = []
            for a, b in zip(polygon, polygon[1:] + polygon[:1]):
                inside_a = sign * (a[axis] - limit) >= 0
                inside_b = sign * (b[axis] - limit) >= 0
                if inside_a:
                    result.append(a)
                if inside_a != inside_b:
                    t = (limit - a[axis]) / (b[axis] - a[axis])
                    result.append(tuple(a[k] + t * (b[k] - a[k]) for k in range(2)))
            polygon = result
        return polygon

    x_edges = [-12.5, -9, -6, -3, 0, 3, 6, 9, 12.5]
    y_edges = [-12.5, -9, -6, -3, 0, 3, 6, 9, 12.5]
    gap = .008
    count = 0
    for row, (y0, y1) in enumerate(zip(y_edges, y_edges[1:])):
        columns = x_edges
        for column, (x0, x1) in enumerate(zip(columns, columns[1:])):
            poly = clipped_slab(x0 + gap / 2, x1 - gap / 2, y0 + gap / 2, y1 - gap / 2)
            if len(poly) < 3:
                continue
            n = len(poly)
            vertices = [(x, y, z) for z in (-.07, 0) for x, y in poly]
            faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
            faces.extend((i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n))
            slab = mesh_object(f'Floor / large smoked slab {row:02d}.{column:02d}', vertices, faces, glass, slabs_col)
            slab['floor_layer'] = 'slab'
            slab['joint_width_m'] = gap
            count += 1

    # The shallow curve inlays read as light beneath the polished finish; they
    # are centreline-exportable, not thick bars or a realized wireframe mesh.
    z = .0012
    def inlay(name, coordinates, bright=False, closed=False):
        obj = path('Floor HUD / ' + name, [(x, y, z) for x, y in coordinates],
                   lit if bright else dim, hud_col, .0012 if bright else .0008, closed)
        obj['floor_layer'] = 'inlay'
        return obj

    # Single centreline per recessed seam: hairline white, never a double border.
    seam_mat = material('Floor / hairline white slab seams', .48, emission=True, strength=.7)
    for axis in (0, 1):
        for fixed in x_edges[1:-1]:
            reach = math.sqrt(RADIUS ** 2 - fixed ** 2)
            coords = [(fixed, -reach), (fixed, reach)] if axis == 0 else [(-reach, fixed), (reach, fixed)]
            seam = path('Floor / hairline recessed square slab seam', [(x, y, z) for x, y in coords],
                        seam_mat, hud_col, .00065)
            seam['floor_layer'] = 'seam'

    # Selected entire square panels carry tiny dots, as in the supplied photo.
    # Spread selected panels through the entry, central aisles and rear wall.
    # More than half the room remains plain glass, with no dots under the dais.
    dot_centers = ((-4.5, -7.5), (-1.5, -7.5), (1.5, -7.5), (4.5, -4.5),
                   (-7.5, -1.5), (7.5, 1.5), (-4.5, 7.5), (4.5, 7.5),
                   (-4.5, -1.5), (-4.5, 1.5), (4.5, -1.5), (4.5, 1.5),
                   (-1.5, -4.5), (1.5, -4.5), (-4.5, 4.5), (4.5, 4.5),
                   (-1.5, 4.5), (1.5, 4.5), (-1.5, 7.5), (1.5, 7.5),
                   (-7.5, 4.5), (7.5, 4.5), (-1.5, 10.5), (1.5, 10.5))
    dot_mat = material('Floor / tiny white panel dots', .55, emission=True, strength=.8)
    for index, (cx, cy) in enumerate(dot_centers):
        vertices = [(cx + (i - 6) * .2, cy + (j - 6) * .2, z) for i in range(13) for j in range(13)]
        dots = points(f'Floor HUD / selected square dot panel {index + 1:02d}',
                      vertices, [.003] * len(vertices), dot_mat, hud_col)
        dots['floor_layer'] = 'inlay'
        dots['dotted_floor_panel'] = True
    for x, y in ((-6, -6), (0, -9), (3, -6), (9, 0)):
        inlay('tiny illuminated diamond connector', [(x, y + .035), (x + .035, y),
                                                      (x, y - .035), (x - .035, y)], True, True)
    # Just two short corner brackets and one tiny stacked inscription.
    for x, y in ((-5.8, -8.8), (3.2, -8.8)):
        coords = [(x, y + .48), (x, y + .1)]
        coords.extend((x + .1 + .1 * math.cos(math.radians(180 + i * 90 / 8)),
                       y + .1 + .1 * math.sin(math.radians(180 + i * 90 / 8))) for i in range(9))
        coords.append((x + .65, y))
        inlay('short rounded slab corner', coords, True)
    label = text('Floor HUD / training', 'TRAIN\nEVOLVE\nREPEAT', (-4.5, -5.3, z), .07,
                 hud_col, dim, rotation=(0, 0, 0), spacing=1.8)
    label['floor_layer'] = 'inlay'
    return {'slabs': count, 'jointWidthMeters': gap, 'surfaceHeightMeters': 0,
            'slabDepthMeters': .07, 'hudLineDiameterMeters': .0016,
            'hudSystems': 0, 'squareSlabSizeMeters': 3, 'dottedPanels': len(dot_centers),
            'dotDiameterMeters': .006, 'plainPanelAreaFraction': 1 - len(dot_centers) * 9 / (math.pi * RADIUS ** 2),
            'palette': 'black / charcoal / white',
            'layers': ['foundation', 'smoked glass slabs', 'embedded HUD inlays', 'selected LED joints']}


def build():
    global scene, architecture, timeline, cosmos, WHITE, BRIGHT, TYPE, MUTED, BLACK, SCREEN, STAR
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.name = 'TIMELINE OBSERVATORY / My Journey So Far'
    scene.unit_settings.system = 'METRIC'
    scene['npc_count'] = 0
    scene['room_radius_m'] = RADIUS
    scene['reference_style'] = 'Satin black architectural panels / recessed white LEDs / smooth ceiling ring / dotted glass floor'
    architecture = collection('01 / Circular architecture')
    grid_col = collection('02 / Wireframe grids and dotted ribs')
    timeline = collection('03 / Editable milestone timeline')
    cosmos = collection('04 / Exterior space and three-dimensional planets')
    centre = collection('05 / Central globe and observatory dais')
    furniture = collection('06 / Benches and floor typography')
    cameras = collection('07 / Cameras and soft lighting')
    windows = collection('08 / Actual observation windows')
    pillars = collection('09 / Architectural wall ribs and recessed white lights')
    BLACK = material('Observatory / charcoal architecture', .006, metallic=.15, roughness=.38)
    WALL = material('Observatory / satin black architectural wall panels', .003, metallic=.12, roughness=.52)
    CEILING = material('Observatory / smooth satin black ceiling', .002, metallic=.1, roughness=.48)
    SEAM = material('Observatory / recessed dark panel seams', .001, roughness=.5)
    # Fine procedural microtexture, not a visible patterned or tiled texture.
    shader = WALL.node_tree.nodes.get('Principled BSDF')
    noise = WALL.node_tree.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 180
    bump = WALL.node_tree.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = .12
    bump.inputs['Distance'].default_value = .008
    WALL.node_tree.links.new(noise.outputs['Fac'], bump.inputs['Height'])
    WALL.node_tree.links.new(bump.outputs['Normal'], shader.inputs['Normal'])
    SCREEN = material('Observatory / black holographic card', .003, emission=True)
    WHITE = material('Observatory / luminous white outlines', .8, emission=True, strength=1.4)
    CEILING_LIGHT = material('Observatory / dim architectural ceiling light', .32, emission=True)
    BRIGHT = material('Observatory / timeline node glow', .9, emission=True, strength=2.2)
    TYPE = material('Observatory / white typography', .78, emission=True)
    MUTED = material('Observatory / secondary detail', .40, emission=True)
    WIRE = material('Observatory / fine architectural grid', .075, emission=True)
    STAR = material('Observatory / monochrome celestial stars', .6, emission=True)
    floor_specs = interface_floor()
    wall_vertices, wall_faces = [], []
    wall_angles = sorted({i * math.tau / 128 for i in range(129)}
                         | {math.radians(center + sign * WINDOW_HALF_ANGLE) % math.tau
                            for center in WINDOW_ANGLES for sign in (-1, 1)})
    for angle in wall_angles:
        wall_vertices.extend([(RADIUS * math.sin(angle), RADIUS * math.cos(angle), z)
                              for z in (0, WINDOW_BOTTOM, WINDOW_TOP, HEIGHT)])
    for i, (a, b) in enumerate(zip(wall_angles, wall_angles[1:])):
        mid = (a + b) / 2
        if math.cos(mid) > -.84:
            for level in range(3):
                if level != 1 or window_at(mid) is None:
                    wall_faces.append((i * 4 + level, i * 4 + level + 1, (i + 1) * 4 + level + 1, (i + 1) * 4 + level))
    wall = mesh_object('Observatory / curved wall with actual observation openings', wall_vertices, wall_faces, WALL, architecture)
    for polygon in wall.data.polygons:
        polygon.use_smooth = True
    wall['physical_window_openings'] = 4
    shell = wall.modifiers.new('Solid architectural wall / outward thickness', 'SOLIDIFY')
    shell.thickness = .16
    shell.offset = 1
    shell.use_even_offset = True
    wall['wall_thickness_m'] = .16
    window_specs = observation_windows(windows)
    roof_vertices, roof_faces = [], []
    for i in range(128):
        a = i * math.tau / 128
        roof_vertices.extend([(r * math.sin(a), r * math.cos(a), HEIGHT) for r in (6.6, RADIUS)])
    for i in range(128):
        j = (i + 1) % 128
        roof_faces.append((2 * i, 2 * j, 2 * j + 1, 2 * i + 1))
    roof = mesh_object('Observatory / annular ceiling with glazed space oculus', roof_vertices, roof_faces, CEILING, architecture)
    roof['oculus_radius_m'] = 6.6
    # Broad smooth ceiling fascia with a single white cove at the wall.
    fascia_vertices = [(12.4 * math.sin(i * math.tau / 128), 12.4 * math.cos(i * math.tau / 128), z)
                       for i in range(128) for z in (7.9, HEIGHT)]
    fascia_faces = [(2 * i, 2 * i + 1, 2 * ((i + 1) % 128) + 1, 2 * ((i + 1) % 128)) for i in range(128)]
    fascia = mesh_object('Observatory / smooth curved ceiling fascia', fascia_vertices, fascia_faces, CEILING, architecture)
    for polygon in fascia.data.polygons:
        polygon.use_smooth = True
    for radius, z in ((6.6, 8.27), (6.85, 8.27), (12.38, 7.88)):
        circle('Observatory / architectural ceiling light ring', (0, 0, z), radius, CEILING_LIGHT, grid_col, .009)
    circle('Observatory / recessed wall base light', (0, 0, .07), 12.43, CEILING_LIGHT, grid_col, .005)
    # Large wall panels: quiet black recessed joints instead of a luminous grid.
    for degrees in range(-130, 131, 10):
        a = math.radians(degrees)
        spans = ((.12, WINDOW_BOTTOM), (WINDOW_TOP, 7.88)) if window_at(a) is not None else ((.12, 7.88),)
        lines('Observatory / dark vertical wall panel joint',
              [((12.49 * math.sin(a), 12.49 * math.cos(a), low),
                (12.49 * math.sin(a), 12.49 * math.cos(a), high)) for low, high in spans], SEAM, architecture, .006)
    for z in (2, 5.6):
        segments = []
        for a, b in zip(wall_angles, wall_angles[1:]):
            if math.cos((a + b) / 2) > -.84 and window_at((a + b) / 2) is None:
                segments.append(((12.49 * math.sin(a), 12.49 * math.cos(a), z),
                                 (12.49 * math.sin(b), 12.49 * math.cos(b), z)))
        lines('Observatory / dark horizontal wall panel joint', segments, SEAM, architecture, .006)
    pillar_specs = architectural_wall_lights(pillars, WALL)
    planet_specs = exterior_space()
    for side in (-1, 1):
        root = bpy.data.objects.new('Observatory / suspended quote panel', None)
        cosmos.objects.link(root)
        root.location = (side * 10.8, 2.2, 0)
        root.rotation_euler.z = math.atan2(-side * 10.8, 13.8)
        board = box('Observatory / quote backing', (0, 0, 5.65), (1.65, .05, 4.4), SCREEN, cosmos)
        frame = outline(board, MUTED, cosmos, .003)
        board.parent = root
        frame.parent = root
        words = 'PEOPLE\nPROJECTS\nPLACES\nIDEAS\n\nA BRIGHTER\nME' if side < 0 else 'SAME\nCURIOSITY\nFURTHER\nHORIZONS\n\nTHE JOURNEY\nCONTINUES'
        text('Observatory / wall quote', words, (0, -.035, 7.20), .13, cosmos, MUTED, root, spacing=1.4)
    text('Observatory / journey headline', '  '.join(CONTENT['title'].split()), (0, 10.4, 6.35), .39, timeline, spacing=1.9)
    text('Observatory / journey subtitle', CONTENT['subtitle'], (0, 10.38, 5.92), .14, timeline, MUTED, spacing=1.65)
    lines('Observatory / headline light rule', [((-.52, 10.34, 7.12), (.52, 10.34, 7.12))], WHITE, timeline, .006)
    count = len(CONTENT['milestones'])
    if count < 2:
        raise RuntimeError('Use at least two editable timeline milestones.')
    positions = [milestone(item, math.radians(-64 + index * 128 / (count - 1)), index)
                 for index, item in enumerate(CONTENT['milestones'])]
    path('Observatory / luminous timeline arc', [(8 * math.sin(a), 8 * math.cos(a), .08)
                                               for a in [math.radians(-76 + i * 152 / 160) for i in range(161)]], WHITE, timeline, .005)
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=2.70, depth=.60, location=(0, 0, .30))
    pedestal = bpy.context.object
    pedestal.name = 'Observatory / central globe dais'
    pedestal.data.materials.append(BLACK)
    move_to(pedestal, centre)
    pedestal['central_dais'] = True
    for radius, z, mat in ((2.70, .025, WHITE), (2.70, .61, WHITE), (2.25, .618, TYPE), (2.31, .618, MUTED)):
        circle('Observatory / luminous dais ring', (0, 0, z), radius, mat, centre, .005)
    for i in range(96):
        a = i * math.tau / 96
        lines('Observatory / fine dais fluting', [((2.705 * math.sin(a), 2.705 * math.cos(a), .07),
                                                 (2.705 * math.sin(a), 2.705 * math.cos(a), .56))], WIRE, centre, .0015)
    globe = wire_sphere('Observatory / central rotating geodesic globe', (0, 0, 1.24), .62, TYPE, centre, 2, .003)
    globe['observatory_globe'] = True
    globe.rotation_euler = (.18, .12, 0)
    globe.keyframe_insert(data_path='rotation_euler', index=2, frame=1)
    globe.rotation_euler.z = math.tau
    globe.keyframe_insert(data_path='rotation_euler', index=2, frame=1201)
    for layer in globe.animation_data.action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:
                        key.interpolation = 'LINEAR'
                    curve.modifiers.new('CYCLES')
    text('Observatory / dais inscription', 'S A M E  P E R S O N\nB I G G E R  P O S S I B I L I T I E S',
         (0, -2.715, .39), .075, centre, spacing=1.2)
    p0, p1, p2, p3 = [Vector(p) for p in ((7.20, 3.51, .65), (10.3, 3.2, .75), (7.6, 7.0, 1.8), (11.3, 5.0, 2.2))]
    def future(t):
        return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3
    path('Observatory / rising future trajectory', [future(i / 80) for i in range(81)], MUTED, timeline, .0025)
    for index in range(1, 17):
        t = index / 17
        orb = wire_sphere('Observatory / future constellation node', future(t), .065 * (1 - t) + .018,
                          WHITE, timeline, 1, .002)
        orb['future_node'] = True
    label = bpy.data.objects.new('Observatory / further-ahead label', None)
    timeline.objects.link(label)
    label.location = (11.1, 3.4, 0)
    label.rotation_euler.z = math.atan2(-11.1, 15.0)
    text('Observatory / future caption', 'F U R T H E R\nA H E A D', (0, 0, 2.70), .11, timeline, MUTED, label)
    arrow = lines('Observatory / future arrow', [((-.18, 0, 2.25), (.18, 0, 2.25)),
                                                ((.08, 0, 2.33), (.18, 0, 2.25)), ((.08, 0, 2.17), (.18, 0, 2.25))], TYPE, timeline, .003)
    arrow.parent = label
    for x, body in ((-3.15, 'P A S T'), (0, 'P R E S E N T'), (3.15, 'F U T U R E')):
        text('Observatory / floor era ' + body, body, (x, -3.9, .018), .14, furniture, MUTED, rotation=(0, 0, 0))
    for side in (-1, 1):
        bench = box('Observatory / outlined viewing bench', (side * 5.1, -3.8, .48), (2.60, .9, .12), BLACK, furniture)
        bench.rotation_euler.z = side * .18
        outline(bench, WHITE, furniture, .004)
        for dx in (-1.10, 1.10):
            support = box('Observatory / bench open support',
                          (side * 5.1 + dx * math.cos(side * .18), -3.8 + dx * math.sin(side * .18), .23),
                          (.08, .78, .42), BLACK, furniture)
            support.rotation_euler.z = side * .18
            outline(support, MUTED, furniture, .003)
    for position in ((-5, -3, 7.8), (5, -3, 7.8), (-5, 5, 7.8), (5, 5, 7.8)):
        data = bpy.data.lights.new('Observatory / subtle ceiling bounce', 'AREA')
        data.energy = 12
        data.size = 4
        obj = bpy.data.objects.new(data.name, data)
        cameras.objects.link(obj)
        obj.location = position
    for name, eye, target, lens in (
        ('Main gallery', (0, -11.6, 3.7), (0, 3.0, 2.95), 20.5),
        ('Globe detail', (4.4, -7.0, 2.5), (0, 0, 1.20), 30),
        ('Star oculus', (0, -1.5, 2.5), (0, 8, 19.5), 18),
        ('Space window', (-9.0, 2.8, 3.9), (-18.55, 14.46, 5.46), 21),
        ('Interface floor', (-3.8, -9.6, 6.2), (0, -5.9, 0), 27),
    ):
        data = bpy.data.cameras.new('Timeline Observatory / ' + name)
        data.lens = lens
        data.clip_start = .05
        data.clip_end = 100
        camera = bpy.data.objects.new(data.name, data)
        cameras.objects.link(camera)
        camera.location = eye
        camera.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat('-Z', 'Y').to_euler()
    scene.camera = scene.objects['Timeline Observatory / Main gallery']
    guided_layout = create_guided_walk(cameras, positions)
    detail_data = bpy.data.cameras.new('Timeline Observatory / Node detail')
    detail_data.lens = 20.5
    detail = bpy.data.objects.new(detail_data.name, detail_data)
    cameras.objects.link(detail)
    detail.location = Vector(guided_layout['stations'][0]['viewPosition']) + Vector((0, 0, 2.45))
    detail.rotation_euler = (Vector(positions[0]['position']) + Vector((0, 0, 2.75)) - detail.location).to_track_quat('-Z', 'Y').to_euler()
    scene.world = bpy.data.worlds.new('Observatory / empty black cosmos')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value = (.002, .002, .002, 1)
    scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value = .1
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = .035
    scene.cycles.max_bounces = 6
    scene.cycles.diffuse_bounces = 2
    scene.cycles.glossy_bounces = 4
    scene.cycles.transparent_max_bounces = 16
    scene.render.resolution_x = 1360
    scene.render.resolution_y = 780
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    transforms = scene.view_settings.bl_rna.properties['view_transform'].enum_items.keys()
    scene.view_settings.view_transform = 'AgX' if 'AgX' in transforms else 'Standard'
    scene.render.fps = 30
    scene.frame_start, scene.frame_end = 1, guided_layout['periodFrames']
    scene.frame_set(1)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces.active.region_3d.view_perspective = 'CAMERA'
                area.spaces.active.shading.type = 'MATERIAL'
                area.spaces.active.lock_camera = False
    bpy.ops.object.select_all(action='DESELECT')
    scene.camera.select_set(True)
    bpy.context.view_layer.objects.active = scene.camera
    bpy.context.preferences.filepaths.save_version = 0
    scene.render.filepath = str(OUT / 'timeline-observatory-preview.png')
    bpy.ops.wm.save_as_mainfile(filepath=str(MODEL), compress=True)
    (OUT / 'observatory-layout.json').write_text(json.dumps({
        'model': MODEL.name, 'roomRadiusMeters': RADIUS, 'heightMeters': HEIGHT, 'npcCount': 0,
        'milestones': positions, 'mainCamera': 'Timeline Observatory / Main gallery',
        'defaultCamera': scene.camera.name, 'guidedWalk': guided_layout, 'oculusRadiusMeters': 6.6,
        'globeLoopFrames': 1200, 'coordinateSystem': 'Blender Z-up',
        'windows': window_specs, 'exteriorPlanets': planet_specs, 'wallPillars': pillar_specs, 'interfaceFloor': floor_specs,
        'wallDesign': 'Solid satin-black panels / recessed white LEDs / smooth ceiling fascia',
    }, indent=2) + '\n')
    print('TIMELINE OBSERVATORY BUILT:', json.dumps({'milestones': count, 'npcs': 0, 'objects': len(scene.objects)}))


def render_previews():
    original = scene.camera
    views = [('Main gallery', 'timeline-observatory-preview.png')]
    if '--all-previews' in sys.argv:
        views.extend([('Globe detail', 'timeline-observatory-globe.png'), ('Star oculus', 'timeline-observatory-oculus.png'),
                      ('Node detail', 'timeline-observatory-node.png'), ('Space window', 'timeline-observatory-window.png'),
                      ('Interface floor', 'timeline-observatory-floor.png')])
    if '--node-preview' in sys.argv:
        views = [('Node detail', 'timeline-observatory-node.png')]
    if '--window-preview' in sys.argv:
        views = [('Space window', 'timeline-observatory-window.png')]
    if '--floor-preview' in sys.argv:
        views = [('Interface floor', 'timeline-observatory-floor.png')]
    for name, filename in views:
        scene.camera = scene.objects['Timeline Observatory / ' + name]
        scene.render.filepath = str(OUT / filename)
        bpy.ops.render.render(write_still=True)
    scene.camera = original


if __name__ == '__main__':
    if '--preview-only' in sys.argv:
        bpy.ops.wm.open_mainfile(filepath=str(MODEL))
        scene = bpy.context.scene
    else:
        build()
    if '--no-render' not in sys.argv:
        render_previews()
