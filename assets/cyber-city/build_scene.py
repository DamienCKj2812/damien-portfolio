"""Run inside Blender's Python environment. Creates an independent scene."""
from pathlib import Path
import math
import random
import bpy
from mathutils import Vector

ROOT = Path('/home/damienckj/Documents/damien-portfolio/assets/cyber-city')
random.seed(47)
scene = bpy.data.scenes.new('NEON / Kaze Megacity')
bpy.context.window.scene = scene
scene.unit_settings.system = 'METRIC'
collections = {}
for name in ['01 Megatower', '02 Neon media', '03 Sky garden', '04 Skyline', '05 Elevated highways', '06 Flying vehicles', '07 Street life', '08 Atmosphere & lighting']:
    col = bpy.data.collections.new(name)
    scene.collection.children.link(col)
    collections[name] = col
current = collections['01 Megatower']

def mat(name, color, metal=0, rough=.4, glow=0):
    m = bpy.data.materials.new('City • ' + name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Metallic'].default_value = metal
    p.inputs['Roughness'].default_value = rough
    if glow:
        p.inputs['Emission Color'].default_value = (*color, 1)
        p.inputs['Emission Strength'].default_value = glow
    return m

steel = mat('Graphite titanium', (.016,.026,.05), .8, .3)
frame = mat('Facade mullions', (.035,.057,.09), .75, .26)
glass = mat('Midnight blue architectural glass', (.012,.065,.115), .7, .18)
blueglass = mat('Cobalt curtain wall', (.014,.075,.20), .5, .2)
warm = mat('Warm occupied offices', (1,.55,.22), .15, .35, 2)
white = mat('Cool occupied offices', (.3,.65,.8), .1, .4, 1.8)
cyan = mat('Electric cyan', (.015,.45,1), .1, .3, 8)
ice = mat('Ice blue', (.12,.8,1), .1, .3, 6)
pink = mat('Hot magenta', (1,.005,.38), .1, .3, 8)
violet = mat('Ultraviolet', (.25,.008,1), .1, .3, 8)
amber = mat('Warm architectural lighting', (1,.65,.25), .1, .3, 4)
red = mat('Aircraft warning red', (1,.015,.05), 0, .4, 5)
concrete = mat('Bridge concrete', (.055,.06,.085), .25, .6)
roadmat = mat('Wet highway asphalt', (.012,.016,.026), .2, .23)
green = mat('Garden foliage', (.02,.075,.042), .1, .75)
greenlight = mat('Garden foliage lighter', (.045,.11,.058), 0, .65)
bark = mat('Tree bark', (.048,.025,.016), 0, .9)
black = mat('Pedestrian silhouette', (.007,.008,.014), .05, .7)
vehicle = mat('Vehicle metallic midnight', (.02,.035,.085), .8, .22)
windshield = mat('Vehicle dark canopy', (.005,.06,.12), .8, .1)

batches = {}
def batch_box(center, size, material):
    key = (current.name, material.name)
    verts, faces = batches.setdefault(key, ([], []))
    x,y,z = center; a,b,c = [s/2 for s in size]; k = len(verts)
    verts.extend([(x+dx*a,y+dy*b,z+dz*c) for dx,dy,dz in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]])
    faces.extend([tuple(k+i for i in f) for f in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]])

def mesh_obj(name, verts, faces, material, uv=None):
    mesh=bpy.data.meshes.new(name); mesh.from_pydata(verts,[],faces); mesh.update()
    obj=bpy.data.objects.new(name,mesh); current.objects.link(obj); mesh.materials.append(material)
    if uv:
        layer=mesh.uv_layers.new(name='UVMap')
        for poly in mesh.polygons:
            for index in poly.loop_indices:
                layer.data[index].uv=uv[mesh.loops[index].vertex_index]
    return obj

def box(name, center, size, material, bevel=0):
    x,y,z=center; a,b,c=[s/2 for s in size]
    verts=[(dx*a,dy*b,dz*c) for dx,dy,dz in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    obj=mesh_obj(name,verts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],material); obj.location=center
    if bevel:
        mod=obj.modifiers.new('Manufactured edge bevel','BEVEL'); mod.width=bevel; mod.segments=2
        obj.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    return obj

