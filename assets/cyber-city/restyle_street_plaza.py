"""Focused, repeatable illuminated-plaza update to the production city master.

Native wire sources remain GPU lines in the browser; signs are mesh lettering.
Run after full styling, without rebuilding architecture, crowd or the route.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parent
PREFIX = 'Street plaza • '
parser = argparse.ArgumentParser()
parser.add_argument('--preview', action='store_true')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
scene = bpy.context.scene
assert scene.name == 'MONO / Wire & Particle City'
assert Path(bpy.data.filepath).resolve() == ROOT / 'monochrome-city-solid-tower.blend'
scene.frame_set(1)
bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT')
route_frames = (1, 90, 150, 245, 383, 450)
originals = [obj for obj in scene.objects if not obj.name.startswith(PREFIX)]
poses = {}
for frame in route_frames:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    poses[frame] = {obj.name: obj.matrix_world.copy() for obj in originals}
scene.frame_set(1)
old = bpy.data.collections.get(PREFIX + 'Illuminated precinct')
if old:
    for obj in list(old.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(old)
for blocks in (bpy.data.meshes, bpy.data.curves, bpy.data.node_groups, bpy.data.materials):
    for block in list(blocks):
        if block.name.startswith(PREFIX) and block.users == 0:
            blocks.remove(block)
collection = bpy.data.collections.new(PREFIX + 'Illuminated precinct')
scene.collection.children.link(collection)
materials, groups = {}, {}
template = next(group for group in bpy.data.node_groups if group.name.startswith('Mono • Wires'))
stats = {'line_segments': 0, 'fixtures': 0, 'labels': 0}


def emission(value):
    if value not in materials:
        mat = bpy.data.materials.new(PREFIX + str(value))
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        nodes.clear()
        out = nodes.new('ShaderNodeOutputMaterial')
        node = nodes.new('ShaderNodeEmission')
        node.inputs['Color'].default_value = (value, value, value, 1)
        mat.node_tree.links.new(node.outputs[0], out.inputs['Surface'])
        materials[value] = mat
    return materials[value]


def mesh(name, vertices, faces, value=0):
    data = bpy.data.meshes.new(PREFIX + name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(data.name, data)
    collection.objects.link(obj)
    data.materials.append(emission(value))
    obj['city_render_kind'] = 'solid' if value else 'mask'
    return obj


def lines(name, paths, value=.28, radius=.008, glow=False):
    vertices, edges = [], []
    for path in paths:
        start = len(vertices)
        vertices.extend(path)
        edges.extend((start + i, start + i + 1) for i in range(len(path) - 1))
    data = bpy.data.meshes.new(PREFIX + name)
    data.from_pydata(vertices, edges, [])
    data.attributes.new('radius', 'FLOAT', 'POINT').data.foreach_set('value', [radius] * len(vertices))
    obj = bpy.data.objects.new(data.name, data)
    collection.objects.link(obj)
    kind = 'glow' if glow else 'lines'
    obj['city_render_kind'] = kind
    key = (kind, value)
    if key not in groups:
        group = template.copy()
        group.name = PREFIX + str(key)
        group.nodes.get('Set Material').inputs['Material'].default_value = emission(value)
        groups[key] = group
    obj.modifiers.new('Native street lines', 'NODES').node_group = groups[key]
    stats['line_segments'] += len(edges)
    return obj


def box(name, center, size, edge=.22, glow=False):
    x, y, z = center
    a, b, c = (v / 2 for v in size)
    vertices = [(x + dx, y + dy, z + dz) for dz in (-c, c) for dy in (-b, b) for dx in (-a, a)]
    mesh(name + ' body', vertices, [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)])
    pairs = [(0, 1), (1, 3), (3, 2), (2, 0), (4, 5), (5, 7), (7, 6), (6, 4), (0, 4), (1, 5), (2, 6), (3, 7)]
    lines(name + ' perimeter', [[vertices[i], vertices[j]] for i, j in pairs], edge, glow=glow)
    stats['fixtures'] += 1


def label(name, body, position, size, floor=False, value=.65):
    data = bpy.data.curves.new(PREFIX + name, 'FONT')
    data.body = body
    data.size = size
    data.space_character = 1.18
    data.space_line = 1.25
    data.resolution_u = 3
    obj = bpy.data.objects.new(data.name, data)
    collection.objects.link(obj)
    obj.location = position
    if not floor:
        obj.rotation_euler.x = math.pi / 2
    data.materials.append(emission(value))
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target='MESH')
    obj.select_set(False)
    obj['city_render_kind'] = 'solid'
    stats['labels'] += 1


def arrow(x, y, z=.038, scale=1, upright=False):
    points = [(-.4, 0), (0, .42), (.4, 0)]
    if upright:
        path = [(x + px * scale, y, z + py * scale) for px, py in points]
    else:
        path = [(x + px * scale, y + py * scale, z) for px, py in points]
    lines('direction chevron', [path], .8, .016, glow=True)


# Fine paving joints: a denser scale than the old four-metre construction grid.
paths = [[(x, -43, .004), (x, -6, .004)] for x in range(-24, 25, 2)]
paths += [[(-24, y, .004), (24, y, .004)] for y in range(-43, -5, 2)]
lines('two metre stone joints', paths, .032, .003)
# Broken inset strips, dotted pedestrian lanes and perpendicular crossing bars.
for x in (-3.5, 7.5):
    strips, dots = [], []
    for i in range(18):
        y = -41 + i * 1.85
        strips.append([(x, y, .026), (x, y + .75, .026)])
    for i in range(80):
        y = -41 + i * .43
        dots.append([(x + .62, y, .027), (x + .62, y + .10, .027)])
    lines('inset linear lights', strips, 1.3, .022, glow=True)
    lines('pedestrian dotted guide', dots, .55, .011, glow=True)
    for y in (-34, -25, -15):
        arrow(x + .62, y, scale=.5)
for x0, y in ((-9, -27), (11, -19)):
    for i in range(8):
        x = x0 + i * .35
        mesh('crosswalk inlay', [(x, y, .024), (x + .15, y, .024), (x + .15, y + 1.25, .024), (x, y + 1.25, .024)], [(0, 1, 2, 3)], .6)
for x, y, text in ((-.9, -30, 'PLAZA 01'), (-.9, -20, 'KAZE / ENTRANCE'), (10, -25, 'TRANSIT  >\nATRIUM   >\nMARKET   >')):
    label('pavement destination', text, (x, y, .031), .28, floor=True, value=.48)
arrow(.2, -28.8, scale=1.3)
arrow(.2, -18.8, scale=1.3)


def pylon(x, y, height, width, title, detail, map_panel=False):
    box('wayfinding plinth', (x, y, .18), (width + .18, .64, .36), .8, True)
    box('wayfinding tower', (x, y, height / 2 + .36), (width, .32, height), .6, True)
    front = y - .168
    label('pylon title', title, (x - width * .39, front, height - .22), width * .14)
    label('pylon routes', detail, (x - width * .39, front, height - 1.02), width * .075)
    lines('pylon section dividers', [[(x - width * .42, front, z), (x + width * .42, front, z)] for z in (.65, height - .78)], .4)
    if map_panel:
        # Technical street map, diagonal routes and a marked current position.
        bottom, top = .86, height - 1.65
        left, right = x - width * .39, x + width * .39
        paths = [[(left, front, bottom), (right, front, bottom), (right, front, top), (left, front, top), (left, front, bottom)]]
        for i in range(1, 5):
            px = left + (right - left) * i / 5
            paths.append([(px, front, bottom), (px, front, top)])
            z = bottom + (top - bottom) * i / 5
            paths.append([(left, front, z), (right, front, z)])
        paths += [[(left, front, bottom), (right, front, top)], [(left, front, top), (right, front, bottom)]]
        lines('precinct schematic map', paths, .35, .005)
        r = .065
        lines('you are here locator', [[(x + r * math.cos(a * math.tau / 32), front - .002, (bottom + top) / 2 + r * math.sin(a * math.tau / 32)) for a in range(33)]], 1.4, .012, True)
    else:
        r, z = width * .32, 1.48
        paths = []
        for squash in (1, .45, .12):
            paths.append([(x + r * squash * math.cos(i * math.tau / 64), front, z + r * math.sin(i * math.tau / 64)) for i in range(65)])
        paths.append([(x - r, front, z), (x + r, front, z)])
        lines('wire globe emblem', paths, .48, .006)


pylon(.8, -25, 3.55, 1.3, 'CENTRAL\nPLAZA  >', 'TRANSIT    >\nENTRANCE   >\nDISTRICT A >', True)
pylon(-8, -15, 3.45, .65, 'T3', 'NORTH\nLINK\n  ^\n\n1.2 KM')
pylon(11.4, -17, 3.35, 1.05, 'A BETTER\nTOMORROW', 'PEOPLE\nPLACES\nPOSSIBILITIES')
# Street furniture stays outside the camera's central approach corridor.
for x, y in ((-8, -24), (13, -21), (-11, -10), (9, -10)):
    box('bench seat', (x, y, .48), (2.7, .7, .18), .7, True)
    box('bench back', (x, y + .3, .85), (2.7, .12, .6), .32)
    for dx in (-1.05, 1.05):
        box('bench support', (x + dx, y, .24), (.12, .55, .4), .25)
    lines('bench luminous lower edge', [[(x - 1.3, y - .36, .29), (x + 1.3, y - .36, .29)]], .9, .014, True)
for x, y in ((-4.5, -34), (13.5, -28), (-7, -21), (10, -19), (-11, -12), (8, -8)):
    box('illuminated bollard', (x, y, .65), (.28, .28, 1.3), .35)
    lines('bollard lamp', [[(x, y - .145, .26), (x, y - .145, 1.18)]], 1.6, .026, True)
    box('bollard foot', (x, y, .06), (.4, .4, .12), .65, True)
for x, y in ((-13, -19), (16, -15), (-15, -9)):
    box('garden planter', (x, y, .3), (3.2, 2, .6), .32)
    lines('planter luminous rim', [[(x - 1.6, y - 1, .61), (x + 1.6, y - 1, .61), (x + 1.6, y + 1, .61)]], .8, .012, True)

# Blender wet-paving material; the browser uses the bounded shared reflector.
floor = scene.objects['Mono • dark reflective ground']
mat = bpy.data.materials.new(PREFIX + 'Wet graphite paving')
mat.use_nodes = True
nodes = mat.node_tree.nodes
bsdf = nodes.get('Principled BSDF')
bsdf.inputs['Base Color'].default_value = (.025, .025, .025, 1)
bsdf.inputs['Metallic'].default_value = .25
bsdf.inputs['Roughness'].default_value = .42
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 180
bump = nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value = .18
bump.inputs['Distance'].default_value = .025
mat.node_tree.links.new(noise.outputs['Fac'], bump.inputs['Height'])
mat.node_tree.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
floor.data.materials.clear()
floor.data.materials.append(mat)

for frame in route_frames:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    for obj in originals:
        assert all(abs(a - b) < 1e-5 for ra, rb in zip(obj.matrix_world, poses[frame][obj.name]) for a, b in zip(ra, rb)), (obj.name, frame)
stats['reflection'] = {'width': 100, 'depth': 70, 'position': [0, -30, -.012], 'strength': .22, 'paving': True}
scene['street_plaza_reference'] = json.dumps(stats)
scene.frame_set(1)
temporary = ROOT / 'street-plaza-saving.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(temporary))
temporary.replace(ROOT / 'monochrome-city-solid-tower.blend')
(ROOT / 'street-plaza.json').write_text(json.dumps(stats, indent=2) + '\n')
print('STREET_PLAZA', json.dumps(stats))
if args.preview:
    # Export-aligned preview only: saved authored anchors and camera stay intact.
    floor.location = (0, 0, -.12)
    scene.frame_set(90)
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 64
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1674
    scene.render.resolution_y = 470
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = str(ROOT / 'street-plaza-preview.png')
    bpy.ops.render.render(write_still=True)
