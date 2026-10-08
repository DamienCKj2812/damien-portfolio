"""Prepare the reference tower's coordinated monochrome display artwork."""
import hashlib
import json
import math
import random
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent
from reference_tower_spec import SCREENS
from prepare_earth_detail import prepare_earth_detail
from prepare_long_banner import prepare_long_banner_artwork

OUTPUT = ROOT / 'textures-monochrome'
FONT = next(path for path in [
    '/usr/share/fonts/google-noto/NotoSansMono-Light.ttf',
    '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
    '/usr/share/fonts/liberation-mono-fonts/LiberationMono-Regular.ttf',
] if Path(path).is_file())


def lettering(draw, text, center, y, size, spacing=4, value=210):
    font = ImageFont.truetype(FONT, size)
    width = sum(draw.textlength(c, font=font) for c in text) + spacing * (len(text) - 1)
    x = center - width / 2
    for char in text:
        draw.text((x, y), char, font=font, fill=value)
        x += draw.textlength(char, font=font) + spacing


def save(image, filename, records):
    key = filename.removeprefix('reference-').removesuffix('.jpg')
    if key in SCREENS:
        target = (round(image.height * SCREENS[key]['aspect']), image.height)
        image = ImageOps.pad(image, target, method=Image.Resampling.LANCZOS, color=3) if key == 'eclipse' else ImageOps.fit(image, target, method=Image.Resampling.LANCZOS)
    path = OUTPUT / filename
    image.save(path, quality=93, optimize=True, progressive=True)
    records[filename] = {'size': list(image.size), 'bytes': path.stat().st_size,
                         'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def mountain_landscape(image, seed=19):
    """Rasterize a shaded, snow-covered height field, then reflect it in a lake.

    Fine terrain triangles carry surface lighting, replacing the earlier flat
    zigzag ridge outlines. All source data is generated locally and repeatably.
    """
    rng = random.Random(seed)
    width, depth = 255, 141
    noise = Image.new('L', (width, depth), 128)
    for size, weight in [(5, .46), (11, .30), (25, .22), (53, .15), (117, .10)]:
        octave = Image.new('L', (size, max(3, size // 2)))
        octave.putdata([rng.randrange(256) for _ in range(octave.width * octave.height)])
        noise = Image.blend(noise, octave.resize((width, depth), Image.Resampling.BICUBIC), weight)
    samples = noise.load()
    terrain = []
    peaks = [(-5.5, 8.8, 5.3, 1.1), (-3.4, 10.2, 6.2, .9),
             (-.7, 8.7, 4.3, 1.0), (2.4, 10.7, 6.0, 1.3), (5.5, 8.0, 4.1, 1.2)]
    for row in range(depth):
        distance = row / (depth - 1) * 12
        line = []
        for col in range(width):
            x = -8 + col / (width - 1) * 16
            height = max(amplitude * math.exp(-((x - px) / spread) ** 2 / 2 - ((distance - py) / 3.2) ** 2 / 2)
                         for px, py, amplitude, spread in peaks)
            grain = samples[col, row] / 255
            height *= .52 + grain * 1.08
            height += max(0, distance - 3) * (.20 + .25 * grain)
            if distance < 2.0:
                height *= (distance / 2) ** 2
            line.append((x, distance, height, grain))
        terrain.append(line)
    draw = ImageDraw.Draw(image)
    def project(point):
        x, distance, height, _ = point
        return (444 + x * (64 - distance * 1.35), 1080 - distance * 15 - height * 22)
    for row in range(depth - 2, -1, -1):
        for col in range(width - 1):
            corners = [terrain[row][col], terrain[row][col + 1],
                       terrain[row + 1][col + 1], terrain[row + 1][col]]
            for a, b, c in [(corners[0], corners[1], corners[2]), (corners[0], corners[2], corners[3])]:
                dx, dy = b[0] - a[0], b[1] - a[1]
                ux, uy = c[0] - a[0], c[1] - a[1]
                dh, uh = b[2] - a[2], c[2] - a[2]
                nx, ny, nz = dy * uh - dh * uy, dh * ux - dx * uh, dx * uy - dy * ux
                length = math.sqrt(nx * nx + ny * ny + nz * nz)
                if nz < 0:
                    nx, ny, nz = -nx, -ny, -nz
                light = max(.05, (nx * -.55 + ny * -.32 + nz * .77) / max(length, 1e-8))
                height = (a[2] + b[2] + c[2]) / 3
                grain = (a[3] + b[3] + c[3]) / 3
                snow = max(0, min(1, (height - 2.25 - grain * 1.1) * .9))
                value = int(13 + light * (40 + 130 * snow) + grain * 13)
                draw.polygon([project(p) for p in (a, b, c)], fill=value)
    reflection = ImageOps.flip(image.crop((0, 730, 888, 1078))).resize((888, 175), Image.Resampling.BICUBIC)
    reflection = Image.blend(Image.new('L', reflection.size, 3), reflection, .38)
    image.paste(reflection, (0, 1080))
    draw = ImageDraw.Draw(image)
    for _ in range(450):
        y = rng.randrange(1080, 1260)
        x = rng.randrange(25, 860)
        draw.line((x, y, x + rng.randrange(5, 38), y), fill=rng.randrange(3, 19))


def prepare_reference_tower_artwork():
    banner = prepare_long_banner_artwork()
    records = banner.pop('outputs')

    order = Image.new('L', (round(1973 * SCREENS['order']['aspect']), 1973), 3)
    draw = ImageDraw.Draw(order)
    for i, text in enumerate(['ORDER', 'EFFICIENCY', 'PROGRESS']):
        lettering(draw, text, order.width / 2, 250 + i * 145, 78, 14)
    draw.line((order.width / 2 - 70, 845, order.width / 2 + 20, 845), fill=175, width=3)
    for i, text in enumerate(['A MORE', 'STABLE', 'TOMORROW']):
        lettering(draw, text, order.width / 2, 1120 + i * 160, 70, 15, 190)
    for x in [28, 47, order.width - 47, order.width - 28]:
        draw.line((x, 24, x, 1949), fill=65 if x in [28, 900] else 24, width=2)
    save(order, 'reference-order.jpg', records)

    globe = Image.new('L', (round(1280 * SCREENS['orbital']['aspect']), 1280), 2)
    draw = ImageDraw.Draw(globe)
    rng = random.Random(71)
    for _ in range(450):
        x, y = rng.randrange(60, globe.width - 60), rng.randrange(70, 1110)
        draw.point((x, y), fill=rng.randrange(15, 80))
    for y in [84, 1196]:
        draw.line((80, y, globe.width - 80, y), fill=25, width=1)
    save(globe, 'reference-orbital.jpg', records)

    eclipse = Image.new('L', (888, 1536), 3)
    draw = ImageDraw.Draw(eclipse)
    rng = random.Random(19)
    for _ in range(900):
        x, y = rng.randrange(45, 843), rng.randrange(40, 900)
        draw.point((x, y), fill=rng.randrange(10, 110))
    halo = Image.new('L', eclipse.size)
    hd = ImageDraw.Draw(halo)
    hd.ellipse((314, 330, 574, 590), outline=230, width=9)
    eclipse = ImageChops.lighter(eclipse, halo.filter(ImageFilter.GaussianBlur(13)))
    draw = ImageDraw.Draw(eclipse)
    draw.ellipse((318, 334, 570, 586), fill=0, outline=245, width=4)
    mountain_landscape(eclipse)
    draw = ImageDraw.Draw(eclipse)
    draw.rectangle((0, 1260, 888, 1536), fill=3)
    lettering(draw, 'A CLEANER', 444, 1325, 27, 8)
    lettering(draw, 'TOMORROW', 444, 1390, 27, 8)
    draw.line((383, 1460, 438, 1460), fill=170, width=2)
    save(eclipse, 'reference-eclipse.jpg', records)
    report = {**banner,
              'screenAspects': {key: value['aspect'] for key, value in SCREENS.items()},
              'outputs': records}
    earth = prepare_earth_detail()
    report['outputs']['reference-earth.jpg'] = {'size': earth['size'], 'bytes': earth['outputBytes'], 'sha256': earth['outputSha256']}
    report['earthSource'] = earth['source']
    (ROOT / 'reference-tower-artwork.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(json.dumps(prepare_reference_tower_artwork(), indent=2))
