"""Continuous cylindrical atlases in the source photo's colour space.

Photo projection fades into reconstructed surfaces inside one material. No
front/back material boundary or emissive-versus-lit brightness discontinuity.
"""
import math

import bpy
import numpy as np

REF_W, REF_H = 1111.0, 1416.0


def smoothstep(a, b, value):
    t = np.clip((value-a)/(b-a), 0, 1)
    return t*t*(3-2*t)


class SurfaceTextures:
    def __init__(self, image, output):
        self.output = output
        self.width, self.height = image.size
        self.pixels = np.asarray(image.pixels[:], dtype=np.float32).reshape(self.height, self.width, 4)[::-1, :, :3]
        self.background = np.median(np.concatenate((self.pixels[:, :48], self.pixels[:, -48:]), axis=1), axis=1)
        self.generated = []
        skin = self.sample(*np.meshgrid(np.linspace(465, 490, 30), np.linspace(365, 435, 50)))
        self.skin = np.median(skin.reshape(-1, 3), axis=0)
        chest = self.sample(*np.meshgrid(np.linspace(385, 725, 160), np.linspace(720, 1100, 160))).reshape(-1, 3)
        gray = np.mean(chest, axis=1)
        self.blue = np.median(chest[gray < np.quantile(gray, .3)], axis=0)
        self.white = np.median(chest[gray > np.quantile(gray, .75)], axis=0)
        band = self.sample(np.linspace(385, 725, 512), np.full(512, 780))
        signal = np.mean(band, axis=1)
        spectrum = np.abs(np.fft.rfft(signal-signal.mean()))
        periods = 340/np.maximum(1, np.arange(len(spectrum)))
        spectrum[(periods < 9) | (periods > 25)] = 0
        self.stripe_period = float(np.clip(periods[np.argmax(spectrum)], 12, 22))
        self.hair_patch = self.sample(*np.meshgrid(np.linspace(463, 642, 256), np.linspace(179, 254, 128)))
        hair_gray = np.mean(self.hair_patch, axis=2)
        self.hair_color = np.median(self.hair_patch[hair_gray < .28], axis=0)
        self.hair_patch[hair_gray > .45] = self.hair_color
        self.front_hairline = []
        for px in np.linspace(425, 680, 256):
            ys = np.arange(244, 315)
            colors = self.sample(np.full(len(ys), px), ys)
            dark = ys[np.mean(colors, axis=1) < .24]
            self.front_hairline.append(float(dark[-1]) if len(dark) else 290)
        self.front_hairline = np.asarray(self.front_hairline)
        self.silhouette = []
        for py in range(int(REF_H)):
            row = self.pixels[min(self.height-1, int(py/REF_H*self.height))]
            bg = np.median(np.concatenate((row[:64], row[-64:])), axis=0)
            subject = np.flatnonzero(np.linalg.norm(row-bg, axis=1) > .12)
            subject = subject[(subject > self.width*.12) & (subject < self.width*.88)]
            self.silhouette.append((subject[0]/self.width*REF_W, subject[-1]/self.width*REF_W) if len(subject) else None)
        valid = [(i, pair) for i, pair in enumerate(self.silhouette) if pair]
        self.bound_rows = np.array([i for i, _ in valid])
        self.left = np.array([pair[0] for _, pair in valid])
        self.right = np.array([pair[1] for _, pair in valid])
        kernel = np.ones(9)/9
        self.left = np.convolve(np.pad(self.left, (4, 4), mode='edge'), kernel, mode='valid')
        self.right = np.convolve(np.pad(self.right, (4, 4), mode='edge'), kernel, mode='valid')

    def sample(self, px, py):
        x, y = np.broadcast_arrays(np.asarray(px), np.asarray(py))
        x = np.clip(x/REF_W*(self.width-1), 0, self.width-1)
        y = np.clip(y/REF_H*(self.height-1), 0, self.height-1)
        x0, y0 = x.astype(int), y.astype(int)
        x1, y1 = np.minimum(x0+1, self.width-1), np.minimum(y0+1, self.height-1)
        fx, fy = (x-x0)[..., None], (y-y0)[..., None]
        return (self.pixels[y0, x0]*(1-fx)+self.pixels[y0, x1]*fx)*(1-fy)+(self.pixels[y1, x0]*(1-fx)+self.pixels[y1, x1]*fx)*fy

    def fit_section(self, py, cx, rx):
        left = np.interp(py, self.bound_rows, self.left)+2
        right = np.interp(py, self.bound_rows, self.right)-2
        low, high = np.maximum(cx-rx, left), np.minimum(cx+rx, right)
        return (low+high)/2, np.maximum(1.5, (high-low)/2)

    def hairline(self, theta):
        angle = np.abs(theta)
        inferred = 308 + 29*np.abs(np.sin(theta))**1.3 + 100*smoothstep(1.75, 2.9, angle)
        px = 553+122*np.sin(theta)
        actual = np.interp(px, np.linspace(425, 680, 256), self.front_hairline)
        line = actual*(1-smoothstep(.7, 1.15, angle)) + inferred*smoothstep(.7, 1.15, angle)
        return line + 2*np.sin(theta*17) + 2*np.sin(theta*11+1) + 12*np.exp(-((angle-1.27)/.13)**2)

    def hair(self, theta, py):
        # Flowing, periodic strand fields use the photograph's measured palette,
        # not tiled photo rectangles whose edges would show around the crown.
        phase = theta*127 + py*.16 + 2*np.sin(theta*7+py/57)
        strands = .5+.5*np.sin(phase)
        fine = .5+.5*np.sin(theta*283+py*.31+np.sin(theta*11))
        clumps = .10*np.sin(theta*7+py/39)+.055*np.cos(theta*13-py/52)
        tone = .80+.24*strands+.07*fine+clumps
        return np.clip(self.hair_color*tone[..., None], 0, 1)

    def skin_color(self, theta, py, head=False):
        color = np.broadcast_to(self.skin, np.broadcast_arrays(theta, py)[0].shape+(3,)).copy()
        shade = .94 + .035*np.cos(theta) + .025*np.cos(theta-1)
        if head:
            # Soft anatomical occlusion rather than abrupt horizontal bands.
            shade -= .07*np.exp(-((py-479)/18)**2)*(1-smoothstep(.3, 1.2, np.abs(theta)))
            shade -= .035*np.exp(-((py-518)/25)**2)
        color *= shade[..., None]
        color += .006*np.sin(theta*19+py*.71)[..., None]
        return np.clip(color, 0, 1)

    def clothing(self, theta, py, rx, depth, kind):
        circumference = math.pi*(3*(rx+depth)-np.sqrt((3*rx+depth)*(rx+3*depth)))
        # One integer repeat count per garment panel, not per row. Changing the
        # count while travelling down a sleeve creates horizontal checker bands.
        count = max(8, round(float(np.median(circumference))/self.stripe_period))
        phase = theta/math.tau*count + .09*np.sin(py/79) + .025*np.sin(py/31+theta*3)
        if kind == 'arm':
            cuff = smoothstep(1188, 1205, py)*(1-smoothstep(1243, 1254, py))
            phase = phase*(1-cuff)+(py/14+theta*.25)*cuff
        band = smoothstep(-.16, .16, np.sin(phase*math.tau))
        color = self.blue[None, None, :]*(1-band[..., None]) + self.white[None, None, :]*band[..., None]
        shade = .92 + .04*np.cos(theta) + .025*np.sin(py/25+theta*4)
        if kind == 'shirt':
            yoke = np.exp(-((py-606-6*np.cos(theta))/2.4)**2)*smoothstep(1.3, 2.0, np.abs(theta))
            shade *= 1-.13*yoke
        color *= shade[..., None]
        weave = .005*np.sin(py*5)*np.sin(theta*720)
        return np.clip(color+weave[..., None], 0, 1)

    def image_material(self, name, rgb):
        h, w, _ = rgb.shape
        image = bpy.data.images.new(name, width=w, height=h)
        rgba = np.ones((h, w, 4), dtype=np.float32)
        rgba[:, :, :3] = np.clip(rgb[::-1], 0, 1)
        image.pixels.foreach_set(rgba.ravel())
        filename = name.split(' / ')[-1].replace(' ', '-').lower()+'.png'
        image.filepath_raw = str(self.output/filename)
        image.file_format = 'PNG'
        image.save()
        image.pack()
        self.generated.append(filename)
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        mat.node_tree.nodes.clear()
        output = mat.node_tree.nodes.new('ShaderNodeOutputMaterial')
        texture = mat.node_tree.nodes.new('ShaderNodeTexImage')
        texture.image = image
        texture.extension = 'EXTEND'
        mat.node_tree.links.new(texture.outputs['Color'], output.inputs['Surface'])
        return mat

    def wrap(self, name, kind, surface, start, end, width=1024, height=1024):
        theta, py = np.meshgrid(np.linspace(-math.pi, math.pi, width), np.linspace(start, end, height))
        px, _, actual_py, rx, depth = surface(py, theta)
        original = self.sample(px, actual_py)
        angle = np.abs(theta)
        photo_weight = 1-smoothstep(.56 if kind in ['head', 'hair'] else .38, 1.40, angle)
        if kind == 'hair':
            synthetic = self.hair(theta, actual_py)
            photo_weight *= 1-smoothstep(.35, .65, np.mean(original, axis=2))
        elif kind in ['head', 'ear']:
            synthetic = self.skin_color(theta, actual_py, head=True)
            if kind == 'head':
                hair_mask = 1-smoothstep(-3, 3, actual_py-self.hairline(theta))
                synthetic = synthetic*(1-hair_mask[..., None])+self.hair(theta, actual_py)*hair_mask[..., None]
            else:
                bowl = .05*np.exp(-((actual_py-365)/22)**2)*np.cos(theta)**2
                synthetic *= (1-bowl)[..., None]
        elif kind in ['shirt', 'arm']:
            synthetic = self.clothing(theta, actual_py, rx, depth, kind)
            if kind == 'arm':
                wrist = smoothstep(1242, 1253, actual_py)
                synthetic = synthetic*(1-wrist[..., None]) + self.skin_color(theta, actual_py)*wrist[..., None]
        else:
            synthetic = np.full(original.shape, .055)
            synthetic *= (.9+.06*np.cos(theta)+.035*np.sin(actual_py/18))[..., None]
        # A photo-background pixel is not allowed to become a white painted
        # patch on a reconstructed surface; keep valid bright fabric stripes.
        bg = np.stack([np.interp(actual_py, np.linspace(0, REF_H, self.height), self.background[:, c]) for c in range(3)], axis=-1)
        valid = smoothstep(.045, .10, np.linalg.norm(original-bg, axis=-1))
        photo_weight *= valid
        if kind == 'shirt':
            trouser_pixels = smoothstep(1220, 1280, actual_py)*(1-smoothstep(.12, .27, np.mean(original, axis=-1)))
            photo_weight *= 1-trouser_pixels
        rgb = original*photo_weight[..., None] + synthetic*(1-photo_weight[..., None])
        return self.image_material(name, rgb)
