"""Rotate the foreground maglev corridor to run beside the tower's left flank.

Preserve follow-path timing, native carriages, background highway and camera.
Retire the disconnected upper-left interchange. Source datablocks make this
update repeatable.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parent
MASTER = ROOT / 'monochrome-city-solid-tower.blend'
PREFIX = 'Left transit • '
parser = argparse.ArgumentParser()
parser.add_argument('--preview', action='store_true')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
scene = bpy.context.scene
assert scene.name == 'MONO / Wire & Particle City'
assert Path(bpy.data.filepath).resolve() == MASTER
scene.frame_set(1)
scene.view_layers[0].update()
train = scene.objects['Mono • Transit • maglev train']
commuter = scene.objects['Mono • Skyway vehicle']
paths = [scene.objects['Mono • Traffic path • ' + name] for name in ('maglev highway pass', 'highway commuter')]
recovery = bpy.data.collections.get(PREFIX + 'Source recovery')
if not recovery:
    recovery = bpy.data.collections.new(PREFIX + 'Source recovery')
    scene.collection.children.link(recovery)
recovery.hide_render = True
recovery.hide_viewport = True
# Older scene-only library saves omitted unreferenced fake-user datablocks.
# Recover those exact baselines from the local authored recovery copy once.
missing_meshes = [o['left_transit_source'] for o in scene.objects if o.type == 'MESH' and o.get('left_transit_source') and o['left_transit_source'] not in bpy.data.meshes]
missing_curves = [o['left_transit_source'] for o in paths if o.get('left_transit_source') and o['left_transit_source'] not in bpy.data.curves]
if missing_meshes or missing_curves:
    with bpy.data.libraries.load(str(MASTER) + '1', link=False) as (available, loaded):
        assert all(name in available.meshes for name in missing_meshes), 'Missing original highway recovery geometry'
        assert all(name in available.curves for name in missing_curves), 'Missing original route recovery geometry'
        loaded.meshes = missing_meshes
        loaded.curves = missing_curves


def retain_source(source):
    if not any(obj.data == source for obj in recovery.objects):
        obj = bpy.data.objects.new(PREFIX + 'Recovery • ' + source.name, source)
        obj.hide_render = True
        recovery.objects.link(obj)


rotation = Matrix.Rotation(math.pi / 2 - math.atan(.17), 4, 'Z')
old_center = Vector((0, -11.56, 0))
new_center = Vector((-14, -12, 0))
transform = Matrix.Translation(new_center) @ rotation @ Matrix.Translation(-old_center)
tangent = Vector((1, .17, 0)).normalized()
lateral = Vector((-tangent.y, tangent.x, 0))


def foreground(point, supports=False):
    """Classify only the original foreground deck or its authored pier boxes."""
    if supports:
        return any(abs(point.x - x) <= .326 and
                   abs(point.y - (-11.56 + .17 * x)) <= .376 and
                   -.001 <= point.z <= 5.4 + .05 * x + .001
                   for x in range(-32, 33, 8))
    offset = point - old_center
    along, across = offset.dot(tangent), offset.dot(lateral)
    deck_height = 5.8 + along * (.05 / math.sqrt(1 + .17 ** 2))
    return abs(along) <= 32.6 and abs(across) <= 1.8 and abs(point.z - deck_height) <= .9


def in_moving_corridor(obj):
    while obj:
        if obj in (train, commuter):
            return True
        obj = obj.parent
    return False


def upper_interchange(point, supports=False):
    if supports:
        return any(abs(point.x - (-25 + 3.4 * i)) <= .326 and
                   abs(point.y - (-4 - 2 * i)) <= .376 and
                   -.001 <= point.z <= 9.6 - .32 * i + .001 for i in range(6))
    start = Vector((-25, -4, 10))
    direction = Vector((1.7, -1, 0)).normalized()
    side = Vector((-direction.y, direction.x, 0))
    length = math.hypot(19.55, 11.5)
    offset = point - start
    along, across = offset.dot(direction), offset.dot(side)
    height = 10 - along * 1.84 / length
    return -.03 <= along <= length + .03 and abs(across) <= 1.8 and abs(point.z - height) <= .9


preserved = [obj for obj in scene.objects if not in_moving_corridor(obj) and obj not in paths]
sample_frames = (1, 90, 145, 245, 383, 450)
poses = {}
for frame in sample_frames:
    scene.frame_set(frame)
    scene.view_layers[0].update()
    poses[frame] = {obj.name: obj.matrix_world.copy() for obj in preserved}
scene.frame_set(1)

for path in paths:
    source_name = path.get('left_transit_source')
    if not source_name:
        source = path.data.copy()
        source.name = PREFIX + 'Source • ' + path.name
        source.use_fake_user = True
        path['left_transit_source'] = source.name
    else:
        source = bpy.data.curves[source_name]
    retain_source(source)
    inverse = path.matrix_world.inverted()
    for spline, original in zip(path.data.splines, source.splines):
        for point, old in zip(spline.bezier_points, original.bezier_points):
            # AUTO handles are recalculated by Blender from the rotated knots.
            point.co = inverse @ transform @ path.matrix_world @ old.co
            point.handle_left_type = old.handle_left_type
            point.handle_right_type = old.handle_right_type
            if old.handle_left_type != 'AUTO':
                point.handle_left = inverse @ transform @ path.matrix_world @ old.handle_left
            if old.handle_right_type != 'AUTO':
                point.handle_right = inverse @ transform @ path.matrix_world @ old.handle_right

stats = {'corridor': 'left flank', 'deckCenterX': -14, 'railCenterX': -14.65,
         'timing': 'original follow-path action', 'modifiedNetworks': {},
         'removedUpperInterchange': {}}
names = ('Clean outlines • Highway edges', 'Clean outlines • Highway supports',
         'Clean outlines • Secondary guide rails',
         'Mono • 05 Elevated highways • particles 0', 'Mono • 05 Elevated highways • particles 1')
for name in names:
    obj = scene.objects.get(name)
    if not obj:
        continue
    source_name = obj.get('left_transit_source')
    if not source_name:
        source = obj.data.copy()
        source.name = PREFIX + 'Source • ' + name
        source.use_fake_user = True
        obj['left_transit_source'] = source.name
    else:
        source = bpy.data.meshes[source_name]
    retain_source(source)
    support_network = name.endswith('Highway supports')
    guide_network = name.endswith('Secondary guide rails')
    chosen = set()
    removed = set()
    if source.edges:
        for edge in source.edges:
            points = [obj.matrix_world @ source.vertices[i].co for i in edge.vertices]
            if guide_network or all(foreground(p, support_network) for p in points):
                chosen.update(edge.vertices)
            elif all(upper_interchange(p, support_network) for p in points):
                removed.update(edge.vertices)
    else:
        chosen = {v.index for v in source.vertices if foreground(obj.matrix_world @ v.co) or foreground(obj.matrix_world @ v.co, True)}
        removed = {v.index for v in source.vertices if upper_interchange(obj.matrix_world @ v.co) or upper_interchange(obj.matrix_world @ v.co, True)}
    local = obj.matrix_world.inverted() @ transform @ obj.matrix_world
    data = source.copy()
    data.name = PREFIX + 'Edited • ' + name
    data.use_fake_user = False
    for vertex, old in zip(data.vertices, source.vertices):
        vertex.co = local @ old.co if vertex.index in chosen else old.co
    if removed:
        editable = bmesh.new()
        editable.from_mesh(data)
        editable.verts.ensure_lookup_table()
        bmesh.ops.delete(editable, geom=[editable.verts[i] for i in removed], context='VERTS')
        editable.to_mesh(data)
        editable.free()
    old_data = obj.data
    obj.data = data
    if old_data.name.startswith(PREFIX + 'Edited • ') and old_data.users == 0:
        bpy.data.meshes.remove(old_data)
    data.update()
    stats['modifiedNetworks'][name] = len(chosen)
    stats['removedUpperInterchange'][name] = len(removed)
assert stats['modifiedNetworks']['Clean outlines • Secondary guide rails'] == 4
print('CORRIDOR_NETWORKS', stats['modifiedNetworks'])
assert stats['modifiedNetworks']['Clean outlines • Highway edges'] >= 24
assert stats['modifiedNetworks']['Clean outlines • Highway supports'] >= 24
assert stats['removedUpperInterchange']['Clean outlines • Highway edges'] >= 24
assert stats['removedUpperInterchange']['Clean outlines • Highway supports'] >= 24

# Check the complete train envelope, rather than just its animated root.
scene.view_layers[0].update()
local_vertices = []
for obj in scene.objects:
    if obj.type == 'MESH' and in_moving_corridor(obj) and 'Maglev' in obj.name:
        basis = train.matrix_world.inverted() @ obj.matrix_world
        local_vertices.extend(basis @ vertex.co for vertex in obj.data.vertices)
low = Vector(tuple(min(p[i] for p in local_vertices) for i in range(3)))
high = Vector(tuple(max(p[i] for p in local_vertices) for i in range(3)))
corners = [Vector((x, y, z)) for x in (low.x, high.x) for y in (low.y, high.y) for z in (low.z, high.z)]
tower_points = [obj.matrix_world @ v.co for obj in scene.objects
                if obj.type == 'MESH' and not obj.hide_render and
                (obj.name.startswith('Reference tower • ') or obj.name == 'Hero solid • Megatower • central occupied volume')
                for v in obj.data.vertices if (obj.matrix_world @ v.co).z < 20]
tower_left = min(p.x for p in tower_points)
clearance = float('inf')
samples = []
for frame in range(1, 451):
    scene.frame_set(frame)
    scene.view_layers[0].update()
    rightmost = max((train.matrix_world @ corner).x for corner in corners)
    clearance = min(clearance, tower_left - rightmost)
    assert rightmost < -12, (frame, rightmost)
    if frame in sample_frames:
        samples.append({'frame': frame, 'trainPosition': list(train.matrix_world.translation)})
        for obj in preserved:
            assert all(abs(a - b) < 1e-5 for ra, rb in zip(obj.matrix_world, poses[frame][obj.name]) for a, b in zip(ra, rb)), (obj.name, frame)
assert clearance > 1, clearance
stats.update({'routeFramesChecked': 450, 'minimumTowerLateralClearanceMeters': clearance, 'samples': samples})
scene['left_transit_route'] = json.dumps(stats)
scene.frame_set(1)
temporary = ROOT / 'left-transit-saving.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(temporary))
temporary.replace(MASTER)
(ROOT / 'left-transit-route.json').write_text(json.dumps(stats, indent=2) + '\n')
print('LEFT_TRANSIT', json.dumps(stats))
if args.preview:
    floor = scene.objects.get('Mono • dark reflective ground')
    if floor:
        floor.location = (0, 0, -.12)
    scene.frame_set(145)
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 48
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1674
    scene.render.resolution_y = 700
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = str(ROOT / 'left-transit-preview.png')
    bpy.ops.render.render(write_still=True)
