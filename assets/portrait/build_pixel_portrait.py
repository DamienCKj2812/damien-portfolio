"""Create a static monochrome pixel-grid portrait from the original photo."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT/'public/portraits'


def smoothstep(a, b, value):
    t = np.clip((value-a)/(b-a), 0, 1)
    return t*t*(3-2*t)


def build(source):
    source_image = Image.open(source).convert('RGBA')
    original = source_image.convert('RGB')
    source_alpha = source_image.getchannel('A')
    has_transparency = source_alpha.getextrema()[0] < 255
    rgb = np.asarray(original, dtype=np.float32)
    height, width = rgb.shape[:2]
    if has_transparency:
        # Background-removed photographs already supply the subject silhouette.
        # Preserve soft edges and transparent gaps instead of estimating a matte.
        alpha = source_alpha
    else:
        # Fill the studio-background photo's outer subject silhouette so white
        # shirt stripes remain intact.
        background = np.median(np.concatenate((rgb[:, :64], rgb[:, -64:]), axis=1), axis=1)
        distance = np.linalg.norm(rgb-background[:, None, :], axis=2)
        matte = np.zeros((height, width), dtype=np.uint8)
        for y in range(height):
            row = np.flatnonzero(distance[y] > 30)
            row = row[(row > width*.12) & (row < width*.88)]
            if len(row) >= 3:
                matte[y, max(0,row[0]-1):min(width,row[-1]+2)] = 255
        neutral = (rgb[:, :, 0]-rgb[:, :, 2]) < 32
        head_region = np.arange(height)[:, None] < height*.36
        edge_confidence = np.where(neutral & head_region, smoothstep(35, 100, distance), 1)
        matte = (matte*edge_confidence).astype(np.uint8)
        yy_source, xx_source = np.indices((height, width))
        forehead = (yy_source > height*.202) & (xx_source > width*.415) & (xx_source < width*.585)
        hair_background = (np.mean(rgb, axis=2) > 205) & (yy_source < height*.235) & ~forehead
        matte[hair_background] = 0
        # Resample premultiplied RGBA later to avoid a bright silhouette halo.
        alpha = Image.fromarray(matte)
    bounds = alpha.getbbox()
    if not bounds:
        raise ValueError('Could not locate the portrait against its studio background.')
    gray = np.asarray(ImageOps.autocontrast(ImageOps.grayscale(original), cutoff=(1, 1)), dtype=np.float32)
    # Apply one restrained tone curve to the entire photograph. Highlight
    # compression prevents a glowing face/shirt without darkening the lower body
    # selectively; natural photographic differences remain intact.
    gray = np.clip(160*np.tanh(gray/180), 0, 255).astype(np.uint8)
    subject = Image.merge('RGBA', (Image.fromarray(gray), Image.fromarray(gray), Image.fromarray(gray), alpha)).crop(bounds)
    frame_w, frame_h, cell = 640, 800, 5
    # Keep the underlying photographic detail. The reference's fine mesh sits
    # over a soft image rather than replacing facial features with large blocks.
    reduced = ImageOps.contain(subject, (frame_w-96, frame_h-192), method=Image.Resampling.LANCZOS)
    result = Image.new('RGBA', (frame_w, frame_h))
    result.alpha_composite(reduced, ((result.width-reduced.width)//2, 128))
    result = result.filter(ImageFilter.GaussianBlur(1.1))
    rgba = np.asarray(result, dtype=np.float32).copy()
    yy, xx = np.indices((result.height, result.width))
    grid = ((xx % cell == 0) | (yy % cell == 0)).astype(np.float32)
    rgba[:, :, :3] *= (1-grid*.15)[:, :, None]
    result = Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8))
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT/'damien-pixel.png'
    result.save(path, optimize=True)
    # Original photographic color/detail, with identical subject matte, crop,
    # scale and placement. No tone curve, grid or photographic blur is applied.
    # Exclude the one-pixel studio-background margin from the ungraded color
    # layer, where it would otherwise become a bright outline on the black frame.
    photo_alpha = alpha if has_transparency else alpha.filter(ImageFilter.MinFilter(3))
    photo_subject = Image.merge('RGBA', (*original.split(), photo_alpha)).crop(bounds)
    photo_reduced = ImageOps.contain(photo_subject, (frame_w-96, frame_h-192), method=Image.Resampling.LANCZOS)
    photo = Image.new('RGBA', (frame_w, frame_h))
    photo.alpha_composite(photo_reduced, ((frame_w-photo_reduced.width)//2, 128))
    original_path = OUT/'damien-original.png'
    photo.save(original_path, optimize=True)
    manifest = {
        'image': 'portraits/damien-pixel.png', 'source': source.name,
        'assetHash': hashlib.sha256(path.read_bytes()).hexdigest()[:16],
        'size': list(result.size), 'cellSize': cell,
        'softness': 1.1,
        'effect': 'Soft monochrome raster portrait with uniform grading, compressed highlights and a faint grid',
        'originalImage': 'portraits/damien-original.png',
        'originalAssetHash': hashlib.sha256(original_path.read_bytes()).hexdigest()[:16],
        'originalEffect': 'Original photographic color and detail with matching transparent subject framing; no tonal grading or grid',
    }
    (HERE/'image-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(f'PIXEL PORTRAIT: {path}')
    print(f'ORIGINAL PORTRAIT: {original_path}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True, type=Path)
    args = parser.parse_args()
    build(args.source.expanduser().resolve())
