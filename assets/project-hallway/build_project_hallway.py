"""Build a standalone, editable monochrome exhibition from the city NPC master.

blender --background --python-exit-code 1 --python assets/project-hallway/build_project_hallway.py
Add -- --no-render to only rebuild the model, or -- --preview-only to render it.
"""
import json
import hashlib
import math
from array import array
from pathlib import Path
import random
import runpy
import sys

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'assets/project-hallway'
MASTER = ROOT / 'assets/cyber-city/monochrome-city-solid-tower.blend'
MODEL = OUT / 'project-hallway.blend'
sys.path.insert(0, str(OUT))
from board_orientation import orient_project_board, stabilize_projector
from hallway_layout import WIDTH, FLOOR_WIDTH, BOARD_X, BAY_SPACING, RIGHT_STAGGER, PROJECT_START, BENCH_X, category_layout as shared_category_layout
if '--preview-only' not in sys.argv and '--ceiling-only' not in sys.argv and '--layout-only' not in sys.argv:
    runpy.run_path(str(OUT / 'build_project_catalogue.py'), run_name='__main__')
CONTENT = json.loads((OUT / 'projects.json').read_text())
PROJECTS = CONTENT['projects']
CATEGORIES = CONTENT['categories']
RNG = random.Random(2812)


def category_layout():
    return shared_category_layout(PROJECTS, CATEGORIES)


def action_curves(action):
    return [curve for layer in action.layers for strip in layer.strips
            for bag in strip.channelbags for curve in bag.fcurves]


def cycle_animation(action):
    for curve in action_curves(action):
        for key in curve.keyframe_points:
            key.interpolation = 'BEZIER'
            key.handle_left_type = key.handle_right_type = 'AUTO_CLAMPED'
        curve.modifiers.new('CYCLES')


def animate_person(npc, rig, placement, index):
    """Native shape-key and transform loops; no handlers or playback scripts."""
    coords = [v.co.copy() for v in npc.data.vertices]
    npc.shape_key_add(name='Basis')
    walking = 'route' in placement
    period = 300 if walking else (120, 150, 200)[index % 3]
    phase = index * .71
    npc['animation_period'] = period
    rig['npc_animation'] = 'walking_loop' if walking else 'interaction_loop'
    rig['loop_frames'] = period

    def add_shape(name, deform):
        key = npc.shape_key_add(name=name)
        for point, original in zip(key.data, coords):
            point.co = deform(original.copy())
        return key

    def head(v, tilt=0, turn=0):
        neck = Vector((0, 0, 1.66))
        weight = min(1, max(0, (v.z - 1.59) / .15))
        return neck + Matrix.Rotation(turn * weight, 4, 'Z') @ Matrix.Rotation(tilt * weight, 4, 'X') @ (v - neck)

    if walking:
        keys = []
        for sign, name in ((1, 'Stride / left'), (-1, 'Stride / right')):
            def gait(v, sign=sign):
                side = 1 if v.x >= 0 else -1
                leg = max(0, min(1, (1.0 - v.z) / .85))
                arm = min(1, max(0, (abs(v.x) - .19) / .15)) * min(1, max(0, (v.z - .85) / .30))
                swing = sign * side
                v.y += swing * leg * .30 - swing * arm * .16
                v.z += .018 * min(1, max(0, v.z / .4))
                return v
            keys.append(add_shape(name, gait))
        for side, name in ((1, 'Foot clearance / right'), (-1, 'Foot clearance / left')):
            def lift(v, side=side):
                if (v.x >= 0) == (side > 0):
                    leg = max(0, min(1, (.95 - v.z) / .80))
                    v.z += .095 * leg
                return v
            keys.append(add_shape(name, lift))
        route = placement['route']
        center = Vector((*route['center'], .02))
        rx, ry = route['radius']
        path = [Vector((rx * math.cos(step * math.tau / 240 + route.get('phase', 0)),
                        ry * math.sin(step * math.tau / 240 + route.get('phase', 0)))) for step in range(241)]
        distances = [0.0]
        for a, b in zip(path, path[1:]):
            distances.append(distances[-1] + (b - a).length)
        strides = max(1, round(distances[-1] / 1.2))
        for step, distance in enumerate(distances):
            frame = 1 + step * period / 240
            gait_phase = distance / distances[-1] * strides * math.tau + phase
            swing, clearance = math.sin(gait_phase), math.cos(gait_phase)
            # Feet lift during their forward recovery, with alternating stance.
            for key, value in zip(keys, (max(0, swing), max(0, -swing), max(0, -clearance), max(0, clearance))):
                key.value = value
                key.keyframe_insert(data_path='value', frame=frame)
        previous_angle = None
        for step in range(61):
            frame = 1 + step * period / 60
            angle = step * math.tau / 60 + route.get('phase', 0)
            rig.location = center + Vector((rx * math.cos(angle), ry * math.sin(angle), 0))
            facing = math.atan2(-rx * math.sin(angle), -ry * math.cos(angle))
            if previous_angle is not None:
                facing += round((previous_angle - facing) / math.tau) * math.tau
            previous_angle = facing
            rig.rotation_euler.z = facing
            rig.keyframe_insert(data_path='location', frame=frame)
            rig.keyframe_insert(data_path='rotation_euler', frame=frame)
        # Small forward lean follows speed; distance-driven steps slow at turns.
        for step in range(61):
            frame = 1 + step * period / 60
            angle = step * math.tau / 60 + route.get('phase', 0)
            speed = math.hypot(rx * math.sin(angle), ry * math.cos(angle)) / ry
            rig.rotation_euler.x = .015 * speed
            rig.keyframe_insert(data_path='rotation_euler', index=0, frame=frame)
    else:
        def shift(v):
            weight = min(1, max(0, v.z / .95))
            v.x += .070 * weight
            v.z += .018 * weight
            return v
        nod = .09 if placement['activity'] == 'phone' else .15
        glance = .10 if placement['activity'] == 'phone' else .23
        keys = [add_shape('Weight shift', shift), add_shape('Head / acknowledge', lambda v: head(v, tilt=nod)),
                add_shape('Head / glance', lambda v: head(v, turn=glance))]
        if placement['activity'] == 'conversation':
            def gesture(v):
                arm = min(1, max(0, (abs(v.x) - .20) / .13)) * min(1, max(0, (v.z - .85) / .25))
                v.y -= .16 * arm
                v.z += (.22 if placement['pose'] == 'talking' else .13) * arm
                return v
            keys.append(add_shape('Conversation / hand gesture', gesture))
        elif placement['activity'] == 'thinking':
            def thinking(v):
                front = min(1, max(0, (-v.y - .14) / .12))
                hand = front * min(1, max(0, (v.z - 1.0) / .22)) * min(1, max(0, (1.65 - v.z) / .12))
                v.z += .23 * hand
                v.y += .07 * hand
                return head(v, tilt=-.08)
            keys.append(add_shape('Thinking / hand to chin', thinking))
        elif placement['activity'] == 'viewing_display' and index % 2:
            def indicate(v):
                arm = min(1, max(0, (v.x - .18) / .13)) * min(1, max(0, (v.z - .85) / .25))
                v.y -= .18 * arm
                v.z += .22 * arm
                return v
            keys.append(add_shape('Display / indicate detail', indicate))
        for step in range(25):
            frame = 1 + step * period / 24
            angle = step * math.tau / 24 + phase
            values = [.5 + .5 * math.sin(angle), .5 + .5 * math.sin(2 * angle + .6),
                      .5 + .5 * math.sin(angle + 1.2)]
            if len(keys) == 4:
                # Opposite phases let one partner gesture while the other listens.
                offset = 0 if placement['pose'] == 'talking' else math.pi
                values.append((.5 + .5 * math.sin(angle + offset)) ** 2)
            for key, value in zip(keys, values):
                key.value = value
                key.keyframe_insert(data_path='value', frame=frame)
            rig.rotation_euler.z = placement['facing'] + .045 * math.sin(angle)
            rig.keyframe_insert(data_path='rotation_euler', index=2, frame=frame)
    cycle_animation(rig.animation_data.action)
    cycle_animation(npc.data.shape_keys.animation_data.action)