def tube(name, points, radius, material):
    data=bpy.data.curves.new(name,'CURVE'); data.dimensions='3D'; data.bevel_depth=radius; data.bevel_resolution=2
    poly=data.splines.new('POLY'); poly.points.add(len(points)-1)
    for p,xyz in zip(poly.points,points): p.co=(*xyz,1)
    obj=bpy.data.objects.new(name,data); current.objects.link(obj); data.materials.append(material); return obj

def cylinder(name, center, radius, depth, material, segments=48):
    verts=[(radius*math.cos(2*math.pi*i/segments),radius*math.sin(2*math.pi*i/segments),z) for z in [-depth/2,depth/2] for i in range(segments)]
    faces=[tuple(reversed(range(segments))),tuple(range(segments,segments*2))]+[(i,(i+1)%segments,(i+1)%segments+segments,i+segments) for i in range(segments)]
    o=mesh_obj(name,verts,faces,material); o.location=center
    for p in o.data.polygons: p.use_smooth=len(p.vertices)==4
    return o

def ring(name, center, radius, material, thickness=.07):
    points=[(center[0]+radius*math.cos(i*math.tau/80),center[1]+radius*math.sin(i*math.tau/80),center[2]) for i in range(81)]
    return tube(name,points,thickness,material)

def poster_material(file, strength=1.5):
    m=bpy.data.materials.new('Billboard • '+file); m.use_nodes=True; nodes=m.node_tree.nodes; nodes.clear()
    out=nodes.new('ShaderNodeOutputMaterial'); emission=nodes.new('ShaderNodeEmission'); emission.inputs['Strength'].default_value=strength
    tex=nodes.new('ShaderNodeTexImage'); tex.image=bpy.data.images.load(str(ROOT/'textures'/file),check_existing=True); tex.image.pack()
    m.node_tree.links.new(tex.outputs['Color'],emission.inputs['Color']); m.node_tree.links.new(emission.outputs[0],out.inputs['Surface']); return m

posters={name:poster_material(name+'.png') for name in ['portrait','kaze','nexus','portal','arasaka','landscape','drive','night','tomorrow']}

def billboard(name, center, width, height, art, border=cyan):
    x,y,z=center
    box(name+' • housing',(x,y+.12,z),(width+.25,.23,height+.25),steel,.04)
    mesh_obj(name+' • LED display',[(x-width/2,y-.02,z-height/2),(x+width/2,y-.02,z-height/2),(x+width/2,y-.02,z+height/2),(x-width/2,y-.02,z+height/2)],[(0,1,2,3)],posters[art],[(0,0),(1,0),(1,1),(0,1)])
    tube(name+' • perimeter',[(x-width/2,y-.06,z-height/2),(x+width/2,y-.06,z-height/2),(x+width/2,y-.06,z+height/2),(x-width/2,y-.06,z+height/2),(x-width/2,y-.06,z-height/2)],.035,border)

def wrapped_screen(name, cx, cy, z, radius, height, art):
    verts=[]; uv=[]; N=40
    for zz,v in [(z-height/2,0),(z+height/2,1)]:
        for i in range(N+1):
            a=-1.05+2.1*i/N; verts.append((cx+radius*math.sin(a),cy-radius*math.cos(a),zz)); uv.append((i/N,v))
    faces=[(i,i+1,N+2+i,N+1+i) for i in range(N)]
    mesh_obj(name,verts,faces,posters[art],uv)
    for zz in [z-height/2,z+height/2]:
        tube(name+' • border',[(cx+(radius+.03)*math.sin(-1.05+2.1*i/N),cy-(radius+.03)*math.cos(-1.05+2.1*i/N),zz) for i in range(N+1)],.045,pink if art=='nexus' else violet)

