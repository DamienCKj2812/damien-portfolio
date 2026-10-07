"""Clean black ground and subtle interior occlusion for the reference style."""
import bpy

scene=bpy.context.scene
if not scene.name.startswith('MONO /'):
    raise RuntimeError('Activate the monochrome scene first.')
floor=bpy.data.materials['Mono • obsidian floor'];floor.use_nodes=True;n= floor.node_tree.nodes;n.clear()
out=n.new('ShaderNodeOutputMaterial');black=n.new('ShaderNodeEmission');black.inputs['Color'].default_value=(0,0,0,1);black.inputs['Strength'].default_value=0;floor.node_tree.links.new(black.outputs[0],out.inputs[0])
source=bpy.data.scenes['NEON / Kaze Megacity']
col=next(c for c in scene.collection.children if c.name=='Mono • 09 Lobby • blockout')
for name in ['Lobby • left wall','Lobby • right wall','Lobby • back wall / future design area','Lobby • ceiling']:
    old=source.objects.get(name)
    if old:
        obj=old.copy();obj.data=old.data.copy();obj.name='Mono backing • '+name;col.objects.link(obj);obj.data.materials.clear();obj.data.materials.append(floor);obj.scale*=.998
bpy.context.view_layer.update()
result={'ground':'unlit black','interior':'fine lines and particles with black wall backings','backings':4}
