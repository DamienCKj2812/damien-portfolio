"""Generate original neon billboard illustrations; run with regular Python + Pillow."""
from pathlib import Path
import math
import random
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent / 'textures'
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'branding'))
from kaju_brand import BRAND, SPACED_BRAND, LOGO_PATHS
ROOT.mkdir(exist_ok=True)
FONT = '/usr/share/fonts/rsms-inter-fonts/InterDisplay-Medium.ttf'
BOLD = '/usr/share/fonts/rsms-inter-fonts/InterDisplay-Bold.ttf'
JP = '/usr/share/fonts/google-droid-sans-fonts/DroidSansJapanese.ttf'
random.seed(28)

def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, size)

def text(draw, xy, content, size, fill='white', bold=False):
    draw.text(xy, content, font=font(size, bold), fill=fill, anchor='ma' if '\n' in content else 'mt', spacing=12, align='center')

def finish(im, name):
    glow=im.filter(ImageFilter.GaussianBlur(6))
    im=Image.blend(im, Image.blend(im, glow, .35), .25)
    im.save(ROOT / name)

def logo(draw, x, y, size, color='#a8ffff'):
    for path,width in zip(LOGO_PATHS,[7,5,5,4]):
        draw.line([(x+px*size,y-py*size) for px,py in path],fill=color,width=width)

# Tall cyborg fashion campaign: polygonal hair, facial planes, glowing eyes.
im=Image.new('RGB',(700,1800),'#100326'); d=ImageDraw.Draw(im)
for _ in range(160):
    x=random.randrange(700); y=random.randrange(1800)
    d.rectangle((x,y,x+random.randrange(8,55),y+random.randrange(20,210)),fill=random.choice(['#14063f','#22034e','#250a78','#3e087f','#44066a']))
