"""Final foliage/framing pass; run once after detail_pass.py."""
import bpy
import random
from pathlib import Path
from mathutils import Vector

ROOT=Path('/home/damienckj/Documents/damien-portfolio/assets/cyber-city')
scene=bpy.context.scene
if not scene.name.startswith('NEON / Kaze Megacity'):
    raise RuntimeError('Activate the city scene first.')
random.seed(109)
# Replace oversized low-poly crown silhouettes with denser, smaller leaf clusters.
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1)
temp=bpy.context.object;foliage=temp.data;foliage.name='City • detailed leaf-cluster geometry'
foliage.materials.append(bpy.data.materials['City • Garden foliage lighter'])
for poly in foliage.polygons:poly.use_smooth=True
bpy.data.objects.remove(temp,do_unlink=True)
for col_name in ['03 Sky garden','07 Street life']:
    col=bpy.data.collections[col_name]
    old_crowns=[obj for obj in col.objects if obj.name.startswith('Tree • leafy crown')]
    for obj in old_crowns:
        obj.hide_render=True;obj.hide_set(True)
        sx,sy,sz=obj.scale
        for i in range(9):
            leaf=bpy.data.objects.new('Tree • detailed leaf cluster',foliage);col.objects.link(leaf)
            leaf.location=obj.location+Vector((random.uniform(-.8,.8)*sx,random.uniform(-.8,.8)*sy,random.uniform(-.7,.7)*sz))
            leaf.scale=(sx*random.uniform(.32,.55),sy*random.uniform(.32,.55),sz*random.uniform(.35,.6))
for obj in scene.objects:
    if obj.name.startswith('Left interchange'):obj.location.x+=6
vehicle=bpy.data.materials['City • Vehicle metallic midnight'].node_tree.nodes.get('Principled BSDF')
vehicle.inputs['Base Color'].default_value=(.055,.09,.17,1)
vehicle.inputs['Metallic'].default_value=.65
scene.camera.data.lens=28
scene.camera.rotation_euler=(Vector((0,0,23.5))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=900;scene.render.resolution_y=1350;scene.cycles.samples=64
scene.render.film_transparent=True;scene.render.image_settings.color_mode='RGBA';scene.render.filepath=str(ROOT/'preview.png')
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'cyber-city.blend'))
result={'scene':scene.name,'objects':len(scene.objects),'final_resolution':[900,1350],'background':'transparent'}