def emission(name, value, strength=1):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    shader = nodes.new('ShaderNodeEmission')
    shader.inputs['Color'].default_value = (value, value, value, 1)
    shader.inputs['Strength'].default_value = strength
    mat.node_tree.links.new(shader.outputs[0], output.inputs['Surface'])
    return mat


def surface(name, value, metallic=0, roughness=.4):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (value, value, value, 1)
    shader.inputs['Metallic'].default_value = metallic
    shader.inputs['Roughness'].default_value = roughness
    return mat


def collection(name):
    col = bpy.data.collections.new(name)
    scene.collection.children.link(col)
    return col


def move_to(obj, col):
    for current in list(obj.users_collection):
        current.objects.unlink(obj)
    col.objects.link(obj)
    return obj


def box(name, center, size, material, col):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    move_to(obj, col)
    return obj


def lines(name, segments, material, col, radius=.006):
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'
    curve.bevel_depth = radius
    curve.bevel_resolution = 0
    curve.resolution_u = 1
    for a, b in segments:
        spline = curve.splines.new('POLY')
        spline.points.add(1)
        spline.points[0].co = (*a, 1)
        spline.points[1].co = (*b, 1)
    obj = bpy.data.objects.new(name, curve)
    col.objects.link(obj)
    curve.materials.append(material)
    return obj


def outline(obj, material, col, radius=.006):
    return lines(obj.name + ' / outline', [
        (obj.matrix_world @ obj.data.vertices[e.vertices[0]].co,
         obj.matrix_world @ obj.data.vertices[e.vertices[1]].co)
        for e in obj.data.edges
    ], material, col, radius)


def gallery_wall(x, length, material, col):
    """Continuous opaque matte-black side wall."""
    wall = box('Gallery / solid black side wall', (x, (length - 10) / 2, 3.1),
               (.18, length + 10, 6.2), material, col)
    wall['hallway_solid_wall'] = True
    return wall


def points(name, vertices, radii, material, col):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], [])
    mesh.update()
    attr = mesh.attributes.new('radius', 'FLOAT', 'POINT')
    attr.data.foreach_set('value', radii)
    obj = bpy.data.objects.new(name, mesh)
    col.objects.link(obj)
    group_name = material.name + ' / shared particle instances'
    existing = bpy.data.node_groups.get(group_name)
    if existing:
        obj.modifiers.new('Native point-cloud particles', 'NODES').node_group = existing
        obj['hallway_render_kind'] = 'points'
        return obj
    group = bpy.data.node_groups.new(group_name, 'GeometryNodeTree')
    group.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    group.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    nodes, links = group.nodes, group.links
    source = nodes.new('NodeGroupInput')
    output = nodes.new('NodeGroupOutput')
    convert = nodes.new('GeometryNodeMeshToPoints')
    attribute = nodes.new('GeometryNodeInputNamedAttribute')
    attribute.data_type = 'FLOAT'
    attribute.inputs['Name'].default_value = 'radius'
    sphere = nodes.new('GeometryNodeMeshIcoSphere')
    sphere.inputs['Radius'].default_value = 1
    sphere.inputs['Subdivisions'].default_value = 1
    set_material = nodes.new('GeometryNodeSetMaterial')
    set_material.inputs['Material'].default_value = material
    instance = nodes.new('GeometryNodeInstanceOnPoints')
    links.new(source.outputs['Geometry'], convert.inputs['Mesh'])
    # Mesh to Points owns the built-in radius attribute: supply the authored
    # radii here so its default .05m does not replace our fine particle sizes.
    links.new(attribute.outputs['Attribute'], convert.inputs['Radius'])
    links.new(convert.outputs['Points'], instance.inputs['Points'])
    links.new(sphere.outputs['Mesh'], set_material.inputs['Geometry'])
    links.new(set_material.outputs['Geometry'], instance.inputs['Instance'])
    links.new(attribute.outputs['Attribute'], instance.inputs['Scale'])
    links.new(instance.outputs['Instances'], output.inputs['Geometry'])
    obj.modifiers.new('Native point-cloud particles', 'NODES').node_group = group
    obj['hallway_render_kind'] = 'points'
    return obj


def text(name, body, local_position, size, parent, material= None):
    data = bpy.data.curves.new(name, 'FONT')
    data.body = body
    data.size = size
    data.space_character = 1.15
    data.space_line = 1.35
    data.extrude = 0
    data.materials.append(material or TYPE)
    obj = bpy.data.objects.new(name, data)
    displays.objects.link(obj)
    obj.parent = parent
    obj.location = local_position
    obj.rotation_euler = (math.pi / 2, 0, 0)
    return obj


def panel(name, x, y, number, title, category, summary, tags, project=None):
    root = bpy.data.objects.new(name, None)
    displays.objects.link(root)
    root.location = (x, y, 0)
    # Local text front is -Y: +90 degrees points east, -90 points west.
    root.rotation_euler.z = math.pi / 2 if x < 0 else -math.pi / 2
    if project:
        orient_project_board(root)
    if not project:
        root['display_facing'] = 'east' if x < 0 else 'west'
    root['hallway_display'] = True
    width, height = (project['video']['width'], project['video']['height']) if project and project.get('video') else (2.05, 3.15)
    bottom = 2.925 - height / 2
    backing = box(name + ' / black display', (0, 0, bottom + height / 2),
                  (width, .07, height), BLACK, displays)
    edge = outline(backing, WHITE, displays, .008)
    backing.parent = root
    edge.parent = root
    # Floating projected card: no physical suspension cables.
    corners = []
    for sign in (-1, 1):
        for z, direction in ((bottom - .05, 1), (bottom + height + .05, -1)):
            px = sign * (width / 2 + .05)
            corners.extend([((px, -.055, z), (px - sign * .2, -.055, z)),
                            ((px, -.055, z), (px, -.055, z + direction * .2))])
    brackets = lines(name + ' / holographic corner brackets', corners, WHITE, displays, .005)
    brackets.parent = root
    text(name + ' / index', number, (-.82, -.045, 4.21), .105, root, MUTED)
    title_obj = text(name + ' / title', title, (-.82, -.046, 3.89), .165, root)
    # Fit long titles to the actual board rather than clipping them.
    bpy.context.view_layer.update()
    if title_obj.dimensions.x > 1.68:
        title_obj.data.size *= 1.68 / title_obj.dimensions.x
    text(name + ' / category', category, (-.82, -.046, 3.25), .085, root, MUTED)
    text(name + ' / summary', summary, (-.82, -.046, 2.93), .106, root)
    text(name + ' / stack', '\n'.join(tags), (-.82, -.046, 2.16), .10, root, MUTED)
    rules = lines(name + ' / typography rules', [
        ((-.82, -.048, 3.39), (-.51, -.048, 3.39)),
        ((-.82, -.048, 1.59), (-.60, -.048, 1.59)),
    ], WHITE, displays, .005)
    rules.parent = root
    text(name + ' / projection label', 'LIVE / HOLOGRAPHIC PROJECTION',
         (-.82, -.047, 1.72), .055, root, MUTED)
    projector(name, root, width, bottom, height, project['id'] if project else name)
    if project:
        stabilize_projector(root)
    if project:
        root['project_id'] = project['id']
        root['project_url'] = project.get('url') or ''
        root['project_section'] = project['section']
        root['project_metadata'] = json.dumps(project)
        if project.get('video'):
            for child in root.children:
                if child.type == 'FONT' or child.name.endswith(' / typography rules'):
                    child.hide_render = True
    return root


