"""Author the reference's monochrome orbital sky in the production city master.

World-fixed geometry is composed from the opening camera, behind the city.
Only this script's collection is replaced; architecture and motion are retained.
"""
import argparse
import json
import math
import random
import sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from bright_star_layout import BRIGHT_STARS
parser = argparse.ArgumentParser()
parser.add_argument('--preview', action='store_true')
args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
scene = bpy.context.scene
assert scene.name == 'MONO / Wire & Particle City'
scene.frame_set(1)
bpy.context.view_layer.update()
camera = scene.camera
collection_name = 'City • Reference orbital sky'
old = bpy.data.collections.get(collection_name)
if old:
    for obj in list(old.objects): bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(old)
for datablocks in [bpy.data.meshes, bpy.data.curves, bpy.data.node_groups, bpy.data.materials]:
    for block in list(datablocks):
        if block.name.startswith('Orbital sky • ') and block.users == 0:
            datablocks.remove(block)
collection = bpy.data.collections.new(collection_name)
scene.collection.children.link(collection)
distance = 150
aspect = 1414 / 610
# Preserve the viewer's vertical FOV; the reference is a wide viewport crop.
height = distance * camera.data.sensor_width / camera.data.lens / (scene.render.resolution_x / scene.render.resolution_y)
width = height * aspect
basis = camera.matrix_world.copy()
stats = {'line_segments': 0, 'sky_points': 0, 'planets': 0, 'labels': 0}


def world(x, y, depth=distance):
    return basis @ Vector(((x-.5)*width, (.5-y)*height, -depth))