# Main building: occupied curtain walls, stacked floor slabs, visible structural grid.
box('Megatower • central occupied volume',(0,0,24),(13.8,10.5,48),steel,.1)
for floor in range(60):
    z=.8+floor*.78
    batch_box((0,-5.3,z),(14,.17,.1),frame)
    batch_box((6.98,0,z),(.15,10.6,.1),frame)
    for col in range(14):
        x=-6.5+col
        m=warm if random.random()<.4 else glass
        batch_box((x,-5.42,z+.34),(.89,.06,.63),m)
        if m==warm:
            batch_box((x,-5.49,z+.6),(.6,.025,.03),amber)
    for col in range(11):
        y=-4.9+col*.94
        batch_box((7.04,y,z+.34),(.06,.82,.63),warm if random.random()<.36 else blueglass)
for x in [-7+i for i in range(15)]: batch_box((x,-5.49,24),(.075,.12,48),frame)
for y in [-5.3+i*.96 for i in range(12)]: batch_box((7.12,y,24),(.13,.065,48),frame)
box('Crown • stepped upper block',(-1.3,1,49.2),(10.8,8.4,3.2),glass,.12)
for z in [48,48.8,49.6,50.4]:
    batch_box((-1.3,-3.24,z),(10.9,.16,.12),frame)
    for x in [-6+i*.9 for i in range(12)]: batch_box((x,-3.34,z+.3),(.74,.05,.5),warm if random.random()<.5 else glass)

# Angular exoskeleton braces with continuous cyan edge light.
for i,(p,q) in enumerate([((-7.1,-5.7,.6),(-4.5,-5.7,37)),((-4.5,-5.7,37),(-2.2,-5.7,51.5)),((2.1,-5.8,2),(5.8,-5.8,23)),((5.8,-5.8,23),(-1,-5.8,51.5)),((7.25,5.2,2),(7.25,-1,26)),((7.25,-1,26),(7.25,3.9,50))]):
    tube(f'Exoskeleton {i} • titanium', [p,q],.32,steel)
    tube(f'Exoskeleton {i} • neon',[(p[0],p[1]-.28,p[2]),(q[0],q[1]-.28,q[2])],.065,cyan if i%2 else violet)
for x in [-7.15,7.2]: tube('Vertical corner light',[(x,-5.6,.5),(x,-5.6,45)],.07,cyan)

current=collections['02 Neon media']
billboard('KAZE • cyborg campaign',(-1.6,-5.95,29.7),5.6,28.5,'portrait',cyan)
billboard('THE NIGHT LIVES ON',(-5.25,-5.9,19.5),2.05,17,'night',violet)
billboard('Clean mobility campaign',(-1.9,-6.1,7.3),8.4,6.5,'drive',cyan)
box('Media cylinder • dark core',(5.4,-5.3,18.3),(4.9,3,31.4),steel,.3)
cylinder('Media cylinder • curved glass',(5.4,-5.35,18.3),2.85,31.4,glass)
for z,art,h in [(30,'nexus',8),(22.7,'portal',5.3),(16.5,'landscape',5),(10.8,'arasaka',5.6)]:
    wrapped_screen('Curved LED • '+art,5.4,-5.35,z,2.91,h,art)
for z in [3,4,5,6,7.6,13.8,19.2,25.6,34.3]:
    ring('Media cylinder • floor rim',(5.4,-5.35,z),2.95,frame,.1)
    for i in range(18):
        a=i*math.tau/18
        tube('Media cylinder • mullion',[(5.4+2.88*math.cos(a),-5.35+2.88*math.sin(a),z),(5.4+2.88*math.cos(a),-5.35+2.88*math.sin(a),z+.8)],.035,frame)

# Terrace gardens and rooftop vegetation.
current=collections['03 Sky garden']
leaf_meshes=[]
for m in [green,greenlight]:
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1)
    temp=bpy.context.object; mesh=temp.data; mesh.name='City • shared foliage cluster'; mesh.materials.append(m); leaf_meshes.append(mesh)
    bpy.data.objects.remove(temp,do_unlink=True)
def tree(x,y,z,size=1):
    tube('Tree • trunk',[(x,y,z),(x+.04*size,y,z+1.5*size)],.075*size,bark)
    for i in range(4):
        dx=random.uniform(-.35,.35)*size; dy=random.uniform(-.35,.35)*size; dz=(1.25+i*.23)*size
        o=bpy.data.objects.new('Tree • leafy crown',leaf_meshes[i%2]); current.objects.link(o); o.location=(x+dx,y+dy,z+dz); o.scale=(.5*size,.48*size,.52*size)
        if i<2:tube('Tree • branch',[(x,y,z+.8*size),(x+dx,y+dy,z+dz)],.03*size,bark)
