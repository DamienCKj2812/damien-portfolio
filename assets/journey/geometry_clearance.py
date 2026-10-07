"""Clear native city points/centerlines from the integration's interior voids."""
import bpy
from mathutils import Vector


def inside_box(point, bounds):
    low, high = bounds
    return all(low[i] <= point[i] <= high[i] for i in range(3))


def outside_segments(start, end, boxes):
    """Subtract axis-aligned voids without dropping the exterior of long lines."""
    intervals = [(0.0, 1.0)]
    direction = end - start
    for low, high in boxes:
        entry, exit = 0.0, 1.0
        for axis in range(3):
            if abs(direction[axis]) < 1e-8:
                if not low[axis] <= start[axis] <= high[axis]:
                    entry, exit = 1.0, 0.0
                    break
            else:
                a = (low[axis] - start[axis]) / direction[axis]
                b = (high[axis] - start[axis]) / direction[axis]
                entry, exit = max(entry, min(a, b)), min(exit, max(a, b))
        if entry >= exit:
            continue
        remaining = []
        for a, b in intervals:
            if b <= entry or a >= exit:
                remaining.append((a, b))
            else:
                if a < entry:
                    remaining.append((a, entry))
                if b > exit:
                    remaining.append((exit, b))
        intervals = remaining
    return intervals


def clear_city_sources(objects, cutters):
    """Edit integration-copy meshes only; animated actors retain their paths."""
    boxes = []
    for cutter in cutters:
        corners = [cutter.matrix_world @ Vector(p) for p in cutter.bound_box]
        boxes.append(([min(p[i] for p in corners) for i in range(3)],
                      [max(p[i] for p in corners) for i in range(3)]))
    changed = []
    for obj in objects:
        if obj.type != 'MESH' or 'radius' not in obj.data.attributes or obj.data.polygons:
            continue
        ancestor = obj
        animated = False
        while ancestor:
            if ancestor.animation_data and ancestor.animation_data.action:
                animated = True
                break
            ancestor = ancestor.parent
        if animated:
            continue
        old = obj.data
        world = obj.matrix_world
        inverse = world.inverted()
        radii = old.attributes['radius'].data
        vertices, edges, values = [], [], []
        if old.edges:
            modified = False
            for edge in old.edges:
                i, j = edge.vertices
                start, end = world @ old.vertices[i].co, world @ old.vertices[j].co
                intervals = outside_segments(start, end, boxes)
                modified |= intervals != [(0.0, 1.0)]
                for a, b in intervals:
                    index = len(vertices)
                    vertices.extend([tuple(inverse @ start.lerp(end, t)) for t in [a, b]])
                    edges.append((index, index + 1))
                    values.extend([radii[i].value + (radii[j].value - radii[i].value) * t for t in [a, b]])
        else:
            for vertex, radius in zip(old.vertices, radii):
                if not any(inside_box(world @ vertex.co, box) for box in boxes):
                    vertices.append(tuple(vertex.co))
                    values.append(radius.value)
            modified = len(vertices) != len(old.vertices)
        if not modified:
            continue
        changed.append({'object': obj.name, 'vertices_before': len(old.vertices), 'vertices_after': len(vertices)})
        mesh = bpy.data.meshes.new(old.name + ' / atrium clearance')
        mesh.from_pydata(vertices, edges, [])
        mesh.update()
        radius = mesh.attributes.new('radius', 'FLOAT', 'POINT')
        radius.data.foreach_set('value', values)
        for material in old.materials:
            mesh.materials.append(material)
        obj.data = mesh
    return changed


def fit_r1_doors(scene, prefix=''):
    """Seal the fitted R1 aperture while preserving the authored slide timing."""
    scene.view_layers[0].update()
    for side in ['left', 'right']:
        door = scene.objects[prefix + 'Lobby • Elevator R1 / ' + side + ' door leaf']
        edge = scene.objects[door.name + ' / feature edges']
        door.data = door.data.copy()
        for vertex in door.data.vertices:
            vertex.co.x *= 1.06 / 1.02
            vertex.co.z *= 3.12 / 3.08
        door.data.update()
        edge.data = edge.data.copy()
        to_door = door.matrix_world.inverted() @ edge.matrix_world
        from_door = to_door.inverted()
        for spline in edge.data.splines:
            for point in spline.points:
                local = to_door @ Vector(point.co[:3])
                local.x *= 1.06 / 1.02
                local.z *= 3.12 / 3.08
                point.co = (*(from_door @ local), point.co.w)
        pocket = scene.objects[prefix + 'Lobby • Navigation / R1 door pocket ' + side]
        pocket.data = pocket.data.copy()
        for vertex in pocket.data.vertices:
            vertex.co.z *= 3.18 / 3.10
        pocket.data.update()
    scene.view_layers[0].update()
