"""Opaque monochrome hero tower, grayscale displays, and selective edge lighting.

Run in the traffic-polished city. Only hero-tower layers are changed; the rest
of the city and every animated root remain in their existing style.
"""
import math
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path('/home/damienckj/Documents/damien-portfolio/assets/cyber-city')
scene=bpy.context.scene
if scene.name!='MONO / Wire & Particle City':raise RuntimeError('Open the traffic-polished city.')
with bpy.data.libraries.load(str(ROOT/'cyber-city-walkthrough.blend'),link=False) as (available,loaded):
    loaded.scenes=['NEON / Kaze Megacity']
source=loaded.scenes[0]
source.frame_set(1)
collection=bpy.data.collections.new('Hero tower • Solid monochrome facade & displays');scene.collection.children.link(collection)

def gray(name,value):
    material=bpy.data.materials.new('Hero • '+name);material.use_nodes=True;nodes=material.node_tree.nodes;nodes.clear()
    out=nodes.new('ShaderNodeOutputMaterial');emission=nodes.new('ShaderNodeEmission');emission.inputs['Color'].default_value=(value,value,value,1);emission.inputs['Strength'].default_value=1
    material.node_tree.links.new(emission.outputs[0],out.inputs[0]);material.diffuse_color=(value,value,value,1);return material

facade=[gray('Shadow black',.005),gray('Graphite wall',.014),gray('Lit gray facets',.032)]
trim=gray('White architectural panels',.10)
window=gray('Monochrome occupied windows',.18)
bright=gray('Architectural light',1)
template=next(group for group in bpy.data.node_groups if group.name.startswith('Mono • Wires'))
glow_group=template.copy();glow_group.name='Hero • light-emitting contours';glow_group.nodes.get('Set Material').inputs['Material'].default_value=bright

def add_mesh(name,mesh,matrix,kind='solid',materials=None):
    obj=bpy.data.objects.new(name,mesh);collection.objects.link(obj);obj.matrix_world=matrix;obj['city_render_kind']=kind
    mesh.materials.clear()
    for material in (materials or facade):mesh.materials.append(material)
    if kind=='solid':
        for poly in mesh.polygons:poly.material_index=2 if poly.normal.z>.4 else 1 if poly.normal.y<-.3 else 0
    return obj

def copy_solid(old):
    with bpy.context.temp_override(scene=source,view_layer=source.view_layers[0]):
        deps=bpy.context.evaluated_depsgraph_get();evaluated=old.evaluated_get(deps)
        mesh=bpy.data.meshes.new_from_object(evaluated,preserve_all_data_layers=True,depsgraph=deps)
    return add_mesh('Hero solid • '+old.name,mesh,old.matrix_world)

# Preserve the actual hollow lobby and its opening from the approved source.
names=['Megatower • central occupied volume','Crown • stepped upper block','Sky lounge • supporting tower','Sky lounge • lower saucer','Sky lounge • roof disc','Media cylinder • dark core','Media cylinder • curved glass']
for name in names:
    if name in source.objects:copy_solid(source.objects[name])
for obj in source.objects:
    if obj.type=='MESH' and obj.name.startswith(('Cantilever garden • slab','Crown • rooftop canopy')):copy_solid(obj)

def panel(name,points,material):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(points,[],[(0,1,2,3)]);mesh.update()
    obj=bpy.data.objects.new(name,mesh);collection.objects.link(obj);obj['city_render_kind']='solid';mesh.materials.append(material);return obj

# Sparse, filled window lights add cyberpunk architecture without restoring a grid.
for row,z in enumerate([4.8,8.3,12.9,17.6,22.2,26.8,31.4,36,40.6,45.2]):
    for col,x in enumerate([-5.6,-4.45,2.3,3.45,6.1]):
        if (row+col)%3==0:continue
        panel('Hero • luminous facade pane',[(x-.27,-5.52,z-.30),(x+.27,-5.52,z-.30),(x+.27,-5.52,z+.30),(x-.27,-5.52,z+.30)],window if (row+col)%4 else trim)
    for y in [-3.9,-1.5,1,3.5]:
        if (row+int(y))%3==0:continue
        panel('Hero • right facade pane',[(7.14,y-.3,z-.3),(7.14,y+.3,z-.3),(7.14,y+.3,z+.3),(7.14,y-.3,z+.3)],window)