def category_gate(category, architecture, particle_material):
    """Open holographic portal: frosted glow, fine hanging filaments and dust."""
    root = bpy.data.objects.new(f'Category {category["number"]:02d} / {category["title"]}', None)
    architecture.objects.link(root)
    root.location = (0, category['door']['y'], 0)
    root['hallway_category_gate'] = category['id']
    light = emission(f'Category {category["number"]:02d} / luminous doorway', .8, 3.2)
    metal = surface(f'Category {category["number"]:02d} / satin portal framing', .024, .65, .28)
    filament = emission(f'Category {category["number"]:02d} / fine holographic filaments', .18)
    haze = bpy.data.materials.new(f'Category {category["number"]:02d} / transparent light veil')
    haze.use_nodes = True
    nodes, links = haze.node_tree.nodes, haze.node_tree.links
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    transparent = nodes.new('ShaderNodeBsdfTransparent')
    glow = nodes.new('ShaderNodeEmission')
    glow.inputs['Color'].default_value = (.35,.35,.35,1)
    mix = nodes.new('ShaderNodeMixShader')
    mix.inputs[0].default_value = .035
    links.new(transparent.outputs[0],mix.inputs[1]);links.new(glow.outputs[0],mix.inputs[2])
    links.new(mix.outputs[0],output.inputs['Surface'])
    rng = random.Random(8100 + category['number'])

    def tag(obj, role):
        obj.parent = root
        obj['hallway_category_id'] = category['id']
        obj['hallway_category_role'] = role
        return obj

    for x in (-(2+WIDTH/2)/2, (2+WIDTH/2)/2):
        tag(box('Category / black partition', (x,0,3.1), (WIDTH/2-2,.24,6.2), BLACK, architecture), 'categoryFrame')
    tag(box('Category / dark header', (0,0,5.75), (4,.24,.9), BLACK, architecture), 'categoryFrame')
    for x in (-1.98,1.98):
        tag(box('Category / satin jamb', (x,.04,2.65), (.10,.56,5.30), metal, architecture), 'categoryFrame')
        for y in (-.25,.25):
            tag(lines('Category / luminous vertical rail', [((x,y,.13),(x,y,5.22))], light, architecture, .009), 'categoryFrame')
    for z in (.055,5.345):
        tag(box('Category / satin threshold cap', (0,.04,z), (4.2,.70,.13), metal, architecture), 'categoryFrame')
        for y in (-.29,.31):
            tag(lines('Category / luminous horizontal rail', [((-1.98,y,z+(.08 if z<1 else -.08)),(1.98,y,z+(.08 if z<1 else -.08)))], light, architecture, .009), 'categoryFrame')
    for depth, inset in ((-.23,0),(.30,.06),(.85,.15)):
        x = 1.83-inset
        tag(lines('Category / transparent tunnel contours', [((-x,depth,.14),(-x,depth,5.18)),
                 ((x,depth,.14),(x,depth,5.18)),((-x,depth,.14),(x,depth,.14)),
                 ((-x,depth,5.18),(x,depth,5.18))], MUTED if depth<0 else WIRE, architecture,.002), 'categoryFrame')
    veil = box('Category / translucent holographic veil', (0,.04,2.65), (3.66,.008,5.10), haze, architecture)
    veil.visible_shadow = False
    tag(veil,'categoryCurtain')
    smoke = emission(f'Category {category["number"]:02d} / smoked transparent depth', 0)
    nodes, links = smoke.node_tree.nodes, smoke.node_tree.links
    transparent = nodes.new('ShaderNodeBsdfTransparent')
    mix = nodes.new('ShaderNodeMixShader')
    mix.inputs[0].default_value = .84
    glow = next(node for node in nodes if node.type=='EMISSION')
    links.new(transparent.outputs[0],mix.inputs[1]);links.new(glow.outputs[0],mix.inputs[2])
    links.new(mix.outputs[0],next(node for node in nodes if node.type=='OUTPUT_MATERIAL').inputs['Surface'])
    mesh = bpy.data.meshes.new('Category / smoked light-depth screen')
    mesh.from_pydata([(-1.83,.09,.10),(1.83,.09,.10),(1.83,.09,5.20),(-1.83,.09,5.20)],[],[(0,1,2,3)])
    mesh.materials.append(smoke)
    depth_screen = bpy.data.objects.new(mesh.name,mesh)
    architecture.objects.link(depth_screen)
    depth_screen.visible_shadow = False
    tag(depth_screen,'categoryCurtain')
    strands, vertices, radii = [], [], []
    for index in range(63):
        x = -1.78 + index*3.56/62
        finish = rng.uniform(.14,1.05)
        strand = [(x,.025,5.20),(x+rng.uniform(-.012,.012),.016,3.8),
                  (x+rng.uniform(-.014,.014),.02,finish)]
        strands.extend(zip(strand,strand[1:]))
        for step in range(83):
            z = .16 + step*.061
            # Keep the center quiet enough for the lettering; dense dust at jambs.
            if abs(x)<1.15 and rng.random()<.85:
                continue
            vertices.append((x+rng.uniform(-.008,.008),rng.uniform(-.06,.09),z))
            radii.append(rng.uniform(.0015,.0045))
    tag(lines('Category / fine hanging filaments', strands, filament, architecture,.001), 'categoryCurtain')
    tag(points('Category / floating holographic dust', vertices, radii, particle_material, architecture),'categoryCurtain')
    brackets = []
    for side in (-1,1):
        x = side*1.62
        brackets.extend([((x,-.075,4.30),(x-side*.30,-.075,4.30)),
                         ((x,-.075,4.30),(x,-.075,3.95)),
                         ((x,-.075,.38),(x-side*.30,-.075,.38))])
    tag(lines('Category / floating corner brackets',brackets,MUTED,architecture,.002),'categoryFrame')
    for name, body, z, size, material in (
        ('number', f'C A T E G O R Y  {category["number"]:02d}', 3.10, .17, TYPE),
        ('entry', 'E N T E R  /  P R O J E C T S', 2.70, .075, MUTED),
    ):
        label = text('Category / ' + name, body, (0,-.065,z), size, root, material)
        label.data.align_x = 'CENTER'
        tag(label, 'categoryDoorLabel')
    tag(lines('Category / title rules', [((-.35,-.068,3.65),(.35,-.068,3.65)),
                                        ((-.35,-.068,2.25),(.35,-.068,2.25))], MUTED, architecture, .003), 'categoryDoorLabel')


