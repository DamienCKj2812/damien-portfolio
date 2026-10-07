"""Fit and compress the owner's black-hole artwork for the curved portal panel."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT/'banner-artwork/black-hole-source.png'
OUTPUT = ROOT/'textures-monochrome/black-hole.jpg'


def prepare_black_hole_banner():
    with Image.open(SOURCE) as original:
        image = ImageOps.exif_transpose(original).convert('L')
        source_size = image.size
        # Match the panel's arc length, preserving the full square artwork and
        # embedded caption with black side padding rather than distortion.
        size = (round(1024*(2.91*2.1)/5.3),1024)
        image = ImageOps.pad(image,size,method=Image.Resampling.LANCZOS,color=0)
        image.save(OUTPUT,quality=92,optimize=True,progressive=True)
    report = {'source':'banner-artwork/black-hole-source.png','suppliedFilename':'black-hole.png',
              'sourceSize':list(source_size),'sourceBytes':SOURCE.stat().st_size,
              'sourceSha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              'fit':'full artwork contained with black side padding; no cropping or stretching',
              'displayArcWidthM':2.91*2.1,'displayHeightM':5.3,
              'output':'textures-monochrome/black-hole.jpg','outputSize':list(size),
              'outputBytes':OUTPUT.stat().st_size,'jpegQuality':92,
              'outputSha256':hashlib.sha256(OUTPUT.read_bytes()).hexdigest()}
    (ROOT/'banner-artwork/black-hole-banner.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__': print(json.dumps(prepare_black_hole_banner()))
