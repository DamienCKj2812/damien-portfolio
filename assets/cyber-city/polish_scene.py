"""Refinement pass; run once after build_scene.py in the new city scene."""
import bpy
from pathlib import Path
from mathutils import Vector

ROOT=Path('/home/damienckj/Documents/damien-portfolio/assets/cyber-city')
scene=bpy.context.scene
if not scene.name.startswith('NEON / Kaze Megacity'):
    raise RuntimeError('Activate the generated city scene before polishing.')

# Pull terraces off the large advertising face and toward the left edge.
for obj in scene.objects:
    if obj.name.startswith('Cantilever garden • slab'):
        obj.scale.x=.26;obj.location.x=-7.45
    if obj.name.startswith(('Garden • luminous underside','Garden • glass rail','Garden • underside support')):
        for spline in obj.data.splines:
            for p in spline.points:p.co.x=-7.45+(p.co.x+1)*.26
garden=bpy.data.collections['03 Sky garden']
for obj in garden.objects:
    if obj.name.startswith('Tree • leafy crown') and obj.location.y < -5:
        obj.location.x=-7.45+(obj.location.x+1)*.26
        obj.scale *= .75
    elif obj.type=='CURVE' and obj.name.startswith(('Tree • trunk','Tree • branch')):
        if obj.data.splines[0].points[0].co.y < -5:
            for spline in obj.data.splines:
                for p in spline.points:p.co.x=-7.45+(p.co.x+1)*.26

# Planter meshes were batched; move their coordinates, but keep other batched details.
for obj in garden.objects:
    if obj.type=='MESH' and obj.name.startswith('Batched details'):
        for v in obj.data.vertices:
            if v.co.y < -6.5 and v.co.z>10:v.co.x=-7.45+(v.co.x+1)*.26

# No sky/backdrop: preserve environmental illumination, render transparent.
scene.objects['Storm clouds • distant canopy'].hide_render=True
scene.objects['Atmosphere • skyline haze'].hide_render=True
world=scene.world;nodes=world.node_tree.nodes;nodes.clear()
out=nodes.new('ShaderNodeOutputWorld');bg=nodes.new('ShaderNodeBackground');bg.inputs['Strength'].default_value=.65
bg.inputs['Color'].default_value=(.025,.04,.085,1)
world.node_tree.links.new(bg.outputs[0],out.inputs[0])
scene.render.film_transparent=True
scene.render.image_settings.color_mode='RGBA'

# Window strips should read as occupied rooms, rather than flat white squares.
for name,strength in [('City • Warm occupied offices',.85),('City • Cool occupied offices',.7),('City • Warm architectural lighting',2.0)]:
    bpy.data.materials[name].node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=strength
bpy.data.materials['City • atmospheric blue haze'].node_tree.nodes.get('Principled Volume').inputs['Density'].default_value=.0035
wet=bpy.data.materials['City • Wet reflective plaza'];wet.node_tree.nodes.get('Noise Texture').inputs['Scale'].default_value=22
wet.node_tree.nodes.get('Bump').inputs['Strength'].default_value=.4
wet.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.19

# Closer, lower viewpoint makes the primary building dominate the composition.
cam=scene.camera;cam.location=(18,-41,2.6);cam.rotation_euler=(Vector((0,0,25))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=27
scene.objects['Aircar 01 • foreground commuter'].location=(-11,-14,13)
scene.objects['Aircar 02 • right approaching'].location=(13,-9,12)

# Soft vehicle fill reveals the sculpted bodies above the emissive thrusters.
col=bpy.data.collections['08 Atmosphere & lighting']
for name,loc,color in [('Aircar 01 • fill',(-10,-17,16),(.15,.45,1)),('Aircar 02 • fill',(13,-12,15),(1,.06,.25))]:
    data=bpy.data.lights.new(name,'AREA');data.energy=180;data.color=color;data.size=4
    obj=bpy.data.objects.new(name,data);col.objects.link(obj);obj.location=loc;obj.rotation_euler=(Vector((loc[0],loc[1]+3,loc[2]-3))-obj.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=850;scene.render.resolution_y=1250;scene.cycles.samples=48
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'cyber-city.blend'))
result={'scene':scene.name,'objects':len(scene.objects),'refinements':['unobstructed central portrait','left-edge gardens','transparent background','balanced windows','closer framing','vehicle fill lights']}