def projector(name, parent, width, bottom, height, identity):
    unit = bpy.data.objects.new(name + ' / projector assembly', None)
    projectors.objects.link(unit)
    unit.parent = parent
    unit['holographic_projector'] = True
    unit['display_id'] = identity
    for label, center, dimensions in (
        ('floor anchor', (0, -.45, .06), (.82, .88, .10)),
        ('emitter housing', (0, -.45, .27), (.56, .62, .34)),
        ('optical head', (0, -.45, .47), (.43, .49, .07)),
    ):
        part = box(name + ' / ' + label, center, dimensions, BLACK, projectors)
        contour = outline(part, MUTED if label == 'emitter housing' else WHITE, projectors, .003)
        part.parent = unit
        # The source geometry is local to the display; inherit its full transform.
        contour.parent = unit
    origin = Vector((0, -.45, .535))
    direction = (Vector((0, -.045, bottom + height / 2)) - origin).normalized()
    tangent = Vector((1, 0, 0))
    bitangent = direction.cross(tangent).normalized()
    for radius in (.09, .15):
        ring = [origin + radius * (math.cos(i * math.tau / 32) * tangent
                                  + math.sin(i * math.tau / 32) * bitangent) for i in range(32)]
        lens = lines(name + ' / concentric luminous lens', list(zip(ring, ring[1:] + ring[:1])),
                     WHITE, projectors, .004)
        lens.parent = unit
    text(name + ' / emitter identifier', 'HOLO / ' + identity[:18].upper(),
         (-.22, -.765, .29), .037, parent, MUTED)
    target_corners = [Vector((-width / 2, -.06, bottom)), Vector((width / 2, -.06, bottom)),
                      Vector((width / 2, -.06, bottom + height)), Vector((-width / 2, -.06, bottom + height))]
    ray = lines(name + ' / projection frustum rays', [(origin, corner) for corner in target_corners],
                BEAM_EDGE, projectors, .0015)
    ray.parent = unit
    mesh = bpy.data.meshes.new(name + ' / subtle projected light field')
    mesh.from_pydata([origin, *target_corners], [], [(0, i + 1, (i + 1) % 4 + 1) for i in range(4)])
    mesh.materials.append(BEAM)
    field = bpy.data.objects.new(mesh.name, mesh)
    projectors.objects.link(field)
    field.parent = unit
    field.visible_shadow = False


def build_ceiling(length, column_positions):
    """Continuous sculpted S-wave louvers with selected integrated light strips."""
    roof = collection('09 / Monochrome circuit ceiling')
    rail = emission('Ceiling / white light rails', .85, 2.2)
    underside = surface('Ceiling / charcoal rib undersides', .018, .30, .38)
    sides = surface('Ceiling / shadowed rib sides', .0075, .22, .45)
    bevel = surface('Ceiling / quiet bevel highlights', .028, .35, .32)
    backing = surface('Ceiling / black recessed backing', .0035, .05, .72)
    starts, finish = -10, length
    width_ratio = WIDTH / 10.2
    samples = math.ceil((finish - starts) / .40)
    ys = [starts + (finish - starts) * index / samples for index in range(samples + 1)]
    wave = math.tau / 18

    def center(y, u):
        envelope = 1 - (u / 4.8) ** 2
        bend = 1.10 * math.sin((y + 4) * wave) + .25 * math.sin((y + 4) * wave * .43 + 1.1)
        slope = envelope * (1.10 * wave * math.cos((y + 4) * wave)
                            + .25 * wave * .43 * math.cos((y + 4) * wave * .43 + 1.1))
        height = .20 + .09 * (.5 + .5 * math.sin((y + 4) * wave + u * .32))
        return u + envelope * bend, slope, height

    cap = box('Ceiling / continuous black backing', (0, (starts + finish) / 2, 6.235),
              (9.65 * width_ratio, finish - starts, .05), backing, roof)
    cap['ceiling_role'] = 'backing'
    lit_ribs = {4, 12, 20, 28, 36}
    for index in range(41):
        u = -4.72 + index * 9.44 / 40
        vertices, faces, light_path = [], [], []
        for y in ys:
            x, slope, height = center(y, u)
            axis = Vector((1, -slope, 0)).normalized()
            profile = [(-.0425, 0), (-.0425, -height + .018), (-.029, -height),
                       (.029, -height), (.0425, -height + .018), (.0425, 0)]
            for lateral, z in profile:
                vertices.append(((x + axis.x * lateral) * width_ratio, y + axis.y * lateral, 6.18 + z))
            light_path.append((x * width_ratio, y, 6.18 - height - .012))
        for station in range(samples):
            for side in range(6):
                a, b = station * 6 + side, station * 6 + (side + 1) % 6
                faces.append((a, a + 6, b + 6, b))
        faces.extend([tuple(reversed(range(6))), tuple(samples * 6 + side for side in range(6))])
        mesh = bpy.data.meshes.new(f'Ceiling / flowing rib {index:02d}')
        mesh.from_pydata(vertices, [], faces);mesh.update()
        for mat in [underside, sides, bevel, backing]:
            mesh.materials.append(mat)
        for polygon in mesh.polygons:
            polygon.material_index = [1, 2, 0, 2, 1, 3][polygon.index % 6] if polygon.index < samples * 6 else 1
        rib = bpy.data.objects.new(f'Ceiling / flowing rib {index:02d}', mesh)
        roof.objects.link(rib);rib['ceiling_role'] = 'wave_rib';rib['ceiling_rib_index'] = index
        if index in lit_ribs:
            strip = lines(f'Ceiling / curved integrated light {index:02d}', list(zip(light_path, light_path[1:])), rail, roof, .014)
            strip['ceiling_role'] = 'light_rail';strip['ceiling_path'] = 'curved'
    for side in [-1, 1]:
        box('Ceiling / dark perimeter fascia', (side * 4.97 * width_ratio, (starts + finish) / 2, 6.11),
            (.20 * width_ratio, finish - starts, .20), backing, roof)['ceiling_role'] = 'perimeter'
        strip = lines('Ceiling / continuous perimeter light', [((side * 4.84 * width_ratio, starts, 5.996),
                                                               (side * 4.84 * width_ratio, finish, 5.996))], rail, roof, .012)
        strip['ceiling_role'] = 'light_rail';strip['ceiling_path'] = 'perimeter'
    scene['ceiling_style'] = 'Flowing S-wave charcoal ribs / curved integrated white strips / quiet perimeter lights'
    scene['ceiling_light_count'] = 0
    return {'style': 'flowing wave ribs', 'recessedLights': [], 'ribCount': 41, 'curvedLightRails': 5,
            'perimeterLightRails': 2, 'wavePeriodMeters': 18, 'palette': 'black and white',
            'longitudinalLightRails': 7, 'ceilingHeightMeters': 6.2, 'minimumLightHeightMeters': 5.878,
            'plainPanels': 0, 'squareJunctions': 0, 'surfaceGrid': False, 'ceilingDots': False}


def room_fingerprint(excluded):
    """Guard authored room geometry, transforms, text and motion outside the roof."""
    digest = hashlib.sha256()
    for obj in sorted((o for o in scene.objects if o not in excluded), key=lambda o: o.name):
        digest.update(repr((obj.name, obj.type, obj.parent.name if obj.parent else None,
                            list(obj.location), list(obj.rotation_euler), list(obj.rotation_quaternion),
                            list(obj.scale), dict(obj.items()))).encode())
        if obj.type == 'MESH':
            coords = array('f', (value for v in obj.data.vertices for value in v.co))
            digest.update(coords.tobytes())
            if obj.data.shape_keys:
                for key in obj.data.shape_keys.key_blocks:
                    digest.update(array('f', (value for v in key.data for value in v.co)).tobytes())
        elif obj.type == 'FONT':
            digest.update(obj.data.body.encode())
        if obj.animation_data and obj.animation_data.action:
            for curve in action_curves(obj.animation_data.action):
                digest.update(repr((curve.data_path, curve.array_index,
                                    [(tuple(k.co), k.interpolation) for k in curve.keyframe_points])).encode())
    return digest.hexdigest()


