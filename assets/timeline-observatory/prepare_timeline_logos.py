"""Prepare original-color timeline logos without editing supplied artwork."""
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / 'logos'
MEDIA=json.loads((ROOT/'assets/media/manifest.json').read_text())['files']
SOURCES = {'apu': MEDIA['apuLogo']['source'], 'lyj': MEDIA['lyjLogo']['source'], 'cos': MEDIA['cosLogo']['source']}
report = {}
for identity, filename in SOURCES.items():
    source = ROOT / filename
    image = Image.open(source).convert('RGBA')
    gray = ImageOps.grayscale(image)
    alpha = image.getchannel('A')
    if alpha.getextrema()[0] < 255:
        bounds = alpha.point(lambda value: 255 if value > 12 else 0).getbbox()
    else:
        # Opaque artwork has a dark surround; crop proportionally around its
        # actual lettering/mark while retaining the supplied glow treatment.
        bounds = gray.point(lambda value: 255 if value > 150 else 0).getbbox()
    assert bounds
    margin = 24
    x0, y0, x1, y1 = bounds
    bounds = (max(0, x0-margin), max(0, y0-margin), min(image.width, x1+margin), min(image.height, y1+margin))
    result = image.crop(bounds)
    result.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
    output = OUT / f'{identity}-logo.png'
    result.save(output, optimize=True)
    report[identity] = {'source': filename, 'sourceSha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                        'texture': f'logos/{output.name}', 'outputSha256': hashlib.sha256(output.read_bytes()).hexdigest(),
                        'size': list(result.size), 'cropBounds': list(bounds), 'palette': 'original-color RGBA'}
    retired = OUT / f'{identity}-monochrome.png'
    if retired.is_file():
        retired.unlink()
(OUT / 'logo-manifest.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
