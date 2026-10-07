"""Author a separate autonomous train on the retained rear highway."""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
MASTER = ROOT / 'monochrome-city-solid-tower.blend'
COLLECTION = 'Background transit • Autonomous train'
parser = argparse.ArgumentParser()
parser.add_argument('--preview', action='store_true')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
scene = bpy.context.scene
assert scene.name == 'MONO / Wire & Particle City'
assert Path(bpy.data.filepath).resolve() == MASTER
scene.frame_set(1)
scene.view_layers[0].update()
source = scene.objects['Mono • Transit • maglev train']
sample_frames = (1, 90, 145, 245, 383, 450)
originals = [obj for obj in scene.objects if not any(c.name == COLLECTION for c in obj.users_collection)]
poses = {}
for frame in sample_frames:
    scene.frame_set(frame)
    scene.view_layers[0].update()
    poses[frame] = {obj.name: obj.matrix_world.copy() for obj in originals}
scene.frame_set(1)
old = bpy.data.collections.get(COLLECTION)
if old:
    for obj in list(old.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(old)
collection = bpy.data.collections.new(COLLECTION)
scene.collection.children.link(collection)
mapping = {}
for obj in (source, *source.children_recursive):
    clone = obj.copy()
    clone.animation_data_clear()
    clone.name = 'Background transit • ' + ('maglev train' if obj == source else obj.name)
    collection.objects.link(clone)
    mapping[obj] = clone
for obj, clone in mapping.items():
    clone.parent = mapping.get(obj.parent)
    clone.matrix_parent_inverse = obj.matrix_parent_inverse.copy()
    clone.matrix_basis = obj.matrix_basis.copy()
train = mapping[source]
for constraint in list(train.constraints):
    train.constraints.remove(constraint)
train.rotation_euler = (0, 0, 0)
train.scale = (1, 1, 1)
motion = {'startFrame': 1, 'endFrame': 450, 'mode': 'one-way',
          'passFrames': 2000, 'resetFrames': 60, 'phase': 1020}
train['city_autonomous'] = True
train['city_motion'] = json.dumps(motion)
for frame, x in ((1, -1000), (450, 1000)):
    train.location = (x, 7, 7.6)
    train.keyframe_insert(data_path='location', frame=frame)
action = train.animation_data.action
curves = action.fcurves if hasattr(action, 'fcurves') else [curve for layer in action.layers for strip in layer.strips for bag in getattr(strip, 'channelbags', []) for curve in bag.fcurves]
for curve in curves:
    for key in curve.keyframe_points:
        key.interpolation = 'LINEAR'

# The rear road's existing deck/guardrails are retained. Add its track gauge.
mesh = bpy.data.meshes.new('Background transit • Guide rails')
mesh.from_pydata([(-50, 6.64, 7.56), (50, 6.64, 7.56), (-50, 7.36, 7.56), (50, 7.36, 7.56)], [(0, 1), (2, 3)], [])
mesh.attributes.new('radius', 'FLOAT', 'POINT').data.foreach_set('value', [.008] * 4)
rails = bpy.data.objects.new(mesh.name, mesh)
collection.objects.link(rails)
rails['city_render_kind'] = 'lines'
template = scene.objects['Clean outlines • Secondary guide rails'].modifiers[0].node_group
rails.modifiers.new('Native rear guide rails', 'NODES').node_group = template

for frame in sample_frames:
    scene.frame_set(frame)
    scene.view_layers[0].update()
    for obj in originals:
        assert all(abs(a - b) < 1e-5 for ra, rb in zip(obj.matrix_world, poses[frame][obj.name]) for a, b in zip(ra, rb)), (obj.name, frame)
    assert abs(train.matrix_world.translation.y - 7) < 1e-6
    assert abs(train.matrix_world.translation.z - 7.6) < 1e-5
# Both reset endpoints must be entirely outside every route camera, including
# ultrawide views. Check the full three-car bounds, not just the train root.
scene.frame_set(1)
scene.view_layers[0].update()
local = []
for obj in train.children_recursive:
    if obj.type == 'MESH':
        basis = train.matrix_world.inverted() @ obj.matrix_world
        local.extend(basis @ v.co for v in obj.data.vertices)
low = [min(p[i] for p in local) for i in range(3)]
high = [max(p[i] for p in local) for i in range(3)]
corners = [Vector((x, y, z)) for x in (low[0], high[0]) for y in (low[1], high[1]) for z in (low[2], high[2])]
aspects = [.5, 1.6, 4.5, 8.0]
camera = scene.camera
source_aspect = scene.render.resolution_x / scene.render.resolution_y
native_tan = camera.data.sensor_width / (2 * camera.data.lens * source_aspect)
for frame in range(1, 451):
    scene.frame_set(frame)
    scene.view_layers[0].update()
    inverse = camera.matrix_world.inverted()
    for aspect in aspects:
        tangent = math.tan(min(math.radians(85) / 2, math.atan(native_tan * max(1, 1.6 / aspect))))
        for x in (-1000, 1000):
            planes = []
            for corner in corners:
                p = inverse @ (corner + Vector((x, 7, 7.6)))
                depth = -p.z
                planes.append((depth - camera.data.clip_start, camera.data.clip_end - depth,
                               depth * tangent * aspect + p.x, depth * tangent * aspect - p.x,
                               depth * tangent + p.y, depth * tangent - p.y))
            assert any(all(p[i] < 0 for p in planes) for i in range(6)), ('Visible reset endpoint', frame, aspect, x)
stats = {'actor': train.name, 'route': [[-1000, 7, 7.6], [1000, 7, 7.6]],
         'motion': motion, 'autonomous': True, 'carriages': 3,
         'clonedNativeParts': len(mapping), 'guideRailSegments': 2,
         'offscreenEndpointChecks': {'cameraFrames': 450, 'viewportAspects': aspects}}
scene['background_train_route'] = json.dumps(stats)
scene.frame_set(1)
temporary = ROOT / 'background-train-saving.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(temporary))
temporary.replace(MASTER)
(ROOT / 'background-train-route.json').write_text(json.dumps(stats, indent=2) + '\n')
print('BACKGROUND_TRAIN', json.dumps(stats))
if args.preview:
    # Show the scroll-driven foreground pass and the autonomous train's initial
    # browser-clock pose simultaneously; preview-only edits follow the save.
    scene.frame_set(145)
    train.animation_data_clear()
    progress = motion['phase'] / motion['passFrames']
    train.location = (-1000 + 2000 * progress, 7, 7.6)
    scene.objects['Mono • dark reflective ground'].location = (0, 0, -.12)
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 48
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1674
    scene.render.resolution_y = 700
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = str(ROOT / 'transit-network-preview.png')
    bpy.ops.render.render(write_still=True)
