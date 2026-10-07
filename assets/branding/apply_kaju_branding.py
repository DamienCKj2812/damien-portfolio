"""Focused master-saving update for KAJU lettering, logo curves and packed ads."""
import argparse
import json
import sys
from pathlib import Path
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kaju_brand import BRAND, logo_paths, replace_wordmark

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--model', required=True, choices=['lobby', 'elevator', 'city', 'original-city'])
parser.add_argument('--preview', action='store_true')
args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
paths = {'lobby': ROOT/'kaze-lobby/kaze-lobby-walkthrough.blend',
         'elevator': ROOT/'kaze-elevator/kaze-elevator-journey.blend',
         'city': ROOT/'cyber-city/monochrome-city-solid-tower.blend',
         'original-city': ROOT/'cyber-city/cyber-city-walkthrough.blend'}
assert Path(bpy.data.filepath).resolve() == paths[args.model].resolve()
scene = bpy.context.scene
frame = scene.frame_current
animated = sorted((obj for obj in scene.objects if obj.animation_data and obj.animation_data.action), key=lambda obj: obj.name)


def motion():
    result = []
    for value in sorted({scene.frame_start, min(90, scene.frame_end), min(245, scene.frame_end), scene.frame_end}):
        scene.frame_set(value)
        scene.view_layers[0].update()
        result.extend(tuple(v for row in obj.matrix_world for v in row) for obj in animated)
    return result


before = motion()
changed = []
for obj in bpy.data.objects:
    if obj.type == 'FONT':
        body = replace_wordmark(obj.data.body)
        if body != obj.data.body:
            obj.data.body = body
            changed.append(obj.name)


def replace_logo(obj, paths):
    assert obj.type == 'CURVE' and obj.data.users == 1
    obj.data.splines.clear()
    for path in paths:
        spline = obj.data.splines.new('POLY')
        spline.points.add(len(path)-1)
        for point, co in zip(spline.points, path): point.co = (*co, 1)
    obj['brand'] = BRAND
    obj['brand_logo'] = 'reference triangular mark'


if args.model == 'lobby':
    replace_logo(scene.objects['Lobby • KAZE angular crest'],
                 [[(x*.72, 5.78, 12+y*.72) for x, y in path] for path in logo_paths()])
elif args.model == 'elevator':
    replace_logo(scene.objects['Elevator / Rear geometric KAZE mark'],
                 [[(x*.18, 2.774, 2.04+y*.18) for x, y in path] for path in logo_paths()])
    controls = bpy.data.texts.get('KAZE_Elevator_Controls.py')
    if controls:
        code = controls.as_string().replace('KAZE / Elevator levels', 'KAJU / Elevator levels').replace('KAZE Elevator', 'KAJU Elevator')
        controls.from_string(code)
    if scene.get('review_instructions'):
        scene['review_instructions'] = scene['review_instructions'].replace('KAZE Elevator', 'KAJU Elevator')

images = []
if args.model in ['city', 'original-city']:
    folder = 'textures-monochrome' if args.model == 'city' else 'textures'
    for image in bpy.data.images:
        name = Path(bpy.path.abspath(image.filepath)).name
        if name in ['kaze.png', 'portrait.png'] and image.users:
            source = ROOT/'cyber-city'/folder/name
            if source.is_file():
                if image.packed_file: image.unpack(method='REMOVE')
                image.filepath = str(source)
                image.reload()
                image.pack()
                images.append(name)

assert motion() == before, 'Camera, doors or actor transforms changed.'
assert all(replace_wordmark(obj.data.body) == obj.data.body for obj in bpy.data.objects if obj.type == 'FONT')
scene['Visible brand'] = BRAND
if isinstance(scene.get('Design reference'), str):
    scene['Design reference'] = replace_wordmark(scene['Design reference'])
scene.frame_set(frame)
scene.view_layers[0].update()
bpy.context.preferences.filepaths.save_version = 1
bpy.ops.wm.save_as_mainfile(filepath=str(paths[args.model]))
if args.model == 'elevator':
    path = ROOT/'kaze-elevator/elevator-manifest.json'
    manifest = json.loads(path.read_text())
    manifest['name'] = replace_wordmark(manifest['name'])
    path.write_text(json.dumps(manifest, indent=2))
print({'model': args.model, 'brand': BRAND, 'text_objects': changed,
       'repacked_images': images, 'motion_preserved': True})
if args.preview and args.model == 'lobby':
    data = bpy.data.cameras.new('KAJU / identity preview camera')
    preview = bpy.data.objects.new(data.name, data)
    scene.collection.objects.link(preview)
    preview.location = (0, .9, 11.5)
    preview.rotation_euler = (Vector((0, 5.78, 11.65))-preview.location).to_track_quat('-Z', 'Y').to_euler()
    data.lens = 50
    scene.camera = preview
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 24
    scene.render.resolution_x = 900
    scene.render.resolution_y = 700
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(ROOT/'branding/lobby-kaju-branding.png')
    bpy.ops.render.render(write_still=True)
elif args.preview and args.model == 'city':
    scene.frame_set(1)
    camera = scene.camera
    camera.data.sensor_fit = 'VERTICAL'
    camera.data.sensor_height = camera.data.sensor_width / (scene.render.resolution_x / scene.render.resolution_y)
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 16
    scene.render.resolution_x = 1414
    scene.render.resolution_y = 610
    scene.render.resolution_percentage = 75
    filename = 'orbital-sky-preview.png' if scene.get('orbital_sky_reference') else 'monochrome-optimized-approach.png'
    scene.render.filepath = str(ROOT/'cyber-city'/filename)
    bpy.ops.render.render(write_still=True)