for z,w in [(12,18),(24,17),(37,18),(44,15)]:
    box('Cantilever garden • slab',(-1,-.7,z),(w,13,.45),steel,.08)
    tube('Garden • luminous underside',[(-1-w/2,-7.25,z-.2),(-1+w/2,-7.25,z-.2)],.045,amber)
    for x in [-w/2+.1+i*1.4 for i in range(int(w/1.4))]:
        tree(x,-6.6,z+.28,.65)
    for x in [-w/2+.1+i*1.8 for i in range(int(w/1.8))]:
        batch_box((x,-7.05,z+.48),(1.3,.65,.4),steel)
    tube('Garden • glass rail',[(-1-w/2,-7.2,z+1),(-1+w/2,-7.2,z+1)],.03,frame)
    # Faceted soffit supports make the projecting balconies readable from below.
    for x in [-w/2+1,w/2-2]: tube('Garden • underside support',[(x,-3,z-1.6),(x,-7,z-.2)],.11,frame)
for x in [-5,-3,-1,1,3]:tree(x,0,51,.85)
for x in [-5,5]:tube('Crown • antenna',[(x,1,50.8),(x,1,54)],.045,frame)

# Circular observation lounge attached to a separate right-hand glass spine.
box('Sky lounge • supporting tower',(8.3,2.5,22),(5.3,5.4,42),blueglass,.15)
for z in [1+i*.85 for i in range(49)]:
    batch_box((11.02,2.5,z),(.09,5.5,.08),frame)
    for y in [.3,1.4,2.5,3.6,4.7]:batch_box((11.1,y,z+.36),(.035,.8,.6),white if random.random()<.3 else glass)
cx,cy,cz=8.2,2,40
cylinder('Sky lounge • lower saucer',(cx,cy,cz),5.8,.55,steel,80)
cylinder('Sky lounge • glowing soffit',(cx,cy,cz-.3),5.1,.07,amber,80)
cylinder('Sky lounge • roof disc',(cx,cy,cz+2.4),5.8,.32,steel,80)
for zz in [cz+.25,cz+2.3,cz+2.6]:ring('Sky lounge • cyan perimeter',(cx,cy,zz),5.8,cyan,.06)
for i in range(40):
    a=i*math.tau/40; x=cx+5.4*math.cos(a); y=cy+5.4*math.sin(a)
    tube('Sky lounge • curtain-wall mullion',[(x,y,cz+.3),(x,y,cz+2.35)],.045,frame)
for i in range(12):
    a=i*math.tau/12; tree(cx+4.5*math.cos(a),cy+4.5*math.sin(a),cz+2.65,.6)
ring('Sky lounge • inside warm ring',(cx,cy,cz+.07),3.8,amber,.07)
current=collections['02 Neon media']
billboard('KAZE INDUSTRIES • rooftop monument',(8.5,.8,46.1),4.5,6.5,'kaze',cyan)

# City skyline with varied stepped crowns, windows, antennae and distant advertising.
current=collections['04 Skyline']
for i in range(34):
    x=random.uniform(-45,45); y=random.uniform(12,50)
    if abs(x)<9:y+=25
    h=random.uniform(9,35); w=random.uniform(2,5); dep=random.uniform(2,5)
    box(f'Skyline {i:02d} • tower',(x,y,h/2),(w,dep,h),steel)
    box(f'Skyline {i:02d} • crown',(x,y,h+1),(w*.6,dep*.6,2),frame)
    tube('Skyline • antenna',[(x,y,h+2),(x,y,h+random.uniform(3,6))],.035,frame)
    batch_box((x,y,h+4),(.1,.1,.18),red)
    for z in range(2,int(h),2):
        for xx in [-w*.3,0,w*.3]:
            if random.random()<.5:batch_box((x+xx,y-dep/2-.01,z),(.17,.03,.38),pink if random.random()<.12 else warm)
        if random.random()<.25:batch_box((x+w/2+.01,y-dep*.2,z),(.03,.12,.3),red)
    if i in [4,13,21]:
        billboard('Distant corporate campaign',(x,y-dep/2-.1,h*.6),w*.8,h*.35,'tomorrow',cyan)
