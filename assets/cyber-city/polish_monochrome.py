"""Dim architectural lines and thin foliage dots in a generated mono scene."""
import random
import bpy

scene=bpy.context.scene
if not scene.name.startswith('MONO /'):
    raise RuntimeError('Activate the monochrome scene first.')
for i,value in enumerate([.05,.15,.45,1.0]):
    material=bpy.data.materials[f'Mono • Gray level {i}'];node=material.node_tree.nodes.get('Emission');node.inputs['Color'].default_value=(value,value,value,1);material.diffuse_color=(value,value,value,1)
for i,value in enumerate([.015,.045,.12,.25]):
    material=bpy.data.materials.new(f'Mono • Wire gray level {i}');material.use_nodes=True;nodes=material.node_tree.nodes;nodes.clear()
    out=nodes.new('ShaderNodeOutputMaterial');emission=nodes.new('ShaderNodeEmission');emission.inputs['Color'].default_value=(value,value,value,1);emission.inputs['Strength'].default_value=1;material.node_tree.links.new(emission.outputs[0],out.inputs[0])
    group=next(g for g in bpy.data.node_groups if g.name.startswith('Mono • Wires') and g.name.endswith(f'Gray level {i}'))
    group.nodes.get('Set Material').inputs['Material'].default_value=material
rng=random.Random(391)
for obj in scene.objects:
    if obj.type!='MESH':continue
    if obj.name in ['Mono • 03 Sky garden • particles 2','Mono • 07 Street life • particles 2']:
        old=obj.data
        selected=[i for i in range(len(old.vertices)) if rng.random()<35/120]
        vertices=[tuple(old.vertices[i].co) for i in selected]
        radii=[old.attributes['radius'].data[i].value*.5 for i in selected]
        mesh=bpy.data.meshes.new(old.name+' • sparser');mesh.from_pydata(vertices,[],[]);mesh.update()
        attribute=mesh.attributes.new('radius','FLOAT','POINT');attribute.data.foreach_set('value',radii);obj.data=mesh
    elif obj.name=='Mono • 07 Street life • particles 3':
        for item in obj.data.attributes['radius'].data:item.value*=.72
floor=bpy.data.materials['Mono • obsidian floor'].node_tree.nodes.get('Principled BSDF')
floor.inputs['Base Color'].default_value=(.002,.002,.002,1);floor.inputs['Metallic'].default_value=1;floor.inputs['Roughness'].default_value=.19
scene.cycles.samples=64
bpy.context.view_layer.update()
result={'style':'thin dim outlines, sparse foliage, bright human particles, dark floor','point_vertices':sum(len(o.data.vertices) for o in scene.objects if o.type=='MESH' and o.modifiers and o.modifiers[0].type=='NODES' and 'Points' in o.modifiers[0].node_group.name)}
