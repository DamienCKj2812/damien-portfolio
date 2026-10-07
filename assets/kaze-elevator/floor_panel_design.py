"""Reference-style chamfered switches, native typography and panel details."""
import math

import bpy
from mathutils import Matrix, Vector

WIDTH, HEIGHT, CORNER = .565, .125, .014
BASE_Z, PITCH = 1.60, .15
CENTER_Y, FACE_X = 1.42, 1.253


def apply_panel_design(scene, levels):
    controls = bpy.data.collections.get('Elevator / Controls')
    assert controls, 'Missing native Controls collection.'
    removable = ('Elevator / Level button ', 'Elevator / Level button border ',
                 'Elevator / Level number ', 'Elevator / Level label ',
                 'Elevator / Level divider ', 'Elevator / Level chevron ',
                 'Elevator / Selected floor highlight', 'Elevator / Operating panel black glass',
                 'Elevator / Control panel ', 'Elevator / Up indicator',
                 'Elevator / Current floor display', 'Elevator / Alarm button ring', 'Elevator / Alarm symbol')
    for obj in list(scene.objects):
        if obj.name == 'Elevator / Control panel brand mark' or any(c == controls for c in obj.users_collection) and obj.name.startswith(removable):
            bpy.data.objects.remove(obj, do_unlink=True)

    def material(name, value, emission=0, metallic=0, roughness=.4):
        mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        mat.diffuse_color = (value, value, value, 1)
        mat.use_nodes = True
        shader = mat.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Base Color'].default_value = mat.diffuse_color
        shader.inputs['Metallic'].default_value = metallic
        shader.inputs['Roughness'].default_value = roughness
        shader.inputs['Emission Color'].default_value = mat.diffuse_color
        shader.inputs['Emission Strength'].default_value = emission
        return mat

    glass = material('Elevator / Reference panel glass', .003, metallic=.45, roughness=.24)
    face = material('Elevator / Reference switch graphite', .010, metallic=.55, roughness=.32)
    rim = material('Elevator / Reference switch luminous rim', .80, emission=1.15)
    number = material('Elevator / Reference floor numbers', .91, emission=1.2)
    label = material('Elevator / Reference floor captions', .43, emission=1.1)
    divider = material('Elevator / Reference subtle divider', .16, emission=.8)

    def link(name, data):
        obj = bpy.data.objects.new('Elevator / '+name, data)
        controls.objects.link(obj)
        return obj

    def contour(w, h, cut):
        return [(-w/2+cut,-h/2),(w/2-cut,-h/2),(w/2,-h/2+cut),
                (w/2,h/2-cut),(w/2-cut,h/2),(-w/2+cut,h/2),
                (-w/2,h/2-cut),(-w/2,-h/2+cut)]

    def plate(name, x, y, z, w, h, depth, cut, mat):
        path = contour(w, h, cut)
        vertices = [(dx,-u,v) for dx in [-depth/2,depth/2] for u,v in path]
        faces = [tuple(range(8)), tuple(reversed(range(8,16)))]
        faces += [(i,i+8,(i+1)%8+8,(i+1)%8) for i in range(8)]
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(vertices, [], faces)
        mesh.materials.append(mat)
        mesh.update()
        obj = link(name, mesh)
        obj.location = (x,y,z)
        return obj

    def lines(name, paths, x, y, z, mat, radius=.0008):
        curve = bpy.data.curves.new(name, 'CURVE')
        curve.dimensions = '3D';curve.bevel_depth = radius;curve.bevel_resolution = 2
        for path in paths:
            spline = curve.splines.new('POLY')
            spline.points.add(len(path)-1)
            for point, (u,v) in zip(spline.points, path): point.co = (0,-u,v,1)
        curve.materials.append(mat)
        obj = link(name, curve)
        obj.location = (x,y,z)
        return obj

    def text(name, body, u, z, size, mat, align='LEFT', tracking=1.5):
        data = bpy.data.curves.new(name, 'FONT')
        data.body = body;data.align_x = align;data.align_y = 'CENTER'
        data.size = size;data.space_character = tracking;data.space_line = 1.45
        data.extrude = .0001;data.resolution_u = 8
        data.materials.append(mat)
        obj = link(name, data)
        obj.location = (1.242,CENTER_Y-u,z)
        obj.rotation_euler = Matrix(((0,-1,0),(0,0,1),(-1,0,0))).transposed().to_euler()
        return obj

    plate('Operating panel black glass',1.282,CENTER_Y,1.91,.64,1.63,.025,.005,glass)
    outer = contour(.64,1.63,.004)
    inner = contour(.607,1.60,.003)
    lines('Control panel outer border',[outer+[outer[0]]],1.264,CENTER_Y,1.91,divider)
    lines('Control panel inner border',[inner+[inner[0]]],1.262,CENTER_Y,1.91,divider,.0005)
    # Keep the status close to the top switch so it remains inside the focused
    # cabin view, rather than being cropped at the top of the tall panel.
    text('Current floor display','--',0,2.20,.065,number,align='CENTER',tracking=1.65)

    labels = {'about':'ABOUT ME','skills':'SKILLS','projects':'PROJECTS',
              'experience':'EXPERIENCE &\nEDUCATION'}
    for level in levels:
        z = BASE_Z+(level['number']-1)*PITCH
        key = level['id']
        button = plate('Level button '+key,FACE_X,CENTER_Y,z,WIDTH,HEIGHT,.012,CORNER,face)
        button['level_id'] = key;button['level_number'] = level['number']
        button['interaction'] = 'show-level-dialog'
        button['panel_corner_cut'] = CORNER
        path = contour(WIDTH,HEIGHT,CORNER)
        details = [lines('Level button border '+key,[path+[path[0]]],1.244,CENTER_Y,z,rim),
                   text('Level number '+key,f'{level["number"]:02}',-.242,z,.043,number,tracking=1.2),
                   text('Level label '+key,labels[key],-.094,z,.0205,label,tracking=1.65),
                   lines('Level divider '+key,[[(-.145,-.037),(-.145,.037)]],1.243,CENTER_Y,z,divider,.0006),
                   lines('Level chevron '+key,[[(.231,-.016),(.244,0),(.231,.016)]],1.242,CENTER_Y,z,number,.0008)]
        for detail in details: detail['level_id'] = key

    ring = [(.042*math.cos(i*math.tau/64),.042*math.sin(i*math.tau/64)) for i in range(65)]
    lines('Alarm button ring',[ring],1.248,CENTER_Y,1.335,rim,.0007)
    text('Alarm symbol','!',0,1.335,.045,number,align='CENTER')
    text('Control panel footer','A CLEANER\nBRIGHTER\nHUMAN FUTURE',0,1.235,.0125,label,align='CENTER',tracking=1.65)
    scene['floor_panel_design'] = 'Chamfered luminous switch frames; separated numbers/captions; chevrons; reference footer'
    return {level['id']: BASE_Z+(level['number']-1)*PITCH for level in levels}