# Tall flank buildings frame the main tower.
for x,y,h in [(-22,9,28),(25,11,36)]:
    box('Flanking skyline • stepped shaft',(x,y,h/2),(5,5,h),steel)
    for level in range(4):box('Flanking skyline • crown',(x,y,h+level*.8),(4-level*.8,4-level*.8,1.5),steel)
    for dx in [-1.6,0,1.6]:
        tube('Flanking skyline • spire',[(x+dx,y,h),(x+dx,y,h+5-abs(dx))],.04,frame)
        batch_box((x+dx,y,h+5-abs(dx)),(.12,.12,.15),red)
    for z in range(2,h,2):
        for dx in [-1.7,-.8,.8,1.7]:
            if random.random()<.65:batch_box((x+dx,y-2.51,z),(.13,.03,.6),warm)
    billboard('Flanking skyline • campaign',(x,y-2.6,h*.65),3.8,8,'tomorrow',cyan)

# Elevated road geometry, continuous guardrails, support columns and lane marks.
current=collections['05 Elevated highways']
def highway(name, points, width=3.2):
    sides=[]
    for i,p in enumerate(points):
        tangent=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(i-1,0)])
        perp=Vector((-tangent.y,tangent.x,0)).normalized()*width/2
        sides.append((Vector(p)+perp,Vector(p)-perp))
    verts=[tuple(v) for pair in sides for v in pair]
    deck=mesh_obj(name+' • road surface',verts,[(2*i,2*i+1,2*i+3,2*i+2) for i in range(len(points)-1)],roadmat)
    solid=deck.modifiers.new('Bridge deck thickness','SOLIDIFY'); solid.thickness=.35
    for side in [0,1]:
        rail=[tuple(v[side]+Vector((0,0,.65))) for v in sides]
        tube(name+' • guardrail',rail,.055,frame)
        tube(name+' • blue edge', [tuple(v[side]+Vector((0,0,.07))) for v in sides],.025,cyan)
        for i,v in enumerate(sides):
            p=v[side];tube(name+' • railing post',[tuple(p),tuple(p+Vector((0,0,.65)))],.025,frame)
    for i in range(0,len(points),4):
        x,y,z=points[i]
        box(name+' • support pier',(x,y,z/2-.2),(.65,.75,z-.4),concrete,.05)
        batch_box((x,y,z+.025),(.12,.7,.015),amber)
        for side in [0,1]:
            p=sides[i][side]; batch_box(tuple(p+Vector((0,0,.08))),(.15,.15,.03),pink)
    return points
highway('Foreground skyway',[(-32+i*2,-17+i*.34,4.2+i*.10) for i in range(33)],3.0)
highway('Left interchange',[(-31+i*.85,-4-i*.5,10-i*.08) for i in range(24)],3.2)
highway('Background transit route',[(-26+i*2,7,7.5) for i in range(27)],2.7)

# Futuristic airborne cars, sculpted fuselage, canopy, glowing thruster rings.
current=collections['06 Flying vehicles']
def flying_car(name, position, size=1, heading=0):
    root=bpy.data.objects.new(name,None);current.objects.link(root);root.location=position;root.rotation_euler.z=heading;root.scale=(size,size,size)
    def child(o):o.parent=root;return o
    verts=[(-1.65,-.65,0),(1.75,-.5,0),(1.9,.48,0),(-1.5,.65,0),(-1.2,-.5,.38),(.7,-.45,.55),(1.4,.4,.35),(-1.1,.5,.38)]
    child(mesh_obj(name+' • faceted fuselage',verts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],vehicle))
    child(box(name+' • canopy',(-.15,0,.53),(1.45,.78,.38),windshield,.16))
    for y in [-.54,.54]:child(tube(name+' • flank light',[(-1.4,y,.12),(.9,y,.17),(1.6,y*.8,.1)],.035,cyan))
    child(tube(name+' • rear lights',[(-1.63,-.5,.16),(-1.63,.5,.16)],.075,pink))
    for y in [-.75,.75]:
        for x in [-.9,.95]:
            child(cylinder(name+' • hover nacelle',(x,y,-.1),.32,.2,steel,20))
            child(ring(name+' • hover ion ring',(x,y,-.22),.27,cyan,.05))
    for y in [-.28,.28]:child(tube(name+' • headlight',[(1.75,y-.1,.14),(1.75,y+.1,.14)],.055,ice))
    return root
