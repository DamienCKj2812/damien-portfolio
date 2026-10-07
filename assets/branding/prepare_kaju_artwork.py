"""Regenerate only owned brand posters; preserve supplied campaign artwork."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageEnhance
from kaju_brand import BRAND, SPACED_BRAND, LOGO_PATHS

ROOT = Path(__file__).resolve().parents[1]
CITY = ROOT/'cyber-city'
FONT = '/usr/share/fonts/rsms-inter-fonts/InterDisplay-Medium.ttf'


def draw_logo(draw, x, y, scale, color):
    for path, width in zip(LOGO_PATHS, [7, 5, 5, 4]):
        draw.line([(x+px*scale, y-py*scale) for px, py in path], fill=color, width=width)


image = Image.new('RGB', (600, 600), '#07162a')
draw = ImageDraw.Draw(image)
draw_logo(draw, 300, 170, 100, '#a8ffff')
for y, body, size in [(320, BRAND, 90), (430, 'INDUSTRIES', 33)]:
    draw.text((300, y), body, font=ImageFont.truetype(FONT, size), fill='white', anchor='mt')
glow = image.filter(ImageFilter.GaussianBlur(6))
image = Image.blend(image, Image.blend(image, glow, .35), .25)
image.save(CITY/'textures/kaze.png')
mono = ImageEnhance.Contrast(ImageOps.autocontrast(image.convert('L'), cutoff=.4)).enhance(1.12)
mono.convert('RGB').save(CITY/'textures-monochrome/kaze.png', optimize=True)

# The original, generated cyborg poster is retained for native/neon rebuilds.
# The production portrait.jpg and its owner's source are never regenerated here.
legacy = CITY/'textures/portrait.png'
if legacy.is_file():
    portrait = Image.open(legacy).convert('RGB')
    assert portrait.size == (700, 1800)
    draw = ImageDraw.Draw(portrait)
    draw.rectangle((90, 195, 610, 290), fill='#100326')
    draw.text((350, 205), SPACED_BRAND, font=ImageFont.truetype(FONT, 76), fill='white', anchor='mt')
    portrait.save(legacy)
    gray = ImageEnhance.Contrast(ImageOps.autocontrast(portrait.convert('L'), cutoff=.4)).enhance(1.12)
    gray.convert('RGB').save(CITY/'textures-monochrome/portrait.png', optimize=True)

preview = Image.new('RGB', (256, 256), 'black')
draw_logo(ImageDraw.Draw(preview), 128, 144, 110, 'white')
preview.save(ROOT/'branding/kaju-logo.png')
print({'brand': BRAND, 'triangle_logo': True, 'billboard_size': image.size})
