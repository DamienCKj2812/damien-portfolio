"""Finish the Blender-only four-level interactive design and review renders."""
import json
import math
import textwrap
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'kaze-elevator-entrance.blend'))
scene=bpy.context.scene
scene.name='KAZE / Four-level elevator review'
levels=[
    ('about','ABOUT ME','Meet Damien: my interests, my approach to building software, and the ideas behind my work.'),
    ('skills','SKILLS','Explore the languages, frameworks, and development tools in my toolkit.'),
    ('projects','PROJECTS','Discover what I am building, the problems each project explores, and the technologies behind it.'),
    ('experience','EXPERIENCE & EDUCATION','Follow my learning and professional journey through education, hands-on experience, and key milestones.'),
]
black=bpy.data.materials['Elevator / Recessed black glass'].copy()
black.name='Elevator / Matte holographic dialog'
black.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.8
black.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value=0
white=bpy.data.materials['Elevator / Silver lettering']
edge=bpy.data.materials['Elevator / Silver hairline']
glow=bpy.data.materials['Elevator / White perimeter lighting']


def link(name,data,col):
    obj=bpy.data.objects.new('Elevator / '+name,data)
    col.objects.link(obj)
    return obj


def rectangle(name,x0,x1,z0,z1,y,mat,col):
    curve=bpy.data.curves.new(name,'CURVE')
    curve.dimensions='3D'
    curve.bevel_depth=.0015
    curve.bevel_resolution=1
    spline=curve.splines.new('POLY')
    coords=[(x0,y,z0),(x1,y,z0),(x1,y,z1),(x0,y,z1),(x0,y,z0)]
    spline.points.add(4)
    for p,xyz in zip(spline.points,coords): p.co=(*xyz,1)
    curve.materials.append(mat)
    return link(name,curve,col)


def text(name,body,pos,size,col,align='LEFT'):
    curve=bpy.data.curves.new(name,'FONT')
    curve.body=body
    curve.size=size
    curve.align_x=align
    curve.align_y='TOP_BASELINE'
    curve.space_line=1.35
    curve.space_character=1.08
    curve.materials.append(white)
    obj=link(name,curve,col)
    obj.location=pos
    obj.rotation_euler.x=math.pi/2
    return obj


for index,(key,title,description) in enumerate(levels):
    col=bpy.data.collections.new('Elevator / Dialog / '+key)
    scene.collection.children.link(col)
    mesh=bpy.data.meshes.new('Dialog plate '+key)
    mesh.from_pydata([(-.89,1.59,1.17),(.49,1.59,1.17),(.49,1.59,2.22),(-.89,1.59,2.22)],[],[(0,1,2,3)])
    mesh.materials.append(black)
    plate=link('Floating dialog '+key,mesh,col)
    plate['level_id']=key
    plate['description']=description
    mod=plate.modifiers.new('Physical glass thickness','SOLIDIFY')
    mod.thickness=.014
    rectangle('Dialog outer border '+key,-.89,.49,1.17,2.22,1.58,edge,col)
    rectangle('Dialog inner border '+key,-.86,.46,1.20,2.19,1.578,edge,col)
    text('Dialog eyebrow '+key,f'LEVEL {index+1:02} / DESTINATION PREVIEW',(-.78,1.572,2.105),.025,col)
    heading=title.replace(' & ',' &\n') if key=='experience' else title
    text('Dialog title '+key,heading,(-.78,1.571,1.985),.060 if key=='experience' else .079,col)
    body_z=1.745 if key=='experience' else 1.805
    text('Dialog description '+key,textwrap.fill(description,width=42),(-.78,1.57,body_z),.036,col)
    rectangle('Dialog continue placeholder '+key,-.78,.04,1.26,1.39,1.565,edge,col)
    text('Dialog level action '+key,'EXPLORE THIS LEVEL  >',(-.70,1.56,1.345),.031,col)
    rectangle('Dialog close button '+key,.10,.38,1.26,1.39,1.565,edge,col)['interaction']='close-level-dialog'
    text('Dialog close label '+key,'CLOSE',(.24,1.56,1.345),.031,col,'CENTER')['interaction']='close-level-dialog'
    # Matching selected-floor outline, attached to each dialog state.
    curve=bpy.data.curves.new('Selected floor border '+key,'CURVE')
    curve.dimensions='3D'
    curve.bevel_depth=.0025
    z=1.48+index*.13
    spline=curve.splines.new('POLY')
    spline.points.add(4)
    for p,xyz in zip(spline.points,[(1.238,1.68,z-.06),(1.238,1.16,z-.06),(1.238,1.16,z+.06),(1.238,1.68,z+.06),(1.238,1.68,z-.06)]): p.co=(*xyz,1)
    curve.materials.append(glow)
    link('Selected floor highlight '+key,curve,col)

data=bpy.data.cameras.new('Dialog review camera')
cam=bpy.data.objects.new('Elevator / Dialog review camera',data)
scene.collection.objects.link(cam)
cam.location=(-.30,-1.15,1.70)
cam.rotation_euler=(Vector((.12,2.2,1.73))-cam.location).to_track_quat('-Z','Y').to_euler()
data.lens=24
data.clip_start=.025
scene.camera=cam
scene.render.resolution_x=1200
scene.render.resolution_y=1100
scene.cycles.samples=32
text_block=bpy.data.texts.new('KAZE_Elevator_Controls.py')
controls=(ROOT/'elevator_controls.py').read_text()
text_block.write(controls)
namespace={'__name__':'__main__'}
exec(compile(controls,'KAZE_Elevator_Controls.py','exec'),namespace)
show_level=namespace['show_level']
show_level(scene,'about')
scene['floor_picking_enabled']=False
scene['review_instructions']='Run KAZE_Elevator_Controls.py in the Text Editor. Sidebar > KAJU Elevator. Enable floor picking to click the four floor meshes.'
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.shading.type='MATERIAL'
scene.render.filepath=str(ROOT/'dialog-about.png')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'kaze-elevator-interactive.blend'))
for key,_,_ in levels:
    show_level(scene,key)
    scene.render.filepath=str(ROOT/f'dialog-{key}.png')
    bpy.ops.render.render(write_still=True)
show_level(scene,'about')
(ROOT/'elevator-levels.json').write_text(json.dumps({
    'source':'kaze-elevator-interactive.blend',
    'levels':[{'id':key,'number':i+1,'title':title,'description':description,'button':'Elevator / Level button '+key,'dialog_collection':'Elevator / Dialog / '+key} for i,(key,title,description) in enumerate(levels)],
    'blender_controls':'KAZE_Elevator_Controls.py (embedded Text datablock)',
    'status':'Four browser destinations: About office, Skills gallery, Projects hallway, and Timeline observatory.'
},indent=2)+'\n')
