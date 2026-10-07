"""Create readable grayscale versions of the hero tower's billboard artwork."""
from pathlib import Path
from PIL import Image, ImageEnhance, ImageOps
from prepare_portrait_banner import SOURCE, prepare_portrait_banner
from prepare_selangor_banner import SOURCE as SELANGOR_SOURCE, prepare_selangor_banner
from prepare_black_hole_banner import SOURCE as BLACK_HOLE_SOURCE, prepare_black_hole_banner
from prepare_drive_banner import SOURCE as DRIVE_SOURCE, prepare_drive_banner
from prepare_nexus_banner import SOURCE as NEXUS_SOURCE, prepare_nexus_banner

ROOT=Path(__file__).resolve().parent
OUTPUT=ROOT/'textures-monochrome'
if not OUTPUT.is_dir():raise RuntimeError('Create textures-monochrome first.')
for name in ['portrait','night','drive','kaze','nexus','portal','landscape','arasaka']:
    if name=='portrait' and SOURCE.is_file():
        prepare_portrait_banner()
        continue
    if name=='landscape' and SELANGOR_SOURCE.is_file():
        prepare_selangor_banner()
        continue
    if name=='portal' and BLACK_HOLE_SOURCE.is_file():
        prepare_black_hole_banner()
        continue
    if name=='drive' and DRIVE_SOURCE.is_file():
        prepare_drive_banner()
        continue
    if name=='nexus' and NEXUS_SOURCE.is_file():
        prepare_nexus_banner()
        continue
    image=Image.open(ROOT/'textures'/f'{name}.png').convert('L')
    image=ImageOps.autocontrast(image,cutoff=.4)
    image=ImageEnhance.Contrast(image).enhance(1.12)
    image.convert('RGB').save(OUTPUT/f'{name}.png',optimize=True)
print('Generated 8 monochrome hero-tower ads')
