"""Read-only native point/line/triangle exports for the authored destinations.

blender --background <room.blend> --python-exit-code 1 --python <this script> -- --level about|skills|projects|experience
"""
import argparse
import hashlib
import json
import math
import shutil
import sys
from array import array
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from public_content import public_content
parser = argparse.ArgumentParser()
parser.add_argument('--level', choices=['about', 'skills', 'projects', 'experience'], required=True)
parser.add_argument('--section', choices=['meeting'])
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
level = args.level
config = json.loads((ROOT / 'assets/journey/room-destinations.json').read_text())[level]
if args.section:
    assert level == 'projects', 'The meeting room belongs to Projects.'
    config = json.loads((ROOT / 'assets/project-hallway/meeting-room/room.json').read_text())
    level = 'project-meeting'
output = ROOT / 'public' / config['assetBase']
assert output.is_dir(), f'Missing package directory: {output}'
scene = bpy.context.scene
assert scene.objects.get(config['mainCamera']), 'Open the configured authored room.'
scene.frame_set(1)
scene.view_layers[0].update()


def shade(material):
    if not material:
        return .25, False, 1.0
    nodes = material.node_tree.nodes if material.use_nodes else []
    opacity = 1.0
    if any(n.type == 'BSDF_TRANSPARENT' for n in nodes):
        mix = next((n for n in nodes if n.type == 'MIX_SHADER'), None)
        opacity = mix.inputs[0].default_value if mix else 0.0
    for node in nodes:
        if node.type == 'EMISSION':
            strength = node.inputs['Strength'].default_value
            return sum(node.inputs['Color'].default_value[:3]) / 3 * strength, strength >= 2, opacity
        if node.type == 'BSDF_PRINCIPLED':
            strength = node.inputs['Emission Strength'].default_value
            value = sum(node.inputs['Base Color'].default_value[:3]) / 3
            return min(1.5, value * max(1, strength)), strength >= 2, opacity
    return sum(material.diffuse_color[:3]) / 3, False, opacity


def pose(camera):
    position, rotation, scale = camera.matrix_world.decompose()
    aspect = scene.render.resolution_x / scene.render.resolution_y
    fov = math.degrees(2 * math.atan(camera.data.sensor_width / (2 * camera.data.lens * aspect)))
    return {'position': list(position), 'quaternion': [rotation.x, rotation.y, rotation.z, rotation.w], 'fov': fov}


def moving_root(obj):
    ancestor = obj
    while ancestor:
        if ancestor.animation_data and ancestor.animation_data.action:
            # Articulated gallery limbs have their own keys under a moving
            # visitor. Bake the closest root's world pose, once, as flat actors.
            return ancestor
        ancestor = ancestor.parent
    return None


def project_root(obj):
    while obj:
        if obj.get('project_id') and obj.get('hallway_display'):
            return obj
        obj = obj.parent
    return None


def exhibit_root(obj):
    while obj:
        if obj.get('category') or obj.get('milestone_id') or obj.get('centre_exhibit_id') or obj.get('dots_only'):
            return obj
        obj = obj.parent
    return None


def exhibit_id(obj):
    if obj.get('milestone_id'):
        return obj['milestone_id']
    if obj.get('centre_exhibit_id'):
        return obj['centre_exhibit_id']
    if obj.get('dots_only'):
        return 'trex'
    return 'skill-' + obj.name.split('Exhibit ')[1].split(' / ')[0]