def material(name, value):
    mat = bpy.data.materials.new('Orbital sky • '+name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    out = nodes.new('ShaderNodeOutputMaterial')
    emission = nodes.new('ShaderNodeEmission')
    emission.inputs['Color'].default_value = (value, value, value, 1)
    emission.inputs['Strength'].default_value = 1
    mat.node_tree.links.new(emission.outputs[0], out.inputs['Surface'])
    return mat


templates = {kind: next(g for g in bpy.data.node_groups if g.name.startswith('Mono • '+kind)) for kind in ['Wires', 'Points']}
groups = {}


def source(name, points, edges, value, radius, kind):
    mesh = bpy.data.meshes.new('Orbital sky • '+name)
    mesh.from_pydata(points, edges, [])
    mesh.update()
    attr = mesh.attributes.new('radius', 'FLOAT', 'POINT')
    attr.data.foreach_set('value', [radius]*len(points))
    obj = bpy.data.objects.new(mesh.name, mesh)
    collection.objects.link(obj)
    obj['city_render_kind'] = kind
    obj['city_sky_element'] = name
    if kind == 'points': obj['city_sky_points'] = True
    key = (kind, value)
    if key not in groups:
        group = templates['Points' if kind == 'points' else 'Wires'].copy()
        group.name = f'Orbital sky • {kind} {value}'
        group.nodes.get('Set Material').inputs['Material'].default_value = material(str(key), value)
        groups[key] = group
    obj.modifiers.new('Native orbital geometry', 'NODES').node_group = groups[key]
    stats['sky_points' if kind == 'points' else 'line_segments'] += len(points) if kind == 'points' else len(edges)
    return obj


def paths(name, lines, value=.13, radius=.008):
    points, edges = [], []
    for line in lines:
        start = len(points)
        points.extend(world(*p) for p in line)
        edges.extend((start+i, start+i+1) for i in range(len(line)-1))
    return source(name, points, edges, value, radius, 'lines')


def circle(center, radius, steps=480):
    return [(center[0]+radius*math.cos(i*math.tau/steps), center[1]+radius*aspect*math.sin(i*math.tau/steps)) for i in range(steps+1)]


paths('large continuous orbital arc', [circle((.493, -.235), .30)], .24)
for i, radius in enumerate([.063, .205, .36, .48]):
    center = (.5, .225) if i == 0 else (.493, -.235)
    dots = [world(*p) for p in circle(center, radius, int(radius*1800))[:-1]]
    source('dotted orbit '+str(i+1), dots, [], .07 if i == 0 else .10, .042, 'points')

# The long diagonal orbit passes behind the tower and across the planet.
def orbital_height(t):
    # Opposing bends produce a shallow S, rather than a single bowed arc.
    return 1.015-.925*t-.55*t*(1-t)*(1-2*t)


diagonal = []
for i in range(401):
    t = i/400
    diagonal.append((t, orbital_height(t)))
paths('diagonal orbital trajectory', [diagonal], .28)

constellations = [
    [(.195, .332), (.218, .385), (.252, .508), (.292, .523)],
    [(.881, .564), (.955, .643)],
    [(.114, .905), (.137, .96)],
    [(.647, .988), (.801, .738)],
]
paths('constellation connections', constellations, .075)
source('constellation stars', [world(*p) for line in constellations for p in line], [], .65, .09, 'points')
source('orbital tracking stars', [world(t, orbital_height(t)) for t in [.19, .67, .81]], [], 1.2, .10, 'points')
source('large orbit stars', [world(*p) for p in [(.306, .297), (.705, .251)]], [], .8, .10, 'points')
# Native point core; the browser uses the authored optical flare radius for a
# transparent, smoothly fading sprite instead of hard crosshair geometry.
for index, (x, y, flare_radius) in enumerate(BRIGHT_STARS):
    name = 'bright star optical shine' + (f' {index+1:02d}' if index else '')
    shine = source(name, [world(x, y)], [], 1.25, .12 * flare_radius / 9, 'points')
    shine['city_sky_shine'] = True
    shine['city_shine_radius'] = flare_radius

rng = random.Random(710)
for name, count, value, radius in [('distant stars', 370, .12, .035), ('near stars', 65, .30, .055)]:
    source(name, [world(rng.random(), rng.random(), distance+2) for _ in range(count)], [], value, radius, 'points')


def planet(name, center, radius):
    # A dark disk with a shaded left crescent; no wire globe or bright full rim.
    vertices = [world(*center, distance-1)]
    normals = [Vector((0, 0, 1))]
    rings, steps = 40, 128
    for ring in range(1, rings+1):
        r = ring/rings
        for i in range(steps):
            a = i*math.tau/steps
            x, y = r*math.cos(a), r*math.sin(a)
            vertices.append(world(center[0]+x*radius, center[1]-y*radius*aspect, distance-1))
            normals.append(Vector((x, y, math.sqrt(max(0, 1-r*r)))))
    faces = [(0, 1+i, 1+(i+1)%steps) for i in range(steps)]
    for ring in range(rings-1):
        a, b = 1+ring*steps, 1+(ring+1)*steps
        for i in range(steps):
            j = (i+1)%steps
            faces.extend([(a+i, b+i, b+j), (a+i, b+j, a+j)])
    mesh = bpy.data.meshes.new('Orbital sky • '+name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    shades = [material(name+' shade '+str(i), (i/63)**1.6*.46) for i in range(64)]
    for shade in shades: mesh.materials.append(shade)
    light = Vector((-.60, .04, -.80)).normalized()
    for face in mesh.polygons:
        n = sum((normals[i] for i in face.vertices), Vector()).normalized()
        face.material_index = round(min(1, max(0, n.dot(light))/.60)*63)
    obj = bpy.data.objects.new(mesh.name, mesh)
    collection.objects.link(obj)
    obj['city_render_kind'] = 'solid'
    obj['city_sky_element'] = name
    stats['planets'] += 1


planet('large crescent planet', (.891, .23), .061)
planet('small crescent moon', (.936, .137), .011)


def label(name, body, x, y, size=.010):
    data = bpy.data.curves.new('Orbital sky • '+name, 'FONT')
    data.body = body
    data.size = height*size
    data.space_character = 1.35
    data.space_line = 1.5
    data.materials.append(material(name, .42))
    obj = bpy.data.objects.new(data.name, data)
    collection.objects.link(obj)
    obj.location = world(x, y)
    obj.rotation_euler = basis.to_euler()
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(deps), depsgraph=deps)
    lettering = bpy.data.objects.new(data.name+' mesh', mesh)
    collection.objects.link(lettering)
    lettering.matrix_world = obj.matrix_world
    lettering['city_render_kind'] = 'solid'
    lettering['city_sky_element'] = name
    bpy.data.objects.remove(obj, do_unlink=True)
    stats['labels'] += 1


label('orbital grid annotation', 'ORBITAL GRID\n// SECTOR 7\nNEXUS', .047, .074)
label('earth distance annotation', 'EARTH\n// 384,400 km', .057, .575)
label('synchronization annotation', 'L4\n// 21\nSYNC', .982, .22)
paths('annotation ticks and distance bracket', [
    [(.047, .171), (.055, .171)], [(.982, .318), (.990, .318)],
    [(.044, .475), (.044, .726)], [(.040, .475), (.049, .475)],
    [(.040, .742), (.048, .742), (.048, .760), (.040, .760), (.040, .742)],
], .22)

scene['orbital_sky_reference'] = json.dumps({'reference_aspect': aspect, 'opening_frame': 1, 'distance_m': distance, 'brightStars': len(BRIGHT_STARS), **stats})
bpy.context.preferences.filepaths.save_version = 1
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'monochrome-city-solid-tower.blend'))
(ROOT/'orbital-sky.json').write_text(scene['orbital_sky_reference'])
print({'orbital_sky': stats, 'master': str(ROOT/'monochrome-city-solid-tower.blend')})
if args.preview:
    camera.data.sensor_fit = 'VERTICAL'
    camera.data.sensor_height = camera.data.sensor_width / (scene.render.resolution_x / scene.render.resolution_y)
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 16
    scene.render.resolution_x = 1414
    scene.render.resolution_y = 610
    scene.render.resolution_percentage = 75
    scene.render.filepath = str(ROOT/'orbital-sky-preview.png')
    bpy.ops.render.render(write_still=True)
