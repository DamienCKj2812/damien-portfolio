"""Raised entrance directory with a downward-facing, ceiling-mounted projector."""
import math
import json
from pathlib import Path
from mathutils import Vector


def configure_directory_board(scene):
    root=scene.objects['Entry / projects directory']
    # Local text faces -Y. Aim the whole assembly at the website's entrance
    # camera while retaining its wall-side position and the clear X=0 lane.
    root.rotation_euler.z=math.atan2(-root.location.x,root.location.y+6.95)
    root['display_facing']='entrance'
    backing=next(obj for obj in root.children if obj.name.endswith(' / black display'))
    unit=next(obj for obj in root.children if obj.get('holographic_projector'))
    identifier=next(obj for obj in root.children if obj.name.endswith(' / emitter identifier'))
    # Raise the complete card, preserving the typography/corner-bracket spacing.
    delta=3.575-backing.location.z
    for obj in root.children:
        if obj not in (unit,identifier):
            obj.location.z+=delta
    root['hallway_directory']=True
    root['directory_projector_position']='above / downward projection'
    backing['hallway_directory_face']=True
    unit.location=(0,-.90,5.86)
    unit.rotation_euler=(math.pi,0,0)
    identifier.location.z=5.59
    scene.view_layers[0].update()
    inverse=unit.matrix_basis.inverted()
    origin=Vector((0,-.45,.535))
    width=max(vertex.co.x for vertex in backing.data.vertices)-min(vertex.co.x for vertex in backing.data.vertices)
    bottom=2.0;height=3.15
    corners=[Vector((-width/2,-.06,bottom)),Vector((width/2,-.06,bottom)),
             Vector((width/2,-.06,bottom+height)),Vector((-width/2,-.06,bottom+height))]
    local_corners=[inverse @ corner for corner in corners]
    rays=next(obj for obj in unit.children if obj.name.endswith(' / projection frustum rays'))
    for spline,corner in zip(rays.data.splines,local_corners):
        spline.points[0].co=(*origin,1);spline.points[1].co=(*corner,1)
    field=next(obj for obj in unit.children if obj.type=='MESH' and 'subtle projected light field' in obj.name)
    for vertex,point in zip(field.data.vertices,[origin,*local_corners]):
        vertex.co=point
    field.data.update()
    direction=(inverse @ Vector((0,-.045,bottom+height/2))-origin).normalized()
    tangent=Vector((1,0,0));bitangent=direction.cross(tangent).normalized()
    lenses=sorted((obj for obj in unit.children if 'concentric luminous lens' in obj.name),key=lambda obj:obj.name)
    for lens,radius in zip(lenses,(.09,.15)):
        ring=[origin+radius*(math.cos(i*math.tau/32)*tangent+math.sin(i*math.tau/32)*bitangent) for i in range(32)]
        for spline,(a,b) in zip(lens.data.splines,zip(ring,ring[1:]+ring[:1])):
            spline.points[0].co=(*a,1);spline.points[1].co=(*b,1)
    scene.view_layers[0].update()
    content=json.loads((Path(__file__).resolve().parent/'projects.json').read_text())
    clients=[project for project in content['projects'] if project['section']=='client']
    bodies={
        'index':('01 / CURRENT CATEGORY',.105),
        'title':('C L I E N T\nR E A L  W O R L D',.165),
        'category':('CATEGORY 01 / CLIENT PROJECTS',.085),
        'summary':('\n'.join(project['title'].replace('\n',' ') for project in clients),.106),
        'stack':(f'{len(clients)} real-world projects\nWalk forward to explore',.10),
    }
    for suffix,(body,size) in bodies.items():
        obj=next(obj for obj in root.children if obj.name.endswith(' / '+suffix))
        obj.data.body=body;obj.data.size=size
        scene.view_layers[0].update()
        actual=max(point[0] for point in obj.bound_box)-min(point[0] for point in obj.bound_box)
        if actual>1.68:
            obj.data.size*=1.68/actual
    root['directory_title']='Client / Real-world Projects'
    root['directory_category']='client'
    return root
