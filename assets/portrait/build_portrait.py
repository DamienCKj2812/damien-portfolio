"""Smooth single-photo bust with continuous, colour-matched surface atlases."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT/'public/models/portrait'
sys.path.insert(0, str(HERE))
from surface_textures import SurfaceTextures, smoothstep

REF_W, REF_H, SCALE = 1111.0, 1416.0, .001


def profile(anchors, samples):
    """Shape-preserving C1 interpolation avoids stacked-cone silhouette bands."""
    points = np.asarray(anchors, dtype=float)
    x, values = points[:, 0], points[:, 1:]
    dx = np.diff(x)
    slopes = np.diff(values, axis=0)/dx[:, None]
    tangent = np.zeros_like(values)
    tangent[0], tangent[-1] = slopes[0], slopes[-1]
    for i in range(1, len(x)-1):
        left, right = slopes[i-1], slopes[i]
        valid = left*right > 0
        w1, w2 = 2*dx[i]+dx[i-1], dx[i]+2*dx[i-1]
        tangent[i, valid] = (w1+w2)/(w1/left[valid]+w2/right[valid])
    sample = np.clip(np.asarray(samples), x[0], x[-1])
    index = np.clip(np.searchsorted(x, sample)-1, 0, len(x)-2)
    span = x[index+1]-x[index]
    t = (sample-x[index])/span
    return ((2*t**3-3*t**2+1)[..., None]*values[index] +
            (t**3-2*t**2+t)[..., None]*span[..., None]*tangent[index] +
            (-2*t**3+3*t**2)[..., None]*values[index+1] +
            (t**3-t**2)[..., None]*span[..., None]*tangent[index+1])


def surface_factory(textures, anchors, kind):
    def surface(py, theta):
        actual_py = py
        if kind == 'shirt':
            hem = 1300 + 48*np.maximum(0, np.cos(theta))**2 + 20*np.maximum(0, -np.cos(theta))**2 - 25*np.sin(theta)**2
            actual_py = py + smoothstep(1140, anchors[-1][0], py)*(hem-anchors[-1][0])
        shape = profile(anchors, actual_py)
        cx, rx, depth, cy = [shape[..., i] for i in range(4)]
        cx, rx = textures.fit_section(actual_py, cx, rx)
        px = cx+rx*np.sin(theta)
        y = cy-depth*np.cos(theta)
        if kind == 'head':
            front = np.maximum(0, np.cos(theta))**4
            nose = (.010*np.exp(-((px-554)/18)**2-((actual_py-371)/24)**2) +
                    .025*np.exp(-((px-554)/23)**2-((actual_py-402)/13)**2))
            lips = .005*np.exp(-((px-554)/36)**2-((actual_py-449)/12)**2)
            chin = .010*np.exp(-((px-554)/45)**2-((actual_py-478)/16)**2)
            eye = .003*(np.exp(-((px-509)/21)**2-((actual_py-347)/15)**2) + np.exp(-((px-599)/21)**2-((actual_py-347)/15)**2))
            y -= (nose+lips+chin-eye)*front
        elif kind in ['shirt', 'arm']:
            y += .0018*np.sin(actual_py/24+theta*3)*np.sin(theta)**2
        return px, y, actual_py, rx, depth/SCALE
    return surface


def mesh_from_grid(name, xyz, uv, mat, close=True):
    rings, segments = xyz.shape[:2]
    vertices = xyz.reshape(-1, 3).tolist()
    faces = []
    for j in range(rings-1):
        for k in range(segments-1):
            faces.append((j*segments+k, (j+1)*segments+k, (j+1)*segments+k+1, j*segments+k+1))
    if close:
        faces += [tuple(range(segments-1)), tuple(reversed([(rings-1)*segments+k for k in range(segments-1)]))]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    mesh.calc_loop_triangles()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    layer = mesh.uv_layers.new(name='SeamlessWrapUV')
    coords = uv.reshape(-1, 2)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
        for loop in polygon.loop_indices:
            layer.data[loop].uv = coords[mesh.loops[loop].vertex_index]
    obj['reconstruction'] = 'Photo front blended continuously into inferred sides/back'
    return obj


def loft(textures, name, kind, anchors, rings=80, segments=64, texture_width=1024, texture_height=1024):
    surface = surface_factory(textures, anchors, kind)
    theta, py = np.meshgrid(np.linspace(-math.pi, math.pi, segments+1), np.linspace(anchors[0][0], anchors[-1][0], rings))
    px, y, actual_py, _, _ = surface(py, theta)
    xyz = np.stack(((px-555.5)*SCALE, y, (REF_H-actual_py)*SCALE), axis=-1)
    uv = np.stack(((theta+math.pi)/math.tau, 1-(py-anchors[0][0])/(anchors[-1][0]-anchors[0][0])), axis=-1)
    mat = textures.wrap(f'Portrait / {name} wrap', kind, surface, anchors[0][0], anchors[-1][0], texture_width, texture_height)
    return mesh_from_grid(f'Portrait / {name}', xyz, uv, mat)


def hair_shell(textures, anchors):
    surface = surface_factory(textures, anchors, 'head')
    theta, t = np.meshgrid(np.linspace(-math.pi, math.pi, 81), np.linspace(0, 1, 56))
    py = 130+t*(textures.hairline(theta)-130)
    px, y, actual_py, _, _ = surface(py, theta)
    # Soft clumps and fine edge irregularity replace the hard helmet silhouette.
    lift = .003 + .0025*np.sin(theta*13+py/43)**2*np.sin(t*math.pi)**2
    px += np.sin(theta)*lift/SCALE
    y -= np.cos(theta)*lift
    xyz = np.stack(((px-555.5)*SCALE, y, (REF_H-actual_py)*SCALE), axis=-1)
    uv = np.stack(((theta+math.pi)/math.tau, 1-t), axis=-1)
    def hair_surface(base_py, angle):
        fraction = (base_py-130)/(415-130)
        final_py = 130+fraction*(textures.hairline(angle)-130)
        return surface(final_py, angle)
    mat = textures.wrap('Portrait / hair detail wrap', 'hair', hair_surface, 130, 415, 1024, 1024)
    return mesh_from_grid('Portrait / layered hair cap', xyz, uv, mat)


def ears(textures):
    for side, mirror in [('left', True), ('right', False)]:
        # Volumetric, front-turned ears overlap the skull. A flat side disk reads
        # as a detached paper triangle from the frontal camera.
        anchors = [(332,670,3,.007,-.004), (344,675,12,.018,-.003),
                   (366,678,17,.022,-.002), (391,676,12,.018,-.001),
                   (405,671,5,.009,0), (409,667,2,.004,0)]
        if mirror: anchors = [(py,1111-cx,rx,d,cy) for py,cx,rx,d,cy in anchors]
        loft(textures, f'{side} rounded ear', 'ear', anchors, rings=34, segments=56, texture_width=512, texture_height=512)


def camera(scene, name, position, target, scale):
    data = bpy.data.cameras.new(name)
    data.type, data.ortho_scale = 'ORTHO', scale
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = position
    obj.rotation_euler = (Vector(target)-obj.location).to_track_quat('-Z', 'Y').to_euler()
    return obj


def build(source, render):
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    image = bpy.data.images.load(str(source), check_existing=False)
    original_size = list(image.size)
    if abs(original_size[0]/original_size[1]-REF_W/REF_H) > .025:
        raise ValueError('Profiles require the supplied uncropped portrait.')
    textures = SurfaceTextures(image, OUT)
    image.scale(1024, round(original_size[1]*1024/original_size[0]))
    image.filepath_raw, image.file_format = str(OUT/'portrait-front.png'), 'PNG'
    image.save();image.pack()

    head = [(130,555,3,.004,.010), (146,554,66,.060,.008), (180,553,115,.100,.008),
            (235,550,132,.118,.010), (293,550,116,.105,.004), (330,550,110,.100,0),
            (375,551,116,.103,0), (421,552,104,.093,-.002), (465,554,79,.080,-.002),
            (492,555,64,.067,0), (518,555,72,.067,.003), (555,555,68,.061,.010), (570,555,65,.057,.012)]
    loft(textures, 'continuous head and neck', 'head', head, rings=110, segments=80)
    hair_shell(textures, head)
    torso = [(505,555,88,.073,.028), (548,555,133,.094,.026), (591,555,218,.126,.025),
             (637,555,230,.143,.026), (752,555,214,.146,.028), (990,555,226,.148,.030),
             (1190,555,230,.149,.028), (1300,555,222,.140,.025), (1348,555,215,.134,.025)]
    loft(textures, 'tailored shirt torso', 'shirt', torso, rings=96, segments=80, texture_width=2048)
    loft(textures, 'rounded trouser waist', 'pants', [(1245,555,228,.104,.040), (1320,555,235,.108,.040),
         (1390,555,245,.112,.040), (1416,555,248,.114,.040)], rings=28, segments=72, texture_height=384)
    for side, mirror in [('left', False), ('right', True)]:
        arm = [(558,410,4,.015,.025), (581,346,44,.082,.020), (602,310,57,.095,.020), (663,290,67,.094,.015),
               (782,276,66,.087,-.015), (945,249,65,.080,-.048), (1030,249,64,.077,-.065),
               (1160,270,62,.072,-.090), (1224,293,51,.061,-.096),
               (1252,320,30,.044,-.025), (1280,346,20,.032,.040), (1308,358,5,.012,.085)]
        if mirror: arm = [(py,1111-cx,rx,d,cy) for py,cx,rx,d,cy in arm]
        loft(textures, f'{side} sleeve and tucked wrist', 'arm', arm, rings=96, segments=64)
    ears(textures)

    scene = bpy.context.scene
    scene.name = 'PORTRAIT / Seamless single-photo half-body reconstruction'
    scene['source_file'] = source.name
    scene['limitations'] = 'Sides/back are inferred, not scanned.'
    bpy.ops.object.select_all(action='DESELECT')
    meshes = [obj for obj in scene.objects if obj.type == 'MESH']
    for obj in meshes: obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(OUT/'portrait.glb'), export_format='GLB', use_selection=True,
                             export_yup=True, export_extras=True, export_cameras=False, export_lights=False)
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 16
    scene.world.color = (.035, .035, .035)
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 640, 800, 100
    scene.render.image_settings.file_format = 'PNG'
    scene.view_settings.view_transform, scene.view_settings.look = 'Standard', 'None'
    views = [('front',(0,-3,.68)), ('three-quarter',(2.12,-2.12,.68)),
             ('side',(3,0,.68)), ('back-three-quarter',(2.12,2.12,.68)), ('back',(0,3,.68))]
    for name, position in views:
        view = camera(scene, f'Portrait / {name} review', position, (0,0,.68), 1.47)
        if name == 'front': scene.camera = view
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'portrait.blend'))
    if render:
        for name, _ in views:
            scene.camera = bpy.data.objects[f'Portrait / {name} review']
            scene.render.filepath = str(HERE/f'portrait-{name}.png')
            bpy.ops.render.render(write_still=True)
    metadata = {
        'source': source.name, 'sourceSize': original_size, 'model': 'portrait.glb',
        'assetHash': hashlib.sha256((OUT/'portrait.glb').read_bytes()).hexdigest()[:16],
        'reconstruction': 'Photo front feathered into inferred surfaces using continuous cylindrical atlases',
        'unseenSurfaces': 'Inferred sides, back, skin, hair, and shirt stripes',
        'surfaceVersion': 2, 'textures': textures.generated,
        'meshCount': len(meshes), 'triangles': sum(len(o.data.loop_triangles) for o in meshes),
    }
    for target in [OUT/'portrait.json', HERE/'browser-manifest.json']:
        target.write_text(json.dumps(metadata, indent=2)+'\n')
    print(f'PORTRAIT exported: {OUT/"portrait.glb"}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--render', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    build(args.source.expanduser().resolve(), args.render)
