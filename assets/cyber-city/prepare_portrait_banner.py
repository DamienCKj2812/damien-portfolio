"""Fit the owner's portrait artwork to the existing hero display and compress it."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT/'banner-artwork/portrait-source.png'
OUTPUT = ROOT/'textures-monochrome/portrait.jpg'
BANNER_SIZE = (5.6,28.5)


def prepare_portrait_banner():
    if not SOURCE.is_file(): raise FileNotFoundError(SOURCE)
    with Image.open(SOURCE) as original:
        image = ImageOps.exif_transpose(original).convert('L')
        width,height = image.size
        aspect = BANNER_SIZE[0]/BANNER_SIZE[1]
        crop_width = min(width,round(height*aspect))
        crop_height = min(height,round(width/aspect))
        left,top = (width-crop_width)//2,(height-crop_height)//2
        box = (left,top,left+crop_width,top+crop_height)
        image = image.crop(box)
        target_height = min(2048,image.height)
        target = (round(target_height*aspect),target_height)
        image = image.resize(target,Image.Resampling.LANCZOS)
        # Grayscale JPEG preserves the monochrome artwork with no alpha or
        # color profile surprises and is supported by Blender and the browser.
        image.save(OUTPUT,quality=92,optimize=True,progressive=True)
    report = {'source':'banner-artwork/portrait-source.png',
              'suppliedFilename':'cyborg-long-banner.png',
              'sourceSize':[width,height],'sourceBytes':SOURCE.stat().st_size,
              'sourceSha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              'cropBox':list(box),'fit':'center crop to existing 5.6 × 28.5 m display; no stretching',
              'output':'textures-monochrome/portrait.jpg','outputSize':list(target),
              'outputBytes':OUTPUT.stat().st_size,'jpegQuality':92,
              'outputSha256':hashlib.sha256(OUTPUT.read_bytes()).hexdigest()}
    (ROOT/'banner-artwork/portrait-banner.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__': print(json.dumps(prepare_portrait_banner()))
