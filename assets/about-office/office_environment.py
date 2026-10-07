"""Authored 360-degree office shell, reference-inspired library and inset aquarium.

Called by build_office.py; geometry stays in Blender Z-up coordinates and exports
as ordinary native surfaces/lines. A local RNG preserves existing office assets.
"""
import math
import random
import json

import bpy
from mathutils import Matrix, Vector


def build_environment(scene, box, lines, text, material, particles, ellipse):
    rng = random.Random(36047)
    group = '11'
    wall = material('Solid charcoal interior walls', .004, roughness=.9)
    joinery = material('Built-in shelving charcoal', .010, roughness=.65)
    backing = material('Library recessed black backing', .003, roughness=.9)
    cabinet = material('Library near-black cabinetry', .005, roughness=.75)
    silver = material('Interior detail silver', .24, emission=1.1)
    quiet = material('Interior secondary edges', .055, emission=.7)
    light = material('Recessed shelf and aquarium lights', .46, emission=2.3)
    paper = material('Library page blocks', .055, roughness=.9)
    art = material('Framed artwork backing', .012, roughness=.85)

    def surface(name, vertices, faces, mat):
        mesh = bpy.data.meshes.new('Office • ' + name)
        mesh.from_pydata(vertices, [], faces);mesh.materials.append(mat)
        obj = bpy.data.objects.new('Office • ' + name, mesh)
        bpy.data.collections['Office • 11 Interior library & aquarium'].objects.link(obj)
        return obj

    # The skyline-facing +Y wall remains glazed. The other three directions
    # are enclosed, with the existing 2.6 x 3.2 m elevator portal kept clear.
    box('Right room wall', (6.10, -1, 2.30), (.20, 12, 4.60), wall, '01', outline=False)
    for sign in [-1, 1]:
        box('Back solid wall / side', (sign * 3.65, -6.82, 2.30), (4.70, .10, 4.60), wall, '01', outline=False)
    box('Back solid wall / entry header', (0, -6.82, 3.90), (2.60, .10, 1.40), wall, '01', outline=False)
    lines('Plain back wall / elevator reveal', [[(-1.3, -6.755, .02), (-1.3, -6.755, 3.2),
                                               (1.3, -6.755, 3.2), (1.3, -6.755, .02)]], quiet, .003, '01')
    scene['Authored entry surround'] = True
    # Flush dark entry panels complete the plain rear wall during a room visit.
    # The browser clears this render-role while arriving/returning so the
    # existing elevator route is never obscured by a static authored wall.
    for sign in [-1, 1]:
        panel = box('Back solid wall / flush entry panel', (sign * .65, -6.82, 1.60),
                    (1.30, .10, 3.20), wall, '01', outline=False)
        panel['office_entry_door'] = True

    # Solid left wall is constructed around an actual recessed tank opening.
    lo_y, hi_y, lo_z, hi_z = -4.6, 1.6, 1.05, 3.05
    for name, center, size in [
        ('Left wall / lower solid panel', (-6.10, -1, lo_z / 2), (.20, 12, lo_z)),
        ('Left wall / upper solid panel', (-6.10, -1, (hi_z + 4.6) / 2), (.20, 12, 4.6 - hi_z)),
        ('Left wall / entrance end', (-6.10, (-7 + lo_y) / 2, 2.05), (.20, lo_y + 7, hi_z - lo_z)),
        ('Left wall / window end', (-6.10, (hi_y + 5) / 2, 2.05), (.20, 5 - hi_y, hi_z - lo_z)),
    ]:
        box(name, center, size, wall, '01', outline=False)
    lines('Solid side walls / quiet skirting', [[(-5.98, -6.77, .10), (-5.98, 5, .10)],
                                               [(5.98, -6.77, .10), (5.98, 5, .10)]], quiet, .002, '01')

    # Quiet feature wall: one large rounded artwork above a long low console,
    # balanced by a single narrow, illuminated end bookshelf.
    bay_centers = [-4.85]
    shelf_heights = [.92, 1.98, 3.06, 4.18]
    book_count = 0
    frame_count = 0

    def wall_text(name, body, y, z, size=.04, x=5.245):
        obj = text(name, body, (x, y, z), size, group, mat=silver)
        obj.rotation_euler = (math.pi / 2, 0, -math.pi / 2)
        return obj

    def standing_book(name, y, base, width, height, gray, lean=0):
        nonlocal book_count
        book_count += 1
        cover = material(name + ' / cloth', gray, roughness=.85)
        root = box(name, (5.47, y, base + height / 2), (.38, width, height), cover, group,
                   edge_mat=quiet, rotation=(lean, 0, 0))
        # Page block and spine bands are kept parent-local when a book leans.
        pages = box(name + ' / pages', (.018, 0, .012), (.31, width * .72, height - .025), paper, group, outline=False)
        pages.parent = root
        bands = lines(name + ' / spine bands', [[(-.197, -width * .42, z), (-.197, width * .42, z)]
                                               for z in [-height * .32, height * .32]], silver, .0016, group)
        bands.parent = root

    def framed_picture(name, y, base, width, height, variant):
        nonlocal frame_count
        frame_count += 1
        z = base + height / 2
        box(name + ' / frame', (5.43, y, z), (.09, width, height), joinery, group, edge_mat=silver)
        box(name + ' / matte', (5.379, y, z), (.012, width * .87, height * .87), paper, group, outline=False)
        box(name + ' / artwork', (5.368, y, z), (.008, width * .70, height * .72), art, group, outline=False)
        x = 5.359
        if variant % 2:
            paths = [ellipse((x, y, z + height * .12), width * .13, height * .12, 'YZ', 24),
                     [(x, y - width * .24, z - height * .25), (x, y - width * .16, z - height * .04),
                      (x, y + width * .16, z - height * .04), (x, y + width * .24, z - height * .25)]]
        else:
            paths = [[(x, y - width * .31, z - height * .24), (x, y - width * .09, z + height * .14),
                      (x, y + width * .09, z - height * .05), (x, y + width * .20, z + height * .03),
                      (x, y + width * .31, z - height * .24)],
                     ellipse((x, y + width * .18, z + height * .20), width * .06, height * .05, 'YZ', 20)]
        lines(name + ' / original monochrome illustration', paths, silver, .002, group)

    titles = ['POSSIBLE', '', 'IDEAS']
    for bay, center in enumerate(bay_centers):
        width = 1.65
        box('Library bay %d / recessed backing' % bay, (5.90, center, 2.48), (.08, width, 3.50), backing, group, outline=False)
        box('Library bay %d / lower cabinet' % bay, (5.65, center, .43), (.60, width, .78), cabinet, group, edge_mat=quiet)
        for side in [-1, 1]:
            y = center + side * width / 2
            box('Library bay %d / vertical stile' % bay, (5.64, y, 2.47), (.62, .055, 3.52), joinery, group, edge_mat=quiet)
        for door in [-1, 1]:
            y = center + door * .40
            box('Library cabinet / plain door', (5.337, y, .43), (.025, .77, .71), cabinet, group, edge_mat=quiet)
            lines('Library cabinet / recessed pull', [[(5.319, y - .12, .66), (5.319, y + .12, .66)]], silver, .002, group)
        for row, base in enumerate(shelf_heights):
            box('Library bay %d / floating shelf %d' % (bay, row), (5.61, center, base), (.64, width, .045), joinery, group, edge_mat=silver)
            lines('Library bay %d / recessed shelf light %d' % (bay, row), [[(5.36, center - .74, base - .032),
                                                                          (5.36, center + .74, base - .032)]], light, .0025, group)
            if row == len(shelf_heights) - 1:
                continue
            base += .026
            if row == 1:
                framed_picture('Library picture %d-%d' % (bay, row), center + .26, base, .48, .60, 0)
            else:
                stack_y = center + (.25 if row == 0 else -.32)
                for stack in range(2):
                    box('Library bay %d / stacked volume %d-%d' % (bay, row, stack),
                        (5.48, stack_y, base + .03 + stack * .058), (.34, .60 - stack * .055, .055),
                        joinery, group, edge_mat=quiet)
                wall_text('Library shelf caption', titles[row], stack_y, base + .035, .040)
            cursor = center + (.24 if row == 2 else -.64)
            for index in range(4 if row == 1 else 3):
                thickness = rng.uniform(.065, .115)
                standing_book('Library book %d-%d-%d' % (bay, row, index), cursor, base,
                              thickness, rng.uniform(.34, .57), rng.uniform(.008, .040),
                              .13 if index == 0 and row % 2 else 0)
                cursor += thickness + .025
    box('Feature wall / tall divider', (5.70, -3.73, 2.25), (.56, .18, 4.40), backing, group, edge_mat=quiet)
    box('Feature wall / outer end pillar', (5.72, 3.65, 2.25), (.52, .20, 4.40), backing, group, edge_mat=quiet)
    lines('Feature wall / end pillar inset light', [[(5.445, 3.65, .22), (5.445, 3.65, 4.19)]], light, .0035, group)

    box('Feature console / low cabinet', (5.66, -.08, .53), (.64, 6.90, .84), cabinet, group, edge_mat=quiet)
    box('Feature console / continuous top', (5.62, -.08, .98), (.72, 6.94, .055), joinery, group, edge_mat=silver)
    for index in range(4):
        y = -2.64 + index * 1.71
        box('Feature console / plain door %d' % index, (5.325, y, .54), (.025, 1.67, .75), cabinet, group, edge_mat=quiet)
    lines('Feature console / upper edge light', [[(5.248, -3.49, 1.011), (5.248, 3.33, 1.011)]], light, .002, group)
    lines('Feature console / recessed plinth light', [[(5.327, -3.47, .14), (5.327, 3.31, .14)]], light, .003, group)
    for index, title in enumerate(['SYSTEMS', 'HUMANITY']):
        z = 1.05 + index * .075
        box('Feature console / stacked book ' + title, (5.48, -2.58, z), (.38, .92 - index * .07, .070), joinery, group, edge_mat=quiet)
        wall_text('Feature console / book caption ' + title, title, -2.58, z, .046, x=5.279)

    # A softly rounded architectural art panel; native curves carry the glow.
    panel_y, panel_z = -.12, 2.63
    perimeter = []
    for cy, cz, start in [(2.80, .77, 0), (-2.80, .77, math.pi / 2),
                          (-2.80, -.77, math.pi), (2.80, -.77, math.pi * 1.5)]:
        for step in range(13):
            angle = start + step * math.pi / 24
            perimeter.append((5.82, panel_y + cy + .18 * math.cos(angle), panel_z + cz + .18 * math.sin(angle)))
    surface('Feature wall / rounded art panel', perimeter, [tuple(reversed(range(len(perimeter))))], backing)
    perimeter.append(perimeter[0])
    lines('Feature wall / fine rounded frame', [[(5.805, y, z) for _, y, z in perimeter]], silver, .0017, group)
    lines('Feature wall / continuous rounded frame light',
          [[(5.802, y, z) for _, y, z in perimeter]], light, .0035, group)
    lines('Feature wall / quiet outer frame', [[(5.83, panel_y + (y - panel_y) * 1.025,
                                                   panel_z + (z - panel_z) * 1.035) for _, y, z in perimeter]], quiet, .002, group)
    lines('Feature wall / original orbital artwork', [
        ellipse((5.795, 1.58, 2.65), .44, .56, 'YZ', 72),
        ellipse((5.795, .75, 2.90), .028, .036, 'YZ', 24),
        ellipse((5.795, .91, 2.59), .015, .020, 'YZ', 20),
        [(5.795, -.62, 2.31), (5.795, -.77, 2.31)],
    ], silver, .0017, group)
    wall_text('Feature wall / quieter tomorrow', 'A\nQ U I E T E R\nT O M O R R O W', -.98, 2.72, .095, x=5.793)

    # Restrained botanical accent at the far end of the console.
    box('Feature console / small planter', (5.58, 2.57, 1.10), (.34, .43, .18), cabinet, group, edge_mat=quiet)
    plant_paths = []
    for branch in range(7):
        base_y = 2.57
        spread = (branch - 3) * .075
        height = .48 + .21 * math.sin(branch + .6) ** 2
        plant_paths.append([(5.50, base_y + spread * t / 16, 1.19 + height * t / 16) for t in range(17)])
        for leaf in range(1, 5):
            t = leaf / 5
            y, z = base_y + spread * t, 1.19 + height * t
            for side in [-1, 1]:
                path = []
                for step in range(17):
                    u = step / 16
                    path.append((5.49, y + side * .09 * u,
                                 z + .055 * u + .014 * math.sin(u * math.pi)))
                for step in range(16, -1, -1):
                    u = step / 16
                    path.append((5.49, y + side * .09 * u,
                                 z + .055 * u - .014 * math.sin(u * math.pi)))
                plant_paths.append(path)
    lines('Feature console / delicate botanical branches', plant_paths, silver, .0015, group)

    # Embedded aquarium: opaque recess, transparent front pane, illuminated
    # reveals, gravel, rocks, aquatic plants, fish silhouettes and bubbles.
    tank_back = material('Aquarium dark recess', .003, roughness=.8)
    gravel = material('Aquarium pale gravel', .017, roughness=1)
    fish_mat = material('Aquarium fish silver surfaces', .040, emission=.4, roughness=.7)
    water = material('Aquarium transparent front glass', .035, roughness=.15)
    tree = water.node_tree
    principled = tree.nodes.get('Principled BSDF')
    transparent = tree.nodes.new('ShaderNodeBsdfTransparent')
    mix = tree.nodes.new('ShaderNodeMixShader');mix.inputs[0].default_value = .10
    tree.links.new(transparent.outputs[0], mix.inputs[1]);tree.links.new(principled.outputs[0], mix.inputs[2])
    tree.links.new(mix.outputs[0], tree.nodes.get('Material Output').inputs['Surface'])
    box('Aquarium / opaque recessed back', (-6.66, -1.50, 2.05), (.06, 6.20, 2.0), tank_back, group, outline=False)
    for name, center, size in [
        ('Aquarium / top reveal', (-6.30, -1.50, 3.04), (.75, 6.28, .08)),
        ('Aquarium / bottom reveal', (-6.30, -1.50, 1.06), (.75, 6.28, .08)),
        ('Aquarium / entrance jamb', (-6.30, -4.60, 2.05), (.75, .08, 2.02)),
        ('Aquarium / window jamb', (-6.30, 1.60, 2.05), (.75, .08, 2.02)),
    ]:
        box(name, center, size, joinery, group, outline=False)
    lines('Aquarium / fine recessed frame', [
        [(-5.925, -4.64, 1.02), (-5.925, -4.64, 3.08), (-5.925, 1.64, 3.08),
         (-5.925, 1.64, 1.02), (-5.925, -4.64, 1.02)],
        [(-5.937, -4.55, 1.10), (-5.937, -4.55, 3.00), (-5.937, 1.55, 3.00),
         (-5.937, 1.55, 1.10), (-5.937, -4.55, 1.10)],
    ], silver, .0015, group)

    def bed_height(y):
        return 1.19 + .018 * math.sin((y + 4.5) * 1.6) + .065 * (
            math.exp(-((y + 3.95) / .65) ** 2) + math.exp(-((y - .85) / .65) ** 2))

    # A low, gently contoured substrate leaves the middle of the tank open.
    vertices, faces = [], []
    contour = []
    for index in range(33):
        y = -4.50 + index * 6 / 32
        z = bed_height(y)
        vertices.extend([(-6.59, y, 1.09), (-6.035, y, 1.09), (-6.035, y, z), (-6.59, y, z + .018)])
        contour.append((-6.029, y, z))
        if index:
            a, b = (index - 1) * 4, index * 4
            faces.extend([(a + 2, b + 2, b + 3, a + 3), (a + 1, b + 1, b + 2, a + 2),
                          (a, a + 3, b + 3, b), (a, b, b + 1, a + 1)])
    faces.extend([(0, 1, 2, 3), (128, 131, 130, 129)])
    surface('Aquarium / sculpted substrate', vertices, faces, gravel)
    lines('Aquarium / quiet substrate contour', [contour], quiet, .0015, group)
    box('Aquarium / transparent viewing pane', (-5.982, -1.50, 2.05), (.008, 6.08, 1.86), water, group, outline=False)
    lines('Aquarium / concealed upper light', [[(-6.10, -4.47, 2.96), (-6.10, 1.47, 2.96)]], light, .005, group)
    # Smooth tapered ribbons replace the repeating angular plant pattern.
    for index, (y, height, count) in enumerate([(-3.97, 1.60, 7), (-3.12, .42, 5),
                                               (.80, 1.36, 7), (-.10, .48, 5)]):
        paths = []
        for leaf in range(count):
            spread = (leaf / (count - 1) - .5) * .75
            length = height * (.65 + .35 * math.sin((leaf + 1) * 1.9) ** 2)
            base_y = y + spread * .10
            base_z = bed_height(base_y)
            left, right = [], []
            for step in range(33):
                t = step / 32
                center_y = base_y + spread * t + math.sin(t * math.pi * 2.25 + leaf * .7) * min(.20, length * .12) * t
                z = base_z + length * t
                width = .025 * math.sin(t * math.pi) ** .8
                x = -6.25 - leaf * .018
                left.append((x, center_y - width, z))
                right.append((x, center_y + width, z))
            paths.append(left + list(reversed(right)) + [left[0]])
        lines('Aquarium / aquatic plant %02d' % index, paths, silver, .0025, group)
    stone = material('Aquarium near-black rounded stones', .008, roughness=.9)
    for index, (y, radius) in enumerate([(-4.25, .16), (-3.62, .21), (-3.28, .10),
                                        (.40, .21), (.82, .18), (1.10, .11)]):
        base = bed_height(y) - .015
        center = (-6.22, y, base)
        vertices, faces = [], []
        for level in [0, .50, .85]:
            r = math.sqrt(1 - level * level)
            vertices.extend([(center[0] + radius * .60 * r * math.cos(i * math.tau / 16),
                              y + radius * 1.3 * r * math.sin(i * math.tau / 16),
                              base + radius * .72 * level) for i in range(16)])
        vertices.append((center[0], y, base + radius * .72))
        for ring in range(2):
            for i in range(16):
                j = (i + 1) % 16
                faces.append((ring * 16 + i, ring * 16 + j, (ring + 1) * 16 + j, (ring + 1) * 16 + i))
        faces.extend([(32 + i, 32 + (i + 1) % 16, 48) for i in range(16)])
        surface('Aquarium / rounded stone %02d / surface' % index, vertices, faces, stone)
        lines('Aquarium / rounded stone %02d' % index,
              [[(center[0] + .006, y + radius * 1.3 * math.cos(i * math.pi / 24),
                 base + radius * .72 * math.sin(i * math.pi / 24)) for i in range(25)]], quiet, .0017, group)
    loop_frames = 720

    def animated_root(name, kind):
        obj = bpy.data.objects.new('Office • ' + name, None)
        bpy.data.collections['Office • 11 Interior library & aquarium'].objects.link(obj)
        obj['aquarium_actor'] = kind
        return obj

    def cycle_keys(root):
        for layer in root.animation_data.action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        for key in curve.keyframe_points:
                            key.interpolation = 'LINEAR'
                        curve.modifiers.new('CYCLES')

    for index, (y, z, length, direction) in enumerate([(-2.78, 2.38, .18, 1),
                                                      (-1.72, 1.94, .17, 1),
                                                      (.08, 2.34, .15, -1)]):
        x = -6.30 - index * .015;height = length * .43
        # Tapered lens-shaped bodies and a simple tail match the quiet reference.
        body = [(x, y + length * math.cos(i * math.tau / 40),
                 z + height * math.sin(i * math.tau / 40)) for i in range(41)]
        tail_y = y - direction * length
        tail = [(x, tail_y, z), (x, tail_y - direction * length * .55, z + height * .85),
                (x, tail_y - direction * length * .55, z - height * .85), (x, tail_y, z)]
        root = animated_root('Aquarium fish %02d / swim route' % index, 'fish')
        root.location = (x, y, z)
        children = [surface('Aquarium fish %02d / silver body' % index, body[:-1], [tuple(range(len(body) - 1))], fish_mat),
                    lines('Aquarium fish %02d / contours' % index, [body, tail], silver, .0018, group),
                    particles('Aquarium fish %02d / eyes' % index,
                              [(x + side * .006, y + direction * length * .65, z + height * .22)
                               for side in [-1, 1]], .006, group, light)]
        for child in children:
            child.parent = root
            child.matrix_parent_inverse = Matrix.Translation(Vector((-x, -y, -z)))
        amplitude = [.52, .65, .75][index]
        laps = [1, 2, 1][index]
        for frame in range(1, loop_frames + 2):
            angle = math.tau * (frame - 1) / loop_frames * laps
            root.location = (x, y + direction * amplitude * math.sin(angle), z + .07 * math.sin(angle * 2))
            local_angle = angle % math.tau
            heading = math.atan2(.20 * math.sin(local_angle), math.cos(local_angle))
            if heading < 0:
                heading += math.tau
            root.rotation_euler.z = heading + math.floor(angle / math.tau) * math.tau
            root.keyframe_insert(data_path='location', frame=frame)
            root.keyframe_insert(data_path='rotation_euler', frame=frame)
        cycle_keys(root)
    for column_index, column in enumerate([-3.16, -.95]):
        for step in range(8):
            root = animated_root('Aquarium bubble %02d-%02d / rise loop' % (column_index, step), 'bubble')
            ring = lines('Aquarium bubble %02d-%02d / ring' % (column_index, step),
                         [ellipse((0, 0, 0), .009 + step * .0007, .012 + step * .0007, 'YZ', 16)], quiet, .0011, group)
            ring.parent = root
            for frame in range(1, loop_frames + 2):
                phase = ((frame - 1) / 120 + (step + .35) / 8 + column_index * .025) % 1
                root.location = (-6.08, column + math.sin(phase * math.tau + step) * .025, 1.30 + phase * 1.48)
                fade = max(.001, min(1, phase / .10, (1 - phase) / .10))
                size = (.72 + phase * .28) * fade
                root.scale = (size, size, size)
                root.keyframe_insert(data_path='location', frame=frame)
                root.keyframe_insert(data_path='scale', frame=frame)
            cycle_keys(root)
    scene['Aquarium loop frames'] = loop_frames
    scene['Aquarium animation bounds'] = json.dumps({'min': [-6.65, -4.55, 1.09], 'max': [-5.98, 1.55, 3.05]})
    scene['Environment layout'] = 'Right: rounded art panel, low console and end library. Left: minimal recessed aquarium. Back: plain solid wall around elevator portal.'
    return {'right_wall': 'Rounded orbital art panel above a long low console, with one narrow lit end bookshelf',
            'library_books': book_count, 'framed_pictures': frame_count,
            'left_wall': 'Minimal recessed aquarium with end-planted flowing ribbons and contoured substrate', 'aquarium_fish': 3,
            'aquarium_animation': {'loop_frames': loop_frames, 'fps': 30, 'fish_routes': 3, 'bubble_loops': 16},
            'back_wall': 'Plain solid wall with flush entry panels that clear during elevator transitions'}