# Replace only main-media particle layers. Distant advertising keeps its old style.
for obj in list(scene.objects):
    if obj.name.startswith('Mono • 01 Megatower • particles') or obj.name.startswith('Mono • 02 Neon media • particles') or obj.name=='Mono • 03 Sky garden • particles 1':
        obj.hide_render=True;obj.hide_set(True)
for name in ['Clean outlines • Primary tower silhouette','Clean outlines • Major structure']:
    obj=scene.objects.get(name)
    if obj:
        obj['city_render_kind']='glow';obj.modifiers[0].node_group=glow_group

def edge_mesh(name,segments):
    vertices=[];edges=[]
    for a,b in segments:
        index=len(vertices);vertices.extend([tuple(a),tuple(b)]);edges.append((index,index+1))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,edges,[]);mesh.update()
    attr=mesh.attributes.new('radius','FLOAT','POINT');attr.data.foreach_set('value',[.016]*len(vertices))
    obj=bpy.data.objects.new(name,mesh);collection.objects.link(obj);obj['city_render_kind']='glow';modifier=obj.modifiers.new('Lit frame','NODES');modifier.node_group=glow_group

display_names=[
    'KAZE • cyborg campaign • LED display',
    'Clean mobility campaign • LED display','KAZE INDUSTRIES • rooftop monument • LED display',
    'Curved LED • nexus','Curved LED • portal','Curved LED • landscape','Curved LED • arasaka',
]
display_count=0
for name in display_names:
    old=source.objects.get(name)
    if not old:continue
    original=old.data.materials[0]
    image=next(node.image for node in original.node_tree.nodes if node.type=='TEX_IMAGE' and node.image)
    file=Path(image.filepath).name
    if file=='portrait.png' and (ROOT/'banner-artwork/portrait-source.png').is_file():
        file='portrait.jpg'
    if file=='landscape.png' and (ROOT/'banner-artwork/selangor-source.png').is_file():
        file='selangor.jpg'
    if file=='portal.png' and (ROOT/'banner-artwork/black-hole-source.png').is_file():
        file='black-hole.jpg'
    if file=='drive.png' and (ROOT/'banner-artwork/drive-the-next-horizon-source.png').is_file():
        file='drive-the-next-horizon.jpg'
    if file=='nexus.png' and (ROOT/'banner-artwork/shaping-a-brighter-tomorrow-source.png').is_file():
        file='shaping-a-brighter-tomorrow.jpg'
    texture=bpy.data.images.load(str(ROOT/'textures-monochrome'/file),check_existing=True);texture.pack()
    material=bpy.data.materials.new('Hero display • '+file);material.use_nodes=True;nodes=material.node_tree.nodes;nodes.clear()
    out=nodes.new('ShaderNodeOutputMaterial');emission=nodes.new('ShaderNodeEmission');emission.inputs['Strength'].default_value=.9;tex=nodes.new('ShaderNodeTexImage');tex.image=texture
    material.node_tree.links.new(tex.outputs['Color'],emission.inputs['Color']);material.node_tree.links.new(emission.outputs[0],out.inputs[0])
    mesh=old.data.copy();obj=add_mesh('Hero display • '+name,mesh,old.matrix_world,'screen',[material]);obj['city_texture']=file
    # Clean outside boundaries only; curved display subdivisions remain invisible.
    counts={}
    for poly in mesh.polygons:
        for key in poly.edge_keys:counts[tuple(sorted(key))]=counts.get(tuple(sorted(key)),0)+1
    segments=[tuple(old.matrix_world@mesh.vertices[index].co for index in edge.vertices) for edge in mesh.edges if counts.get(tuple(sorted(edge.vertices)))==1]
    edge_mesh('Hero glow • '+name,segments);display_count+=1

scene.frame_set(1);scene.view_layers[0].update()
output=ROOT/'monochrome-city-solid-tower.blend'
bpy.data.libraries.write(str(output),{scene},fake_user=False,compress=True)
result={'file':str(output),'solid_objects':sum(1 for o in collection.objects if o.get('city_render_kind')=='solid'),'monochrome_displays':display_count,'scope':'hero tower only; camera, traffic, lobby, and surrounding buildings preserved'}
