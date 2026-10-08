"""Map the supplied tall campaign across the existing two curved A-bay panels."""
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageOps
from reference_tower_spec import SCREENS

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'banner-artwork/long-banner-source.png'
OUTPUT = ROOT / 'textures-monochrome'


def prepare_long_banner_artwork():
    keys = ('logo', 'portrait')
    bottom = min(SCREENS[key]['z'][0] for key in keys)
    top = max(SCREENS[key]['z'][1] for key in keys)
    height = top - bottom
    arc = SCREENS['portrait']['arcLength']
    assert all(SCREENS[key]['azimuth'] == SCREENS['portrait']['azimuth'] for key in keys)
    canvas_size = (round(4096 * arc / height), 4096)
    with Image.open(SOURCE) as original:
        original = ImageOps.exif_transpose(original).convert('L')
        source_size = list(original.size)
        # Keep all authored lettering and outer borders. Map the entire image
        # to the whole bay before slicing by the real panel heights/UV ranges.
        canvas = original.resize(canvas_size, Image.Resampling.LANCZOS)
    records, slices = {}, {}
    for key in keys:
        spec = SCREENS[key]
        y0 = round((top - spec['z'][1]) / height * canvas.height)
        y1 = round((top - spec['z'][0]) / height * canvas.height)
        image = canvas.crop((0, y0, canvas.width, y1))
        image = image.resize((round(image.height * spec['aspect']), image.height), Image.Resampling.LANCZOS)
        filename = f'reference-{key}.jpg'
        output = OUTPUT / filename
        image.save(output, quality=93, optimize=True, progressive=True)
        records[filename] = {'size': list(image.size), 'bytes': output.stat().st_size,
                             'sha256': hashlib.sha256(output.read_bytes()).hexdigest()}
        slices[key] = {'zMeters': list(spec['z']), 'canvasRows': [y0, y1]}
    return {'source': str(SOURCE.relative_to(ROOT)),
            'sourceSha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            'sourceSize': source_size,
            'portraitPanelMeters': [arc, SCREENS['portrait']['z'][1] - SCREENS['portrait']['z'][0]],
            'portraitFit': 'full supplied long banner mapped across both existing curved A-bay panels; no added captions or padding',
            'longBanner': {'canvasSize': list(canvas_size), 'spanMeters': [bottom, top],
                           'panelSlices': slices, 'existingGapPreserved': True},
            'outputs': records}


if __name__ == '__main__':
    prepared = prepare_long_banner_artwork()
    metadata = ROOT / 'reference-tower-artwork.json'
    report = json.loads(metadata.read_text())
    outputs = report['outputs']
    outputs.update(prepared.pop('outputs'))
    report.update(prepared)
    report['outputs'] = outputs
    metadata.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
