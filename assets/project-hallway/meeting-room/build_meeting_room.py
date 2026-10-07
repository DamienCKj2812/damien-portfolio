"""Build the static Projects meeting-room master; never modifies the hallway."""
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

OUT = Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.name = 'PROJECTS / Office meeting room'
scene.unit_settings.system = 'METRIC'
scene['Authored entry surround'] = True
scene['nested_project_room'] = True
scene['meeting_chair_count'] = 12
scene['meeting_table_count'] = 1
scene['reference_style'] = 'Black conference room / white contours / city glazing / integrated ceiling lights'


def material(name, value, glow=False, roughness=.5):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (value, value, value, 1)
    shader.inputs['Roughness'].default_value = roughness
    if glow:
        shader.inputs['Emission Color'].default_value = (value, value, value, 1)
        shader.inputs['Emission Strength'].default_value = 1
        # Use a native emission node so the browser exports the same luminance.
        nodes = mat.node_tree.nodes
        nodes.remove(shader)
        shader = nodes.new('ShaderNodeEmission')
        shader.inputs['Color'].default_value = (value, value, value, 1)
        shader.inputs['Strength'].default_value = 2.4 if name.endswith('light') else 1
        mat.node_tree.links.new(shader.outputs[0], nodes.get('Material Output').inputs['Surface'])
    return mat


BLACK = material('Meeting / black architecture', .007, roughness=.88)
TABLE = material('Meeting / dark conference table', .012, roughness=.28)
CHAIR = material('Meeting / charcoal upholstery', .018, roughness=.68)
FLOOR = material('Meeting / polished black floor', .012, roughness=.14)
EDGE = material('Meeting / white contours', .55, True)
QUIET = material('Meeting / subdued seams', .075, True)
LIGHT = material('Meeting / integrated white light', .8, True)
GLASS = material('Meeting / subtle clear glazing', .008, roughness=.3)
glass_nodes = GLASS.node_tree.nodes
glass_links = GLASS.node_tree.links
glass_transparent = glass_nodes.new('ShaderNodeBsdfTransparent')
glass_mix = glass_nodes.new('ShaderNodeMixShader')
glass_mix.inputs[0].default_value = .05
glass_links.new(glass_transparent.outputs[0], glass_mix.inputs[1])
glass_links.new(glass_nodes.get('Principled BSDF').outputs[0], glass_mix.inputs[2])
glass_links.new(glass_mix.outputs[0], glass_nodes.get('Material Output').inputs['Surface'])


def collection(name):
    col = bpy.data.collections.new(name)
    scene.collection.children.link(col)
    return col


ARCH = collection('01 / Black office architecture')
FURN = collection('02 / Conference table and twelve chairs')
DETAIL = collection('03 / Storage and decorative globe')
WINDOW = collection('04 / Glazed city outlook')
LIGHTS = collection('05 / Ceiling fixtures and camera')


