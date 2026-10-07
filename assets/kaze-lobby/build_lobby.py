"""Standalone KAJU lobby. Run with Blender --background --factory-startup --python.

Only writes assets/kaze-lobby; never opens or modifies the city or live Blender.
All dimensions in meters. +Y points from the entrance toward the reception wall.
"""
import json
import math
from pathlib import Path
import random
import sys

import bpy
from mathutils import Euler, Matrix, Vector

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent/'branding'))
from kaju_brand import logo_paths, SPACED_BRAND
REAR_EXTENSION = 8.0
WIDTH = 20.0
random.seed(31)
scene = bpy.data.scenes.new('KAZE / Monochrome Atrium')
bpy.context.window.scene = scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'METERS'
collections = {}
for name in ['01 Architecture', '02 Twin staircases', '03 Reception',
             '04 Identity & campaigns', '05 Gardens', '06 Particle people',
             '07 Atmosphere', '08 Cameras & lights', '09 Integration anchors',
             '10 Lounge seating', '11 NPC accessories', '12 Reception carpet',
              '13 Upper elevator foyer', '16 Sculpted ceiling', '17 Holographic fish exhibit']:
    col = bpy.data.collections.new('Lobby • ' + name)
    scene.collection.children.link(col)
    collections[name[:2]] = col


def link(name, data, group):
    obj = bpy.data.objects.new('Lobby • ' + name, data)
    collections[group].objects.link(obj)
    return obj


