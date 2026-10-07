"""Shared hallway dimensions and a preserved-scene layout refresh."""
import bisect
import json
import math
from pathlib import Path

WIDTH = 14.2
FLOOR_WIDTH = WIDTH + .2
BOARD_X = 4.8
BAY_SPACING = 11.5
RIGHT_STAGGER = 3.0
PROJECT_START = 8.7
BENCH_X = 4.3


def category_layout(projects, categories):
    sections, bookmarks = [], []
    start = PROJECT_START
    for index, category in enumerate(categories):
        items = [project for project in projects if project['section'] == category['id']]
        door_y = start - PROJECT_START if index else None
        for number, project in enumerate(items):
            x = -BOARD_X if number % 2 == 0 else BOARD_X
            y = start + number // 2 * BAY_SPACING + (RIGHT_STAGGER if number % 2 else 0)
            bookmarks.append({'id': project['id'], 'section': category['id'], 'position': [x, y, 0],
                              'facing': 'east-entrance' if x < 0 else 'west-entrance', 'url': project.get('url')})
        last_y = max(bookmark['position'][1] for bookmark in bookmarks if bookmark['section'] == category['id'])
        section = {**category, 'startY': -10 if index == 0 else door_y, 'displayStartY': start,
                   'endY': last_y + 4, 'projectIds': [project['id'] for project in items]}
        if index:
            section['door'] = {'y': door_y, 'revealY': sections[-1]['endY'] - 3, 'automatic': True,
                               'previousCategory': sections[-1]['id']}
        sections.append(section)
        start = last_y + 17.5
    return sections, bookmarks, sections[-1]['endY'] + 12


