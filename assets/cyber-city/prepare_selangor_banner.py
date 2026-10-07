"""Compress the owner's Selangor artwork and fit the curved landscape display."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT/'banner-artwork/selangor-source.png'
OUTPUT = ROOT/'textures-monochrome/selangor.jpg'


def prepare_selangor_banner():
    with Image.open(SOURCE) as original:
        image = ImageOps.exif_transpose(original).convert('L')
        source_size = image.size
        # The supplied artwork itself has black bands beyond the glowing frame.
        # Trim only that outer background, retaining the frame's faint glow.
        artwork_box = image.point(lambda pixel:255 if pixel>2 else 0).getbbox()
        if artwork_box: image = image.crop(artwork_box)
        # Existing cylinder radius 2.91 m, angular span 2.1 rad, height 5 m.
        # Fit using surface width (arc length), not its projected chord width.
        size = (round(1024*(2.91*2.1)/5),1024)
        if image.width/image.height < size[0]/size[1]:
            crop_height = image.width*size[1]/size[0]
            top = (image.height-crop_height)/2
            crop_box = [0,top,image.width,top+crop_height]
        else:
            crop_width = image.height*size[0]/size[1]
            left = (image.width-crop_width)/2
            crop_box = [left,0,left+crop_width,image.height]
        image = ImageOps.fit(image,size,method=Image.Resampling.LANCZOS)
        image.save(OUTPUT,quality=92,optimize=True,progressive=True)
    report = {'source':'banner-artwork/selangor-source.png','suppliedFilename':'Selangor.png',
              'sourceSize':list(source_size),'sourceBytes':SOURCE.stat().st_size,
              'sourceSha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              'fit':'outer black background trimmed, then edge-to-edge proportional center crop; no padding or stretching',
              'artworkBox':list(artwork_box) if artwork_box else None,'cropBoxWithinArtwork':crop_box,
              'displayArcWidthM':2.91*2.1,'displayHeightM':5,
              'output':'textures-monochrome/selangor.jpg','outputSize':list(size),
              'outputBytes':OUTPUT.stat().st_size,'jpegQuality':92,
              'outputSha256':hashlib.sha256(OUTPUT.read_bytes()).hexdigest()}
    (ROOT/'banner-artwork/selangor-banner.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__': print(json.dumps(prepare_selangor_banner()))