for y in range(-100,1800,150):
    for x in range(-60,760,130):
        x += 65 if (y//150)%2 else 0
        p=[(x+65*math.cos(math.radians(a)),y+75*math.sin(math.radians(a))) for a in range(0,361,60)]
        d.line(p,fill='#8430c1',width=2)
logo(d,350,115,70)
text(d,(350,205),SPACED_BRAND,76)
text(d,(350,300),'A BRIGHTER\nHUMANITY',30)
d.polygon([(150,1020),(480,1000),(700,1550),(680,1800),(30,1800),(30,1500)],fill='#060a34')
d.polygon([(290,1090),(390,1090),(470,1420),(280,1560),(160,1410)],fill='#52b5f5')
d.polygon([(360,1120),(450,1100),(500,1410),(290,1590)],fill='#e1269e')
d.polygon([(80,1450),(230,1330),(300,1540),(30,1710)],fill='#f337a6')
d.polygon([(460,1320),(650,1480),(510,1770),(350,1640)],fill='#1838bd')
d.polygon([(200,470),(420,435),(540,540),(550,840),(460,1120),(350,1280),(210,1150),(115,920),(100,650)],fill='#151251')
d.polygon([(225,520),(420,490),(515,600),(500,875),(443,1070),(351,1225),(238,1120),(163,920),(145,690)],fill='#a7eafa')
d.polygon([(420,490),(515,600),(500,875),(443,1070),(351,1225),(386,967),(440,760)],fill='#5dcde8')
d.polygon([(145,690),(225,520),(240,710),(190,855),(230,1060),(163,920)],fill='#e0f7ff')
d.polygon([(160,580),(220,530),(300,555),(340,640),(280,725),(210,720),(170,650)],fill='#ff326e')
d.polygon([(440,720),(515,650),(511,755),(473,840),(417,852)],fill='#ff3979')
d.polygon([(180,850),(225,790),(300,790),(337,845),(270,884),(208,891)],fill='#562079')
d.polygon([(367,825),(416,780),(481,773),(489,825),(428,861)],fill='#752067')
d.polygon([(197,847),(234,816),(290,822),(318,847),(263,864),(225,865)],fill='#f1feff')
d.polygon([(386,824),(417,798),(465,803),(479,820),(435,842),(410,842)],fill='#f1feff')
for x,y in [(262,842),(432,820)]:
    d.ellipse((x-18,y-24,x+18,y+24),fill='#1355ce'); d.ellipse((x-9,y-16,x+9,y+16),fill='#08092c'); d.ellipse((x-8,y-15,x-1,y-8),fill='white')
d.line([(328,836),(314,971),(353,985),(377,966)],fill='#237aa9',width=5)
d.polygon([(306,1045),(331,1035),(354,1045),(379,1032),(404,1044),(365,1078),(330,1074)],fill='#e20d83')
d.line([(312,1051),(348,1057),(390,1048)],fill='#410c4f',width=5)
d.line([(340,1074),(368,1075)],fill='#ffd4ef',width=4)
for pts in [[(217,534),(239,618),(209,715),(230,799)],[(498,650),(447,700),(464,756)],[(163,918),(243,929),(267,1099),(351,1225)],[(420,890),(382,937),(391,1040),(443,1070)]]:
    d.line(pts,fill='#437de3',width=3)
for _ in range(65):
    x=random.randrange(130,550); y=random.randrange(550,1250); d.rectangle((x,y,x+3,y+8),fill='#497bb1')
finish(im,'portrait.png')

im=Image.new('RGB',(600,600),'#07162a'); d=ImageDraw.Draw(im); logo(d,300,170,100); text(d,(300,320),BRAND,90); text(d,(300,430),'INDUSTRIES',33); finish(im,'kaze.png')

im=Image.new('RGB',(700,1000),'#140428'); d=ImageDraw.Draw(im)
for y in range(1000):
    v=int(55+100*math.sin(y/1000*math.pi)); d.line((0,y,700,y),fill=(v,2,int(v*.9)))
text(d,(350,50),'NEXUS',100,bold=True); text(d,(350,240),'BETTER\nTOGETHER',43)
d.line((40,385,660,385),fill='#ff7deb',width=3)
d.multiline_text((350,470),'未来は\n私たちのもの',font=ImageFont.truetype(JP,65),fill='white',anchor='ma',align='center')
text(d,(350,760),'THE FUTURE\nIS OURS',49); finish(im,'nexus.png')

im=Image.new('RGB',(700,700),'#070c35'); d=ImageDraw.Draw(im)
for r in range(280,20,-18):
    c=['#3c18e7','#a32cf0','#f24ce9','#3fdcfc'][r//18%4]
    d.ellipse((350-r,305-r*.85,350+r,305+r*.85),outline=c,width=9)
text(d,(350,585),'SYNTHETIC REALITIES',34); finish(im,'portal.png')

def skyline(name, title, subtitle, colors):
    im=Image.new('RGB',(800,600)); d=ImageDraw.Draw(im)
    for y in range(600):
        t=y/600; d.line((0,y,800,y),fill=tuple(int(a*(1-t)+b*t) for a,b in zip(colors[0],colors[1])))
    d.ellipse((520,65,665,210),fill='#c8efff')
    for i in range(35):
        x=i*27-30; h=random.randrange(70,260); d.rectangle((x,400-h,x+random.randrange(15,30),420),fill=random.choice(['#0e2c67','#134381','#1461a6']))
        if i%6==0:d.line((x+10,400-h,x+10,350-h),fill='#68edff',width=2)
    d.polygon([(0,420),(190,350),(380,430),(620,300),(800,390),(800,600),(0,600)],fill='#122351')
    text(d,(400,450),title,56); text(d,(400,535),subtitle,21); finish(im,name)
skyline('arasaka.png','ARASAKA','PEOPLE / PLANET / PROGRESS',[(28,202,233),(171,38,209)])
skyline('landscape.png','NEW HORIZONS','LIVE BEYOND THE ORDINARY',[(33,216,238),(82,18,183)])

im=Image.new('RGB',(1000,700),'#06132e'); d=ImageDraw.Draw(im)
for i in range(65):
    y=random.randrange(400); d.line((0,y,1000,y-random.randrange(20,130)),fill=random.choice(['#02bce5','#1657bc','#981ed4']),width=random.randrange(1,5))
def car(x,y,s,c):
    p=[(x,y),(x+70*s,y-60*s),(x+170*s,y-85*s),(x+250*s,y-20*s),(x+300*s,y),(x+285*s,y+45*s),(x+35*s,y+45*s)]
    d.polygon(p,fill=c); d.line(p+[p[0]],fill='#9cf9ff',width=3)
    d.polygon([(x+82*s,y-48*s),(x+166*s,y-70*s),(x+218*s,y-18*s),(x+65*s,y-18*s)],fill='#071a43')
    for wx in [x+67*s,x+237*s]:
        d.ellipse((wx-22*s,y+14*s,wx+22*s,y+63*s),fill='#08112d',outline='#37e6ff',width=4)
    d.line((x+255*s,y+8*s,x+295*s,y+8*s),fill='#ff40f3',width=5)
car(270,220,1.7,'#1571bb'); car(510,110,1.05,'#071742')
text(d,(300,455),'DRIVE\nA CLEANER\nTOMORROW',58,bold=True); logo(d,800,550,75); finish(im,'drive.png')

im=Image.new('RGB',(500,1300),'#071527');d=ImageDraw.Draw(im)
d.multiline_text((250,70),'未来は、\nまだ終わらない',font=ImageFont.truetype(JP,66),fill='#94edff',anchor='ma',align='center',spacing=30)
text(d,(250,880),'THE\nNIGHT\nLIVES\nON',64);finish(im,'night.png')
im=Image.new('RGB',(500,700),'#07172b');d=ImageDraw.Draw(im)
d.ellipse((165,75,335,245),outline='#9bffff',width=6);d.ellipse((120,145,380,180),outline='#9bffff',width=5)
text(d,(250,335),'CLEANER\nBRIGHTER\nTOMORROW',45);finish(im,'tomorrow.png')
print(f'Generated {len(list(ROOT.glob("*.png")))} original billboard textures in {ROOT}')
