"""Read-only checks for visible labels, shared logo curves and browser exports."""
import argparse
import json
import struct
import sys
from pathlib import Path
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kaju_brand import BRAND, logo_paths, replace_wordmark

parser = argparse.ArgumentParser()
parser.add_argument('--model', required=True, choices=['lobby', 'elevator', 'city'])
args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
ROOT = Path(__file__).resolve().parents[2]
scene = bpy.context.scene
assert scene.get('Visible brand') == BRAND
assert all(replace_wordmark(obj.data.body) == obj.data.body for obj in bpy.data.objects if obj.type == 'FONT')
names = {'lobby': 'Lobby • KAZE angular crest', 'elevator': 'Elevator / Rear geometric KAZE mark'}
count = 0
if args.model in names:
    obj = scene.objects[names[args.model]]
    scale, cy, cz = (.72, 5.78, 12) if args.model == 'lobby' else (.18, 2.774, 2.04)
    paths = [[Vector((x*scale, cy, cz+y*scale)) for x, y in path] for path in logo_paths()]
    assert len(obj.data.splines) == len(paths)
    for spline, path in zip(obj.data.splines, paths):
        assert len(spline.points) == len(path)
        assert all((Vector(point.co[:3])-expected).length < 1e-5 for point, expected in zip(spline.points, path))
    base = ROOT/'public/models'/args.model
    manifest = json.loads((base/'scene.json').read_text())
    binary = (base/'geometry.bin').read_bytes()

    def key(point):
        return tuple(round(value, 4) for value in point)

    actual = set()
    for group in manifest['groups']:
        if group['actor'] == 0 and group['kind'] in ['lines', 'glow', 'outline']:
            for i in range(0, group['vertexCount'], 2):
                a = struct.unpack_from('<3f', binary, group['byteOffset']+i*group['stride']*4)
                b = struct.unpack_from('<3f', binary, group['byteOffset']+(i+1)*group['stride']*4)
                actual.add((key(a), key(b)))
    for path in paths:
        for a, b in zip(path, path[1:]):
            assert (key(obj.matrix_world @ a), key(obj.matrix_world @ b)) in actual, 'Logo segment missing from browser geometry'
            count += 1
    assert count == 9
else:
    images = [image for image in bpy.data.images if Path(bpy.path.abspath(image.filepath)).name == 'kaze.png']
    assert images and all(image.packed_file for image in images)
    assert (ROOT/'public/models/city/ads/kaze.png').read_bytes() == (ROOT/'assets/cyber-city/textures-monochrome/kaze.png').read_bytes()
print({'model': args.model, 'brand': BRAND, 'native_labels': True, 'exported_logo_segments': count,
       'shared_triangular_logo': True})