flying_car('Aircar 01 • foreground commuter',(-14,-15,14),1.35,-.25)
flying_car('Aircar 02 • right approaching',(16,-7,12),.95,.35)
flying_car('Aircar 03 • upper transit',(14,2,31),.65,-.4)
flying_car('Aircar 04 • distant',(-18,12,24),.65,.15)
flying_car('Skyway vehicle',(-10,-13.3,6.0),.75,0)

# Reflective paving, street fixtures, foreground trees, people and urban furniture.
current=collections['07 Street life']
wet=mat('Wet reflective plaza',(.012,.018,.035),.65,.13)
nodes=wet.node_tree.nodes; p=nodes.get('Principled BSDF'); noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=6;noise.inputs['Detail'].default_value=4;noise.inputs['Roughness'].default_value=.7
bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.28;bump.inputs['Distance'].default_value=.05
wet.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height']);wet.node_tree.links.new(bump.outputs['Normal'],p.inputs['Normal'])
box('Rain-soaked city plaza',(0,0,-.12),(150,150,.2),wet)
for x in range(-40,41,4):batch_box((x,-18,.012),(.018,65,.01),frame)
for y in range(-45,26,4):batch_box((0,y,.014),(90,.018,.01),frame)
for x in [-18,-14,13,18]:
    for y in [-22,-15,-7,1]:
        tube('Streetlight • mast',[(x,y,0),(x,y,3.4),(x+.5,y,3.6)],.045,steel)
        batch_box((x+.5,y,3.6),(.3,.12,.05),amber)
for x in [-13,-9,10,14]:
    box('Neon street bollard',(x,-17,.5),(.18,.18,1),steel,.02)
    batch_box((x,-17,.55),(.19,.19,.48),pink if x%2 else cyan)
for x,y,s in [(-19,-20,2.8),(-16,-9,2),(-12,-4,1.6),(18,-18,2.1),(15,0,1.7),(-24,-15,2.5),(21,-3,1.7)]:
    tree(x,y,0,s)
for _ in range(38):
    x=random.uniform(-18,18);y=random.uniform(-19,-7)
    if abs(x)<3 and y>-9:continue
    size=random.uniform(.8,1.1)
    cylinder('Pedestrian • head',(x,y,1.52*size),.12*size,.23*size,black,8)
    box('Pedestrian • coat',(x,y,.94*size),(.32*size,.2*size,.85*size),black,.04)
    for dx in [-.095,.095]:tube('Pedestrian • leg',[(x+dx,y,.65*size),(x+dx,y+.04,.08)],.055,black)
    for dx in [-.21,.21]:tube('Pedestrian • arm',[(x+dx,y,1.25*size),(x+dx,y,.65*size)],.045,black)
for x in [-5.3,-3.4,-1.5,.4,2.3]:
    batch_box((x,-5.57,1.7),(1.7,.04,3.0),warm)
    batch_box((x,-5.65,1.7),(.05,.05,3.1),frame)
box('Street-side utility wall',(22,-15,2.1),(7,.5,4.2),concrete,.07)
billboard('SAME SKIES • pedestrian message',(22,-15.3,2.25),4.8,3.1,'tomorrow',cyan)

# Commit merged static details: small windows/fixtures remain organized by material.
for (col_name,material_name),(verts,faces) in batches.items():
    current=collections[col_name]
    mesh_obj('Batched details • '+material_name,verts,faces,bpy.data.materials[material_name])