def refresh_ceiling():
    """Replace only the roof collection in the existing authored master."""
    global scene
    bpy.ops.wm.open_mainfile(filepath=str(MODEL))
    scene = bpy.context.scene
    scene.view_layers[0].update()
    old = bpy.data.collections['09 / Monochrome circuit ceiling']
    before = room_fingerprint(set(old.objects))
    active_name = bpy.context.view_layer.objects.active.name if bpy.context.view_layer.objects.active else None
    selected = [o.name for o in bpy.context.selected_objects if o not in old.objects[:]]
    for obj in list(old.objects):
        data = obj.data
        if len(obj.users_collection) > 1:
            old.objects.unlink(obj)
        else:
            bpy.data.objects.remove(obj, do_unlink=True)
            if data and data.users == 0:
                if isinstance(data, bpy.types.Mesh):
                    bpy.data.meshes.remove(data)
                elif isinstance(data, bpy.types.Curve):
                    bpy.data.curves.remove(data)
    bpy.data.collections.remove(old)
    for group in list(bpy.data.node_groups):
        if group.name.startswith('Ceiling /') and group.users == 0:
            bpy.data.node_groups.remove(group)
    for mat in list(bpy.data.materials):
        if mat.name.startswith('Ceiling /') and mat.users == 0:
            bpy.data.materials.remove(mat)
    positions = set()
    for obj in scene.objects:
        if obj.get('dotted_pillar'):
            ys = [(obj.matrix_world @ v.co).y for v in obj.data.vertices]
            positions.add(round((min(ys) + max(ys)) / 2, 4))
    assert positions, 'No authored hallway pillars found.'
    ceiling = build_ceiling(float(scene['hallway_length_m']), sorted(positions))
    scene.view_layers[0].update()
    after = room_fingerprint(set(bpy.data.collections['09 / Monochrome circuit ceiling'].objects))
    assert before == after, 'Unexpected change outside the ceiling; master not saved.'
    bpy.ops.object.select_all(action='DESELECT')
    for name in selected:
        scene.objects[name].select_set(True)
    if active_name and active_name in scene.objects:
        bpy.context.view_layer.objects.active = scene.objects[active_name]
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(MODEL), compress=True)
    layout = json.loads((OUT / 'hallway-layout.json').read_text())
    layout['ceiling'] = ceiling
    (OUT / 'hallway-layout.json').write_text(json.dumps(layout, indent=2) + '\n')
    (OUT / 'ceiling-refresh.json').write_text(json.dumps({'nonCeilingFingerprint': after,
        'authoredRoomPreserved': True, 'ceiling': ceiling}, indent=2) + '\n')
    print('CEILING REFRESHED:', json.dumps(ceiling))


