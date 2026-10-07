"""Thin luminous 02/03 wall signage beside the two category portals."""
import math
import bpy


def cubic(a,b,c,d,steps=14):
    return [tuple((1-t)**3*a[j]+3*(1-t)**2*t*b[j]+3*(1-t)*t*t*c[j]+t**3*d[j] for j in range(2))
            for t in [index/steps for index in range(steps+1)]]


def zero():
    points=[]
    for x,z,start in ((.18,.58,0),(-.18,.58,90),(-.18,-.58,180),(.18,-.58,270)):
        points.extend((x+.27*math.cos(math.radians(start+angle)),z+.27*math.sin(math.radians(start+angle))) for angle in range(0,91,6))
    return points+[points[0]]


def digit(number):
    if number==2:
        return cubic((-.43,.52),(-.43,.94),(.43,.94),(.43,.48))+cubic((.43,.48),(.43,.14),(-.43,-.06),(-.43,-.44))[1:]+[(-.43,-.85),(.45,-.85)]
    return cubic((-.43,.65),(-.12,1.02),(.43,.97),(.43,.43))+cubic((.43,.43),(.43,.13),(.15,.02),(-.12,.02))[1:]+cubic((-.12,.02),(.20,.02),(.45,-.10),(.45,-.45))[1:]+cubic((.45,-.45),(.45,-.99),(-.10,-1.02),(-.43,-.68))[1:]


def configure_category_wall_numbers(scene):
    name='Hallway / category wall-number light'
    material=bpy.data.materials.get(name)
    if material is None:
        material=bpy.data.materials.new(name);material.use_nodes=True
        nodes,links=material.node_tree.nodes,material.node_tree.links;nodes.clear()
        output=nodes.new('ShaderNodeOutputMaterial');emission=nodes.new('ShaderNodeEmission')
        emission.inputs['Color'].default_value=(.82,.82,.82,1);emission.inputs['Strength'].default_value=2.6
        links.new(emission.outputs[0],output.inputs['Surface'])
    for root in [obj for obj in scene.objects if obj.get('hallway_category_gate')]:
        number=2 if root['hallway_category_gate']=='academic' else 3
        paths=[]
        for x,shape in ((-4.13,zero()),(-2.97,digit(number))):
            paths.append([(x+px,-.16,2.65+pz) for px,pz in shape])
        paths.extend([[(-3.55,-.16,3.99),(-3.55,-.16,4.58)],
                      [(-3.69,-.16,1.39),(-3.41,-.16,1.39)]])
        for z in (1.05,.92,.79):
            paths.append([(-3.55+.009*math.cos(index*math.tau/12),-.16,z+.009*math.sin(index*math.tau/12)) for index in range(13)])
        name=f'Category {number:02d} / luminous wall number and accents'
        obj=scene.objects.get(name)
        if obj is None:
            data=bpy.data.curves.new(name,'CURVE');obj=bpy.data.objects.new(name,data)
            root.users_collection[0].objects.link(obj);obj.parent=root
        data=obj.data
        for spline in list(data.splines):
            data.splines.remove(spline)
        data.dimensions='3D';data.bevel_depth=.005;data.bevel_resolution=0;data.resolution_u=1
        data.materials.clear();data.materials.append(material)
        for path in paths:
            spline=data.splines.new('POLY');spline.points.add(len(path)-1)
            for point,co in zip(spline.points,path):
                point.co=(*co,1)
        obj['hallway_category_id']=root['hallway_category_gate']
        obj['hallway_category_role']='categoryFrame'
        obj['hallway_category_wall_number']=f'{number:02d}'
    scene.view_layers[0].update()