def material(name, color, emission=0, metallic=0, roughness=.5):
    mat = bpy.data.materials.new('Lobby • ' + name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    p = mat.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Metallic'].default_value = metallic
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Emission Color'].default_value = (*color, 1)
    p.inputs['Emission Strength'].default_value = emission
    return mat


black = material('Obsidian architecture', (.002, .002, .002), roughness=.8)
floor_mat = material('Polished black stone', (.009, .009, .009), metallic=.72, roughness=.105)
desk_mat = material('Reception charcoal', (.012, .012, .012), metallic=.35, roughness=.23)
line_mat = material('Fine silver edges', (.34, .34, .34), emission=.65)
quiet_mat = material('Secondary gray edges', (.10, .10, .10), emission=.45)
white = material('White light channels', (.7, .7, .7), emission=2)
type_mat = material('Silver typography', (.50, .50, .50), emission=.7)
dot_mat = material('White surface particles', (.55, .55, .55), emission=1.1)
dust_mat = material('Sparse atmospheric dust', (.16, .16, .16), emission=.5)


def lines(name, paths, mat=line_mat, radius=.004, group='01'):
    curve = bpy.data.curves.new('Lobby • ' + name, 'CURVE')
    curve.dimensions = '3D'
    curve.resolution_u = 1
    curve.bevel_depth = radius
    curve.bevel_resolution = 0
    for path in paths:
        spline = curve.splines.new('POLY')
        spline.points.add(len(path)-1)
        for p, co in zip(spline.points, path):
            p.co = (*co, 1)
    obj = link(name, curve, group)
    obj.data.materials.append(mat)
    return obj


def box(name, center, size, mat=black, group='01', outline=True, edge_mat=line_mat):
    x, y, z = (v/2 for v in size)
    vertices = [(-x,-y,-z), (x,-y,-z), (x,y,-z), (-x,y,-z),
                (-x,-y,z), (x,-y,z), (x,y,z), (-x,y,z)]
    faces = [(0,3,2,1), (0,1,5,4), (1,2,6,5), (2,3,7,6), (3,0,4,7), (4,5,6,7)]
    mesh = bpy.data.meshes.new('Lobby • ' + name)
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(mat)
    obj = link(name, mesh, group)
    obj.location = center
    if outline:
        edges = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
        paths = [[tuple(Vector(vertices[a])+Vector(center)), tuple(Vector(vertices[b])+Vector(center))] for a,b in edges]
        lines(name + ' / feature edges', paths, edge_mat, group=group)
    return obj


def text(name, body, position, size=.22, group='04', mat=type_mat, spacing=1.15):
    data = bpy.data.curves.new('Lobby • ' + name, 'FONT')
    data.body = body
    data.align_x = 'CENTER'
    data.align_y = 'CENTER'
    data.size = size
    data.space_character = spacing
    data.space_line = 1.25
    obj = link(name, data, group)
    obj.location = position
    obj.rotation_euler = (math.pi/2, 0, 0)
    obj.data.materials.append(mat)
    return obj


def particles(name, vertices, radius, group, mat=dot_mat):
    mesh = bpy.data.meshes.new('Lobby • ' + name + ' / editable point positions')
    mesh.from_pydata(vertices, [], [])
    obj = link(name, mesh, group)
    tree = bpy.data.node_groups.new('Lobby • ' + name + ' / particle display', 'GeometryNodeTree')
    tree.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    tree.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    nodes, links = tree.nodes, tree.links
    inp = nodes.new('NodeGroupInput'); inp.location = (-500, 80)
    out = nodes.new('NodeGroupOutput'); out.location = (400, 80)
    points = nodes.new('GeometryNodeMeshToPoints'); points.mode = 'VERTICES'; points.location = (-300, 80)
    ico = nodes.new('GeometryNodeMeshIcoSphere'); ico.location = (-300, -140)
    ico.inputs['Radius'].default_value = radius
    ico.inputs['Subdivisions'].default_value = 1
    setmat = nodes.new('GeometryNodeSetMaterial'); setmat.location = (-80, -140)
    setmat.inputs['Material'].default_value = mat
    inst = nodes.new('GeometryNodeInstanceOnPoints'); inst.location = (160, 80)
    links.new(inp.outputs['Geometry'], points.inputs['Mesh'])
    links.new(ico.outputs['Mesh'], setmat.inputs['Geometry'])
    links.new(points.outputs['Points'], inst.inputs['Points'])
    links.new(setmat.outputs['Geometry'], inst.inputs['Instance'])
    links.new(inst.outputs['Instances'], out.inputs['Geometry'])
    mod = obj.modifiers.new('Editable point-cloud rendering', 'NODES'); mod.node_group = tree
    obj['particle_count'] = len(vertices)
    return obj


# A grand, double-height lobby with dark occluding walls and no exterior scenery.
box('Reflective atrium floor', (0, REAR_EXTENSION/2, -.10), (WIDTH, 24+REAR_EXTENSION, .2), floor_mat, outline=False)
for side in [-1, 1]:
    box('Side wall', (side*10.1, REAR_EXTENSION/2, 9), (.2, 24+REAR_EXTENSION, 18), outline=False)
    for y in [-8, -2, 4, 10, 18]:
        box('Full-height pilaster', (side*9.9, y, 9), (.20, .32, 18), edge_mat=quiet_mat)
    for z in [3.8, 6.2, 12, 17.9]:
        lines('Side wall horizontal reveal', [[(side*9.98,-12,z),(side*9.98,12+REAR_EXTENSION,z)]], quiet_mat, .003)
    for y in [-6, 0, 6]:
        lines('Angular wall inset', [[(side*9.96,y,6.4),(side*9.96,y,11.4),
                                     (side*9.96,y+2.3,14.2),(side*9.96,y+2.3,17.8)]], quiet_mat, .003)
    box('Mezzanine side gallery', (side*8.8, 3.5+REAR_EXTENSION/2, 5.98), (2.4, 16+REAR_EXTENSION, .24))
    paths = [[(side*7.6,-4.5,6.15),(side*7.6,11.5+REAR_EXTENSION,6.15)],
             [(side*7.6,-4.5,7.1),(side*7.6,11.5+REAR_EXTENSION,7.1)]]
    for y in [-4.5, -2, .5, 3, 5.5, 8, 10.5, 13, 15.5, 18, 19.5]:
        paths.append([(side*7.6,y,6.15),(side*7.6,y,7.1)])
    lines('Gallery balustrade', paths, line_mat, .004)
    # Fine rectangular panel rhythm on the lower wall.
    for y in [-8, -4, 0, 4, 8, 12, 16]:
        lines('Ground-floor wall panel', [[(side*9.97,y, .25),(side*9.97,y,3.1),
                                          (side*9.97,y+2.8,3.1),(side*9.97,y+2.8,.25)]], quiet_mat, .003)
box('Rear atrium wall', (0,12.1+REAR_EXTENSION,9), (WIDTH,.2,18), outline=False)
box('Dark overhead canopy', (0,REAR_EXTENSION/2,18.1), (WIDTH,24+REAR_EXTENSION,.2), outline=False)
def build_sculpted_ceiling():
    """A continuous branching soffit with five asymmetric, recessed openings.

    The reference is a tree-like roof, not a set of framed oval panels. Its
    defining features are a left opening, a narrow central slit, a larger
    diagonal right opening, and smaller openings behind the pillar. Rounded
    returns connect each cutout to the elevated, double-line silver lattice.
    """
    rim_light = material('Ceiling / luminous rim',(.80,.80,.80),emission=4.2)
    lattice = material('Ceiling / silver lattice',(.43,.43,.43),emission=1.8)
    secondary = material('Ceiling / recessed edge',(.25,.25,.25),emission=1.1)
    openings = [
        ('Left sweep', [(-9.0,-14),(-3.8,-14),(-3.7,-7),(-4.7,-1),
                        (-5.8,2.5),(-7.1,4.0),(-7.9,1.8),(-8.2,-2.0)]),
        ('Central slit', [(-1.8,-14),(3.6,-14),(1.4,-7),(-2.1,-1),
                          (-4.8,2.0),(-5.05,1.4),(-4.0,-1),(-2.8,-7)]),
        ('Right sweep', [(4.8,-14),(9.7,-14),(9.65,-5),(9.4,1.8),
                         (7.3,4.7),(3.4,6.0),(-1.1,6.0),(-1.9,4.6),
                         (-.3,1.6),(2.4,-5.0)]),
        ('Rear fan', [(-6.5,11.5),(-2.2,10.2),(.9,11.3),(4.5,14.0),
                      (6.2,18.7),(4.2,22.0),(-8.2,22.0),(-8.0,16.1)]),
        ('Right rear fork', [(2.5,8.7),(5.7,7.2),(8.9,3.7),(9.7,6.0),
                             (9.6,20.0),(7.4,17.8),(5.2,12.2)]),
    ]

    def smooth_loop(anchors):
        """Sample an interpolated cubic contour, retaining authored asymmetry."""
        anchors = [Vector((x,y)) for x,y in anchors]
        result = []
        for i in range(len(anchors)):
            p0,p1,p2,p3 = [anchors[j%len(anchors)] for j in [i-1,i,i+1,i+2]]
            for sample in range(20):
                t = sample/20
                result.append(.5*((2*p1)+(-p0+p2)*t+
                                  (2*p0-5*p1+4*p2-p3)*t*t+
                                  (-p0+3*p1-3*p2+p3)*t*t*t))
        area = sum(a.x*b.y-b.x*a.y for a,b in zip(result,result[1:]+result[:1]))
        return result if area>0 else result[::-1]

    def inset_loop(loop,distance):
        result = []
        for i,p in enumerate(loop):
            tangent = (loop[(i+1)%len(loop)]-loop[i-1]).normalized()
            result.append(p+Vector((-tangent.y,tangent.x))*distance)
        return result

    # The broad black branch junctions are actual occluding architecture. The
    # sampled polygon cutters are authoring-only and never enter the package.
    canopy = box('Ceiling / continuous branching soffit',(0,3.325,16.66),
                 (20,30.65,.08),black,'16',outline=False)
    canopy['role'] = 'Continuous asymmetric roof branches with recessed grid openings'
    contours = []
    for label,anchors in openings:
        loop = smooth_loop(anchors)
        contours.append((label,loop))
        n = len(loop)
        vertices = [(p.x,p.y,z) for z in [16.0,18.3] for p in loop]
        faces = [tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
        faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        mesh = bpy.data.meshes.new('Lobby • Ceiling / temporary opening cutter')
        mesh.from_pydata(vertices,[],faces); mesh.update()
        cutter = link('Ceiling / temporary opening cutter',mesh,'16')
        mod = canopy.modifiers.new('Ceiling / '+label+' aperture','BOOLEAN')
        mod.operation = 'DIFFERENCE'; mod.solver = 'EXACT'; mod.object = cutter
        bpy.context.view_layer.objects.active = canopy
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(cutter,do_unlink=True)
        bpy.data.meshes.remove(mesh)

    for label,loop in contours:
        name = 'Ceiling / '+label
        # A rounded, upward recessed reveal, rather than a raised tubular rim.
        # Keep the narrow slit readable by using a shallower inset there.
        inset = .19 if label=='Central slit' else .46
        profiles = [(0,16.60),(.16,16.82),(.42,17.16),(.78,17.52),(1,17.73)]
        rings = [[(p.x,p.y,z) for p in inset_loop(loop,inset*fraction)]
                 for fraction,z in profiles]
        n = len(loop)
        vertices = [p for ring in rings for p in ring]
        faces = [(layer*n+i,layer*n+(i+1)%n,
                  (layer+1)*n+(i+1)%n,(layer+1)*n+i)
                 for layer in range(len(rings)-1) for i in range(n)]
        mesh = bpy.data.meshes.new('Lobby • '+name+' / sculpted return')
        mesh.from_pydata(vertices,[],faces); mesh.materials.append(black)
        for face in mesh.polygons:
            face.use_smooth = True
        link(name+' / sculpted return',mesh,'16')
        for index,mat,radius in [(0,rim_light,.010),(2,secondary,.003),(4,line_mat,.004)]:
            path = rings[index]+rings[index][:1]
            lines(name+' / '+['luminous lip','recessed contour','upper contour'][index//2],
                  [path],mat,radius,'16')

        boundary = inset_loop(loop,inset)
        # Clip a single architectural grid to the irregular openings. Slightly
        # raised paired members reproduce the fine structural depth in the image.
        angle = math.radians(-18)
        ca,sa = math.cos(angle),math.sin(angle)
        planar = [Vector((ca*p.x+sa*p.y,-sa*p.x+ca*p.y)) for p in boundary]
        grid,back_grid = [],[]
        for axis in [0,1]:
            other = 1-axis
            minimum = min(p[axis] for p in planar)
            maximum = max(p[axis] for p in planar)
            spacing = 1.15
            for index in range(math.ceil(minimum/spacing),math.floor(maximum/spacing)+1):
                fixed = index*spacing
                crossings = []
                for a,b in zip(planar,planar[1:]+planar[:1]):
                    if (a[axis]<=fixed<b[axis]) or (b[axis]<=fixed<a[axis]):
                        t = (fixed-a[axis])/(b[axis]-a[axis])
                        crossings.append(a[other]+t*(b[other]-a[other]))
                crossings.sort()
                for lower,upper in zip(crossings[::2],crossings[1::2]):
                    if upper-lower<.025:
                        continue
                    path,back = [],[]
                    for step in range(25):
                        varying = lower+(upper-lower)*step/24
                        u,v = (fixed,varying) if axis==0 else (varying,fixed)
                        x,y = ca*u-sa*v,sa*u+ca*v
                        z = 17.75+.12*math.sin(math.pi*step/24)
                        path.append((x,y,z))
                        back.append((x+.025,y+.025,z+.065))
                    grid.append(path); back_grid.append(back)
        lines(name+' / silver structural grid',grid,lattice,.0045,'16')
        lines(name+' / grid depth lines',back_grid,secondary,.002,'16')

    # One closed collar replaces four independent shoulder strips. Its two
    # visible fillets start exactly at the pillar's top/front corners and end
    # on sampled roof-lip vertices, with vertical and roof-tangent continuity.
    # The rear of the collar has no separate luminous edges to protrude through
    # the pillar or look like short floating horizontal tabs from the entrance.
    roof_loop = next(loop for label,loop in contours if label=='Right sweep')
    front_paths = []
    junctions = []
    junction_steps = 128
    for side,target in [(-1,Vector((-1.9,4.6))),(1,Vector((3.4,6.0)))]:
        index = min(range(len(roof_loop)),key=lambda i:(roof_loop[i]-target).length_squared)
        point = roof_loop[index]
        start = Vector((side*1.75,5.8,16.0))
        end = Vector((point.x,point.y,16.60))
        tangent2 = (roof_loop[(index+1)%len(roof_loop)]-roof_loop[index-1]).normalized()
        tangent = Vector((tangent2.x,tangent2.y,0))
        if tangent.dot(end-start)<0:
            tangent = -tangent
        control1 = start+Vector((0,0,.42))
        control2 = end-tangent*.45
        path = []
        for i in range(junction_steps+1):
            t = i/junction_steps
            p = ((1-t)**3*start+3*(1-t)**2*t*control1+
                 3*(1-t)*t*t*control2+t**3*end)
            path.append(tuple(p))
        front_paths.append(path)
        junctions.append({'side':side,'pillar_corner':list(start),'roof_lip':list(end)})
    vertices = []
    for left,right in zip(*front_paths):
        vertices.extend([left,right,(right[0],8.0,right[2]),(left[0],8.0,left[2])])
    faces = [(3,2,1,0)]
    for row in range(junction_steps):
        for edge in range(4):
            a,b = row*4+edge,row*4+(edge+1)%4
            faces.append((a,b,b+4,a+4))
    last_row = junction_steps*4
    faces.append(tuple(range(last_row,last_row+4)))
    mesh = bpy.data.meshes.new('Lobby • Ceiling / integrated pillar collar')
    mesh.from_pydata(vertices,[],faces); mesh.materials.append(black)
    for face in mesh.polygons:
        face.use_smooth = True
    collar = link('Ceiling / integrated pillar collar',mesh,'16')
    collar['role'] = 'Closed tangent-continuous pillar-to-roof junction'
    lines('Ceiling / continuous pillar fillets',front_paths,line_mat,.004,'16')
    scene['Ceiling design'] = 'Asymmetric branching black soffit: left sweep, narrow slit, diagonal right sweep, rear forks; luminous recessed reveals and silver grid'
    return {'openings':[label for label,_ in openings],
            'continuous_soffit':True,'collection':collections['16'].name,
            'height_range_m':[16.0,17.87],'grid_spacing_m':1.15,
            'pillar_junctions':junctions,
            'flared_left_support':False,'trailing_vines':0}


ceiling_manifest = build_sculpted_ceiling()
for x in [-9,-6,-3,0,3,6,9]:
    lines('Floor longitudinal joint', [[(x,-12,.012),(x,12+REAR_EXTENSION,.012)]], quiet_mat, .002)
for y in range(-11,12+int(REAR_EXTENSION),2):
    lines('Floor transverse joint', [[(-10,y,.012),(10,y,.012)]], quiet_mat, .002)
for side in [-1,1]:
    lines('Floor approach light', [[(side*3.05,-10,.016),(side*3.05,3.9,.016)]], line_mat, .004)

# The existing landing and gallery remain connected to the escalator exits.
for side in [-1,1]:
    x = side*6.85
    box('Top stair landing', (x,11.4,5.98), (1.8,1.1,.24), group='02')
box('Rear mezzanine bridge', (0,11.5,5.98), (15.2,1,.24), group='02')
lines('Rear gallery railing', [[(-7.6,11,7.1),(7.6,11,7.1)],
                              [(-7.6,11,6.15),(7.6,11,6.15)]], line_mat, .004, '02')
for obj in collections['02'].objects:
    obj.location.y += REAR_EXTENSION


def build_escalators():
    """Simple recognizable escalator forms: steps, skirts, capsule handrails."""
    profile = [(8.45,.025),(9.3,.025),(18.65,5.55),(19.5,5.55),
               (19.5,6.98),(18.65,7.04),(9.3,1.02),(8.45,1.02)]
    for side in [-1,1]:
        x = side*6.85
        label = 'L' if side<0 else 'R'
        root = link('Escalator '+label+' / assembly',None,'02')
        root['type'] = 'Simple escalator; static presentation model'
        root['direction'] = 'down toward entrance' if side<0 else 'up toward mezzanine'
        nosings = []
        for i in range(34):
            y = 9.3+(i+.5)*.275
            top = (i+1)*.18
            step = box('Escalator '+label+' / step %02d' % (i+1),
                       (x,y,top-.09),(1.2,.275,.18),desk_mat,'02',outline=False)
            step.parent = root
            nosings.append([(x-.60,y-.1375,top+.003),(x+.60,y-.1375,top+.003)])
        lines('Escalator '+label+' / step edges',nosings,line_mat,.003,'02').parent = root
        box('Escalator '+label+' / entry plate',(x,8.875,.02),(1.25,.85,.04),desk_mat,'02').parent = root
        box('Escalator '+label+' / exit plate',(x,19.075,6.10),(1.25,.85,.04),desk_mat,'02').parent = root
        for offset in [-.74,.74]:
            xx = x+offset
            verts = [(xx+dx,y,z) for dx in [-.045,.045] for y,z in profile]
            n = len(profile)
            faces = [tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
            faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
            mesh = bpy.data.meshes.new('Lobby • Escalator side skirt')
            mesh.from_pydata(verts,[],faces); mesh.materials.append(black)
            panel = link('Escalator '+label+' / enclosed side panel',mesh,'02'); panel.parent = root
            paths = [[(xx-.045,y,z) for y,z in profile]+[(xx-.045,*profile[0])],
                     [(xx+.045,y,z) for y,z in profile]+[(xx+.045,*profile[0])]]
            lines('Escalator '+label+' / skirt edges',paths,line_mat,.004,'02').parent = root
            # Closed rounded belt silhouette; no mechanical rollers or grooves.
            lower = Vector((9.0,.80)); upper = Vector((18.9,6.92))
            axis = (upper-lower).normalized(); normal = Vector((-axis.y,axis.x))
            path = []
            for center,angles in [(upper,[math.pi/2-j*math.pi/12 for j in range(13)]),
                                  (lower,[-math.pi/2-j*math.pi/12 for j in range(13)])]:
                for a in angles:
                    yz = center+.29*(math.cos(a)*axis+math.sin(a)*normal)
                    path.append((xx,yz.x,yz.y))
            path.append(path[0])
            rail = lines('Escalator '+label+' / rounded handrail',[path],line_mat,.018,'02')
            rail.data.bevel_resolution = 2; rail.parent = root
    return [o for o in collections['02'].objects if o.name.endswith('/ assembly')]


build_escalators()

# Reception island and fine illuminated shadow-gap plinth.
box('Reception island', (0,3.7,.77), (5,1.6,1.44), desk_mat, '03')
box('Reception floating countertop', (0,3.7,1.52), (5.2,1.8,.08), desk_mat, '03')
lines('Reception luminous plinth', [[(-2.5,2.89,.12),(2.5,2.89,.12),(2.5,4.5,.12),
                                    (-2.5,4.5,.12),(-2.5,2.89,.12)]], white, .012, '03')
text('Reception motto', 'A CLEANER BRIGHTER\nHUMAN FUTURE.', (0,2.885,.89), .145, '03')
for x in [-1.7,1.7]:
    box('Reception terminal', (x,3.75,1.78), (.48,.075,.32), desk_mat, '03')
    lines('Terminal stand', [[(x,3.78,1.53),(x,3.78,1.65)]], line_mat, .009, '03')


def build_reception_carpet():
    """A continuous matte charcoal runner from the entrance to reception."""
    mat = material('Woven charcoal carpet',(.038,.038,.038),roughness=.98)
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    p = nodes.get('Principled BSDF')
    noise = nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 260
    noise.inputs['Detail'].default_value = 2
    coord = nodes.new('ShaderNodeTexCoord')
    links.new(coord.outputs['Object'],noise.inputs['Vector'])
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (.024,.024,.024,1)
    ramp.color_ramp.elements[1].color = (.050,.050,.050,1)
    links.new(noise.outputs['Fac'],ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'],p.inputs['Base Color'])
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = .22
    bump.inputs['Distance'].default_value = .0015
    links.new(noise.outputs['Fac'],bump.inputs['Height'])
    links.new(bump.outputs['Normal'],p.inputs['Normal'])
    carpet = box('Reception woven carpet',(0,-3.625,.023),(4.0,16.75,.022),mat,'12',outline=False)
    carpet['purpose'] = 'Continuous entrance-to-reception carpet runner'
    seam = material('Carpet stitched border',(.09,.09,.09),emission=.2,roughness=1)
    lines('Carpet inset stitched border',[[(-1.88,-11.88,.035),(1.88,-11.88,.035),
                                          (1.88,4.63,.035),(-1.88,4.63,.035),
                                          (-1.88,-11.88,.035)]],seam,.003,'12')
    return carpet


build_reception_carpet()

def build_identity_pillar():
    """A freestanding column capped beneath the branching roof shoulders."""
    pillar = box('KAZE identity pillar', (0,6.9,8), (3.5,2.2,16), edge_mat=line_mat)
    pillar['role'] = 'Central structural pillar supporting the branching ceiling'
    pillar['reception_clearance_m'] = 1.2
    # Hairline inset borders and side reveals articulate the column's thickness.
    for x in [-1.63,1.63]:
        lines('Pillar front reveal', [[(x,5.785,.1),(x,5.785,15.9)]],line_mat,.005)
    for x in [-1.756,1.756]:
        lines('Pillar side reveal', [[(x,6.0,.1),(x,6.0,15.9)],
                                     [(x,7.75,.1),(x,7.75,15.9)]],quiet_mat,.004)
    y = 5.78
    z = -2.3
    lines('KAZE angular crest', [[(px*.72,y,14.30+z+py*.72) for px,py in path]
                                for path in logo_paths()],line_mat,.009,'04')
    text('KAZE wordmark',SPACED_BRAND,(0,y,12.85+z),.58)
    text('Industries subline','I N D U S T R I E S',(0,y,12.30+z),.15)
    text('Japanese-inspired subline','H U M A N   /   F U T U R E',(0,y,11.83+z),.10)
    text('Values','PEOPLE\nCULTURE\nTECH\nTOMORROW',(0,y,9.65+z),.24)
    text('Numbered manifesto','01   A CLEANER\n02   BRIGHTER\n03   HUMAN\n04   FUTURE',(0,y,7.72+z),.18)
    return pillar


build_identity_pillar()
for side in [-1,1]:
    x = side*6.4
    # Suspended architectural banners with nearly invisible black backing.
    box('Suspended campaign banner', (x,6.9,12.2), (2.1,.07,6.7), group='04', edge_mat=quiet_mat)
    lines('Banner suspension', [[(x-.9,6.9,15.55),(x-.9,6.9,18)],
                                [(x+.9,6.9,15.55),(x+.9,6.9,18)]], quiet_mat, .003, '04')
    body = 'REAL\nHUMAN\nMORE' if side<0 else 'A\nCLEANER\nBRIGHTER\nHUMAN\nFUTURE'
    text('Campaign heading', body, (x,6.85,11.4), .255)
    text('Campaign footer', '2 7 . H U M A N', (x,6.85,9.8), .10)
    lines('Campaign underline', [[(x-.62,6.84,9.32),(x+.62,6.84,9.32)]], line_mat, .003, '04')
    text('Lower gallery manifesto', 'STRIVING\nFOR A\nBETTER\nTOMORROW' if side<0 else
         'HUMAN\n×\nTECH\n=\nA BRIGHTER\nWORLD', (side*8.7,5.7,4.35), .19)


def tree(name, origin, height=3):
    base = Vector(origin)
    paths, dots = [], []
    trunk = [base, base+Vector((.04,0,height*.45)), base+Vector((-.04,.02,height*.78))]
    paths.append([tuple(p) for p in trunk])
    for i in range(22):
        angle = random.uniform(0, math.tau)
        start = base+Vector((0,0,random.uniform(.4,.72)*height))
        end = base+Vector((math.cos(angle)*random.uniform(.45,.9),
                           math.sin(angle)*random.uniform(.4,.8),random.uniform(.72,1)*height))
        mid = start.lerp(end,.62)
        paths.append([tuple(start),tuple(mid),tuple(end)])
        for _ in range(48):
            v = end+Vector((random.gauss(0,.23),random.gauss(0,.22),random.gauss(0,.24)))
            dots.append(tuple(v))
    lines(name+' / branches', paths, quiet_mat, .003, '05')
    particles(name+' / foliage', dots, .008, '05')
    box(name+' / planter', (origin[0],origin[1],origin[2]-.32), (1.1,1.1,.64), desk_mat, '05')


for side in [-1,1]:
    for y,h in [(-5,3.1),(-.7,3.4),(6,2.8)]:
        tree('Ground garden', (side*9.1,y,.64), h)
    for y in [-2.5,5.2,10]:
        tree('Mezzanine garden', (side*9.0,y,6.65), 2.6)


def person(name, origin, scale=1, angle=0, count=1, pose='standing', phase=1, stride=.40):
    """Articulated surface particles; local forward is -Y, pose in meters."""
    dots = []
    walk_stride = stride
    forms = []

    def ellipsoid(center, size, n, rotation=None):
        forms.append((Vector(center), size, n, rotation))

    def limb(a, b, radius, n):
        a, b = Vector(a), Vector(b)
        axis = b-a
        ellipsoid((a+b)/2, (radius, radius*.9, axis.length*.56), n,
                  axis.to_track_quat('Z','Y'))

    seated = pose.startswith('seated_') or pose == 'sitting'
    hip_z = .64 if seated else 1.04
    lean = {'leaning':.27,'seated_reading':.16,'seated_phone':.10,
            'seated_relaxed':-.08,'phone':.09,'climbing':.12}.get(pose,.04 if seated else 0)
    hip = Vector((0,0,hip_z))
    chest = Vector((0,-lean,hip_z+.39))
    head = Vector((0,-lean*1.3,hip_z+.73))
    ellipsoid(hip, (.16,.11,.15), 190)
    torso_axis = chest-hip
    ellipsoid((hip+chest)/2+Vector((0,0,.07)), (.22,.12,.27), 480,
              torso_axis.to_track_quat('Z','Y'))
    limb(chest+Vector((0,0,.13)),head-Vector((0,0,.12)),.055,65)
    head_tilt = .42 if pose in ['phone','seated_phone','seated_reading','checking_terminal'] else .06
    head_rotation = Euler((head_tilt,0,.06*phase)).to_quaternion()
    ellipsoid(head, (.115,.11,.155), 220,head_rotation)
    # A subtle nose indicates the facing direction in the monochrome silhouette.
    ellipsoid(head+head_rotation @ Vector((0,-.105,-.015)), (.033,.045,.045), 35)
    hands = {}
    for side in [-1,1]:
        pelvis = hip+Vector((side*.12,0,-.035))
        shoulder = chest+Vector((side*.23,0,.075))
        if seated:
            knee = Vector((side*.15,-.43,.51))
            ankle = Vector((side*.15,-.48,.09))
            elbow = Vector((side*.30,-.14,hip_z+.20))
            hand = Vector((side*.17,-.35,.72))
            if pose == 'seated_reading':
                elbow = Vector((side*.29,-.18,.91))
                hand = Vector((side*.14,-.42,.88))
            elif pose == 'seated_phone':
                elbow = Vector((side*.24,-.12,.88))
                hand = Vector((side*.065,-.31,1.08))
            elif pose == 'seated_drinking' and side == 1:
                elbow = Vector((.32,-.13,.99))
                hand = Vector((.13,-.23,1.24))
            elif pose == 'seated_relaxed':
                knee = Vector((side*.22,-.36,.51))
                ankle = Vector((side*.27,-.71,.09))
                elbow = Vector((side*.35,.07,.81))
                hand = Vector((side*.42,.15,.82))
        elif pose in ['walking','carrying_bag']:
            stride = side*phase
            knee = Vector((side*.12,stride*.20,.55))
            ankle = Vector((side*.12,stride*walk_stride,.10 if stride>0 else .075))
            elbow = Vector((side*.29,-stride*.17,1.17))
            hand = Vector((side*.28,-stride*.27,.93))
            if pose == 'carrying_bag' and side == 1:
                elbow = Vector((.29,.015,1.13))
                hand = Vector((.32,.01,.79))
        elif pose == 'leaning':
            knee = Vector((side*.13,.025,.56))
            ankle = Vector((side*.15,.10,.075))
            elbow = Vector((side*.30,-.48,.98))
            hand = Vector((side*.16,-.61,.98))
            if side == 1:
                elbow = Vector((.31,-.14,1.12))
                hand = Vector((.18,-.10,1.03))
        elif pose == 'talking':
            knee = Vector((side*.14,0,.55))
            ankle = Vector((side*.15,side*.05,.075))
            elbow = Vector((side*.34,-.10,1.19))
            hand = Vector((side*.40,-.37,1.37 if side==phase else 1.05))
        else:
            knee = Vector((side*.12,0,.55))
            ankle = Vector((side*.12,0,.075))
            elbow = Vector((side*.29,0,1.12))
            hand = Vector((side*.30,-.025,.78))
            if pose in ['phone','checking_terminal']:
                elbow = Vector((side*.27,-.07,1.18))
                hand = Vector((side*.07,-.32,1.36))
                if pose == 'checking_terminal':
                    elbow.z = 1.48
                    hand.z = 1.67
            elif pose == 'listening':
                elbow = Vector((side*.29,.03,1.17))
                hand = Vector((side*.15,-.11,1.12))
            elif pose == 'observing':
                elbow = Vector((side*.26,.15,1.17))
                hand = Vector((side*.06,.21,.96))
                ankle.x = side*.18
            elif pose == 'pointing' and side == 1:
                elbow = Vector((.48,-.24,1.55))
                hand = Vector((.68,-.52,1.66))
            elif pose == 'greeting' and side == 1:
                elbow = Vector((.38,-.06,1.65))
                hand = Vector((.40,-.09,1.99))
            elif pose == 'climbing':
                knee = Vector((side*.12,-.18 if side<0 else .12,.65 if side<0 else .55))
                ankle = Vector((side*.12,-.22 if side<0 else .05,.24 if side<0 else .075))
                elbow = Vector((side*.27,side*.10,1.18))
                hand = Vector((side*.29,side*.20,.97))
            elif pose == 'riding_escalator' and side == 1:
                elbow = Vector((.43,-.08,1.24))
                hand = Vector((.68,-.14,1.10))
        hands[side] = hand
        limb(pelvis,knee,.076,230)
        limb(knee,ankle,.057,200)
        ellipsoid(ankle+Vector((0,-.07,-.025)), (.072,.145,.047),80)
        limb(shoulder,elbow,.057,185)
        limb(elbow,hand,.043,140)
        ellipsoid(hand, (.042,.044,.065),65)
    for center, size, n, rotation in forms:
        for _ in range(int(n*count)):
            u = random.uniform(-1,1); phi = random.uniform(0,math.tau)
            r = math.sqrt(1-u*u)
            v = Vector((size[0]*r*math.cos(phi),size[1]*r*math.sin(phi),size[2]*u))
            if rotation:
                v = rotation @ v
            x,y,z = (center+v)*scale
            dots.append((origin[0]+x*math.cos(angle)-y*math.sin(angle),
                         origin[1]+x*math.sin(angle)+y*math.cos(angle),origin[2]+z))
    obj = particles(name, dots, .005, '06')
    obj['pose'] = pose
    obj['facing_angle_rad'] = angle
    obj['pose_origin'] = origin
    obj['stride_m'] = walk_stride
    obj['gait_phase'] = phase
    if seated:
        obj['facing_direction'] = 'east (+X)' if origin[0]<0 else 'west (-X)'
    # Small solid props explain the activity without adding dense particle noise.
    props_before = set(scene.objects)
    if pose in ['phone','seated_phone']:
        palm = (hands[-1]+hands[1])/2
        box(name+' / phone',tuple(palm+Vector((0,-.025,.04))),(.082,.018,.145),desk_mat,'11')
    elif pose == 'seated_reading':
        box(name+' / open book left',(-.075,-.43,.90),(.145,.20,.023),desk_mat,'11')
        box(name+' / open book right',(.075,-.43,.90),(.145,.20,.023),desk_mat,'11')
    elif pose == 'seated_drinking':
        center = hands[1]+Vector((0,-.02,.035))
        paths = []
        for z in [-.055,.055]:
            paths.append([tuple(center+Vector((.04*math.cos(i*math.tau/16),
                                               .04*math.sin(i*math.tau/16),z))) for i in range(17)])
        for x in [-.04,.04]:
            paths.append([tuple(center+Vector((x,0,-.055))),tuple(center+Vector((x,0,.055)))])
        lines(name+' / cup',paths,line_mat,.004,'11')
    elif pose == 'carrying_bag':
        palm = hands[1]
        box(name+' / briefcase',tuple(palm+Vector((0,0,-.22))),(.12,.38,.30),desk_mat,'11')
        lines(name+' / bag handle',[[tuple(palm+Vector((0,-.065,-.07))),
                                    tuple(palm+Vector((0,-.065,.015))),
                                    tuple(palm+Vector((0,.065,.015))),
                                    tuple(palm+Vector((0,.065,-.07)))]],line_mat,.004,'11')
    transform = Matrix.Translation(Vector(origin)) @ Matrix.Rotation(angle,4,'Z') @ Matrix.Scale(scale,4)
    for prop in set(scene.objects)-props_before:
        prop.matrix_world = transform @ prop.matrix_world
        prop['npc_owner'] = obj.name
    return obj


def build_lounge_furniture():
    """Inward-facing outlined lounges without chunky solid sofa bases."""
    for side in [-1,1]:
        x = side*6.7
        lounge_before = set(scene.objects)
        box('Lounge sofa backrest', (x,.25,.87), (2.9,.15,.85), desk_mat,'10')
        for dx in [-1.38,1.38]:
            box('Lounge sofa armrest',(x+dx,-.2,.65),(.14,.95,.4),desk_mat,'10')
        for dx in [-.75,.75]:
            box('Lounge seat cushion',(x+dx,-.22,.48),(1.25,.77,.12),desk_mat,'10')
        # A fine support frame replaces the removed opaque plinth.
        paths = []
        for dx in [-1.28,1.28]:
            for dy in [-.55,.15]:
                paths.append([(x+dx,dy,.02),(x+dx,dy,.42)])
        lines('Lounge fine seat supports',paths,line_mat,.004,'10')
        box('Lounge low coffee table',(x,-1.75,.35),(1.8,.65,.09),desk_mat,'10')
        for dx in [-.6,.6]:
            box('Coffee table leg',(x+dx,-1.75,.16),(.055,.45,.32),desk_mat,'10')
        pivot = Vector((x,-.2,0))
        facing = -side*math.pi/2
        transform = (Matrix.Translation(pivot) @ Matrix.Rotation(facing,4,'Z')
                     @ Matrix.Translation(-pivot))
        # Flush new objects' locations before reading their world matrices.
        bpy.context.view_layer.update()
        for obj in set(scene.objects) - lounge_before:
            obj.matrix_world = transform @ obj.matrix_world
        bpy.context.view_layer.update()


build_lounge_furniture()


def populate_people():
    """Asymmetric activity vignettes, avoiding mirrored crowds and identical poses."""
    random.seed(81)
    for name,origin,pose,angle in [
        ('Lounge / reading a book',(-6.67,-.95,0),'seated_reading',math.pi/2),
        ('Lounge / resting with legs stretched',(-6.67,.55,0),'seated_relaxed',math.pi/2),
        ('Lounge / checking a phone',(6.67,.55,0),'seated_phone',-math.pi/2),
        ('Lounge / sipping coffee',(6.67,-.95,0),'seated_drinking',-math.pi/2),
        ('Conversation / explaining',(-4.75,3.0,0),'talking',1.35),
        ('Conversation / listening',(-3.55,3.2,0),'listening',-1.80),
        ('Reception / working at terminal',(-1.70,4.2,0),'checking_terminal',0),
        ('Reception / greeting arriving guest',(.75,4.9,0),'greeting',-.18),
        ('Visitor / checking messages',(4.6,4.3,0),'phone',-.45),
        ('Gallery / resting one arm on rail',(-8.21,1.0,6.12),'leaning',math.pi/2),
        ('Gallery / looking across the atrium',(8.15,2.4,6.12),'observing',-math.pi/2),
        ('Gallery / pointing out the view',(-8.20,8.2,6.12),'pointing',1.8),
        ('Gallery / reading messages',(8.6,10.2,6.12),'phone',-.65),
    ]:
        person(name,origin,angle=angle,pose=pose)
    person('Visitor / walking toward entrance',(-.9,-6.6,0),1.04,
           angle=.16,pose='walking',phase=-1,stride=.36,count=1.1)
    person('Visitor / carrying a briefcase',(2.8,-1.6,0),.98,
           angle=-.23,pose='carrying_bag',phase=1,stride=.25)
    person('Visitor / heading deeper into lobby',(-2.8,7.0,0),1.02,
           angle=2.85,pose='walking',phase=1,stride=.30)
    person('Gallery / slow stroll',(8.5,16.1,6.12),.96,
           angle=math.pi,pose='walking',phase=-1,stride=.20,count=.8)


populate_people()
particles('Atrium floating dust', [(random.uniform(-9.8,9.8),random.uniform(-10,20),
                                   random.uniform(.1,18)) for _ in range(2200)], .004, '07', dust_mat)


def camera(name, position, target, lens):
    data = bpy.data.cameras.new('Lobby • '+name)
    obj = link(name, data, '08')
    obj.location = position
    obj.rotation_euler = (Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
    data.lens = lens
    data.clip_start = .05; data.clip_end = 100
    return obj


def build_upper_elevator_foyer():
    """Upper-floor arrival behind the escalators, two closed lifts per side."""
    # Extend the rear shell rather than placing elevator doors through the wall.
    for name in ['Reflective atrium floor','Dark overhead canopy','Side wall','Side wall.001']:
        obj = scene.objects['Lobby • '+name]
        obj.location.y = 6.25
        obj.dimensions.y = 36.5
    scene.objects['Lobby • Rear atrium wall'].location.y = 24.6
    # Clear the escalator exits through the previous full-width gallery rail.
    rail = scene.objects['Lobby • Rear gallery railing']
    for spline in rail.data.splines:
        spline.points[0].co.x = -5.95
        spline.points[-1].co.x = 5.95
    deck = box('Upper foyer walking deck',(0,21.75,6.02),(20,5.5,.20),floor_mat,'13',outline=False)
    deck['walking_surface_m'] = 6.12
    lines('Upper foyer front deck edge',[[(-10,19,6.12),(10,19,6.12)]],quiet_mat,.003,'13')
    box('Upper foyer ceiling',(0,21.75,10.88),(20,5.5,.12),black,'13',edge_mat=quiet_mat)
    for x in [-8.7,-2.0,2.0,8.7]:
        lines('Upper foyer ceiling light', [[(x,19.8,10.80),(x,23.8,10.80)]],white,.012,'13')
    for x in [-8,-4,0,4,8]:
        lines('Upper foyer floor joint',[[(x,19,6.125),(x,24.4,6.125)]],quiet_mat,.002,'13')
    for y in [20.5,22,23.5]:
        lines('Upper foyer transverse joint',[[(-9.9,y,6.125),(9.9,y,6.125)]],quiet_mat,.002,'13')
    for side in [-1,1]:
        lines('Upper foyer side wall reveals',[[(side*9.98,20,7.1),(side*9.98,24.4,7.1)],
                                               [(side*9.98,20,10.8),(side*9.98,24.4,10.8)]],quiet_mat,.003,'13')
        for index,x_abs in enumerate([4.05,7.5],1):
            x = side*x_abs
            label = ('L' if side<0 else 'R')+str(index)
            before = set(collections['13'].objects)
            root = link('Elevator '+label+' / assembly',None,'13')
            root['type'] = 'Upper-floor elevator entrance'
            root['side'] = 'left' if side<0 else 'right'
            root['door_state'] = 'closed; static model'
            box('Elevator '+label+' / wall surround',(x,24.20,8.32),(2.85,.40,4.40),black,'13')
            # Two independent door leaves remain editable for later animation.
            for leaf_side in [-1,1]:
                box('Elevator '+label+' / '+('left' if leaf_side<0 else 'right')+' door leaf',
                    (x+leaf_side*.515,23.965,7.66),(1.02,.065,3.08),desk_mat,'13',edge_mat=quiet_mat)
            lines('Elevator '+label+' / portal', [[(x-1.08,23.90,6.14),(x-1.08,23.90,9.25),
                                                 (x+1.08,23.90,9.25),(x+1.08,23.90,6.14)]],line_mat,.010,'13')
            lines('Elevator '+label+' / center door seam',[[(x,23.925,6.15),(x,23.925,9.18)]],line_mat,.004,'13')
            box('Elevator '+label+' / threshold',(x,23.75,6.13),(2.20,.46,.025),desk_mat,'13')
            text('Elevator '+label+' / number',label,(x,23.945,9.66),.22,'13')
            text('Elevator '+label+' / floor display','06  ↑',(x,23.91,9.40),.13,'13')
            panel_x = x+side*1.26
            box('Elevator '+label+' / call panel',(panel_x,23.935,7.38),(.14,.04,.35),desk_mat,'13')
            lines('Elevator '+label+' / call button',[[(panel_x-.035,23.907,7.38),
                                                      (panel_x+.035,23.907,7.38)]],white,.007,'13')
            for obj in set(collections['13'].objects)-before:
                if obj != root:
                    obj.parent = root
    box('Upper foyer central directory',(0,24.28,8.28),(3.3,.12,4.3),black,'13',edge_mat=quiet_mat)
    text('Upper foyer directory brand',SPACED_BRAND,(0,24.20,9.52),.35,'13')
    text('Upper foyer level label','LEVEL 06',(0,24.20,8.85),.20,'13')
    text('Upper foyer lift wayfinding','←  L1 / L2     R1 / R2  →',(0,24.20,8.23),.15,'13')
    text('Upper foyer destinations','WORKSPACE\nMEETING ROOMS\nOBSERVATION',(0,24.20,7.38),.15,'13')
    for x in [-5.5,5.5]:
        data = bpy.data.lights.new('Lobby • Upper foyer soft light','AREA')
        data.energy = 65; data.shape = 'RECTANGLE'; data.size = 3; data.size_y = 3
        obj = link('Upper foyer soft light',data,'13'); obj.location = (x,21.6,10.70)
    overview = camera('Upper elevator foyer camera',(0,17.6,8.15),(0,24,8.20),12)
    arrival = camera('Escalator arrival camera',(6.85,19.65,7.82),(5.65,24.1,7.90),19)
    reverse = camera('Upper foyer back toward escalators camera',(8.0,22.2,8.6),(5.0,11.7,3.8),20)
    scene['Integration note'] = 'Standalone design: 20m wide, 36.5m deep, 18m high; upper elevator foyer at Z=6.12m.'
    bpy.context.view_layer.update()
    return overview,arrival,reverse


build_upper_elevator_foyer()


def build_holographic_fish_exhibit():
    """Monochrome projection alcove behind the identity pillar, under the bridge.

    Fish surfaces and projection dust stay editable native point sources;
    outlines, fin rays and halos stay sampled curves in the browser package.
    All randomness is local so the existing people and gardens remain stable.
    """
    group = '17'
    cy = 15.55
    rng = random.Random(2471)
    light = material('Exhibit / luminous white edges',(.76,.76,.76),emission=3.8)
    silver = material('Exhibit / translucent silver lines',(.32,.32,.32),emission=1.45)
    faint = material('Exhibit / projection traces',(.11,.11,.11),emission=.8)
    fish_dots = material('Exhibit / fish surface particles',(.38,.38,.38),emission=1.6)
    fin_dots = material('Exhibit / fin membrane particles',(.34,.34,.34),emission=1.4)
    projection_dots = material('Exhibit / floating projection dust',(.22,.22,.22),emission=1.3)

    def ring(radius,z,center_x=0,center_y=cy):
        return [(center_x+radius*math.cos(i*math.tau/96),
                 center_y+radius*math.sin(i*math.tau/96),z) for i in range(97)]

    def cylinder(name,radius,bottom,top,mat=desk_mat):
        n = 64
        verts = [(radius*math.cos(i*math.tau/n),cy+radius*math.sin(i*math.tau/n),z)
                 for z in [bottom,top] for i in range(n)]
        faces = [tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
        faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        mesh = bpy.data.meshes.new('Lobby • Exhibit / '+name)
        mesh.from_pydata(verts,[],faces); mesh.materials.append(mat)
        for face in mesh.polygons[2:]:
            face.use_smooth = True
        return link('Exhibit / '+name,mesh,group)

    # The exhibit sits between the escalators with open space above the fish.
    box('Exhibit / rear display wall',(0,18.75,2.95),(11.6,.18,5.9),black,group,outline=False)
    for side in [-1,1]:
        x = side*5.45
        box('Exhibit / flanking architectural column',(x,18.05,2.93),(.24,.34,5.86),
            black,group,edge_mat=quiet_mat)
        lines('Exhibit / vertical column light',[[(x-side*.09,17.868,.10),
                                                  (x-side*.09,17.868,5.83)]],light,.009,group)
        for offset in [-.13,.13]:
            lines('Exhibit / wall panel reveal',[[(side*3.4+offset,18.653,.16),
                                                  (side*3.4+offset,18.653,5.78)]],quiet_mat,.002,group)
        bx = side*3.30
        box('Exhibit / low waiting bench',(bx,17.65,.30),(2.25,.70,.52),desk_mat,group,
            edge_mat=quiet_mat)
        lines('Exhibit / bench luminous base',[[(bx-1.12,17.295,.08),(bx+1.12,17.295,.08)]],
              light,.010,group)
        px = side*4.85
        box('Exhibit / sculptural rock plinth',(px,16.95,.40),(1.25,1.05,.76),desk_mat,group)
        # Sparse triangulated stone peaks match the low side sculptures.
        vertices = [(px-.48,16.57,.78),(px+.48,16.57,.78),
                    (px+.46,17.30,.78),(px-.46,17.30,.78),
                    (px-.13,16.96,1.42),(px+.20,17.08,1.20)]
        faces = [(0,1,4),(1,5,4),(1,2,5),(2,3,5),(3,4,5),(3,0,4)]
        mesh = bpy.data.meshes.new('Lobby • Exhibit / faceted stone')
        mesh.from_pydata(vertices,[],faces); mesh.materials.append(black)
        link('Exhibit / faceted stone',mesh,group)
        edges = sorted({tuple(sorted((face[i],face[(i+1)%3]))) for face in faces for i in range(3)})
        lines('Exhibit / stone facet edges',[[vertices[a],vertices[b]] for a,b in edges],
              quiet_mat,.0025,group)

    text('Exhibit / wall manifesto','P E O P L E\nC U L T U R E\nT E C H\nT O M O R R O W',
         (-4.55,18.648,3.20),.17,group,spacing=1.0)
    matrix = [(x,18.645,z) for x in [2.9+i*.24 for i in range(10)]
              for z in [1.15+i*.21 for i in range(21)]]
    particles('Exhibit / wall light matrix',matrix,.006,group,silver)

    pedestal = cylinder('circular projection pedestal',.82,.04,1.07)
    pedestal['role'] = 'Hologram projector base behind the central pillar'
    cylinder('projector inset top',.70,1.071,1.095,black)
    lines('Exhibit / pedestal light rings',[ring(.825,.06),ring(.825,1.07),ring(.56,1.10)],
          light,.010,group)
    lines('Exhibit / pedestal vertical reveals',
          [[(.825*math.cos(a),cy+.825*math.sin(a),.07),
            (.825*math.cos(a),cy+.825*math.sin(a),1.06)]
           for a in [i*math.tau/6 for i in range(6)]],line_mat,.003,group)
    lines('Exhibit / ceiling projection halo',[ring(1.48,5.765)],silver,.006,group)
    lines('Exhibit / floating lower halos',[ring(1.48,1.49),ring(1.08,1.60)],silver,.005,group)

    # A recognisable goldfish silhouette: a tapered rounded body, forked tail,
    # swept dorsal fin, two lower fins, eye and gill. The face looks toward +X.
    def body(u,theta):
        swelling = math.sin(math.pi*u)
        rz = .12*(1-u)+.78*swelling**.65*(1-.18*u)
        ry = .08*(1-u)+.48*swelling**.8*(1-.35*u)
        return Vector((-1.05+3.15*u,cy+ry*math.cos(theta),
                       3.45+.05*swelling+rz*math.sin(theta)))

    surface_points = []
    for _ in range(7600):
        p = body(rng.random(),rng.uniform(0,math.tau))
        p += Vector((rng.gauss(0,.003),rng.gauss(0,.003),rng.gauss(0,.003)))
        surface_points.append(tuple(p))
    fish = particles('Exhibit / holographic fish body',surface_points,.0038,group,fish_dots)
    fish['role'] = 'Native point-source holographic goldfish'
    fish['forward_axis'] = '+X'
    upper = [tuple(body(i/96,math.pi/2)) for i in range(97)]
    lower = [tuple(body(i/96,3*math.pi/2)) for i in range(96,-1,-1)]
    lines('Exhibit / fish luminous silhouette',[upper+lower+upper[:1]],light,.008,group)
    contour_paths = [[tuple(body(i/64,theta)) for i in range(65)]
                     for theta in [math.pi*.65,math.pi*.82,math.pi,math.pi*1.18,math.pi*1.35]]
    lines('Exhibit / fish body contour traces',contour_paths,faint,.0015,group)

    def fin(label,root,controls,depth,count=560):
        root = Vector((root[0],cy+depth,root[1]))
        controls = [Vector((x,cy+depth,z)) for x,z in controls]

        def edge(t):
            a,b,c,d = controls
            return (1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d

        def membrane(t,v):
            p = root.lerp(edge(t),v)
            p.y -= .045*math.sin(math.pi*v)*math.sin(math.pi*t)
            p.z += .10*math.sin(math.pi*v)*(.5+.5*math.cos(math.pi*t))
            return p

        outline = ([tuple(membrane(0,i/24)) for i in range(25)]+
                   [tuple(edge(i/48)) for i in range(1,49)])
        if label!='dorsal':
            outline += [tuple(membrane(1,i/24)) for i in range(23,-1,-1)]
        lines('Exhibit / '+label+' outline',[outline],light,.005,group)
        rays = [[tuple(membrane(t,i/24)) for i in range(25)]
                for t in [i/20 for i in range(21)]]
        lines('Exhibit / '+label+' fin rays',rays,silver,.0018,group)
        dots = [tuple(membrane(rng.random(),math.sqrt(rng.random()))) for _ in range(count)]
        particles('Exhibit / '+label+' translucent membrane',dots,.004,group,fin_dots)

    fin('upper tail',(-1.03,3.49),[(-2.65,4.12),(-2.32,4.05),(-1.95,3.75),(-2.0,3.45)],-.03)
    fin('lower tail',(-1.03,3.40),[(-2.0,3.45),(-2.2,3.15),(-2.45,2.80),(-2.72,2.72)],-.03)
    fin('dorsal',(-.25,4.175),[(-.75,5.05),(-.12,5.01),(.58,4.64),(.98,4.185)],.10)
    fin('near pectoral',(.15,3.22),[(-.35,2.91),(-.43,2.56),(-.62,2.46),(-.80,2.42)],-.27,420)
    fin('lower ventral',(1.08,3.02),[(.70,2.85),(.87,2.45),(.59,2.13),(.27,1.98)],-.05,480)
    eye = [(1.70+.063*math.cos(i*math.tau/32),cy-.24,
            3.66+.063*math.sin(i*math.tau/32)) for i in range(33)]
    gill = [(1.28-.18*math.sin(i*math.pi/32),cy-.315,
             3.94-1.01*i/32) for i in range(33)]
    lines('Exhibit / fish eye and gill',[eye,gill],light,.006,group)

    # Broken particle columns suggest a volumetric projection without a solid
    # transparent cylinder or thousands of realised sphere meshes in the export.
    curtain,shaft = [],[]
    for _ in range(1550):
        a = rng.uniform(0,math.tau)
        radius = rng.uniform(1.1,1.48)
        curtain.append((radius*math.cos(a),cy+radius*math.sin(a),rng.uniform(1.15,5.73)))
    for _ in range(650):
        z = rng.uniform(1.11,2.95)
        spread = .08+.18*(z-1.11)
        shaft.append((rng.gauss(0,spread),cy+rng.gauss(0,spread),z))
    particles('Exhibit / falling hologram particles',curtain,.0035,group,projection_dots)
    particles('Exhibit / projector light shaft',shaft,.004,group,fish_dots)
    traces = []
    for i in range(28):
        a = i*math.tau/28
        radius = rng.uniform(1.15,1.45)
        traces.append([(radius*math.cos(a),cy+radius*math.sin(a),1.16),
                       (radius*math.cos(a),cy+radius*math.sin(a),5.73)])
    lines('Exhibit / vertical projection traces',traces,faint,.0012,group)
    rays = []
    for i in range(36):
        a = i*math.tau/36
        rays.append([(.10*math.cos(a),cy+.10*math.sin(a),1.10),
                     (.60*math.cos(a),cy+.60*math.sin(a),2.70)])
    lines('Exhibit / projector volumetric rays',rays,faint,.0007,group)
    camera('Holographic fish exhibit camera',(0,8.70,1.70),(0,16.25,2.65),18)
    data = bpy.data.lights.new('Lobby • Exhibit / soft floor reflection','AREA')
    data.energy = 40; data.shape = 'DISK'; data.size = 3
    obj = link('Exhibit / soft floor reflection',data,group); obj.location = (0,cy,5.70)
    return {'center':[0,cy,0],'collection':collections[group].name,
            'fish_bounds_m':{'x':[-2.72,2.10],'z':[1.98,5.05]},
            'pedestal_radius_m':.82,'pedestal_height_m':1.07,
            'sub_ceiling':False,'escalator_clearance_x_m':.31,
            'native_particle_geometry':True,'camera':'Lobby • Holographic fish exhibit camera'}


exhibit_manifest = build_holographic_fish_exhibit()

hero = camera('Concept portrait camera', (0,-10.8,2.2), (0,6,4.8), 23)
wide = camera('Wide lobby activity camera', (0,-14,3), (0,6,5.8), 24)
camera('Sculpted ceiling detail camera', (-.6,-7,9), (-.9,4.5,18.9), 14)
camera('Pillar ceiling junction camera', (0,-4,12.8), (0,6,16.2), 45)
camera('Eye-level walkthrough camera', (0,-8,1.7), (0,5,3), 22)
camera('Architecture overview camera', (10,-15,11), (0,4,6), 24)
scene.camera = hero
for name,pos in [('Entrance threshold',(0,-12,0)), ('Reception focus',(0,3.7,1.5)),
                 ('Mezzanine landing',(0,11.5+REAR_EXTENSION,6.12))]:
    obj = link(name,None,'09'); obj.location = pos; obj.empty_display_type = 'ARROWS'
    obj.empty_display_size = .5

world = bpy.data.worlds.new('Lobby • Absolute black world'); world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (0,0,0,1)
world.node_tree.nodes['Background'].inputs[1].default_value = 0
scene.world = world
for x in [-4,4]:
    data = bpy.data.lights.new('Lobby • Soft monochrome bounce','AREA')
    data.energy = 90; data.shape = 'DISK'; data.size = 5
    obj = link('Soft monochrome bounce',data,'08'); obj.location = (x,1,10)
scene.render.engine = 'CYCLES'
scene.cycles.samples = 32
scene.cycles.use_denoising = False
scene.cycles.max_bounces = 5
scene.cycles.diffuse_bounces = 1
scene.cycles.glossy_bounces = 3
scene.render.resolution_x = 720
scene.render.resolution_y = 1120
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'None'
scene.render.filepath = str(ROOT/'lobby-concept.png')


def apply_cyber_lighting():
    """Selective luminous architecture and a restrained monochrome bloom pass."""
    if '15' not in collections:
        collections['15'] = bpy.data.collections.new('Lobby • 15 Cyber lighting accents')
        scene.collection.children.link(collections['15'])
    for obj in list(collections['15'].objects):
        bpy.data.objects.remove(obj,do_unlink=True)

    def emissive(name,color,strength):
        mat = bpy.data.materials.get('Lobby • '+name)
        if mat is None:
            mat = material(name,(color,color,color),emission=strength)
        else:
            p = mat.node_tree.nodes.get('Principled BSDF')
            p.inputs['Base Color'].default_value = (color,color,color,1)
            p.inputs['Emission Color'].default_value = (color,color,color,1)
            p.inputs['Emission Strength'].default_value = strength
        return mat

    hero = emissive('Cyber / Hero white light',.85,5.0)
    architectural = emissive('Cyber / Architectural silver light',.55,2.3)
    understated = emissive('Cyber / Secondary silver light',.22,1.1)
    # A small general lift supports the accents without overexposing particles.
    for name,strength in [('Fine silver edges',1.05),('Secondary gray edges',.65),
                          ('Silver typography',1.0),('White light channels',3.0)]:
        p = bpy.data.materials['Lobby • '+name].node_tree.nodes.get('Principled BSDF')
        p.inputs['Emission Strength'].default_value = strength
    for obj in scene.objects:
        if obj.type not in {'CURVE','FONT'}:
            continue
        name = obj.name
        accent = None
        if any(s in name for s in ['KAZE identity pillar / feature edges','Pillar front reveal',
                                   'KAZE angular crest','rounded handrail',' / portal',
                                   'Reception luminous plinth']):
            accent = hero
        elif any(s in name for s in ['Pillar side reveal','KAZE wordmark','Gallery balustrade',
                                     'Rear gallery railing','Mezzanine side gallery / feature edges',
                                     'Rear mezzanine bridge / feature edges',' / skirt edges',
                                     ' / wall surround / feature edges','Upper foyer front deck edge',
                                     'Upper foyer ceiling light','Carpet inset stitched border',
                                     'Floor approach light']):
            accent = architectural
        elif 'Elevator ' in name and '/ feature edges' in name:
            accent = understated
        if accent is not None:
            obj.data.materials.clear(); obj.data.materials.append(accent)
    for side in [-1,1]:
        lines('Cyber / gallery underside light',
              [[(side*7.59,-4.45,5.88),(side*7.59,19.45,5.88)]],hero,.008,'15')
        lines('Cyber / upper arrival floor light',
              [[(side*3.0,19.75,6.14),(side*3.0,23.55,6.14)],
               [(side*8.85,19.75,6.14),(side*8.85,23.55,6.14)]],architectural,.006,'15')
    # In older walkthroughs the door-pocket facade masks the portal jambs.
    # Add luminous trim in front of it so the opening stays outlined when open.
    if scene.objects.get('Lobby • Navigation / walkthrough camera'):
        portal = scene.objects['Lobby • Elevator R1 / portal']
        if portal.location.y>-.059:
            lines('Cyber / R1 visible portal jambs',
                  [[(2.97,23.84,6.14),(2.97,23.84,9.25)],
                   [(5.13,23.84,6.14),(5.13,23.84,9.25)]],hero,.010,'15')
    for obj in scene.objects:
        if obj.type=='LIGHT' and obj.name.startswith('Lobby • Soft monochrome bounce'):
            obj.data.energy = 135
        elif obj.type=='LIGHT' and obj.name.startswith('Lobby • Upper foyer soft light'):
            obj.data.energy = 95
    # Blender 5.2 compositor uses a node group with an Image output.
    tree = scene.compositing_node_group
    if tree is None:
        tree = bpy.data.node_groups.new('Lobby • Cyber restrained glow','CompositorNodeTree')
        tree.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
        render = tree.nodes.new('CompositorNodeRLayers'); render.scene = scene
        render.location = (-300,0)
        glare = tree.nodes.new('CompositorNodeGlare'); glare.location = (-40,0)
        glare.name = 'Lobby / restrained cyber glow'
        glare.inputs['Type'].default_value = 'Fog Glow'
        glare.inputs['Quality'].default_value = 'High'
        glare.inputs['Threshold'].default_value = 1.4
        glare.inputs['Strength'].default_value = .22
        glare.inputs['Size'].default_value = .20
        output = tree.nodes.new('NodeGroupOutput'); output.location = (220,0)
        tree.links.new(render.outputs['Image'],glare.inputs['Image'])
        tree.links.new(glare.outputs['Image'],output.inputs['Image'])
        scene.compositing_node_group = tree
    scene.render.use_compositing = True
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D' and hasattr(area.spaces.active.shading,'use_compositor'):
                area.spaces.active.shading.use_compositor = 'CAMERA'
    scene['Lighting style'] = 'Cyber monochrome: selective bright outlines, luminous gallery edges, restrained bloom.'
    return {'hero_emission':5.0,'architecture_emission':2.3,'bloom_strength':.22}


apply_cyber_lighting()

scene['Design reference'] = 'KAJU monochrome particle atrium; twin escalators and reflective floor'
scene['Integration note'] = 'Standalone design: 20m wide, 36.5m deep, 18m high; upper elevator foyer at Z=6.12m.'
scene['Entrance direction'] = '+Y into lobby; Z up; entrance center (0,-12,0)'
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.region_3d.view_perspective = 'CAMERA'
            area.spaces.active.shading.type = 'MATERIAL'
            area.spaces.active.overlay.show_overlays = False
bpy.context.view_layer.objects.active = hero
hero.select_set(True)
if '--defer-save' not in sys.argv:
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'kaze-lobby-walkthrough.blend'))
manifest = {'blend':'kaze-lobby-walkthrough.blend','scene':scene.name,
            'dimensions_m':{'width':WIDTH,'depth':36.5,'height':18,'mezzanine_floor':6.12},
            'elevators':4,'elevators_per_side':2,
            'upper_foyer':{'floor_z':6.12,'front_y':19,'rear_y':24.5},
            'escalator_entry_y':8.45,
            'clearance_behind_reception_m':8.45-4.6,
             'identity_pillar':{'center':[0,6.9,8],'dimensions_m':[3.5,2.2,16],
                               'front_y':5.8,'reception_clearance_m':1.2},
            'entrance_center':[0,-12,0],'forward_axis':'+Y','up_axis':'+Z',
            'objects':len(scene.objects),'escalators':2,'escalator_steps_per_flight':34,
             'lounge_sofa_bases':0,
             'ceiling':ceiling_manifest,
             'rear_exhibit':exhibit_manifest,
            'reception_carpet':{'center':[0,-3.625,.023],'dimensions_m':[4.0,16.75,.022]},
            'people':len(collections['06'].objects),'trees':12,
            'npc_poses':{pose:sum(o.get('pose')==pose for o in collections['06'].objects)
                         for pose in sorted({o.get('pose') for o in collections['06'].objects})},
            'particle_count':sum(o.get('particle_count',0) for o in scene.objects),
            'camera':hero.name,'city_files_modified':False}
(ROOT/'lobby-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
if '--render' in sys.argv:
    bpy.ops.render.render(write_still=True)
    scene.camera = wide
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 800
    scene.render.filepath = str(ROOT/'lobby-wide.png')
    bpy.ops.render.render(write_still=True)
    for camera_name,width,height,filename in [
        ('Lobby • Sculpted ceiling detail camera',1236,578,'ceiling-detail.png'),
        ('Lobby • Pillar ceiling junction camera',960,560,'pillar-ceiling-junction.png'),
        ('Lobby • Holographic fish exhibit camera',1200,800,'holographic-fish-exhibit.png'),
        ('Lobby • Upper elevator foyer camera',1280,800,'upper-landing-elevators.png'),
        ('Lobby • Escalator arrival camera',1280,800,'escalator-arrival.png'),
        ('Lobby • Upper foyer back toward escalators camera',1280,800,'upper-landing-back-view.png')]:
        scene.camera = scene.objects[camera_name]
        scene.render.resolution_x = width; scene.render.resolution_y = height
        scene.render.filepath = str(ROOT/filename)
        bpy.ops.render.render(write_still=True)
    scene.camera = hero
    scene.render.resolution_x = 720
    scene.render.resolution_y = 1120
    scene.render.filepath = str(ROOT/'lobby-concept.png')
print(json.dumps(manifest))