def build():
    global scene, displays, projectors, BLACK, WHITE, WIRE, TYPE, MUTED, BEAM, BEAM_EDGE
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.name = 'PROJECT HALLWAY / Monochrome Exhibition'
    scene.unit_settings.system = 'METRIC'
    architecture = collection('01 / Architecture')
    structure = collection('02 / Wireframe and particle columns')
    displays = collection('03 / Project displays / editable typography')
    furniture = collection('04 / Gallery benches')
    crowd_col = collection('05 / City-reference NPCs')
    cameras = collection('06 / Cameras and lighting')
    projectors = collection('08 / Holographic projectors and light fields')
    BLACK = surface('Hallway / charcoal display faces', .006, .15, .32)
    WALL = surface('Hallway / matte black architecture', .0065, 0, .92)
    FLOOR = surface('Hallway / polished obsidian floor', .012, .82, .12)
    WHITE = emission('Hallway / bright edge accents', .8, 1.5)
    WIRE = emission('Hallway / fine structural wires', .055)
    TYPE = emission('Hallway / white typography', .75)
    MUTED = emission('Hallway / secondary typography', .4)
    DOT = emission('Hallway / column particles', .5)
    BASE_DOT = emission('Hallway / extra bright ground particles', 1, 3.5)
    PERSON = emission('Hallway / city NPC particles', .9, 1.4)
    BEAM_EDGE = emission('Hallway / faint projection rays', .085)
    BEAM = bpy.data.materials.new('Hallway / transparent projected light field')
    BEAM.use_nodes = True
    nodes, links = BEAM.node_tree.nodes, BEAM.node_tree.links
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    transparent = nodes.new('ShaderNodeBsdfTransparent')
    glow = nodes.new('ShaderNodeEmission')
    glow.inputs['Color'].default_value = (.18, .18, .18, 1)
    glow.inputs['Strength'].default_value = 1
    mix = nodes.new('ShaderNodeMixShader')
    mix.inputs[0].default_value = .045
    links.new(transparent.outputs[0], mix.inputs[1])
    links.new(glow.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], output.inputs['Surface'])
    sections, bookmarks, length = category_layout()
    scene['reference_style'] = 'Dark gallery / solid matte black walls / luminous project cards'
    scene['npc_design_reference'] = str(MASTER.relative_to(ROOT))
    scene['project_source'] = 'docs/project-catalogue.md / approved reviewed catalogue'
    scene['project_count'] = len(PROJECTS)
    scene['hallway_length_m'] = length
    scene['hallway_width_m'] = WIDTH
    scene['project_bay_spacing_m'] = BAY_SPACING
    scene['pillar_width_m'] = 1.1
    window_layout = []
    box('Polished reflective floor', (0, length / 2 - 6, -.13), (FLOOR_WIDTH, length + 12, .24), FLOOR, architecture)
    column_positions = [-2 + bay * BAY_SPACING for bay in range(math.ceil((length + 2) / BAY_SPACING))
                        if -2 + bay * BAY_SPACING < length]
    for x in (-WIDTH / 2, WIDTH / 2):
        gallery_wall(x, length, WALL, architecture)
    scene['window_count'] = len(window_layout)
    box('Dark ceiling', (0, length / 2 - 3, 6.3), (FLOOR_WIDTH, length + 6, .16), WALL, architecture)
    box('Gallery end wall', (0, length, 3.1), (FLOOR_WIDTH, .16, 6.2), WALL, architecture)
    grid = []
    for x in (-(WIDTH/2-.1), -(WIDTH/2-.1)/2, 0, (WIDTH/2-.1)/2, WIDTH/2-.1):
        grid.append(((x, -10, .004), (x, length, .004)))
    for index in range(math.ceil((length + 10) / BAY_SPACING) + 1):
        y = -10 + index * BAY_SPACING
        if y > length:
            continue
        grid.append(((-(WIDTH/2-.1), y, .004), (WIDTH/2-.1, y, .004)))
    for z in (.1, 1.05, 5.15, 6.15):
        for x in (-(WIDTH/2-.1), WIDTH/2-.1):
            grid.append(((x, -8, z), (x, length, z)))
    lines('Perspective / floor ceiling and wall grids', grid, WIRE, structure, .0015)
    for bay, y in enumerate(column_positions):
        for x in (-(WIDTH/2-.65), WIDTH/2-.65):
            vertices, radii, base_vertices, base_radii = [], [], [], []
            for z_step in range(89):
                z = .025 + z_step * .07
                for j in range(11):
                    t = -.525 + j * .105
                    target_vertices, target_radii = (base_vertices, base_radii) if z_step < 4 else (vertices, radii)
                    target_vertices.extend([(x + t, y - .55, z), (x + t, y + .55, z),
                                            (x - .55, y + t, z), (x + .55, y + t, z)])
                    target_radii.extend([RNG.uniform(.005, .0085)] * 4)
            pillar = points(f'Column {bay:02d} / {x:+} / pure dot structure', vertices, radii, DOT, structure)
            pillar['dotted_pillar'] = True
            for ix in range(11):
                for iy in range(11):
                    base_vertices.append((x - .525 + ix * .105, y - .525 + iy * .105, .021))
                    base_radii.append(.008)
            base = points(f'Column {bay:02d} / {x:+} / bright dotted ground',
                          base_vertices, base_radii, BASE_DOT, structure)
            base['dotted_pillar_base'] = True
        for x in (-(WIDTH/2-.85), WIDTH/2-.85):
            lines(f'Floor / light strip {bay:02d} {x:+}', [((x, y, .035), (x, y + .7, .035))], WHITE, structure, .009)
    ceiling_layout = build_ceiling(length, column_positions)
    panel('Entry / projects directory', -3.15, -.2, '01 / DAMIEN', 'P R O J E C T S', 'THE PROJECT HALLWAY',
          'Client / real world\nAcademic assignments\nPersonal projects', [f'{len(PROJECTS)} curated projects', 'Walk forward to explore'])
    import importlib.util
    directory_spec=importlib.util.spec_from_file_location('hallway_directory',OUT/'directory_board.py')
    directory_module=importlib.util.module_from_spec(directory_spec);directory_spec.loader.exec_module(directory_module)
    directory_module.configure_directory_board(scene)
    for section in sections[1:]:
        category_gate(section, architecture, DOT)
    title_spec=importlib.util.spec_from_file_location('hallway_category_titles',OUT/'category_titles.py')
    title_module=importlib.util.module_from_spec(title_spec);title_spec.loader.exec_module(title_module)
    title_module.refresh_category_titles(scene)
    number_spec=importlib.util.spec_from_file_location('hallway_wall_numbers',OUT/'category_wall_numbers.py')
    number_module=importlib.util.module_from_spec(number_spec);number_spec.loader.exec_module(number_module)
    number_module.configure_category_wall_numbers(scene)
    for index, project in enumerate(PROJECTS):
        bookmark = next(bookmark for bookmark in bookmarks if bookmark['id'] == project['id'])
        x, y, _ = bookmark['position']
        panel(f'Project {index + 1:02d} / {project["id"]}', x, y,
              f'{index + 1:02d} / ' + ('FEATURED FYP' if project.get('featured') else 'PROJECT'), project['title'], project['category'],
              project['summary'], project['tags'], project)
    bench_positions = [section['displayStartY'] + index * BAY_SPACING * 2 + BAY_SPACING / 2
                       for section in sections for index in range(math.ceil(math.ceil(len(section['projectIds']) / 2) / 2))]
    for index, y in enumerate(bench_positions):
        for x in (-BENCH_X, BENCH_X):
            bench_y = y + (RIGHT_STAGGER if x > 0 else 0)
            bench = box(f'Bench {index:02d} / {x:+}', (x, bench_y, .55), (1.15, 2.55, .10), BLACK, furniture)
            outline(bench, WHITE, furniture, .004)
            for dy in (-1.08, 1.08):
                leg = box('Bench / open support', (x, bench_y + dy, .28), (1.10, .05, .50), BLACK, furniture)
                outline(leg, WIRE, furniture, .004)
    # Load only a read-only scene copy, then extract original city cloud vertices.
    with bpy.data.libraries.load(str(MASTER), link=False) as (available, loaded):
        loaded.scenes = ['MONO / Wire & Particle City']
    reference = loaded.scenes[0]
    reference.frame_set(1)
    source = next(o for o in reference.objects if o.type == 'MESH' and 'person_metadata' in o and 'person_id' in o.data.attributes)
    people = json.loads(source['person_metadata'])
    ids = source.data.attributes['person_id'].data
    by_id = {}
    for vertex, identity in zip(source.data.vertices, ids):
        by_id.setdefault(identity.value, []).append(source.matrix_world @ vertex.co)
    for walker in reference.objects:
        if walker.get('city_role') != 'walking_npc':
            continue
        person = json.loads(walker['person_metadata'])
        body_meshes = [o for o in walker.children_recursive if o.type == 'MESH'
                       and 'radius' in o.data.attributes and not o.data.edges]
        if body_meshes:
            people.append(person)
            # Appended scene depsgraph transforms may be stale. Walker bodies
            # are authored in rig-local coordinates; place them from metadata.
            source_transform = (Matrix.Translation(Vector(person['base']))
                                @ Matrix.Rotation(person['facing'], 4, 'Z')
                                @ Matrix.Scale(person.get('scale', 1), 4))
            by_id[person['id']] = [source_transform @ o.matrix_basis @ vertex.co
                                  for o in body_meshes for vertex in o.data.vertices]
    placements = [
        {'position': [-1.85, 14.0], 'target': [-3.05, 14.7, 1.7], 'pose': 'talking', 'activity': 'conversation', 'group': 'conversation-left'},
        {'position': [-3.05, 14.7], 'target': [-1.85, 14.0, 1.7], 'pose': 'listening', 'activity': 'conversation', 'group': 'conversation-left'},
        {'position': [1.85, 55.0], 'target': [3.05, 55.7, 1.7], 'pose': 'talking', 'activity': 'conversation', 'group': 'conversation-right'},
        {'position': [3.05, 55.7], 'target': [1.85, 55.0, 1.7], 'pose': 'listening', 'activity': 'conversation', 'group': 'conversation-right'},
    ]
    for index in (0, 3, 4, 7, 10, len(PROJECTS)-1):
        display = bookmarks[index]
        x, y, _ = display['position']
        placements.append({'position': [-1.95 if x < 0 else 1.95, y + (.18 if index % 2 else -.15)],
                           'target': [x, y, 2.85], 'pose': 'listening', 'activity': 'viewing_display',
                           'project_id': display['id']})
    personal_display = next(bookmark for bookmark in bookmarks if bookmark['section']=='personal')
    bag_y = sections[1]['endY']-8
    placements.extend([
        {'position': [2.05, sections[1]['door']['y']+4.5], 'target': [1.65, sections[1]['door']['y']+3.3, 1.4], 'pose': 'phone', 'activity': 'phone'},
        {'position': [-1.95, bag_y-1.7], 'target': [-1.65, bag_y+.5, 1.7], 'pose': 'carrying_bag', 'activity': 'carrying_bag',
         'route': {'center': [-1.90, bag_y], 'radius': [.04, 2.2], 'phase': 1.1}},
        {'position': [2.15, 11.7], 'target': [2.15, 14.7, 1.7], 'pose': 'walking', 'activity': 'walking',
         'route': {'center': [1.90, 11.7], 'radius': [.04, 3], 'phase': .3}},
        {'position': [-2.15, 40], 'target': [-2.15, 43, 1.7], 'pose': 'walking', 'activity': 'walking',
         'route': {'center': [-1.90, 39], 'radius': [.04, 2.5], 'phase': 2.1}},
        {'position': [-1.95, personal_display['position'][1]+.18], 'target': [-BOARD_X, personal_display['position'][1], 2.85], 'pose': 'phone', 'activity': 'thinking',
         'project_id': personal_display['id']},
    ])
    if not people:
        raise RuntimeError('City master has no usable NPC reference metadata.')
    for index, placement in enumerate(placements):
        x, y = placement['position']
        if y > length - 3:
            continue
        options = [person for person in people if person['pose'] == placement['pose']]
        if not options:
            raise RuntimeError(f'City master lacks required pose: {placement["pose"]}')
        person = options[index % len(options)]
        cloud = by_id[person['id']]
        base = Vector(person['base'])
        target_direction = Vector(placement['target']) - Vector((x, y, 1.7))
        facing = math.atan2(target_direction.x, -target_direction.y)
        placement['facing'] = facing
        rotation = Matrix.Rotation(facing - person.get('facing', 0), 4, 'Z')
        target = Vector((x, y, .02))
        if placement['activity'] in {'viewing_display', 'thinking'}:
            # Reuse the relaxed listening silhouette, with a gently raised gaze
            # toward the display rather than a phone or conversation gesture.
            to_local = Matrix.Rotation(-person.get('facing', 0), 4, 'Z')
            to_world = Matrix.Rotation(facing, 4, 'Z')
            neck = Vector((0, 0, 1.66))
            tilt = min(math.radians(25), math.atan2(target_direction.z, target_direction.xy.length))
            body = []
            for vertex in cloud:
                local = to_local @ (vertex - base)
                weight = min(1, max(0, (local.z - 1.60) / .15))
                head_rotation = Matrix.Rotation(-tilt * weight, 4, 'X')
                local = neck + head_rotation @ (local - neck)
                body.append(tuple(target + to_world @ local))
        else:
            body = [tuple(target + rotation @ (v - base)) for v in cloud]
        rest_inverse = Matrix.Rotation(-facing, 4, 'Z') @ Matrix.Translation(-target)
        local_body = [tuple(rest_inverse @ Vector(v)) for v in body]
        if placement['pose'] == 'walking':
            # Authored walking clouds can include a vertical source offset.
            # Anchor their lowest point to the hallway floor before gait baking.
            floor = min(v[2] for v in local_body)
            local_body = [(vx, vy, vz - floor) for vx, vy, vz in local_body]
        rig = bpy.data.objects.new(f'NPC {index + 1:02d} / looping motion rig', None)
        crowd_col.objects.link(rig)
        rig.location = target
        rig.rotation_euler.z = facing
        npc = points(f'NPC {index + 1:02d} / {placement["activity"]}', local_body,
                      [.0065] * len(body), PERSON, crowd_col)
        npc.parent = rig
        npc['pose'] = ('thinking' if placement['activity'] == 'thinking' else
                       'observing' if placement['activity'] == 'viewing_display' else person['pose'])
        npc['source_pose'] = person['pose']
        npc['activity'] = placement['activity']
        npc['placement'] = json.dumps(placement)
        if 'group' in placement:
            npc['interaction_group'] = placement['group']
        if 'project_id' in placement:
            npc['viewing_project'] = placement['project_id']
        npc['source_person_id'] = person['id']
        npc['source_file'] = str(MASTER.relative_to(ROOT))
        npc['person_metadata'] = json.dumps(person)
        # Preserve hand-aligned phones and bags from the city design too.
        for prop in reference.objects:
            if placement['activity'] == 'thinking':
                continue
            if prop.type != 'MESH' or prop.get('npc_owner') != person['id']:
                continue
            transformed = [rest_inverse @ (target + rotation @ (prop.matrix_world @ v.co - base))
                           for v in prop.data.vertices]
            if prop.data.polygons:
                mesh = bpy.data.meshes.new(f'NPC {index + 1:02d} / accessory')
                mesh.from_pydata(transformed, [], [tuple(p.vertices) for p in prop.data.polygons])
                mesh.materials.append(BLACK)
                accessory = bpy.data.objects.new(mesh.name, mesh)
                crowd_col.objects.link(accessory)
                accessory.parent = rig
            elif prop.data.edges:
                contour = lines(f'NPC {index + 1:02d} / accessory contours',
                                [(transformed[e.vertices[0]], transformed[e.vertices[1]]) for e in prop.data.edges],
                                MUTED, crowd_col, .003)
                contour.parent = rig
        animate_person(npc, rig, placement, index)
    # Prevent the appended city and its render settings from becoming part of the deliverable.
    bpy.data.scenes.remove(reference)
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    end = bpy.data.objects.new('End / exhibition message', None)
    displays.objects.link(end)
    end.location = (0, length - .2, 0)
    final = box('End / outlined portal', (0, length - .1, 3.1), (3.8, .08, 5.0), BLACK, architecture)
    outline(final, WHITE, structure, .009)
    text('End / message', 'I D E A S\nB U I L T\nI N T O\nR E A L I T Y', (-1.22, -.1, 4.1), .23, end)
    text('End / signature', 'D A M I E N  /  P R O J E C T S', (-1.22, -.1, 1.65), .095, end, MUTED)
    for y in range(-2, int(length), 10):
        light_data = bpy.data.lights.new(f'Gallery softbox {y}', 'AREA')
        light_data.energy = 5
        light_data.shape = 'RECTANGLE'
        light_data.size = 6
        light_data.size_y = 3
        light = bpy.data.objects.new(light_data.name, light_data)
        cameras.objects.link(light)
        light.location = (0, y, 5.95)
    camera_data = bpy.data.cameras.new('Project Hallway / 24mm walkthrough')
    camera = bpy.data.objects.new('Project Hallway / walkthrough camera', camera_data)
    cameras.objects.link(camera)
    camera_data.lens = 24
    camera_data.clip_start = .05
    camera_data.clip_end = 250
    scene.camera = camera
    for side, eye, look_at in (
        ('Left / east-facing display', (1.35, PROJECT_START - 4.2, 2.45), (-3.2, PROJECT_START, 2.2)),
        ('Right / west-facing display', (-1.35, PROJECT_START + RIGHT_STAGGER - 4.2, 2.45),
         (3.2, PROJECT_START + RIGHT_STAGGER, 2.2)),
        ('Conversation review', (1.4, 10.1, 2.2), (-2.45, 14.4, 1.15)),
        ('Walking review', (-1.2, 7.7, 2.2), (2.15, 11.7, 1.1)),
        ('Thinking review', (1.2, personal_display['position'][1]-4, 2.2), (-1.95, personal_display['position'][1]+.18, 1.25)),
        ('Academic doorway', (0, sections[1]['door']['y']-7, 2.45), (0,sections[1]['door']['y'],2.65)),
        ('Personal doorway', (0, sections[2]['door']['y']-7, 2.45), (0,sections[2]['door']['y'],2.65)),
        ('Ceiling review', (0, 1.9, 1.8), (0, 1.9, 6.05)),
        ('Ceiling perspective', (0, -3.5, 3.2), (0, 3.5, 6.05)),
    ):
        detail_data = bpy.data.cameras.new('Project Hallway / ' + side)
        detail_data.lens = (14 if side == 'Ceiling review' else 18 if side == 'Ceiling perspective'
                            else 32 if 'review' in side else 23)
        detail_data.clip_end = 250
        detail = bpy.data.objects.new(detail_data.name, detail_data)
        cameras.objects.link(detail)
        detail.location = eye
        detail.rotation_euler = (Vector(look_at) - Vector(eye)).to_track_quat('-Z', 'Y').to_euler()
    scene.frame_start = 1
    scene.frame_end = 1200
    scene.render.fps = 30
    camera.rotation_mode = 'QUATERNION'
    for frame, y in ((1, -7.8), (1200, length - 7)):
        camera.location = (0, y, 2.45)
        camera.rotation_quaternion = (Vector((0, y + 20, 2.9)) - camera.location).to_track_quat('-Z', 'Y')
        camera.keyframe_insert(data_path='location', frame=frame)
        camera.keyframe_insert(data_path='rotation_quaternion', frame=frame)
    action = camera.animation_data.action
    for layer in action.layers:
        for strip in layer.strips:
            for channelbag in strip.channelbags:
                for curve in channelbag.fcurves:
                    for key in curve.keyframe_points:
                        key.interpolation = 'LINEAR'
    scene.timeline_markers.new('01 / Project Hallway entrance', frame=1)
    for index, bookmark in enumerate(bookmarks):
        frame = max(1, round(1 + (bookmark['position'][1] - 4 + 7.8) / (length + .8) * 1199))
        bookmark['frame'] = frame
        scene.timeline_markers.new(f'{index + 2:02d} / {bookmark["id"]}', frame=frame)
    scene.timeline_markers.new('End / Ideas built into reality', frame=1200)
    scene.world = bpy.data.worlds.new('Hallway / black world')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value = (.003, .003, .003, 1)
    scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value = .025
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = .035
    scene.cycles.max_bounces = 6
    scene.cycles.diffuse_bounces = 2
    scene.cycles.glossy_bounces = 4
    scene.cycles.transparent_max_bounces = 16
    scene.render.use_simplify = True
    scene.render.simplify_subdivision = 0
    scene.render.resolution_x = 1360
    scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    transforms = scene.view_settings.bl_rna.properties['view_transform'].enum_items.keys()
    scene.view_settings.view_transform = 'AgX' if 'AgX' in transforms else 'Standard'
    scene.frame_set(1)
    interactive = bpy.data.objects.new('Project Hallway / free-look camera', camera.data.copy())
    cameras.objects.link(interactive)
    interactive.rotation_mode = 'QUATERNION'
    interactive.location = camera.location.copy()
    interactive.rotation_quaternion = camera.rotation_quaternion.copy()
    interactive['hallway_controller_camera'] = True
    scene.camera = interactive
    scene['hallway_controls'] = 'Run embedded hallway_controls.py; F3 > Project Hallway: Walk'
    controls = bpy.data.texts.new('hallway_controls.py')
    controls.write((OUT / 'hallway_controls.py').read_text())
    welcome = bpy.data.texts.new('START HERE / Hallway Controls')
    welcome.write('PROJECT HALLWAY / INTERACTIVE BLENDER VIEW\n\n'
                  '1. Open Scripting workspace, choose hallway_controls.py in the Text Editor.\n'
                  '2. Press Run Script (Alt+P with the pointer over the Text Editor).\n'
                  '3. Return to Layout, place the pointer over the 3D viewport.\n'
                  '4. Press F3 and choose Project Hallway: Walk.\n\n'
                  'Mouse = free look. W/S or Up/Down = walk straight. Shift = faster.\n'
                  'Tab = release/capture mouse. Esc = exit controller.\n'
                  'The Hallway sidebar (N) also has Start/Stop buttons.\n'
                  'NPC animation runs on its own clock, even without walking.\n'
                  'The free-look camera has no baked animation. The tour camera is optional.\n')
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces.active.region_3d.view_perspective = 'CAMERA'
                area.spaces.active.shading.type = 'MATERIAL'
                area.spaces.active.lock_camera = False
    bpy.context.view_layer.objects.active = interactive
    interactive.select_set(True)
    scene.render.filepath = str(OUT / 'project-hallway-preview.png')
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(MODEL), compress=True)
    manifest = {'model': MODEL.name, 'coordinateSystem': 'Blender Z-up',
                'lengthMeters': length, 'projectCount': len(PROJECTS), 'npcCount': len(placements),
                'camera': interactive.name, 'tourCamera': camera.name, 'controlsScript': 'hallway_controls.py',
                'frameStart': 1, 'frameEnd': 1200,
                'projectBaySpacingMeters': BAY_SPACING, 'rightDisplayStaggerMeters': RIGHT_STAGGER,
                'displayFacing': {'left': 'east (+X)', 'right': 'west (-X)'},
                'pillarWidthMeters': 1.1, 'projectorCount': len(PROJECTS) + 1,
                'windows': window_layout, 'npcLayout': placements,
                'categories': sections,
                'galleryLighting': {'solidBlackWalls': 2, 'spotlightCount': 0,
                                    'worldStrength': .025, 'softboxWatts': 5},
                'floorSlabs': {'widthMeters': 2.5, 'lengthMeters': BAY_SPACING},
                'ceiling': ceiling_layout,
                'npcAnimation': {'globalLoopFrames': 1200, 'walkingLoopFrames': 300,
                                 'interactionLoopFrames': [120, 150, 200], 'nativeShapeKeys': True,
                                 'independentOfUserMovement': True},
                'projects': bookmarks, 'npcSource': str(MASTER.relative_to(ROOT))}
    (OUT / 'hallway-layout.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('PROJECT HALLWAY BUILT:', json.dumps({'projects': len(PROJECTS), 'length': length, 'objects': len(scene.objects)}))


if '--layout-only' in sys.argv:
    from hallway_layout import refresh_existing
    bpy.ops.wm.open_mainfile(filepath=str(MODEL))
    scene = bpy.context.scene
    refresh_existing(scene, OUT)
elif '--ceiling-only' in sys.argv:
    refresh_ceiling()
elif '--preview-only' in sys.argv:
    bpy.ops.wm.open_mainfile(filepath=str(MODEL))
    scene = bpy.context.scene
else:
    build()
if '--no-render' not in sys.argv:
    default_camera = scene.camera
    previews = [] if any(flag in sys.argv for flag in ['--detail-previews','--ceiling-previews','--category-previews']) else [(1, 'project-hallway-preview.png')]
    if '--all-previews' in sys.argv:
        previews.extend([(190, 'project-hallway-interior.png'), (1160, 'project-hallway-end.png')])
    for frame, filename in previews:
        scene.camera = scene.objects['Project Hallway / walkthrough camera']
        scene.frame_set(frame)
        scene.render.filepath = str(OUT / filename)
        bpy.ops.render.render(write_still=True)
    if '--all-previews' in sys.argv or '--detail-previews' in sys.argv:
        scene.frame_set(1)
        walkthrough = scene.camera
        for side, filename in (('Left / east-facing display', 'project-hallway-projector-left.png'),
                               ('Right / west-facing display', 'project-hallway-projector-right.png')):
            scene.camera = scene.objects['Project Hallway / ' + side]
            scene.render.filepath = str(OUT / filename)
            bpy.ops.render.render(write_still=True)
        scene.camera = walkthrough
    if '--all-previews' in sys.argv or '--ceiling-previews' in sys.argv:
        scene.frame_set(1)
        for name, filename in (('Ceiling review', 'project-hallway-ceiling.png'),
                               ('Ceiling perspective', 'project-hallway-ceiling-perspective.png')):
            scene.camera = scene.objects['Project Hallway / ' + name]
            scene.render.filepath = str(OUT / filename)
            bpy.ops.render.render(write_still=True)
    if '--all-previews' in sys.argv or '--category-previews' in sys.argv:
        scene.frame_set(1)
        for name, filename in (('Academic doorway', 'project-hallway-academic-door.png'),
                               ('Personal doorway', 'project-hallway-personal-door.png')):
            scene.camera = scene.objects['Project Hallway / ' + name]
            scene.render.filepath = str(OUT / filename)
            bpy.ops.render.render(write_still=True)
    scene.camera = default_camera
