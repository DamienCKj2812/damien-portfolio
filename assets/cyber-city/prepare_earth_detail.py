"""Bake a monochrome, geographically detailed glass-like Earth texture.

Natural Earth land geometry is public domain. Cache the source unchanged and
record both source and output hashes so future builds reproduce this surface.
"""
import hashlib
import json
import math
import random
import urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'banner-artwork/natural-earth-land-110m.geojson'
SOURCE_URL = 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_land.geojson'
OUTPUT = ROOT / 'textures-monochrome/reference-earth.jpg'
FRONT_LONGITUDE = 25
SIZE = (2048, 1024)


def prepare_earth_detail():
    if not SOURCE.is_file():
        request = urllib.request.Request(SOURCE_URL, headers={'User-Agent': 'KAJU-asset-authoring'})
        with urllib.request.urlopen(request, timeout=45) as response:
            data = response.read()
        parsed = json.loads(data)
        assert parsed['type'] == 'FeatureCollection'
        SOURCE.write_bytes(data)
    geography = json.loads(SOURCE.read_text())
    width, height = SIZE
    land = Image.new('L', SIZE)
    coast = Image.new('L', SIZE)
    ld, cd = ImageDraw.Draw(land), ImageDraw.Draw(coast)
    for feature in geography['features']:
        geometry = feature['geometry']
        polygons = [geometry['coordinates']] if geometry['type'] == 'Polygon' else geometry['coordinates']
        for polygon in polygons:
            for index, ring in enumerate(polygon):
                points = [((lon + 180) / 360 * (width - 1), (90 - lat) / 180 * (height - 1))
                          for lon, lat, *_ in ring]
                ld.polygon(points, fill=255 if index == 0 else 0)
                cd.line(points, fill=255, width=1)
    # Coherent cloud texture rather than per-face random patches.
    rng = random.Random(619)
    clouds = Image.new('L', SIZE, 110)
    for size, blend in [(16, .45), (35, .30), (78, .25), (160, .15)]:
        octave = Image.new('L', (size * 2, size))
        octave.putdata([rng.randrange(256) for _ in range(octave.width * octave.height)])
        clouds = Image.blend(clouds, octave.resize(SIZE, Image.Resampling.BICUBIC), blend)
    clouds = clouds.filter(ImageFilter.GaussianBlur(.7))
    land_pixels, coast_pixels, cloud_pixels = land.load(), coast.load(), clouds.load()
    image = Image.new('L', SIZE)
    pixels = image.load()
    light = (-.48, -.81, .34)
    length = math.sqrt(sum(v * v for v in light))
    light = tuple(v / length for v in light)
    longitudes = [math.radians(x / (width - 1) * 360 - 180 - FRONT_LONGITUDE) for x in range(width)]
    sine = [math.sin(v) for v in longitudes]
    cosine = [math.cos(v) for v in longitudes]
    for y in range(height):
        latitude = math.radians(90 - y / (height - 1) * 180)
        cp, sp = math.cos(latitude), math.sin(latitude)
        for x in range(width):
            nx, ny, nz = cp * sine[x], -cp * cosine[x], sp
            incidence = max(0, nx * light[0] + ny * light[1] + nz * light[2])
            cloud = max(0, (cloud_pixels[x, y] - 123) / 40)
            terrain = land_pixels[x, y] / 255
            base = 13 + terrain * (33 + cloud_pixels[x, y] * .12)
            value = base * (.22 + .78 * incidence)
            value += coast_pixels[x, y] / 255 * (22 + 32 * incidence)
            value += cloud * 32 * (.2 + .8 * incidence)
            value += 165 * incidence ** 80 + 22 * incidence ** 8
            # Soft horizontal/diagonal reflections give the ball the reference's
            # layered glass appearance without hiding its continent detail.
            facing = max(0, -ny)
            value += 13 * math.exp(-((latitude - .38) / .045) ** 2) * facing ** 3
            value += 11 * math.exp(-((latitude + nx * .19 + .18) / .035) ** 2) * facing ** 3
            pixels[x, y] = round(max(1, min(235, value)))
    image.save(OUTPUT, quality=95, optimize=True, progressive=True)
    report = {
        'source': 'banner-artwork/natural-earth-land-110m.geojson', 'sourceUrl': SOURCE_URL,
        'sourceLicense': 'Natural Earth public domain',
        'sourceSha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'output': 'textures-monochrome/reference-earth.jpg', 'size': list(SIZE),
        'frontLongitudeDegrees': FRONT_LONGITUDE, 'features': len(geography['features']),
        'outputSha256': hashlib.sha256(OUTPUT.read_bytes()).hexdigest(), 'outputBytes': OUTPUT.stat().st_size,
    }
    (ROOT / 'earth-detail.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(json.dumps(prepare_earth_detail(), indent=2))