def refresh_existing(scene, out):
    import bpy
    from mathutils import Vector
    from board_orientation import orient_project_board, stabilize_projector

    out = Path(out)
    layout_path = out / 'hallway-layout.json'
    old = json.loads(layout_path.read_text())
    content = json.loads((out / 'projects.json').read_text())
    sections, bookmarks, length = category_layout(content['projects'], content['categories'])
    if abs(old.get('widthMeters', 10.2) - WIDTH) < .001 and abs(old['projectBaySpacingMeters'] - BAY_SPACING) < .001:
        print('PASS spacious hallway layout already current')
        return
    scene.frame_set(1)
    scene.view_layers[0].update()
    old_by_id = {item['id']: item for item in old['projects']}
    new_by_id = {item['id']: item for item in bookmarks}
    anchors = [(-12., -12.), (-10., -10.), (PROJECT_START, PROJECT_START)]
    anchors += [(item['position'][1], new_by_id[item['id']]['position'][1]) for item in old['projects']]
    anchors += [(item['door']['y'], next(new['door']['y'] for new in sections if new['id'] == item['id'])) for item in old['categories'] if item.get('door')]
    anchors += [(old['lengthMeters'], length)]
    anchors = sorted(dict(anchors).items())
    xs = [a for a, _ in anchors]

    def move_y(y):
        if y <= xs[0]:
            return y
        if y >= xs[-1]:
            return y + length - old['lengthMeters']
        index = bisect.bisect_right(xs, y) - 1
        a, b = anchors[index], anchors[index + 1]
        return a[1] + (y - a[0]) / (b[0] - a[0]) * (b[1] - a[1])

    old_width = old.get('widthMeters', 10.2)
    xratio = WIDTH / old_width
    roots = [obj for obj in scene.objects if obj.get('project_id') and obj.get('hallway_display')]
    directory = scene.objects['Entry / projects directory']
    category_roots = [obj for obj in scene.objects if obj.get('hallway_category_gate')]
    npcs = [obj for obj in scene.objects if obj.get('source_person_id')]
    rigs = {obj.parent for obj in npcs}
    special = {obj for root in [*roots, directory, *category_roots, *rigs] for obj in [root, *root.children_recursive]}
    matrices = {obj: obj.matrix_world.copy() for obj in scene.objects}
    bodies = {npc: [tuple(vertex.co) for vertex in npc.data.vertices] for npc in npcs}
    weights = {npc: [[tuple(point.co) for point in key.data] for key in npc.data.shape_keys.key_blocks] for npc in npcs}
    morph_actions = {npc: npc.data.shape_keys.animation_data.action for npc in npcs}
    main_camera = scene.objects['Project Hallway / free-look camera']
    main_pose = main_camera.matrix_world.copy()

    def points_of(obj):
        if obj.type == 'MESH':
            return [vertex.co for vertex in obj.data.vertices]
        if obj.type == 'CURVE':
            return [point.co for spline in obj.data.splines for point in spline.points]
        return []

    def world_center(obj):
        corners = [matrices[obj] @ Vector(corner) for corner in obj.bound_box]
        return Vector(tuple((min(point[axis] for point in corners) + max(point[axis] for point in corners)) / 2 for axis in range(3)))

    def transform_geometry(obj, transform):
        before = matrices[obj]
        inverse = before.inverted()
        if obj.data.users > 1:
            obj.data = obj.data.copy()
        for coordinate in points_of(obj):
            result = inverse @ transform(before @ Vector(coordinate[:3]))
            coordinate.x, coordinate.y, coordinate.z = result
        if obj.type == 'CURVE':
            for spline in obj.data.splines:
                for point in spline.bezier_points:
                    point.co = inverse @ transform(before @ point.co)
                    point.handle_left = inverse @ transform(before @ point.handle_left)
                    point.handle_right = inverse @ transform(before @ point.handle_right)

    def stretch(point):
        return Vector((point.x * xratio, move_y(point.y), point.z))

    bench_seats = [obj for obj in scene.objects if obj.type == 'MESH' and obj.name.startswith('Bench ') and 'open support' not in obj.name]
    bench_centers = [world_center(obj) for obj in bench_seats]
    for obj in scene.objects:
        if obj in special:
            continue
        collections = {col.name.split(' / ')[0] for col in obj.users_collection}
        if obj == main_camera:
            continue
        if '04' in collections:
            center = world_center(obj)
            seat = min(bench_centers, key=lambda candidate: (candidate - center).length)
            delta = Vector((math.copysign(BENCH_X, seat.x) - seat.x, move_y(seat.y) - seat.y, 0))
            transform_geometry(obj, lambda point, delta=delta: point + delta)
        elif obj.get('dotted_pillar') or obj.get('dotted_pillar_base') or obj.name.startswith('Floor / light strip'):
            center = world_center(obj)
            target_x = math.copysign(WIDTH / 2 - (.85 if obj.name.startswith('Floor /') else .65), center.x)
            delta = Vector((target_x - center.x, move_y(center.y) - center.y, 0))
            transform_geometry(obj, lambda point, delta=delta: point + delta)
        elif obj.type in {'MESH', 'CURVE'}:
            if obj.name in {'Polished reflective floor', 'Dark ceiling', 'Gallery end wall'}:
                transform_geometry(obj, lambda point: Vector((point.x * FLOOR_WIDTH / (old_width + .2), move_y(point.y), point.z)))
            else:
                transform_geometry(obj, stretch)
        elif obj.type in {'EMPTY', 'FONT', 'LIGHT'} and obj.parent is None:
            obj.location.y = move_y(obj.location.y)

    for root in roots:
        root.location = new_by_id[root['project_id']]['position']
        orient_project_board(root)
        stabilize_projector(root)
    # The directory stays at its original raised entrance position/pose.
    for root in category_roots:
        root.location.y = next(item['door']['y'] for item in sections if item['id'] == root['hallway_category_gate'])
        for part in root.children:
            if part.name.startswith('Category / black partition'):
                sign = -1 if part.location.x < 0 else 1
                part.location.x = sign * (2 + WIDTH / 2) / 2
                part.scale.x *= (WIDTH / 2 - 2) / 3.1
            elif part.get('hallway_category_wall_number'):
                for coordinate in points_of(part):
                    coordinate.x -= (WIDTH - old_width) / 4

    def curves(owner):
        if not owner.animation_data or not owner.animation_data.action:
            return []
        return [curve for layer in owner.animation_data.action.layers for strip in layer.strips for bag in strip.channelbags for curve in bag.fcurves]

    for npc in npcs:
        placement = json.loads(npc['placement'])
        rig = npc.parent
        old_position = Vector(placement['position'])
        old_target = Vector(placement['target'])
        new_position = old_position.copy()
        new_position.y = move_y(old_position.y)
        new_target = old_target.copy()
        if npc.get('viewing_project'):
            item = new_by_id[npc['viewing_project']]
            new_target.x, new_target.y = item['position'][:2]
            new_position.y = new_target.y + old_position.y - old_by_id[npc['viewing_project']]['position'][1]
        else:
            new_target.y = move_y(old_target.y)
        shift = new_position.y - old_position.y
        walking = rig.get('npc_animation') == 'walking_loop'
        if walking:
            center_y = placement['route']['center'][1]
            shift = move_y(center_y) - center_y
            new_position.y = old_position.y + shift
            new_target.y = old_target.y + shift
            placement['route']['center'][1] += shift
        else:
            rig.location.y += shift
        new_facing = math.atan2(new_target.x - new_position.x, -(new_target.y - new_position.y))
        rotation_shift = math.atan2(math.sin(new_facing - placement['facing']), math.cos(new_facing - placement['facing']))
        for curve in curves(rig):
            delta = shift if curve.data_path == 'location' and curve.array_index == 1 else rotation_shift if not walking and curve.data_path == 'rotation_euler' and curve.array_index == 2 else 0
            for key in curve.keyframe_points:
                key.co.y += delta;key.handle_left.y += delta;key.handle_right.y += delta
        placement.update(position=list(new_position), target=list(new_target), facing=placement['facing'] if walking else new_facing)
        npc['placement'] = json.dumps(placement)

    tour = scene.objects['Project Hallway / walkthrough camera']
    for curve in curves(tour):
        if curve.data_path == 'location' and curve.array_index == 1:
            for key in curve.keyframe_points:
                key.co.y = move_y(key.co.y);key.handle_left.y = move_y(key.handle_left.y);key.handle_right.y = move_y(key.handle_right.y)
    for camera in [obj for obj in scene.objects if obj.type == 'CAMERA' and obj not in {tour, main_camera}]:
        camera.location.y = move_y(camera.location.y)
    for item in bookmarks:
        item['frame'] = max(1, round(1 + (item['position'][1] + 3.8) / (length + .8) * 1199))
    layout = {**old, 'widthMeters': WIDTH, 'floorWidthMeters': FLOOR_WIDTH, 'lengthMeters': length,
              'projectBaySpacingMeters': BAY_SPACING, 'rightDisplayStaggerMeters': RIGHT_STAGGER,
              'categories': sections, 'projects': bookmarks, 'npcLayout': [json.loads(npc['placement']) for npc in npcs],
              'displayFacing': {'left': 'east / entrance 45°', 'right': 'west / entrance 45°'}}
    scene['hallway_length_m'] = length;scene['hallway_width_m'] = WIDTH;scene['project_bay_spacing_m'] = BAY_SPACING
    scene['structural_pillar_pair_count'] = len([obj for obj in scene.objects if obj.get('dotted_pillar')]) // 2
    scene.frame_set(1);scene.view_layers[0].update()
    assert main_camera.matrix_world == main_pose, 'Entrance/main camera changed'
    for npc in npcs:
        assert [tuple(vertex.co) for vertex in npc.data.vertices] == bodies[npc], 'NPC body geometry changed'
        assert [[tuple(point.co) for point in key.data] for key in npc.data.shape_keys.key_blocks] == weights[npc], 'NPC morph performance changed'
        assert npc.data.shape_keys.animation_data.action == morph_actions[npc], 'NPC gait/gesture actions replaced'
    layout_path.write_text(json.dumps(layout, indent=2) + '\n')
    bpy.context.preferences.filepaths.save_version = 1
    bpy.ops.wm.save_as_mainfile(filepath=str(out / 'project-hallway.blend'))
    print(f'PASS spacious hallway {WIDTH} × {length:.1f} m; 16 boards; original 15 NPC bodies/morph performances retained')