def portal_box(name, center, size):
    x, y, z = center
    a, b, c = [v / 2 for v in size]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([(x + dx*a, y + dy*b, z + dz*c) for dx,dy,dz in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]], [], [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    obj['browser_portal_mask'] = True


# Close only the integration copy's cutaway front around the cabin-sized portal.
# The authored room remains unchanged. Local +Y points away from the elevator.
y = config['entranceAnchor'][1] - .02
side_width = (config['width'] - 2.6) / 2
if not scene.get('Authored entry surround'):
    for sign in [-1, 1]:
        portal_box('Browser / destination entry surround', (sign * (1.3 + side_width/2), y, config['height']/2), (side_width, .10, config['height']))
    portal_box('Browser / destination entry header', (0, y, (3.2 + config['height'])/2), (2.6, .10, config['height'] - 3.2))
scene.view_layers[0].update()
objects = [o for o in scene.objects if o.type in ['MESH','CURVE','FONT'] and not o.hide_render and not any(c.hide_render for c in o.users_collection)]
roots = sorted({root for obj in objects if (root := moving_root(obj))}, key=lambda o: o.name)
indices = {root: i + 1 for i, root in enumerate(roots)}
shapes = {}
for obj in objects:
    if obj.type == 'MESH' and obj.data.shape_keys:
        root = moving_root(obj)
        assert root and len(obj.data.shape_keys.key_blocks) <= 5
        shapes[root] = obj
buffers = {}
logo_textures = {}
morph_buffers = {}
statistics = {'points': 0, 'lineSegments': 0, 'glowSegments': 0, 'solidTriangles': 0}
deps = bpy.context.evaluated_depsgraph_get()
for obj in objects:
    root = moving_root(obj)
    actor = indices.get(root, 0)
    transform = root.matrix_world.inverted() @ obj.matrix_world if root else obj.matrix_world
    project = project_root(obj)
    exhibit = exhibit_root(obj)
    role = 'project' if project and obj.name.endswith(' / black display') else 'contact' if obj.name == 'Office • Name card / contact face' else ''
    identity = project['project_id'] if role == 'project' else 'card' if role == 'contact' else ''
    if level=='projects' and obj.get('hallway_directory_face'):
        role='directory';identity='directory'
    if level == 'about' and obj.get('office_entry_door'):
        role = 'officeDoor';identity = 'office-entry'
    if level == 'about' and obj.get('office_screen_map'):
        role = 'officeScreenMap';identity = 'malaysia'
    if level == 'about' and obj.name.startswith('Office • Printer /'):
        role = 'printer';identity = 'printer'
    if level == 'projects' and obj.get('ceiling_role') == 'wave_rib':
        role = 'ceilingRib';identity = 'wave-ribs'
    elif level == 'projects' and obj.get('ceiling_role') == 'light_rail':
        role = 'ceilingLight';identity = 'ceiling-lights'
    if level == 'projects' and obj.get('hallway_category_role'):
        role = obj['hallway_category_role'];identity = obj['hallway_category_id']
    if exhibit and (obj.name.endswith((' / content surface', ' / black floating card')) or exhibit.get('dots_only') or exhibit.get('centre_exhibit_id')):
        role = 'exhibit';identity = exhibit_id(exhibit)
    modifier = next((m for m in obj.modifiers if m.type == 'NODES'), None)
    if obj.type == 'MESH' and not obj.data.polygons and len(obj.data.vertices):
        assert modifier, f'Point source without Geometry Nodes: {obj.name}'
        material_node = next(n for n in modifier.node_group.nodes if n.bl_idname == 'GeometryNodeSetMaterial')
        radius_node = next((n for n in modifier.node_group.nodes if n.bl_idname == 'GeometryNodeMeshIcoSphere'), None)
        radius = radius_node.inputs['Radius'].default_value if radius_node else .005
        radii = obj.data.attributes.get('radius')
        luminance, _, _ = shade(material_node.inputs['Material'].default_value)
        key = (actor, 'points', role, identity, 1.0)
        values = buffers.setdefault(key, array('f'))
        scale = max(abs(v) for v in transform.to_scale())
        basis = obj.data.shape_keys.key_blocks[0].data if obj.data.shape_keys else obj.data.vertices
        for i, vertex in enumerate(basis):
            values.extend((*(transform @ vertex.co), (radii.data[i].value if radii else radius)*scale, luminance))
        if obj.data.shape_keys:
            assert len(values) == len(basis)*5, 'One deforming point source per actor is required.'
            for shape in list(obj.data.shape_keys.key_blocks)[1:]:
                delta = array('f')
                for a, b in zip(basis, shape.data):
                    delta.extend(transform.to_3x3() @ (b.co - a.co))
                morph_buffers.setdefault(key, []).append(delta)
        statistics['points'] += len(basis)
    elif obj.type == 'CURVE':
        luminance, glow, _ = shade(obj.data.materials[0] if obj.data.materials else None)
        kind = 'glow' if glow else 'lines'
        values = buffers.setdefault((actor, kind, role, identity, 1.0), array('f'))
        for spline in obj.data.splines:
            points = [Vector(p.co[:3]) for p in spline.points] if spline.type != 'BEZIER' else [p.co for p in spline.bezier_points]
            if spline.use_cyclic_u and points:
                points.append(points[0])
            for a, b in zip(points, points[1:]):
                for p in [a, b]:
                    values.extend((*(transform @ p), luminance))
                statistics['glowSegments' if glow else 'lineSegments'] += 1
    elif obj.get('milestone_logo'):
        texture = obj['milestone_logo_texture']
        logo_textures[texture] = ROOT / 'assets/timeline-observatory' / texture
        mesh = obj.data
        mesh.calc_loop_triangles()
        values = buffers.setdefault((actor, 'screen', 'milestoneLogo', texture, 1.0), array('f'))
        for triangle in mesh.loop_triangles:
            for vertex, loop in zip(triangle.vertices, triangle.loops):
                values.extend((*(transform @ mesh.vertices[vertex].co), *mesh.uv_layers.active.data[loop].uv))
    elif obj.get('meeting_screen'):
        mesh = obj.data
        mesh.calc_loop_triangles()
        values = buffers.setdefault((actor, 'screen', 'meetingScreen', 'project-presentation', 1.0), array('f'))
        for triangle in mesh.loop_triangles:
            for vertex, loop in zip(triangle.vertices, triangle.loops):
                values.extend((*(transform @ mesh.vertices[vertex].co), *mesh.uv_layers.active.data[loop].uv))
    else:
        evaluated = obj.evaluated_get(deps)
        mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=deps)
        if not mesh:
            continue
        mesh.calc_loop_triangles()
        for triangle in mesh.loop_triangles:
            luminance, _, opacity = shade(mesh.materials[triangle.material_index] if mesh.materials else None)
            if obj.get('browser_portal_mask') or luminance < .006:
                luminance = 0
            values = buffers.setdefault((actor, 'solid', role, identity, opacity), array('f'))
            for i in triangle.vertices:
                values.extend((*(transform @ mesh.vertices[i].co), luminance))
        statistics['solidTriangles'] += len(mesh.loop_triangles)
        evaluated.to_mesh_clear()