def mesh(name, vertices, faces, mat, col, parent=None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.materials.append(mat)
    data.update()
    obj = bpy.data.objects.new(name, data)
    col.objects.link(obj)
    obj.parent = parent
    return obj


def lines(name, segments, mat=EDGE, col=FURN, parent=None, radius=.004):
    data = bpy.data.curves.new(name, 'CURVE')
    data.dimensions = '3D'
    data.bevel_depth = radius
    data.bevel_resolution = 0
    for a, b in segments:
        spline = data.splines.new('POLY')
        spline.points.add(1)
        spline.points[0].co = (*a, 1)
        spline.points[1].co = (*b, 1)
    obj = bpy.data.objects.new(name, data)
    col.objects.link(obj)
    data.materials.append(mat)
    obj.parent = parent
    return obj


def path(name, vertices, mat=EDGE, col=FURN, parent=None, closed=False):
    return lines(name, list(zip(vertices, vertices[1:] + vertices[:1] if closed else vertices[1:])), mat, col, parent)


def box(name, center, size, mat=BLACK, col=ARCH, parent=None, contour=False):
    vertices = [(center[0] + dx * size[0] / 2, center[1] + dy * size[1] / 2,
                 center[2] + dz * size[2] / 2)
                for dx, dy, dz in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
                                   (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    obj = mesh(name, vertices, [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)], mat, col, parent)
    if contour:
        lines(name + ' / contours', [(vertices[e.vertices[0]], vertices[e.vertices[1]]) for e in obj.data.edges], EDGE, col, parent)
    return obj


def ring(name, center, radius, mat=EDGE, col=FURN, parent=None, axis='z'):
    vertices = []
    for index in range(48):
        a = index * math.tau / 48
        delta = (radius * math.cos(a), radius * math.sin(a), 0) if axis == 'z' else (radius * math.cos(a), 0, radius * math.sin(a))
        vertices.append(tuple(Vector(center) + Vector(delta)))
    return path(name, vertices, mat, col, parent, True)


def smooth_profile(profile, closed=False):
    """Sample a smooth upholstered silhouette rather than faceted corners."""
    result = []
    count = len(profile)
    for index in range(count if closed else count - 1):
        points = [Vector(profile[(index + offset) % count] if closed else profile[max(0, min(count - 1, index + offset))])
                  for offset in (-1, 0, 1, 2)]
        a, b, c, d = points
        for step in range(6):
            t = step / 6
            result.append(tuple(.5 * (2*b + (-a+c)*t + (2*a-5*b+4*c-d)*t*t + (-a+3*b-3*c+d)*t*t*t)))
    if not closed:
        result.append(profile[-1])
    return result


def chair(index, x, y):
    root = bpy.data.objects.new(f'Chair {index:02d} / ergonomic conference seat', None)
    FURN.objects.link(root)
    root.location = (x, y, 0)
    root.rotation_euler.z = math.pi / 2 if x < 0 else -math.pi / 2
    root['meeting_chair'] = True
    # Continuous curved side profiles, with a gently tapered head/shoulder area.
    profile = [(-.48,.92,.43),(-.48,1.04,.46),(-.12,1.08,.46),(.22,1.06,.45),
               (.36,1.22,.45),(.43,1.55,.45),(.38,1.84,.43),(.29,2.05,.38),
               (.30,2.24,.32),(.38,2.34,.30),(.49,2.28,.32),(.51,1.92,.43),
               (.56,1.55,.46),(.48,1.16,.46),(.31,.94,.43),(-.2,.89,.43)]
    profile = smooth_profile(profile, closed=True)
    vertices = [(sign * width, py, z) for sign in (-1, 1) for py, z, width in profile]
    count = len(profile)
    faces = [tuple(reversed(range(count))), tuple(range(count, 2 * count))]
    faces.extend((i, (i+1)%count, (i+1)%count+count, i+count) for i in range(count))
    mesh(root.name + ' / upholstered shell', vertices, faces, CHAIR, FURN, root)
    for sign in (-1, 1):
        path(root.name + ' / sculpted side contour', [(sign*w, py, z) for py,z,w in profile], parent=root, closed=True)
        path(root.name + ' / stitched inset', [(sign*w*.89, py-.012, z) for py,z,w in profile[:60]], QUIET, parent=root)
        arm = [(sign*.55, -.40, 1.16),(sign*.55,-.46,1.35),(sign*.55,-.37,1.43),
               (sign*.55,.20,1.43),(sign*.55,.34,1.34),(sign*.55,.33,1.13)]
        arm = smooth_profile(arm)
        path(root.name + ' / curved armrest', arm, parent=root)
        path(root.name + ' / armrest inner contour', [(px-sign*.045,py,z-.055) for px,py,z in arm], QUIET, parent=root)
    for station in (6, 18, 36, 54):
        py,z,w = profile[station]
        lines(root.name + ' / cushion edge', [((-w,py,z),(w,py,z))], EDGE, parent=root)
    box(root.name + ' / pedestal', (0,.06,.53), (.10,.10,.75), TABLE, FURN, root, True)
    # A low solid circular base with a luminous perimeter, like the reference.
    circle = [(math.cos(i*math.tau/48)*.46, .06+math.sin(i*math.tau/48)*.46, z)
              for z in (.08,.14) for i in range(48)]
    mesh(root.name + ' / circular base', circle, [tuple(reversed(range(48))), tuple(range(48,96))]
         + [(i,(i+1)%48,(i+1)%48+48,i+48) for i in range(48)], TABLE, FURN, root)
    ring(root.name + ' / base upper contour', (0,.06,.14), .46, parent=root)
    ring(root.name + ' / base floor light', (0,.06,.08), .46, LIGHT, parent=root)


box('Meeting / polished floor', (0,2,-.12), (12,16,.24), FLOOR)
box('Meeting / back wall', (0,10,2.4), (12,.18,4.8))
box('Meeting / right wall', (6,2,2.4), (.18,16,4.8))
box('Meeting / entry wall', (0,-6,2.4), (12,.18,4.8))
box('Meeting / dark ceiling', (0,2,4.85), (12,16,.12))
for x in (-6,-4,-2,0,2,4,6):
    lines('Floor / large slab joint', [((x,-6,.008),(x,10,.008))], QUIET, ARCH)
for y in (-6,-3,0,3,6,9,10):
    lines('Floor / transverse slab joint', [((-6,y,.008),(6,y,.008))], QUIET, ARCH)
for x in (-4.8,-2.4,2.4,4.8):
    lines('Back wall / luminous panel joint', [((x,9.895,.1),(x,9.895,4.65))], LIGHT, ARCH)
for z in (.15,1.25,3.7,4.65):
    lines('Architecture / quiet horizontal seams', [((-6,9.89,z),(6,9.89,z)),((5.895,-6,z),(5.895,10,z))], QUIET, ARCH)
path('Ceiling / luminous inset perimeter', [(-4.9,-4.8,4.70),(4.9,-4.8,4.70),(4.9,8.8,4.70),(-4.9,8.8,4.70)], LIGHT, LIGHTS, closed=True)
for x in (-2.6,2.6):
    lines('Ceiling / longitudinal integrated light', [((x,-4,4.70),(x,8,4.70))], LIGHT, LIGHTS)
box('Table / long black conference top', (0,2.3,1.16), (3.35,8,.12), TABLE, FURN, contour=True)['meeting_table'] = True
box('Table / central pedestal', (0,2.3,.57), (1.65,6.4,1.02), BLACK, FURN, contour=True)
box('Table / recessed cable channel', (0,2.3,1.223), (.34,5.5,.012), BLACK, FURN, contour=True)
for y in (-.4,.95,2.3,3.65,5):
    lines('Table / panel seams', [((-1.675,y,1.225),(-.18,y,1.225)),((.18,y,1.225),(1.675,y,1.225))], QUIET)
for index, y in enumerate((-1.1,.25,1.6,2.95,4.3,5.65)):
    chair(index * 2 + 1, -2.45, y)
    chair(index * 2 + 2, 2.45, y)

box('Presentation / double frame outer', (0,9.78,2.95), (4.7,.10,2.65), TABLE, ARCH, contour=True)
box('Presentation / double frame inner', (0,9.71,2.95), (4.52,.035,2.47), BLACK, ARCH, contour=True)
screen = mesh('Presentation / project screen', [(-2.17,9.68,1.80),(2.17,9.68,1.80),(2.17,9.68,4.10),(-2.17,9.68,4.10)], [(0,1,2,3)], BLACK, ARCH)
uv = screen.data.uv_layers.new(name='Presentation UV')
for polygon in screen.data.polygons:
    for loop in polygon.loop_indices:
        uv.data[loop].uv = [(0,0),(1,0),(1,1),(0,1)][screen.data.loops[loop].vertex_index]
screen['meeting_screen'] = True
box('Presentation / sensor', (0,9.64,1.73), (.12,.025,.045), TABLE, ARCH, contour=True)
box('Storage / low sideboard', (5.28,3.2,.69), (1.12,10.5,1.36), TABLE, DETAIL, contour=True)
for y in (-1.6,.3,2.2,4.1,6,8):
    lines('Storage / cabinet seams', [((4.71,y,.06),(4.71,y,1.34))], QUIET, DETAIL)
box('Globe / square plinth', (5.15,7.4,1.48), (.55,.55,.2), TABLE, DETAIL, contour=True)
for index in range(8):
    globe = ring('Globe / longitude', (0,0,0), .46, EDGE, DETAIL, axis='y')
    globe.rotation_euler.z = index * math.pi / 8
    globe.location = (5.15,7.4,2.04)
for z in (-.3,-.15,0,.15,.3):
    ring('Globe / latitude', (5.15,7.4,2.04+z), math.sqrt(.46**2-z**2), EDGE, DETAIL)

# Glazed outlook: thin native contours, no mirror surfaces or linked city master.
for y in (-6,-2,2,6,10):
    box('Glazing / dark mullion', (-5.98,y,2.4), (.08,.09,4.8), BLACK, WINDOW, contour=True)
for z in (.10,4.65):
    lines('Glazing / continuous rail', [((-5.92,-6,z),(-5.92,10,z))], EDGE, WINDOW)
for y in (-6,-2,2,6):
    pane = mesh('Glazing / clear office window', [(-5.97,y+.06,.10),(-5.97,y+3.94,.10),
                                               (-5.97,y+3.94,4.65),(-5.97,y+.06,4.65)],
                [(0,1,2,3)], GLASS, WINDOW)
    pane['meeting_glazing'] = True
for index in range(18):
    x = -8.3 - (index % 3) * 1.4
    y = -5 + index * .9
    height = 2 + ((index * 7) % 11) * .42
    tower = box(f'Outlook / wire building {index:02d}', (x,y,height/2), (.75,.65,height), BLACK, WINDOW)
    lines(tower.name + ' / skyline edges', [(tower.data.vertices[e.vertices[0]].co, tower.data.vertices[e.vertices[1]].co) for e in tower.data.edges], QUIET, WINDOW)
    for floor in range(1, math.floor(height / .4)):
        path(tower.name + ' / floor contour', [(x-.375,y-.325,floor*.4),(x+.375,y-.325,floor*.4),(x+.375,y+.325,floor*.4),(x-.375,y+.325,floor*.4)], QUIET, WINDOW, closed=True)
for y in (-1,2.5,6):
    lines('Pendant / suspension', [((0,y,4.7),(0,y,4.18))], QUIET, LIGHTS)
    box('Pendant / black fixture', (0,y,4.06), (.20,.20,.24), TABLE, LIGHTS, contour=True)
    ring('Pendant / luminous aperture', (0,y,3.935), .085, LIGHT, LIGHTS)

camera_data = bpy.data.cameras.new('Meeting / presentation camera')
camera = bpy.data.objects.new(camera_data.name, camera_data)
LIGHTS.objects.link(camera)
camera.location = (4.25,-4.55,2.65)
target = Vector((0,3.9,2.1))
camera.rotation_euler = (target-camera.location).to_track_quat('-Z','Y').to_euler()
camera_data.lens = 22
camera_data.clip_end = 100
scene.camera = camera
scene.frame_start = scene.frame_end = 1
scene.render.fps = 30
scene.world = bpy.data.worlds.new('Meeting / black world')
scene.world.use_nodes = True
scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value = (.003,.003,.003,1)
scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value = .04
for y in (-2,3,8):
    data = bpy.data.lights.new('Meeting / gentle ceiling fill', 'AREA')
    data.energy = 30
    data.size = 5
    light = bpy.data.objects.new(data.name, data)
    LIGHTS.objects.link(light)
    light.location = (0,y,4.65)
scene.render.engine = 'CYCLES'
scene.cycles.samples = 32
scene.cycles.use_denoising = True
scene.render.resolution_x = 1360
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
transforms = scene.view_settings.bl_rna.properties['view_transform'].enum_items.keys()
scene.view_settings.view_transform = 'AgX' if 'AgX' in transforms else 'Standard'
scene.render.filepath = str(OUT / 'project-meeting-room-preview.png')
for workspace in bpy.data.screens:
    for area in workspace.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.region_3d.view_perspective = 'CAMERA'
            area.spaces.active.shading.type = 'MATERIAL'
assert len([o for o in scene.objects if o.get('meeting_chair')]) == 12
assert len([o for o in scene.objects if o.get('meeting_table')]) == 1
assert len([o for o in scene.objects if o.get('meeting_screen')]) == 1
assert not any(o.type == 'LIGHT' and o.data.type == 'SPOT' for o in scene.objects)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'project-meeting-room.blend'), compress=True)
(OUT / 'validation.json').write_text(json.dumps({'chairs':12,'tables':1,'screens':1,'elevatorLevel':False,'objects':len(scene.objects),'validation':'passed'}, indent=2)+'\n')
if '--no-render' not in sys.argv:
    bpy.ops.render.render(write_still=True)
