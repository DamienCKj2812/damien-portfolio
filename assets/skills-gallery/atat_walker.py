"""Reference-led AT-AT exhibit: black armor and native thin white contour curves.

No external model downloads or realized point instances are required. Geometry
is authored under one semantic root and remains editable in the gallery master.
"""
import math

import bpy
from mathutils import Vector


PREFIX = 'Gallery • AT-AT / '
EXHIBIT_SCALE = .72


def build_atat_exhibit(scene, collection):
    def material(name, gray, emission=0):
        mat = bpy.data.materials.get(PREFIX + name) or bpy.data.materials.new(PREFIX + name)
        mat.diffuse_color = (gray, gray, gray, 1)
        mat.use_nodes = True
        shader = mat.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Base Color'].default_value = (gray, gray, gray, 1)
        shader.inputs['Emission Color'].default_value = (gray, gray, gray, 1)
        shader.inputs['Emission Strength'].default_value = emission
        shader.inputs['Roughness'].default_value = .72
        return mat

    armor = material('black armor', .001)
    outline = material('white contour light', .88, 1.15)
    detail = material('secondary panel lines', .56, 1.1)
    root = bpy.data.objects.new(PREFIX + 'walker exhibit', None)
    collection.objects.link(root)
    root.location = (0, 3.85, .34)
    root.scale = (EXHIBIT_SCALE,) * 3
    root['centre_exhibit_id'] = 'atat'
    root['exhibit_role'] = 'AT-AT walker / reference-led black armor and white contours'
    root['reference'] = 'User-supplied three-quarter white-outline AT-AT image'
    objects = []

    def link(name, data):
        obj = bpy.data.objects.new(PREFIX + name, data)
        collection.objects.link(obj)
        obj.parent = root
        objects.append(obj)
        return obj

    def lines(name, paths, secondary=False):
        curve = bpy.data.curves.new(PREFIX + name, 'CURVE')
        curve.dimensions = '3D';curve.resolution_u = 1
        curve.bevel_depth = .0019 if secondary else .0027
        curve.bevel_resolution = 0
        for path in paths:
            spline = curve.splines.new('POLY');spline.points.add(len(path) - 1)
            for point, value in zip(spline.points, path): point.co = (*value, 1)
        curve.materials.append(detail if secondary else outline)
        return link(name, curve)

    def mesh(name, vertices, faces, edges=None):
        data = bpy.data.meshes.new(PREFIX + name)
        data.from_pydata(vertices, [], faces);data.materials.append(armor)
        data.update()
        obj = link(name, data)
        if edges is None:
            edges = sorted({tuple(sorted((face[index], face[(index + 1) % len(face)]))) for face in faces for index in range(len(face))})
        lines(name + ' / silhouette', [[vertices[a], vertices[b]] for a, b in edges])
        return obj

    def box(name, center, size):
        c = Vector(center);h = Vector(size) / 2
        verts = [tuple(c + Vector((x * h.x, y * h.y, z * h.z))) for x, y, z in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
        return mesh(name, verts, [(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)])

    def shell(name, rings):
        verts = [point for ring in rings for point in ring]
        faces = [(0,3,2,1), tuple(range(len(verts) - 4, len(verts)))]
        for ring in range(len(rings) - 1):
            for index in range(4):
                a = ring * 4 + index;b = ring * 4 + (index + 1) % 4
                faces.append((a, b, b + 4, a + 4))
        return mesh(name, verts, faces)

    def rectangle(x1, x2, y, z1, z2):
        return [(x1,y,z1),(x2,y,z1),(x2,y,z2),(x1,y,z2),(x1,y,z1)]

    def cylinder(name, center, radius, length, axis='Y', sides=32):
        c = Vector(center)
        direction = Vector((1,0,0)) if axis == 'X' else Vector((0,1,0))
        u = Vector((0,1,0)) if axis == 'X' else Vector((1,0,0))
        v = Vector((0,0,1))
        vertices = [tuple(c + direction * offset + radius * (u * math.cos(index * math.tau / sides) + v * math.sin(index * math.tau / sides))) for offset in [-length/2, length/2] for index in range(sides)]
        faces = [tuple(reversed(range(sides))), tuple(range(sides, sides * 2))]
        faces += [(index, (index+1)%sides, (index+1)%sides+sides, index+sides) for index in range(sides)]
        edges = [(index, (index+1)%sides) for index in range(sides)] + [(index+sides, (index+1)%sides+sides) for index in range(sides)]
        edges += [(index,index+sides) for index in range(0,sides,8)]
        return mesh(name, vertices, faces, edges)

    def ring(center, radius, axis='Y', sides=48):
        x, y, z = center
        return [(x, y + radius * math.cos(index * math.tau / sides), z + radius * math.sin(index * math.tau / sides)) if axis == 'X' else (x + radius * math.cos(index * math.tau / sides), y, z + radius * math.sin(index * math.tau / sides)) for index in range(sides + 1)]

    def beam(name, start, end, width, depth):
        a, b = Vector(start), Vector(end)
        direction = (b - a).normalized()
        u = Vector((0,1,0));v = direction.cross(u).normalized()
        verts = [tuple(center + u * depth/2 * y + v * width/2 * x) for center in [a,b] for x,y in [(-1,-1),(1,-1),(1,1),(-1,1)]]
        return mesh(name, verts, [(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)])

    # Tall chamfered cargo body with large flat side panels and a beveled roof.
    body = shell('main armored body', [
        [(-.96,-.60,2.88),(1.82,-.60,2.88),(1.82,.60,2.88),(-.96,.60,2.88)],
        [(-1.10,-.74,3.08),(2.02,-.74,3.08),(2.02,.74,3.08),(-1.10,.74,3.08)],
        [(-1.16,-.74,4.17),(1.96,-.74,4.17),(1.96,.74,4.17),(-1.16,.74,4.17)],
        [(-1.05,-.63,4.31),(1.84,-.63,4.31),(1.84,.63,4.31),(-1.05,.63,4.31)],
    ])
    body['atat_part'] = 'body'
    box('belly reactor housing', (.35,0,2.81), (2.28,1.02,.26))
    for side in [-1,1]:
        y = side * .746
        panels = [rectangle(-1.02, .48, y, 3.16, 4.09), rectangle(.59, 1.87, y, 3.16, 4.09)]
        panels += [[(.53,y,3.08),(.53,y,4.17)], [(-1.07,y,3.12),(1.94,y,3.12)]]
        lines(f'body side {side} / armor seams', panels)
        hatches = [rectangle(x, x+w, y + side*.003, z, z+h) for x,z,w,h in [(-.91,3.78,.27,.23),(-.98,4.00,.11,.08),(-.38,3.44,.35,.24),(.71,3.93,.24,.14),(1.40,3.29,.22,.19),(1.66,3.91,.13,.11)]]
        for x in [-1.04,.49,.60,1.87]:
            for z in [3.20,3.47,3.75,4.06]: hatches.append(rectangle(x-.022,x+.022,y+side*.006,z-.025,z+.025))
        lines(f'body side {side} / access hatches and fasteners', hatches, True)
        ladder = [[(1.17,y+side*.013,3.10),(1.17,y+side*.013,3.91)],[(1.34,y+side*.013,3.10),(1.34,y+side*.013,3.91)]]
        ladder += [[(1.17,y+side*.015,z),(1.34,y+side*.015,z)] for z in [3.16 + index*.073 for index in range(10)]]
        lines(f'body side {side} / service ladder', ladder, True)
        lines(f'body side {side} / lower angled ribs', [[(x,y*.87,2.89),(x+.07,y,3.075)] for x in [-.72,-.35,.02,.39,.76,1.13,1.50]], True)
    lines('roof / perimeter rail', [[(-1.01,-.60,4.335),(1.80,-.60,4.335),(1.80,.60,4.335),(-1.01,.60,4.335),(-1.01,-.60,4.335)]])
    lines('roof / armor ribs', [[(x,-.62,4.33),(x,.62,4.33)] for x in [-.86,-.41,.04,.49,.94,1.39]], True)

    # Flexible circular neck and a wedge-shaped head with the narrow visor.
    cylinder('neck / armored core', (-1.47,0,3.55), .34, .66, 'X')
    lines('neck / concentric flexible ribs', [ring((x,0,3.55), .37, 'X') for x in [-1.18,-1.28,-1.38,-1.48,-1.58,-1.68,-1.78]])
    head = shell('head / faceted command armor', [
        [(-2.76,-.46,3.19),(-1.78,-.46,3.19),(-1.78,.46,3.19),(-2.76,.46,3.19)],
        [(-2.92,-.53,3.40),(-1.76,-.53,3.40),(-1.76,.53,3.40),(-2.92,.53,3.40)],
        [(-2.77,-.48,3.81),(-1.85,-.48,3.81),(-1.85,.48,3.81),(-2.77,.48,3.81)],
        [(-2.49,-.35,3.94),(-1.91,-.35,3.94),(-1.91,.35,3.94),(-2.49,.35,3.94)],
    ])
    head['atat_part'] = 'head'
    lines('head / forward visor', [[(-2.86,-.38,3.61),(-2.86,.38,3.61),(-2.82,.38,3.72),(-2.82,-.38,3.72),(-2.86,-.38,3.61)], [(-2.845,-.37,3.635),(-2.845,.37,3.635)]])
    box('head / chin armor', (-2.39,0,3.13), (.66,.67,.17))
    for side in [-1,1]:
        y = side * .544
        cylinder(f'head side {side} / circular turret', (-2.17,y,3.56), .235, .09)
        lines(f'head side {side} / turret concentric rings', [ring((-2.17,y+side*.05,3.56), radius) for radius in [.215,.172,.092]])
        cylinder(f'head side {side} / side laser', (-2.48,side*.65,3.58), .035, .91, 'X', 16)
        cylinder(f'head side {side} / side muzzle', (-2.96,side*.65,3.58), .047, .12, 'X', 16)
        lines(f'head side {side} / small hatches', [rectangle(-2.70,-2.55,y,3.74,3.80),rectangle(-1.95,-1.84,y,3.31,3.38),rectangle(-2.61,-2.50,y,3.39,3.45)], True)
    for side in [-1,1]:
        cylinder(f'chin laser {side} / breech', (-2.70,side*.22,3.14), .09, .24, 'X', 20)
        cylinder(f'chin laser {side} / long barrel', (-3.01,side*.22,3.14), .037, .58, 'X', 16)
        cylinder(f'chin laser {side} / ringed muzzle', (-3.32,side*.22,3.14), .050, .13, 'X', 16)
        lines(f'chin laser {side} / collars', [ring((x,side*.22,3.14), .053, 'X', 24) for x in [-2.89,-3.08,-3.26,-3.35]], True)

    # Four separate mechanical legs: circular hips/knees, pistons, and broad feet.
    for front in [-1,1]:
        for side in [-1,1]:
            label = ('front' if front < 0 else 'rear') + (' near' if side < 0 else ' far')
            hip = Vector((-.79 if front < 0 else 1.49, side*.72, 2.73))
            knee = Vector((hip.x + front*.24, side*.82, 1.47))
            ankle = Vector((hip.x + front*.41, side*.86, .49))
            plate_end = hip.lerp(knee, .62)
            limb = beam(label + ' leg / upper armored segment', hip, plate_end, .40, .32)
            limb['atat_leg'] = label
            beam(label + ' leg / exposed upper strut', plate_end, knee, .16, .20)
            for offset in [-.105,.105]:
                lines(label + ' leg / upper hydraulic rods', [[tuple(plate_end + Vector((offset,-.175,0))),tuple(knee + Vector((offset,-.175,.05)))], [tuple(plate_end + Vector((offset,-.15,.07))),tuple(knee + Vector((offset,-.15,.11)))]])
            beam(label + ' leg / narrow shin', knee, ankle, .22, .24)
            for joint, center, radius, width in [('hip',hip,.32,.35),('knee',knee,.23,.32)]:
                cylinder(label + ' leg / ' + joint + ' drum', center, radius, width)
                for face in [-1,1]:
                    surface = center.copy();surface.y += face*(width/2+.004)
                    lines(label + ' leg / ' + joint + f' rings {face}', [ring(surface,r) for r in [radius*.91,radius*.74,radius*.38,radius*.15]])
            for offset in [-.085,.085]:
                lines(label + ' leg / twin hydraulic piston', [[tuple(knee + Vector((offset,-.17,-.10))),tuple(ankle + Vector((offset,-.17,.10)))]])
                lines(label + ' leg / piston sleeve', [[tuple(knee + Vector((offset+.025,-.175,-.16))),tuple(ankle + Vector((offset+.025,-.175,.24)))], [tuple(knee + Vector((offset-.025,-.175,-.16))),tuple(ankle + Vector((offset-.025,-.175,.24)))]], True)
            ax, ay = ankle.x, ankle.y
            shell(label + ' leg / flared ankle armor', [
                [(ax-.31,ay-.26,.24),(ax+.31,ay-.26,.24),(ax+.31,ay+.26,.24),(ax-.31,ay+.26,.24)],
                [(ax-.21,ay-.19,.65),(ax+.21,ay-.19,.65),(ax+.21,ay+.19,.65),(ax-.21,ay+.19,.65)],
            ])
            shell(label + ' foot / flared pad', [
                [(ax-.44,ay-.37,0),(ax+.44,ay-.37,0),(ax+.44,ay+.37,0),(ax-.44,ay+.37,0)],
                [(ax-.39,ay-.33,.17),(ax+.39,ay-.33,.17),(ax+.39,ay+.33,.17),(ax-.39,ay+.33,.17)],
                [(ax-.30,ay-.25,.25),(ax+.30,ay-.25,.25),(ax+.30,ay+.25,.25),(ax-.30,ay+.25,.25)],
            ])
            for edge_x in [-1,1]:
                for edge_y in [-1,1]: box(label + f' foot / toe tab {edge_x} {edge_y}', (ax+edge_x*.43,ay+edge_y*.31,.045), (.18,.20,.09))
            lines(label + ' leg / ankle plates', [rectangle(ax-.15,ax+.15,ay-.27,.31,.52)], True)

    # Match the reference's tall cargo armor and larger command head, while
    # retaining circular turrets and staying beneath the gallery ceiling.
    for obj in objects:
        name = obj.name.removeprefix(PREFIX)
        points = [vertex.co for vertex in obj.data.vertices] if obj.type == 'MESH' else [point.co for spline in obj.data.splines for point in spline.points]
        if name.startswith(('main armored body','body side','roof /')):
            for point in points:
                if point.z > 3.08: point.z = 3.08 + (point.z - 3.08) * 1.4
        elif name.startswith(('head /','head side','chin laser','neck /')):
            turret = 'circular turret' in name or 'turret concentric rings' in name
            for point in points:
                point.z += .30
                if not name.startswith('neck /'):
                    point.x = point.x - .1025 if turret else -1.76 + (point.x + 1.76) * 1.25
        if obj.type == 'MESH': obj.data.update()
    scene.view_layers[0].update()
    vertices = [obj.matrix_world @ vertex.co for obj in objects if obj.type == 'MESH' for vertex in obj.data.vertices]
    lo = [min(point[axis] for point in vertices) for axis in range(3)]
    hi = [max(point[axis] for point in vertices) for axis in range(3)]
    root['bounds_min'] = lo;root['bounds_max'] = hi
    return {'id':'atat','root':root.name,'style':'Black armored surfaces with fine white contour lines',
            'bounds_min':lo,'bounds_max':hi,'dimensions_m':[hi[axis]-lo[axis] for axis in range(3)],
            'plinth_rect':[-.20,3.85,7.40,3.20],'legs':4,'display_scale':EXHIBIT_SCALE,
            'reference':'User-supplied AT-AT outline image'}