# A forgiving raycast-only volume for the tiny flat card, including oblique views.
if level == 'about':
    card = scene.objects['Office • Name card / contact face']
    values = array('f')
    corners = [card.matrix_world @ Vector((x, y, z))
               for x, y, z in [(-.35,-.24,-.015),(.35,-.24,-.015),(.35,.24,-.015),(-.35,.24,-.015),
                               (-.35,-.24,.12),(.35,-.24,.12),(.35,.24,.12),(-.35,.24,.12)]]
    for face in [(0,3,2),(0,2,1),(4,5,6),(4,6,7),(0,1,5),(0,5,4),
                 (1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]:
        for index in face:
            values.extend((*corners[index], 0))
    buffers[(0, 'solid', 'contactPick', 'card', 0.0)] = values
    # Precise, raycast-only link faces sit just above the printed text. The
    # authored fonts own placement, so focused-card links cannot drift visually.
    for label, identity in [('contact link', 'contact-github'), ('whatsapp', 'contact-whatsapp')]:
        lettering = scene.objects.get('Office • Name card / ' + label)
        if lettering is None:
            continue
        bounds = [Vector(corner) for corner in lettering.bound_box]
        lo = [min(point[i] for point in bounds) for i in range(3)]
        hi = [max(point[i] for point in bounds) for i in range(3)]
        x0, x1 = lo[0] - .001, hi[0] + .001
        y0, y1 = lo[1] - .001, hi[1] + .001
        z = hi[2] + .00002
        corners = [lettering.matrix_world @ Vector(point) for point in
                   [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]]
        values = array('f')
        for index in [0, 1, 2, 0, 2, 3]:
            values.extend((*corners[index], 0))
        buffers[(0, 'solid', 'contactLinkPick', identity, 0.0)] = values
    observer = next((obj for obj in objects if obj.type == 'MESH' and obj.name.startswith('Office • Observer /')), None)
    assert observer, 'The About-office Observer point source is missing.'
    observer_points = [observer.matrix_world @ vertex.co for vertex in observer.data.vertices]
    lo = [min(point[i] for point in observer_points) - (.10 if i < 2 else .025) for i in range(3)]
    hi = [max(point[i] for point in observer_points) + (.10 if i < 2 else .025) for i in range(3)]
    corners = [Vector((hi[0] if x else lo[0], hi[1] if y else lo[1], hi[2] if z else lo[2]))
               for x, y, z in [(0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1)]]
    values = array('f')
    for face in [(0,3,2),(0,2,1),(4,5,6),(4,6,7),(0,1,5),(0,5,4),
                 (1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]:
        for index in face:
            values.extend((*corners[index], 0))
    buffers[(0, 'solid', 'observerPick', 'observer', 0.0)] = values

if level == 'experience':
    # Small luminous nodes get a matching forgiving, invisible 3D pick volume.
    for obj in objects:
        if not obj.get('timeline_node'):
            continue
        identity = obj.name.split(' / ')[1]
        corners = [obj.matrix_world @ Vector(p) for p in obj.bound_box]
        values = array('f')
        for triangle in [(0,1,2),(0,2,3),(4,6,5),(4,7,6),(0,4,5),(0,5,1),(2,6,7),(2,7,3),(0,3,7),(0,7,4),(1,5,6),(1,6,2)]:
            for index in triangle: values.extend((*corners[index], 0))
        buffers[(0, 'solid', 'exhibitPick', identity, 0.0)] = values

geometry = array('f')
groups = []
for key, values in sorted(buffers.items()):
    actor, kind, role, identity, opacity = key
    stride = 5 if kind in ['points', 'screen'] else 4
    group = {'actor': actor, 'kind': kind, 'byteOffset': len(geometry)*4, 'floatCount': len(values), 'vertexCount': len(values)//stride, 'stride': stride, 'role': role or None, 'id': identity or None, 'opacity': opacity}
    geometry.extend(values)
    if kind == 'screen':
        group['texture'] = identity
    if key in morph_buffers:
        group['morphs'] = []
        for delta in morph_buffers[key]:
            group['morphs'].append({'byteOffset': len(geometry)*4, 'floatCount': len(delta)})
            geometry.extend(delta)
    groups.append(group)
frame_end = config.get('animationFrames', 1200 if level == 'projects' else scene.get('Aquarium loop frames', 1) if level == 'about' else 1)
channel_stride = 12 if level == 'skills' else 16
camera = scene.objects[config['mainCamera']]
channels = [camera, *roots]
animation = array('f')
for frame in range(1, frame_end + 1):
    scene.frame_set(frame)
    scene.view_layers[0].update()
    for index, obj in enumerate(channels):
        p, q, s = obj.matrix_world.decompose()
        weights = [key.value for key in list(shapes[obj].data.shape_keys.key_blocks)[1:]] if obj in shapes else []
        animation.extend((*p, q.x, q.y, q.z, q.w, *s, pose(camera)['fov'] if index == 0 else 0, 1))
        if channel_stride == 16: animation.extend(weights + [0]*(4-len(weights)))
scene.frame_set(1)
scene.view_layers[0].update()
cameras = {'main': pose(camera)}
for key, field in [('entry','entryCamera'), ('card','focusCamera')]:
    if field in config:
        cameras[key] = pose(scene.objects[config[field]])
for key, name in config.get('detailCameras', {}).items():
    cameras[key] = pose(scene.objects[name])
if level == 'projects':
    cameras['main']['position'] = [0, config['entranceAnchor'][1] + 3.05, 2.45]
projects = []
exhibits = []
navigation = {'type': 'axis', 'minY': config['entranceAnchor'][1] + .2, 'maxY': scene.get('hallway_length_m', 12)-3, 'eyeHeight': 2.45, 'speed': 3, 'fastSpeed': 8} if level == 'projects' else None
if level in ['about', 'project-meeting']:
    direction = camera.matrix_world.to_quaternion() @ Vector((0, 0, -1))
    navigation = {'type': 'look', 'eyeHeight': cameras['main']['position'][2],
                  'initialYaw': math.atan2(direction.x, direction.y),
                  'initialPitch': math.asin(max(-1, min(1, direction.z))),
                    'lookTarget': ([0, 9.68, 2.95] if level == 'project-meeting' else list(scene.objects['Office • About content screen / web texture target'].matrix_world.translation))}
    if scene.get('Aquarium animation bounds'):
        navigation['animationBounds'] = json.loads(scene['Aquarium animation bounds'])
route = array('f')
if config.get('guidedFrames'):
    for frame in range(1, config['guidedFrames'] + 1):
        scene.frame_set(frame);scene.view_layers[0].update()
        route.extend(camera.matrix_world.translation)
    scene.frame_set(1);scene.view_layers[0].update()
    if level == 'skills':
        stops = json.loads(scene['Gallery tour stops'])
        for root in sorted((obj for obj in scene.objects if obj.get('category')), key=lambda o:o.name):
            identity = exhibit_id(root)
            stop = next(s for s in stops if s['index'] == int(identity.split('-')[1]))
            surface = next(obj for obj in root.children if obj.name.endswith(' / content surface'))
            content=json.loads(root['skill_metadata']) if root.get('skill_metadata') else {}
            points=[surface.matrix_world @ vertex.co for vertex in surface.data.vertices]
            center=sum(points,Vector())/len(points)
            rotation=root.matrix_world.to_quaternion()
            normal=rotation @ Vector((0,-1,0))
            right=rotation @ Vector((1,0,0))
            exhibits.append({**content,'id': identity, 'title': root['category'], 'items': content.get('items',root['concept_items'].split(' / ')), 'position': list(surface.matrix_world.translation), 'start': stop['start'], 'end': stop['end'], 'hint': stop['hint'],
                             'card':{'center':list(center),'normal':list(normal),'right':list(right),'width':(points[1]-points[0]).length,'height':(points[2]-points[1]).length}})
        stop = next(s for s in stops if s['index'] == 0)
        sculpture = next(obj for obj in scene.objects if obj.get('centre_exhibit_id'))
        exhibits.append({'id': sculpture['centre_exhibit_id'], 'title': 'AT-AT walker', 'items': [], 'caption': 'Star Wars AT-AT · Black armor and fine white contours', 'position': list(scene.objects['Gallery • Sculpture / anchor'].matrix_world.translation), 'start': stop['start'], 'end': stop['end'], 'hint': stop['hint']})
    else:
        stops = json.loads(scene['guided_walk_stations'])
        for stop in stops:
            root = next(obj for obj in scene.objects if obj.get('milestone_id') == stop['id'])
            card = next(obj for obj in root.children if obj.name.endswith(' / black floating card'))
            rotation = card.matrix_world.to_quaternion()
            dimensions = card.dimensions
            face = {'center': list(card.matrix_world @ Vector((0, -.025, 0))),
                    'normal': list(rotation @ Vector((0, -1, 0))),
                    'right': list(rotation @ Vector((1, 0, 0))),
                    'width': dimensions.x, 'height': dimensions.z}
            exhibits.append({**json.loads(root['milestone_metadata']), 'card': face, 'position': list(card.matrix_world.translation), 'start': stop['arrivalFrame'], 'end': stop['leaveFrame'], 'hint': 'Select the timeline card to read its story'})
    direction = camera.matrix_world.to_quaternion() @ Vector((0,0,-1))
    navigation = {'type': 'guided', 'eyeHeight': cameras['main']['position'][2], 'initialYaw': math.atan2(direction.x, direction.y), 'initialPitch': math.asin(max(-1,min(1,direction.z))), 'animationFollowsWalk': False, 'route': {'file': 'route.bin', 'frameStart': 1, 'frameEnd': config['guidedFrames'], 'stride': 3, 'loop': config['guidedLoop']}, 'stations': exhibits}
    (output/'route.bin').write_bytes(route.tobytes())
if level == 'projects':
    layout = json.loads((ROOT / 'assets/project-hallway/hallway-layout.json').read_text())
    content = {p['id']: p for p in json.loads((ROOT / 'assets/project-hallway/projects.json').read_text())['projects']}
    projects = [{**content[p['id']], **p} for p in layout['projects']]
    for project in projects:
        root = next(obj for obj in scene.objects if obj.get('project_id') == project['id'] and obj.get('hallway_display'))
        face = next(obj for obj in root.children if obj.name.endswith(' / black display'))
        rotation = face.matrix_world.to_quaternion()
        scale = face.matrix_world.to_scale()
        low = Vector(tuple(min(corner[axis] for corner in face.bound_box) for axis in range(3)))
        high = Vector(tuple(max(corner[axis] for corner in face.bound_box) for axis in range(3)))
        project['card'] = {'center':list(face.matrix_world @ ((low+high)/2)),
                           'normal':list(rotation @ Vector((0,-1,0))), 'right':list(rotation @ Vector((1,0,0))),
                           'width':(high.x-low.x)*abs(scale.x),'height':(high.z-low.z)*abs(scale.z),
                           'frontDepth':(high.y-low.y)*abs(scale.y)/2}
    navigation['categories'] = layout['categories']
manifest = {'version': 3, 'level': level, 'label': config['label'], 'geometry': 'geometry.bin', 'animation': 'animation.bin', 'assetHash': hashlib.sha256(geometry.tobytes()+animation.tobytes()+route.tobytes()).hexdigest()[:12], 'frameStart': 1, 'frameEnd': frame_end, 'fps': 30, 'channelStride': channel_stride, 'channelCount': len(channels), 'channels': [o.name for o in channels], 'actors': [{'index': indices[o], 'name': o.name, 'style': 'room', 'morphCount': len(shapes[o].data.shape_keys.key_blocks)-1 if o in shapes else 0} for o in roots], 'camera': {'verticalFov': cameras['main']['fov'], 'sourceAspect': scene.render.resolution_x/scene.render.resolution_y, 'near': .01, 'far': 350, 'fovOffset': 10}, 'cameras': cameras, 'entranceAnchor': config['entranceAnchor'], 'textures': [], 'groups': groups, 'statistics': statistics, 'projects': public_content(projects), 'exhibits': public_content(exhibits), 'navigation': public_content(navigation), 'npcCount': 6 if level == 'skills' else 15 if level == 'projects' else 0}
(output / 'geometry.bin').write_bytes(geometry.tobytes())
(output / 'animation.bin').write_bytes(animation.tobytes())
manifest['loop'] = frame_end > 1
if logo_textures:
    digest = hashlib.sha256(geometry.tobytes() + animation.tobytes() + route.tobytes())
    for texture, source in sorted(logo_textures.items()):
        destination = output / texture
        destination.parent.mkdir(parents=True, exist_ok=True)
        retired = destination.with_name(destination.name.replace('-logo.png', '-monochrome.png'))
        if retired != destination and retired.is_file():
            retired.unlink()
        shutil.copyfile(source, destination)
        digest.update(source.read_bytes())
    manifest['textures'] = sorted(logo_textures)
    manifest['assetHash'] = digest.hexdigest()[:12]
if level == 'about' and scene.get('office_malaysia_map'):
    manifest['officeScreen'] = json.loads(scene['office_malaysia_map'])
if level=='projects':
    root=scene.objects.get('Entry / projects directory')
    if root and root.get('hallway_directory'):
        face=next(obj for obj in root.children if obj.get('hallway_directory_face'))
        rotation=root.matrix_world.to_quaternion()
        face_points=[face.matrix_world @ Vector(point) for point in face.bound_box]
        low=min(point.z for point in face_points)-.05
        unit=next(obj for obj in root.children if obj.get('holographic_projector'))
        device_parts=[obj for obj in unit.children if obj.type=='MESH' and any(label in obj.name for label in ('floor anchor','emitter housing','optical head'))]
        high=max((obj.matrix_world @ Vector(point)).z for obj in device_parts for point in obj.bound_box)
        center=face.matrix_world.translation.copy();center.z=(low+high)/2
        manifest['directory']={'id':'directory','title':root.get('directory_title','Projects directory'),'category':root.get('directory_category','client'),'position':list(root.location),
            'card':{'center':list(center),'normal':list(rotation @ Vector((0,-1,0))),'right':list(rotation @ Vector((1,0,0))),
                    'width':max(vertex.co.x for vertex in face.data.vertices)-min(vertex.co.x for vertex in face.data.vertices),
                    'height':high-low,'frontDepth':.95},'zoomOnly':True,'projectorPosition':'above'}
(output / 'scene.json').write_text(json.dumps(manifest, indent=2))
print(json.dumps({'level': level, 'groups': len(groups), 'geometry_bytes': len(geometry)*4, 'animation_bytes': len(animation)*4, 'actors': len(roots), 'statistics': statistics, 'authored_room_modified': False}))
