"""Build the specified cylindrical reference tower in the production master.

All existing transforms/actions and the active journey camera are retained.
The reference inspection camera is separate. Exterior geometry uses native
solid meshes, emissive tubes, line sources and lightweight particle sources.
"""
import json
import math
import random
import shutil
import sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from reference_tower_spec import SCALE, CENTER, RADIUS, SCREENS, PREVIEW_CAMERA, height, surface
from restore_wireframe_skyline import restore_skyline

PREFIX = 'Reference tower • '
MASTER = ROOT / 'monochrome-city-solid-tower.blend'
scene = bpy.context.scene
assert scene.name == 'MONO / Wire & Particle City'
assert Path(bpy.data.filepath).resolve() == MASTER
originals = [o for o in scene.objects if not o.name.startswith(PREFIX)]
poses = {}
for frame in (1, 90, 150, 245, 383, 450):
    scene.frame_set(frame)
    scene.view_layers[0].update()
    poses[frame] = {o.name: o.matrix_world.copy() for o in originals}
scene.frame_set(1)
camera = scene.camera
old = bpy.data.collections.get(PREFIX + 'Architectural redesign')
if old:
    for obj in list(old.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(old)
for blocks in (bpy.data.meshes, bpy.data.curves, bpy.data.node_groups, bpy.data.materials,
               bpy.data.images, bpy.data.cameras, bpy.data.lights):
    for block in list(blocks):
        if block.name.startswith(PREFIX) and block.users == 0:
            blocks.remove(block)
collection = bpy.data.collections.new(PREFIX + 'Architectural redesign')
scene.collection.children.link(collection)
templates = {kind: next(g for g in bpy.data.node_groups if g.name.startswith('Mono • ' + kind))
             for kind in ['Wires', 'Points']}
materials, groups = {}, {}
stats = {'lineSegments': 0, 'points': 0, 'solidObjects': 0, 'screens': 0}


def material(value, style='emission'):
    key = (round(value, 5), style)
    if key not in materials:
        mat = bpy.data.materials.new(PREFIX + str(key))
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        nodes.clear()
        out = nodes.new('ShaderNodeOutputMaterial')
        em = nodes.new('ShaderNodeEmission')
        em.name = 'Browser luminance proxy'
        em.inputs['Color'].default_value = (value, value, value, 1)
        mat['city_browser_luminance'] = value
        if style in ['metal', 'glass']:
            bsdf = nodes.new('ShaderNodeBsdfPrincipled')
            bsdf.inputs['Base Color'].default_value = (.02, .02, .02, 1) if style == 'glass' else (.015, .015, .015, 1)
            bsdf.inputs['Metallic'].default_value = 0 if style == 'glass' else .9
            bsdf.inputs['Roughness'].default_value = .1 if style == 'glass' else .28
            if style == 'glass':
                bsdf.inputs['Transmission Weight'].default_value = .3
            noise = nodes.new('ShaderNodeTexNoise')
            noise.inputs['Scale'].default_value = 180
            bump = nodes.new('ShaderNodeBump')
            bump.inputs['Strength'].default_value = .05
            mat.node_tree.links.new(noise.outputs['Fac'], bump.inputs['Height'])
            mat.node_tree.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
            if style == 'glass':
                facing = nodes.new('ShaderNodeLayerWeight')
                ramp = nodes.new('ShaderNodeValToRGB')
                ramp.color_ramp.elements[0].position = .15
                ramp.color_ramp.elements[1].position = .95
                rim = nodes.new('ShaderNodeEmission')
                rim.inputs['Strength'].default_value = 10
                add = nodes.new('ShaderNodeAddShader')
                mat.node_tree.links.new(facing.outputs['Fresnel'], ramp.inputs[0])
                mat.node_tree.links.new(ramp.outputs['Color'], rim.inputs['Color'])
                mat.node_tree.links.new(bsdf.outputs[0], add.inputs[0])
                mat.node_tree.links.new(rim.outputs[0], add.inputs[1])
                mat.node_tree.links.new(add.outputs[0], out.inputs[0])
            else:
                mat.node_tree.links.new(bsdf.outputs[0], out.inputs[0])
        else:
            em.inputs['Strength'].default_value = 20 if style == 'led' else 1
            mat.node_tree.links.new(em.outputs[0], out.inputs[0])
        mat.diffuse_color = (value, value, value, 1)
        materials[key] = mat
    return materials[key]


def mesh(name, vertices, faces, value=.002, style='emission', clearance=None):
    data = bpy.data.meshes.new(PREFIX + name)
    data.from_pydata(vertices, [], faces)
    data.update()
    data.materials.append(material(value, style))
    obj = bpy.data.objects.new(PREFIX + name, data)
    collection.objects.link(obj)
    obj['city_render_kind'] = 'solid'
    if clearance:
        obj['tower_' + clearance + '_clearance'] = True
    stats['solidObjects'] += 1
    return obj


def lines(name, paths, value=.2, radius=.006, glow=False):
    vertices, edges = [], []
    for path in paths:
        start = len(vertices)
        vertices.extend(path)
        edges.extend((start + i, start + i + 1) for i in range(len(path) - 1))
    data = bpy.data.meshes.new(PREFIX + name)
    data.from_pydata(vertices, edges, [])
    data.update()
    data.attributes.new('radius', 'FLOAT', 'POINT').data.foreach_set('value', [radius] * len(vertices))
    kind = 'glow' if glow else 'lines'
    key = (kind, value)
    if key not in groups:
        group = templates['Wires'].copy()
        group.name = PREFIX + str(key)
        group.nodes.get('Set Material').inputs['Material'].default_value = material(value, 'led' if glow else 'emission')
        groups[key] = group
    obj = bpy.data.objects.new(PREFIX + name, data)
    collection.objects.link(obj)
    obj['city_render_kind'] = kind
    if glow:
        # Tube meshes carry physical LED width. Thin browser centerlines avoid
        # screen-space expanded-line artifacts on the dense circular layout.
        obj['city_browser_render_kind'] = 'lines'
    obj['city_browser_luminance'] = value
    obj.modifiers.new('Native illuminated source', 'NODES').node_group = groups[key]
    stats['lineSegments'] += len(edges)
    return obj


def points(name, vertices, value=.3, radius=.018):
    data = bpy.data.meshes.new(PREFIX + name)
    data.from_pydata(vertices, [], [])
    data.update()
    data.attributes.new('radius', 'FLOAT', 'POINT').data.foreach_set('value', [radius] * len(vertices))
    group = templates['Points'].copy()
    group.name = PREFIX + name
    group.nodes.get('Set Material').inputs['Material'].default_value = material(value)
    obj = bpy.data.objects.new(PREFIX + name, data)
    collection.objects.link(obj)
    obj['city_render_kind'] = 'points'
    obj.modifiers.new('Native sparkle points', 'NODES').node_group = group
    stats['points'] += len(vertices)


def path(radius, z, start=-180, end=180, count=96):
    return [surface(radius, start + (end - start) * i / count, z) for i in range(count + 1)]


def sector(name, radius, z0, z1, start, end, value=.002, count=96, clearance=None, style='emission'):
    vertices = path(radius, z0, start, end, count) + path(radius, z1, start, end, count)
    n = count + 1
    return mesh(name, vertices, [(i, i + 1, n + i + 1, n + i) for i in range(count)], value, style, clearance)


def slab(name, inner, outer, z0, z1, start=-180, end=180, value=.003):
    count = 96
    vertices = path(inner, z0, start, end) + path(outer, z0, start, end)
    vertices += path(inner, z1, start, end) + path(outer, z1, start, end)
    n = count + 1
    faces = []
    for i in range(count):
        faces.extend([(i, i + 1, n + i + 1, n + i), (2*n+i, 3*n+i, 3*n+i+1, 2*n+i+1),
                      (n+i, n+i+1, 3*n+i+1, 3*n+i), (i, 2*n+i, 2*n+i+1, i+1)])
    faces.extend([(0, n, 3*n, 2*n), (count, 2*n+count, 3*n+count, n+count)])
    return mesh(name, vertices, faces, value, 'metal')


def tube(name, coordinates, radius=.04, value=.9):
    vertices, faces = [], []
    coordinates = [Vector(p) for p in coordinates]
    for i, point in enumerate(coordinates):
        tangent = (coordinates[min(i+1, len(coordinates)-1)] - coordinates[max(0, i-1)]).normalized()
        axis = Vector((1, 0, 0)) if abs(tangent.z) > .9 else Vector((0, 0, 1))
        u = tangent.cross(axis).normalized()
        v = tangent.cross(u).normalized()
        vertices.extend(tuple(point + radius * (math.cos(a)*u + math.sin(a)*v)) for a in [j*math.tau/8 for j in range(8)])
    for i in range(len(coordinates)-1):
        faces.extend((8*i+j, 8*i+(j+1)%8, 8*(i+1)+(j+1)%8, 8*(i+1)+j) for j in range(8))
    return mesh(name, vertices, faces, value, 'led')


def box(name, center, size, value=.002, edge=0):
    vertices = [tuple(center[i] + sign[i]*size[i]/2 for i in range(3)) for sign in
                [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    obj = mesh(name, vertices, [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)], value, 'metal')
    if edge:
        lines(name + ' sparse edges', [[vertices[a], vertices[b]] for a,b in
              [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]], edge)
    return obj


def display(key, object_name):
    spec = SCREENS[key]
    a, b = spec['azimuth']
    z0, z1 = spec['z']
    count = 96
    vertices = path(spec['radius'], z0, a, b) + path(spec['radius'], z1, a, b)
    obj = scene.objects[object_name]
    data = bpy.data.meshes.new(PREFIX + key + ' cylindrical display')
    inverse = obj.matrix_world.inverted()
    data.from_pydata([tuple(inverse @ Vector(p)) for p in vertices], [],
                    [(i, i+1, count+2+i, count+1+i) for i in range(count)])
    data.update()
    uv = data.uv_layers.new(name='Cylindrical UV')
    for polygon in data.polygons:
        for loop in polygon.loop_indices:
            index = data.loops[loop].vertex_index
            uv.data[loop].uv = (index % (count+1) / count, 0 if index <= count else 1)
    image = bpy.data.images.load(str(ROOT/'textures-monochrome'/('reference-'+key+'.jpg')), check_existing=False)
    image.name = PREFIX + key + ' packed artwork'
    image.pack()
    mat = bpy.data.materials.new(PREFIX + key + ' screen')
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    out, em, tex = nodes.new('ShaderNodeOutputMaterial'), nodes.new('ShaderNodeEmission'), nodes.new('ShaderNodeTexImage')
    tex.image = image
    em.inputs['Strength'].default_value = 3
    mat.node_tree.links.new(tex.outputs['Color'], em.inputs['Color'])
    coat = nodes.new('ShaderNodeBsdfAnisotropic')
    coat.inputs['Roughness'].default_value = .12
    mix = nodes.new('ShaderNodeMixShader')
    mix.inputs[0].default_value = .15
    mat.node_tree.links.new(em.outputs[0], mix.inputs[1])
    mat.node_tree.links.new(coat.outputs[0], mix.inputs[2])
    mat.node_tree.links.new(mix.outputs[0], out.inputs[0])
    data.materials.append(mat)
    obj.data = data
    obj.material_slots[0].link = 'DATA'
    obj['city_render_kind'] = 'screen'
    obj['city_texture'] = 'reference-'+key+'.jpg'
    obj['tower_reference_display'] = True
    obj['tower_display_key'] = key
    if key in ('logo', 'portrait'):
        artwork = json.loads((ROOT / 'reference-tower-artwork.json').read_text())
        obj['banner_artwork_source'] = artwork['source']
        obj['banner_artwork_sha256'] = artwork['outputs'][f'reference-{key}.jpg']['sha256']
    obj.hide_render = False
    obj.hide_set(False)
    stats['screens'] += 1


# The former block tower and scaffold skyline are recovery inputs.
# Preserve the authored orbital sky; only its annotation labels are suppressed.
for obj in originals:
    retire = obj.name.startswith(('Hero solid •', 'Hero glow •', 'Hero • luminous', 'Hero • right facade'))
    retire |= obj.name in ['Clean outlines • Primary tower silhouette', 'Clean outlines • Major structure',
                          'Clean outlines • Skyline silhouettes', 'Clean outlines • Billboard frames',
                          'Hero display • Clean mobility campaign • LED display', 'Hero display • Curved LED • arasaka']
    retire |= obj.name.startswith(('Mono • 04 Skyline', 'Mono backing • Skyline', 'Mono backing • Flanking', 'Mono • 03 Sky garden'))
    retire |= obj.name == 'Humanoid • editable silhouette source'
    if obj.name.startswith('Street plaza • ') and obj.type == 'MESH':
        middle = sum((obj.matrix_world @ Vector(p) for p in obj.bound_box), Vector()) / 8
        retire |= -.1 < middle.x < 1.7 and -25.5 < middle.y < -24.5 and middle.z < 4.3
    retire |= 'scaffold' in obj.name.lower() or 'CYBER sign' in obj.name
    if retire:
        obj.hide_render = True
        obj.hide_set(True)
    outdoor_npc = obj.name.startswith('City NPC') or bool(obj.get('person_metadata'))
    ancestor = obj.parent
    while ancestor:
        outdoor_npc |= ancestor.get('city_role') == 'walking_npc'
        ancestor = ancestor.parent
    if outdoor_npc:
        obj.hide_render = False
        obj.hide_set(False)
sky_annotations = {'orbital grid annotation', 'earth distance annotation',
                   'synchronization annotation', 'annotation ticks and distance bracket'}
for obj in originals:
    if obj.name.startswith('Orbital sky • '):
        hidden = obj.get('city_sky_element') in sky_annotations
        obj.hide_render = hidden
        obj.hide_set(hidden)
sky_source = scene.get('orbital_sky_reference') or scene.get('retired_orbital_sky_reference')
if sky_source:
    sky_meta = json.loads(sky_source)
    sky_meta.update(showAnnotations=False, visibleLabels=0)
    scene['orbital_sky_reference'] = json.dumps(sky_meta)

# A continuous cylindrical skin, with material-backed highlights instead of a
# wire cage. Rear clearance and the front portal are independent export cuts.
front = slab('Cylindrical core front skin', RADIUS-.16, RADIUS, 0, height(104), -105, 105, .003)
rear = slab('Cylindrical core rear skin', RADIUS-.16, RADIUS, 0, height(104), 105, 255, .001)
front['tower_portal_clearance'] = True
rear['tower_atrium_clearance'] = True
for obj in [front, rear]:
    for polygon in obj.data.polygons:
        normal = polygon.normal
        value = .001 + .006*max(0, normal.dot(Vector((-.4,-.9,.1)).normalized()))**6
        mat = material(round(value, 4), 'metal')
        if mat.name not in obj.data.materials:
            obj.data.materials.append(mat)
        polygon.material_index = list(obj.data.materials).index(mat)
        polygon.use_smooth = True
lines('Subtle four-metre floor seams', [path(RADIUS+.008, height(z), -105, 105) for z in range(4, 104, 4)], .008, .003)

# A raised screen cassette and a genuinely recessed channel between the bays.
sector('Raised A cassette backing', RADIUS+.26, height(15)-.1, height(101)+.12, -40.4, 9.4, .001)
sector('Recessed inter-bay channel', 20.5*SCALE, height(15), height(104), 9, 15, .0004)
for angle, value in [(-40, 1.4), (9, .9), (15, .45), (58, .65)]:
    coordinates = [surface(RADIUS + (.37 if angle <= 9 else .09), angle, z) for z in [height(4) if angle <= 9 else 0, height(104) if angle <= 9 else height(80)]]
    tube('Bay vertical LED edge', coordinates, .055 if angle == -40 else .026, value)
    lines('Bay edge soft halo', [coordinates], value, .01, True)
lines('Recessed channel inner LED', [[surface(20.5*SCALE+.01, 12, z) for z in [height(15), height(104)]]], .24, .007, True)
for key, name in [('logo','Hero display • KAZE INDUSTRIES • rooftop monument • LED display'),
                  ('portrait','Hero display • KAZE • cyborg campaign • LED display'),
                  ('order','Hero display • Curved LED • nexus'), ('orbital','Hero display • Curved LED • portal'),
                  ('eclipse','Hero display • Curved LED • landscape')]:
    display(key, name)
    spec = SCREENS[key]
    lines(key + ' fine curved header and sill', [path(spec['radius']+.012, z, *spec['azimuth']) for z in spec['z']], .12 if key in ['logo','portrait'] else .23, .005)

# Parapet and setback crown drum, floating halo, four unequal paired antennas.
slab('Full circular parapet slab', RADIUS-.22, 23*SCALE, height(104), height(106))
slab('Roof plate', .02, RADIUS-.2, height(106)-.08, height(106), value=.001)
sector('Setback crown drum', 15*SCALE, height(106), height(118), -180, 180, .004, style='metal')
for z in [109, 113]:
    sector('Crown horizontal glass band', 15*SCALE+.012, height(z)-.28, height(z)+.28, -180, 180, .018)
    lines('Crown glass band mullions', [[surface(15*SCALE+.02, a, h) for h in [height(z)-.28,height(z)+.28]] for a in range(-180,180,7)], .07, .004)
for radius, z, thickness, value in [(15*SCALE, height(118), .05, .85),
                                     (24*SCALE, height(113), .12, 1.5),
                                     (22.8*SCALE, height(106)+1.2*SCALE, .025, .7)]:
    coordinates = path(radius, z, count=192)
    tube('Crown luminous ring', coordinates, thickness, value)
    lines('Crown ring bloom', [coordinates], value, .01, True)
railing = [path(22.8*SCALE, z) for z in [height(106)+.10, height(106)+1.2*SCALE]]
railing += [[surface(22.8*SCALE, a, z) for z in [height(106),height(106)+1.2*SCALE]] for a in range(-180,180,4)]
lines('Full circular parapet glass railing', railing, .19, .005)
for angle, tip in [(-45,140),(-37,135),(36,145),(46,150)]:
    coordinates = [surface(12*SCALE, angle, height(z)) for z in [118, tip]]
    tube('Paired antenna dark mast', coordinates, .10, .003)
    glow = [(x, y-.135, z) for x,y,z in coordinates]
    tube('Paired antenna luminous core', glow, .028, .9)
    lines('Antenna light halo', [glow], .9, .007, True)
for angle in [-6, 8]:
    tube('Short central rooftop mast', [surface(4*SCALE,angle,height(z)) for z in [118,125]], .035, .10)


def balcony(label, start, end, outer, z0, z1):
    outer *= SCALE
    slab(label + ' rounded slab', RADIUS-.08, outer, height(z0), height(z1), start, end)
    top = height(z1)
    rails = [path(outer-.06, z, start, end) for z in [top+.1,top+.29,top+1.2*SCALE]]
    rails += [[surface(outer-.06,a,z) for z in [top,top+1.2*SCALE]]
              for a in [start+(end-start)*i/32 for i in range(33)]]
    lines(label + ' glazed railing', rails, .35, .006)
    for z in [height(z0), top]:
        tube(label + ' luminous slab rim', path(outer,z,start,end), .022, .75)
        lines(label + ' subtle rim bloom', [path(outer,z,start,end)], .35, .007, True)
    return outer, top


balcony('L2 upper balcony', 25, 110, 27, 92, 94)
l1_radius, l1_top = balcony('L1 lower balcony', 35, 120, 29, 78, 80)
grid = [path(RADIUS+.02,height(z),25,110) for z in [80+i*3.5 for i in range(8)]]
grid += [[surface(RADIUS+.022,a,height(z)) for z in [80,104]] for a in range(25,111,6)]
lines('Upper right glazed curtain wall grid', grid, .075, .004)
fin = [surface(l1_radius+(23*SCALE-l1_radius)*t*t, 75+14*t, height(80)+(height(60)-height(80))*t)
       for t in [i/96 for i in range(97)]]
tube('L1 downward crescent fin', fin, .055, .85)
lines('Crescent fin soft halo', [fin], .7, .01, True)
for a, top in [(60,92),(70,78)]:
    coordinates = [surface(RADIUS+.5*SCALE,a,z) for z in [0,height(top)]]
    tube('Right corner continuous LED fin', coordinates, .05, .65)
    lines('Right corner secondary glow', [coordinates], .5, .008, True)


def tree(label, base, size):
    rng = random.Random(label)
    trunk = [tuple(Vector(base)+Vector((0,0,z))) for z in [0,size*.7]]
    tube(label+' trunk', trunk, .035, .018)
    dots = []
    for _ in range(500):
        p = Vector((rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(-1,1)))
        if p.length > 1:
            continue
        p *= size*.45
        p.z += size*.75
        dots.append(tuple(Vector(base)+p))
    points(label+' fairy-light canopy', dots, .32, .014)
    points(label+' bright sparkle nodes', dots[::17], 1.4, .027)


for angle in [69,91]:
    tree('Balcony sparkle tree '+str(angle), surface(l1_radius-.6,angle,l1_top), 1.6)

# Retain the receding left facade's luminous rectangles. The long banner's
# right-edge glitch strip is retired; its thin frame/LED rails remain intact.
rng = random.Random(186)
for angle_range, z_range, count in [((-72,-41),(10,100),220)]:
    for i in range(count):
        if rng.random() < .55:
            continue
        angle, z = rng.uniform(*angle_range), rng.uniform(*z_range)
        width, h = rng.uniform(.2,1.4)*SCALE, rng.uniform(.2,1.1)*SCALE
        angular = math.degrees(width/(RADIUS+.34))
        sector('Scattered glitch block', RADIUS+.34, height(z), height(z)+h,
               angle-angular/2, angle+angular/2, rng.choice([.035,.15,.5,1.1]), count=1)
for angle, z0, length in [(-66,25,14),(-60,30,13),(-54,25,10),(-48,42,12),(-70,52,8)]:
    angular = math.degrees(2*SCALE/(RADIUS+.12))
    sector('Large left glowing facade panel',RADIUS+.12,height(z0),height(z0+length),angle-angular/2,angle+angular/2,1.1,count=4)
for a in [-72,-65,-57,-48]:
    lines('Receding left vertical light strips', [[surface(RADIUS+.1,a,z) for z in [height(10),height(104)]]], .30, .006, True)

# Geographically textured, closed glass hologram. Its UV seam is at the rear;
# the geographically detailed map, cloud layers and reflections are pre-baked.
center = Vector(surface(RADIUS+3*SCALE,36,height(44)-1.6))
sphere_radius = 5.2*SCALE
vertices, faces = [], []
earth_detail=json.loads((ROOT/'earth-detail.json').read_text())
front_longitude=math.radians(earth_detail['frontLongitudeDegrees'])
longitude_count, latitude_count = 192,96
for row in range(latitude_count+1):
    phi = -math.pi/2+math.pi*row/latitude_count
    for col in range(longitude_count+1):
        theta = -math.pi+math.tau*col/longitude_count-front_longitude
        direction = Vector((math.cos(phi)*math.sin(theta),-math.cos(phi)*math.cos(theta),math.sin(phi)))
        vertices.append(tuple(center+direction*sphere_radius))
n = longitude_count+1
for row in range(latitude_count):
    for col in range(longitude_count):
        faces.append((row*n+col,row*n+col+1,(row+1)*n+col+1,(row+1)*n+col))
sphere = mesh('Orbital globe shaded spherical surface',vertices,faces,.001)
sphere['city_render_kind']='screen'
sphere['city_texture']='reference-earth.jpg'
sphere['reference_earth_detail']=True
uv=sphere.data.uv_layers.new(name='Geographic equirectangular UV')
for polygon in sphere.data.polygons:
    polygon.use_smooth=True
    for loop in polygon.loop_indices:
        index=sphere.data.loops[loop].vertex_index
        uv.data[loop].uv=(index%n/longitude_count,index//n/latitude_count)
earth=bpy.data.images.load(str(ROOT/'textures-monochrome/reference-earth.jpg'),check_existing=False)
earth.name=PREFIX+'Detailed Earth geographic texture'
earth.pack()
mat=bpy.data.materials.new(PREFIX+'Detailed geographic glass hologram')
mat.use_nodes=True
nodes=mat.node_tree.nodes
nodes.clear()
out=nodes.new('ShaderNodeOutputMaterial')
tex=nodes.new('ShaderNodeTexImage');tex.image=earth
em=nodes.new('ShaderNodeEmission');em.inputs['Strength'].default_value=.7
glass=nodes.new('ShaderNodeBsdfPrincipled')
glass.inputs['Roughness'].default_value=.1
glass.inputs['Transmission Weight'].default_value=.3
facing=nodes.new('ShaderNodeLayerWeight')
rim=nodes.new('ShaderNodeEmission');rim.inputs['Strength'].default_value=10
add=nodes.new('ShaderNodeAddShader')
surface_add=nodes.new('ShaderNodeAddShader')
mat.node_tree.links.new(tex.outputs['Color'],glass.inputs['Base Color'])
mat.node_tree.links.new(tex.outputs['Color'],em.inputs['Color'])
mat.node_tree.links.new(facing.outputs['Fresnel'],rim.inputs['Color'])
mat.node_tree.links.new(glass.outputs[0],add.inputs[0])
mat.node_tree.links.new(em.outputs[0],add.inputs[1])
mat.node_tree.links.new(add.outputs[0],surface_add.inputs[0])
mat.node_tree.links.new(rim.outputs[0],surface_add.inputs[1])
mat.node_tree.links.new(surface_add.outputs[0],out.inputs[0])
sphere.data.materials.clear()
sphere.data.materials.append(mat)
grid=[]
for latitude in [-45,0,45]:
    p=math.radians(latitude)
    grid.append([tuple(center+Vector(((sphere_radius+.018)*math.cos(p)*math.sin(t),
                 -(sphere_radius+.018)*math.cos(p)*math.cos(t),(sphere_radius+.018)*math.sin(p))))
                 for t in [i*math.tau/160 for i in range(161)]])
for longitude in [-60,0,60]:
    p=math.radians(longitude)
    grid.append([tuple(center+Vector(((sphere_radius+.018)*math.cos(t)*math.cos(p),
                 (sphere_radius+.018)*math.cos(t)*math.sin(p),(sphere_radius+.018)*math.sin(t))))
                 for t in [i*math.tau/160 for i in range(161)]])
lines('Earth fine latitude and meridian engraving',grid,.065,.003)
limb = [[tuple(center+Vector((sphere_radius*math.cos(t),-.05,sphere_radius*math.sin(t)))) for t in [i*math.tau/128 for i in range(129)]]]
lines('Holographic sphere luminous rim',limb,.65,.006,True)
normal = Vector((math.sin(math.radians(36)),-math.cos(math.radians(36)),0))
tangent = Vector((normal.y,-normal.x,0))
orbits = []
for radius, tilt in [(10*SCALE,.22),(11*SCALE,-.35)]:
    orbits.append([tuple(center+tangent*(radius*math.cos(t))+normal*(radius*.55*math.sin(t))+
                        Vector((0,0,radius*(.25*math.sin(t)+tilt*math.cos(t)))))
                   for t in [i*math.tau/160 for i in range(161)]])
lines('Two extended hologram orbit rings',orbits,.85,.014,True)

# Canopy is fitted above the established 7.65 m entrance, with four bands.
box('Wide layered atrium canopy',(-2.8,-6.45,8.08),(13.1,3.45,.34),.002)
for z in [7.93,8.00,8.10,8.23]:
    coordinates = [(-9.35,-8.19,z),(3.75,-8.19,z),(3.75,-4.70,z)]
    lines('Canopy stacked horizontal LED band',[coordinates],.75,.012,True)
lines('Canopy luminous underside coffers', [[(x,-8.12,7.895),(x,-4.72,7.895)] for x in [-8,-6.5,-5,-3.5,-2,-.5,1,2.5]], .5,.01,True)
for x in [-6.2,3.15]:
    box('Atrium slender outer column',(x,-7.98,3.99),(.16,.22,7.75),.002)
    lines('Atrium vertical glazing light bar',[[(x,-8.11,.12),(x,-8.11,7.86)]],.8,.01,True)
spec = SCREENS['eclipse']
sector('B storefront dim interior glazing',RADIUS+.05,0,spec['z'][0]-.08,15,58,.008)
storefront = [path(RADIUS+.07,z,15,58) for z in [.12,spec['z'][0]-.1]]
storefront += [[surface(RADIUS+.07,a,z) for z in [.12,spec['z'][0]-.1]] for a in [15,25,36,47,58]]
lines('Lit B storefront mullions',storefront,.27,.006)
for angle in [65,77]:
    tree('Ground right fairy-light tree '+str(angle),surface(RADIUS+3.6,angle,0),3.3)
tree('Ground left fairy-light tree',surface(RADIUS+2.2,-67,0),2.2)

# Native mesh lettering remains KAJU, the shared project brand in the reference.
font = bpy.data.curves.new(PREFIX+'Atrium lettering source','FONT')
font.body='K A J U  A T R I U M'
font.align_x='CENTER'
font.size=.24
font.materials.append(material(.75,'led'))
text = bpy.data.objects.new(font.name,font)
collection.objects.link(text)
text.location=(-1.5,-6.05,6.65)
text.rotation_euler=(math.pi/2,0,0)
scene.view_layers[0].update()
deps=bpy.context.evaluated_depsgraph_get()
data=bpy.data.meshes.new_from_object(text.evaluated_get(deps),depsgraph=deps)
sign=bpy.data.objects.new(PREFIX+'KAJU ATRIUM recessed entrance sign',data)
collection.objects.link(sign)
sign.matrix_world=text.matrix_world.copy()
sign['city_render_kind']='solid'
bpy.data.objects.remove(text,do_unlink=True)

# Retain the restored authored night-city skyline during focused tower rebuilds.
skyline = restore_skyline(scene)
(ROOT/'wireframe-skyline.json').write_text(json.dumps(skyline,indent=2)+'\n')

# A matched low-angle inspection camera is added without changing the route.
data=bpy.data.cameras.new(PREFIX+'Reference inspection camera')
data.lens=34
data.sensor_width=36
view=bpy.data.objects.new(data.name,data)
collection.objects.link(view)
view.location=PREVIEW_CAMERA['position']
view.rotation_euler=(Vector(PREVIEW_CAMERA['target'])-view.location).to_track_quat('-Z','Y').to_euler()
scene.render.engine='CYCLES'
scene.cycles.samples=256
scene.cycles.use_denoising=True
scene.render.use_freestyle=False
if scene.world and scene.world.use_nodes:
    for node in scene.world.node_tree.nodes:
        if node.type=='BACKGROUND':
            node.inputs['Color'].default_value=(.002,.002,.002,1)
            node.inputs['Strength'].default_value=1
light_data=bpy.data.lights.new(PREFIX+'Upper-left soft specular light','AREA')
light_data.energy=900
light_data.shape='DISK'
light_data.size=18
light_obj=bpy.data.objects.new(light_data.name,light_data)
collection.objects.link(light_obj)
light_obj.location=(CENTER[0]-18,CENTER[1]-18,height(112))
light_obj.rotation_euler=(Vector((CENTER[0],CENTER[1],height(65)))-light_obj.location).to_track_quat('-Z','Y').to_euler()
finish=bpy.data.node_groups.new(PREFIX+'Monochrome render finish','CompositorNodeTree')
finish.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
layers=finish.nodes.new('CompositorNodeRLayers')
glow=finish.nodes.new('CompositorNodeGlare')
glow.inputs['Type'].default_value='Fog Glow'
glow.inputs['Threshold'].default_value=1
glow.inputs['Quality'].default_value='High'
glow.inputs['Size'].default_value=.6
streaks=finish.nodes.new('CompositorNodeGlare')
streaks.inputs['Type'].default_value='Streaks'
streaks.inputs['Threshold'].default_value=4
streaks.inputs['Strength'].default_value=.035
mono=finish.nodes.new('CompositorNodeHueSat');mono.inputs['Saturation'].default_value=0
contrast=finish.nodes.new('CompositorNodeCurveRGB')
contrast.mapping.curves[3].points.new(.22,.13)
contrast.mapping.curves[3].points.new(.78,.88)
contrast.mapping.update()
output=finish.nodes.new('NodeGroupOutput')
for a,b in [(layers,glow),(glow,streaks),(streaks,mono),(mono,contrast),(contrast,output)]:
    finish.links.new(a.outputs['Image'],b.inputs['Image'])
scene.compositing_node_group=finish
scene.render.use_compositing=True
try:
    scene.view_settings.view_transform='AgX'
    scene.view_settings.look='AgX - Medium High Contrast'
except (TypeError,ValueError):
    pass  # Keep the installed color configuration when AgX is unavailable.
scene.view_settings.exposure=-.5

for frame,snapshot in poses.items():
    scene.frame_set(frame)
    scene.view_layers[0].update()
    assert all(scene.objects[name].matrix_world==matrix for name,matrix in snapshot.items()),f'Pose changed at {frame}'
assert scene.camera==camera
for blocks in (bpy.data.meshes,bpy.data.curves,bpy.data.node_groups,bpy.data.materials,bpy.data.images,bpy.data.cameras,bpy.data.lights):
    for block in list(blocks):
        if block.name.startswith(PREFIX) and block.users==0:
            blocks.remove(block)
scene.frame_set(1)
scene.view_layers[0].update()
report={'version':2,'siteScale':SCALE,'coreCenter':CENTER,'coreRadius':RADIUS,'coreHeight':height(104),
        'longBannerGlitchBorderRemoved':True,
        'screens':SCREENS,'previewCamera':PREVIEW_CAMERA,'antennaTips':[height(z) for z in [140,135,145,150]],
        'balconies':{'L1':[height(78),height(80)],'L2':[height(92),height(94)]},'stats':stats,
        'cameraAndExistingPosesPreserved':True}
scene['reference_tower_redesign']=json.dumps(report)
temporary=ROOT/'reference-tower-save.blend'
bpy.data.libraries.write(str(temporary),{scene},fake_user=False,compress=True)
shutil.copy2(MASTER,MASTER.with_suffix('.blend1'))
temporary.replace(MASTER)
(ROOT/'reference-tower.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