# Atmosphere, local neon spill and a low-angle architectural camera.
current=collections['08 Atmosphere & lighting']
world=bpy.data.worlds.new('City • blue midnight');scene.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.008,.015,.042,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.3
def light(name,loc,color,power,size=5,target=None,kind='AREA'):
    data=bpy.data.lights.new(name,kind);data.energy=power;data.color=color
    if kind=='AREA':data.shape='DISK';data.size=size
    else:data.shadow_soft_size=size
    obj=bpy.data.objects.new(name,data);current.objects.link(obj);obj.location=loc
    if target:obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
    return obj
light('Moon • cool architectural fill',(-20,-15,55),(.2,.38,1),6500,30,(0,0,25))
light('Front • blue softbox',(20,-30,30),(.15,.4,1),5000,25,(0,0,25))
light('Purple horizon',(-30,25,15),(.55,.09,.8),8000,30,(0,0,20))
for pos,color,power in [((-3,-9,26),(.3,.01,1),950),((6,-10,28),(1,.005,.22),1100),((-3,-9,7),(.01,.35,1),650),((8,-9,11),(.08,.4,1),750),((-12,-18,1),(1,.005,.2),180),((13,-15,1),(.01,.4,1),180)]:
    light('Neon • colored spill',pos,color,power,3,kind='POINT')
for x,y in [(-9,-6),(9,-5),(-2,-7)]:light('Lobby • warm pool',(x,y,3),(1,.52,.2),250,2,kind='POINT')

# Haze fades the distant skyline; billboards stay in front of the volume.
fog=bpy.data.materials.new('City • atmospheric blue haze');fog.use_nodes=True;n=fog.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');vol=n.new('ShaderNodeVolumePrincipled');vol.inputs['Density'].default_value=.006;vol.inputs['Color'].default_value=(.22,.28,.5,1);vol.inputs['Anisotropy'].default_value=.2;fog.node_tree.links.new(vol.outputs['Volume'],out.inputs['Volume'])
box('Atmosphere • skyline haze',(0,32,18),(115,65,42),fog)
cloud=bpy.data.materials.new('City • procedural storm clouds');cloud.use_nodes=True;n=cloud.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');vol=n.new('ShaderNodeVolumePrincipled');vol.inputs['Color'].default_value=(.19,.22,.36,1)
noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=3.5;noise.inputs['Detail'].default_value=4
ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.45;ramp.color_ramp.elements[0].color=(0,0,0,1);ramp.color_ramp.elements[1].position=.7;ramp.color_ramp.elements[1].color=(.11,.11,.11,1)
cloud.node_tree.links.new(noise.outputs['Fac'],ramp.inputs[0]);cloud.node_tree.links.new(ramp.outputs[0],vol.inputs['Density']);cloud.node_tree.links.new(vol.outputs[0],out.inputs['Volume'])
box('Storm clouds • distant canopy',(0,34,51),(140,55,24),cloud)

camera_data=bpy.data.cameras.new('City • hero camera');camera=bpy.data.objects.new('City • hero camera',camera_data);current.objects.link(camera)
camera.location=(23,-48,4.0);target=Vector((0,0,25));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera_data.lens=28;camera_data.clip_end=300;scene.camera=camera
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=850;scene.render.resolution_y=1250;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(ROOT/'preview.png');scene.render.film_transparent=False
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=-.8
compositor=bpy.data.node_groups.new('City • cinematic neon bloom','CompositorNodeTree')
compositor.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
scene.compositing_node_group=compositor
n=compositor.nodes;layers=n.new('CompositorNodeRLayers');layers.scene=scene;glare=n.new('CompositorNodeGlare');glare.inputs['Type'].default_value='Fog Glow';glare.inputs['Quality'].default_value='High';glare.inputs['Threshold'].default_value=1.5
out=n.new('NodeGroupOutput');compositor.links.new(layers.outputs['Image'],glare.inputs['Image']);compositor.links.new(glare.outputs['Image'],out.inputs['Image'])
bpy.context.view_layer.update()
for a in bpy.context.screen.areas:
    if a.type=='VIEW_3D':
        a.spaces.active.region_3d.view_perspective='CAMERA';a.spaces.active.overlay.show_overlays=False;a.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'cyber-city.blend'))
result={'scene':scene.name,'objects':len(scene.objects),'collections':list(collections),'blend_file':bpy.data.filepath,'billboard_images':9}
