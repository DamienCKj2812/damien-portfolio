"""Organic dot-only T-Rex conversion; the reconstruction guides never render."""
import bisect
import math
import random

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


def convert_to_dots(scene,collections,material,point_display,previous):
    root = scene.objects[previous['root']]
    approved = list(root.get('approved_dimensions_m',previous['dimensions_m']))
    root['approved_dimensions_m'] = approved
    rng = random.Random(1831)
    parent = collections['08']
    guides = bpy.data.collections.get('Gallery • T-Rex hidden dot sources')
    if guides is None:
        guides = bpy.data.collections.new('Gallery • T-Rex hidden dot sources')
        parent.children.link(guides)
    guides.hide_render = False; guides.hide_viewport = False
    for obj in list(root.children):
        if obj.type=='CURVE' or (obj.type=='MESH' and not obj.data.polygons):
            bpy.data.objects.remove(obj,do_unlink=True)
    sources = [o for o in root.children if o.type=='MESH' and o.data.polygons]
    if not any('organic chest transition' in o.name for o in sources):
        # A smooth overlapping volume joins the chest and neck after subdivision.
        n,rows = 24,14
        verts = []
        for row in range(rows+1):
            theta = row*math.pi/rows
            for j in range(n):
                a = j*math.tau/n
                verts.append((.62+.39*math.sin(theta)*math.cos(a),
                              .37*math.sin(theta)*math.sin(a),2.80+.60*math.cos(theta)))
        faces = [(i*n+j,(i+1)*n+j,(i+1)*n+(j+1)%n,i*n+(j+1)%n)
                 for i in range(rows) for j in range(n)]
        mesh = bpy.data.meshes.new('Gallery • T-Rex / organic chest transition')
        mesh.from_pydata(verts,[],faces)
        obj = bpy.data.objects.new(mesh.name,mesh); parent.objects.link(obj)
        obj.parent = root; obj['trex_surface'] = True
        sources.append(obj)
    if not root.get('organic_guides_prepared'):
        hinge = Vector((1.22,0,3.15))
        opening = Matrix.Translation(hinge) @ Matrix.Rotation(.24,4,'Y') @ Matrix.Translation(-hinge)
        for obj in sources:
            if 'open lower jaw' in obj.name or 'lower tooth' in obj.name:
                for vertex in obj.data.vertices:
                    vertex.co = opening @ vertex.co
            if 'raised neck' in obj.name:
                for vertex in obj.data.vertices:
                    vertex.co.y *= 1.22
            if obj.get('trex_surface') and 'organic chest transition' not in obj.name:
                smooth = obj.modifiers.new('Organic dot reconstruction guide','SUBSURF')
                smooth.levels = 2; smooth.render_levels = 2
        root['organic_guides_prepared'] = True
    for obj in sources:
        obj.hide_render = False; obj.hide_set(False)
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    meshes = []
    for obj in sources:
        evaluated = obj.evaluated_get(deps)
        mesh = evaluated.to_mesh(); mesh.calc_loop_triangles()
        verts = [obj.matrix_local @ vertex.co for vertex in mesh.vertices]
        triangles = [tuple(t.vertices) for t in mesh.loop_triangles]
        areas = []; normals = []
        for tri in triangles:
            a,b,c = (verts[i] for i in tri)
            cross = (b-a).cross(c-a)
            areas.append(max(cross.length/2,.0000001)); normals.append(cross.normalized())
        cumulative = []; total = 0
        for area in areas:
            total += area; cumulative.append(total)
        meshes.append({'name':obj.name,'verts':verts,'tris':triangles,'normals':normals,
                       'cumulative':cumulative,'area':total,
                       'lo':Vector([min(v[i] for v in verts) for i in range(3)]),
                       'hi':Vector([max(v[i] for v in verts) for i in range(3)]),
                       'bvh':BVHTree.FromPolygons(verts,triangles),
                       'feature':('tooth' in obj.name or 'claw' in obj.name)})
        evaluated.to_mesh_clear()
    organic = [m for m in meshes if not m['feature']]

    def sample(data):
        index = min(len(data['tris'])-1,bisect.bisect_left(data['cumulative'],rng.random()*data['area']))
        a,b,c = (data['verts'][i] for i in data['tris'][index])
        u,v = rng.random(),rng.random()
        if u+v>1:
            u,v = 1-u,1-v
        return a+u*(b-a)+v*(c-a),data['normals'][index]

    def exposed(p,own):
        for other in organic:
            if other is own or not all(other['lo'][i]<p[i]<other['hi'][i] for i in range(3)):
                continue
            nearest,normal,_,distance = other['bvh'].find_nearest(p)
            if nearest is not None and distance>.003 and (p-nearest).dot(normal)<-.002:
                return False
        # A small dark eye opening makes the dotted iris legible without solids.
        if abs(p.y)>.30 and ((p.x-1.48)/.090)**2+((p.z-3.62)/.082)**2<1:
            return False
        return True

    def surface_cloud(count,profile=False):
        points = []; attempts = 0
        weights = [m['area'] for m in organic]
        while len(points)<count and attempts<count*40:
            attempts += 1
            data = rng.choices(organic,weights=weights,k=1)[0]
            p,normal = sample(data)
            if not exposed(p,data):
                continue
            if profile and abs(normal.y)>.22:
                continue
            if not profile and normal.y<-.25 and rng.random()>.50:
                continue
            points.append(tuple(p+normal*.002))
        assert len(points)==count, 'Could not sample enough exposed dinosaur points.'
        return points

    body = surface_cloud(4800)
    profile = surface_cloud(850,True)
    details = []
    for data in meshes:
        if data['feature']:
            for _ in range(12 if 'tooth' in data['name'] else 18):
                p,normal = sample(data); details.append(tuple(p+normal*.001))
            # A few discrete points at the tip preserve pointed teeth/claws.
            details.append(tuple(min(data['verts'],key=lambda p:p.z) if 'upper tooth' in data['name']
                                 else max(data['verts'],key=lambda p:p.x)))
    features = []
    for side in [1]:
        for i in range(26):
            a = i*math.tau/26
            features.append((1.48+.100*math.cos(a),side*.423,3.62+.085*math.sin(a)))
        for i in range(8):
            a = i*math.tau/8
            features.append((1.48+.018*math.cos(a),side*.427,3.62+.018*math.sin(a)))
        for i in range(9):
            a = i*math.tau/9
            features.append((2.46+.030*math.cos(a),side*.319,3.43+.021*math.sin(a)))
    all_points = body+profile+details+features
    low = min(p[2] for p in all_points); high = max(p[2] for p in all_points)
    height = approved[2]
    def size_preserving(points):
        return [(x,y,(z-low)*height/(high-low)) for x,y,z in points]
    dot_mat = bpy.data.materials.get('Gallery • T-Rex white dot light')
    if dot_mat is None:
        dot_mat = material('T-Rex white dot light',.75,emission=1.3,roughness=.7)
    clouds = []
    for label,points,radius in [('organic body dots',body,.0082),('silhouette dots',profile,.0085),
                                ('teeth and claw dots',details,.0050),('eye and nostril dots',features,.0065)]:
        obj,tree = point_display('T-Rex / '+label,size_preserving(points),dot_mat,radius,'08')
        obj.parent = root
        obj['gallery_render_kind'] = 'points'; obj['point_radius'] = radius
        obj['trex_dots'] = True
        for node in tree.nodes:
            if node.bl_idname=='GeometryNodeMeshIcoSphere':
                node.inputs['Subdivisions'].default_value = 2
        clouds.append(obj)
    for obj in sources:
        for col in list(obj.users_collection):
            col.objects.unlink(obj)
        guides.objects.link(obj)
        obj['trex_guide'] = True; obj.hide_render = True; obj.hide_set(True)
    guides.hide_render = True; guides.hide_viewport = True
    # Mirror the profile to match the reference: head left, tail right.
    root.rotation_euler.z = math.pi+.18
    root['style'] = 'Dot-only organic reconstruction; no visible surfaces or wire curves'
    root['exhibit_role'] = 'White point-cloud T-Rex sculpture'
    root['export_mode'] = 'points_only'
    root['dots_only'] = True
    bpy.context.view_layer.update()
    # Retain the approved overall length after rounding the reconstruction.
    rotation = root.rotation_euler.to_matrix()
    def span_x(factor):
        values = [(rotation @ Vector((v.co.x*factor,v.co.y,v.co.z))).x
                  for obj in clouds for v in obj.data.vertices]
        return max(values)-min(values)
    low_factor,high_factor = .95,1.10
    for _ in range(18):
        factor = (low_factor+high_factor)/2
        if span_x(factor)<approved[0]:
            low_factor = factor
        else:
            high_factor = factor
    factor = (low_factor+high_factor)/2
    for obj in clouds:
        for vertex in obj.data.vertices:
            vertex.co.x *= factor
        obj.data.update()
    visible = [obj.matrix_world @ v.co for obj in clouds for v in obj.data.vertices]
    lo = [min(v[i] for v in visible) for i in range(3)]
    hi = [max(v[i] for v in visible) for i in range(3)]
    root['bounds_min'] = lo; root['bounds_max'] = hi
    assert all(not obj.data.polygons for obj in clouds)
    assert all(obj.hide_render for obj in sources)
    assert not any(o.type=='CURVE' and not o.hide_render for o in root.children)
    return {'root':root.name,'bounds_min':lo,'bounds_max':hi,
            'dimensions_m':[hi[i]-lo[i] for i in range(3)],
            'plinth_rect':previous['plinth_rect'],'particle_count':sum(len(o.data.vertices) for o in clouds),
            'style':'Dot-only organic T-Rex','visible_surface_meshes':0,'visible_wire_curves':0,
            'facing':'left / matching supplied dot reference'}
