"""Fit and compress the owner's Shaping a Brighter Tomorrow artwork."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT/'banner-artwork/shaping-a-brighter-tomorrow-source.png'
OUTPUT = ROOT/'textures-monochrome/shaping-a-brighter-tomorrow.jpg'


def prepare_nexus_banner():
    with Image.open(SOURCE) as original:
        image = ImageOps.exif_transpose(original).convert('L')
        source_size = image.size
        # Radius 2.91 m × angular span 2.1 rad gives the curved surface width.
        size = (round(1536*(2.91*2.1)/8),1536)
        # Edge-to-edge cover: crop vertically rather than adding blank sides.
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
    report = {'source':'banner-artwork/shaping-a-brighter-tomorrow-source.png',
              'suppliedFilename':'shaping-a-brighter-tomorrow.png','sourceSize':list(source_size),
              'sourceBytes':SOURCE.stat().st_size,
              'sourceSha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              'fit':'edge-to-edge proportional center crop; no padding or stretching',
              'cropBox':crop_box,
              'displayArcWidthM':2.91*2.1,'displayHeightM':8,
              'output':'textures-monochrome/shaping-a-brighter-tomorrow.jpg','outputSize':list(size),
              'outputBytes':OUTPUT.stat().st_size,'jpegQuality':92,
              'outputSha256':hashlib.sha256(OUTPUT.read_bytes()).hexdigest()}
    (ROOT/'banner-artwork/shaping-a-brighter-tomorrow-banner.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__': print(json.dumps(prepare_nexus_banner()))
