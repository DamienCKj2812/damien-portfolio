"""Fit and compress the owner's Drive the Next Horizon artwork."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT/'banner-artwork/drive-the-next-horizon-source.png'
OUTPUT = ROOT/'textures-monochrome/drive-the-next-horizon.jpg'


def prepare_drive_banner():
    with Image.open(SOURCE) as original:
        image = ImageOps.exif_transpose(original).convert('L')
        source_size = image.size
        size = (round(1024*8.4/6.5),1024)
        # Bias the cover crop toward the headline/logo, instead of centering on
        # the decorative sky and cutting off DRIVE THE NEXT HORIZON.
        if image.width/image.height < size[0]/size[1]:
            crop_height = image.width*size[1]/size[0]
            top = (image.height-crop_height)*.9
            crop_box = [0,top,image.width,top+crop_height]
        else:
            crop_width = image.height*size[0]/size[1]
            left = (image.width-crop_width)/2
            crop_box = [left,0,left+crop_width,image.height]
        image = ImageOps.fit(image,size,method=Image.Resampling.LANCZOS,centering=(.5,.9))
        image.save(OUTPUT,quality=92,optimize=True,progressive=True)
    report = {'source':'banner-artwork/drive-the-next-horizon-source.png',
              'suppliedFilename':'drive-the-next-horizon.png','sourceSize':list(source_size),
              'sourceBytes':SOURCE.stat().st_size,
              'sourceSha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              'fit':'edge-to-edge proportional cover crop, biased toward headline/logo; no padding or stretching',
              'cropBox':crop_box,'centering':[.5,.9],
              'displayWidthM':8.4,'displayHeightM':6.5,
              'output':'textures-monochrome/drive-the-next-horizon.jpg','outputSize':list(size),
              'outputBytes':OUTPUT.stat().st_size,'jpegQuality':92,
              'outputSha256':hashlib.sha256(OUTPUT.read_bytes()).hexdigest()}
    (ROOT/'banner-artwork/drive-the-next-horizon-banner.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__': print(json.dumps(prepare_drive_banner()))
