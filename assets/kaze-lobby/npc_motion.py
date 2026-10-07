"""Editable, native NPC loops. Camera and elevator keys are never touched."""
import math
import bpy
from mathutils import Matrix, Vector

PERIOD = 1019  # Frame 1020 duplicates frame 1; navigation remains 1–1020.
ROUTES = {
    'Visitor / walking toward entrance': ((-.9,-6.6,0),(-.9,-9.0,0)),
    'Visitor / carrying a briefcase': ((2.8,-1.6,0),(2.8,1.5,0)),
    'Visitor / heading deeper into lobby': ((-2.8,7.0,0),(-2.8,9.7,0)),
    'Gallery / slow stroll': ((8.5,16.1,6.12),(8.5,19.0,6.12)),
}

ACTIVITIES = {
    'seated_reading': 'read, glance up, and nod to the conversation',
    'seated_relaxed': 'seated conversation with alternating hand gestures',
    'seated_phone': 'tap phone and glance toward the conversation',
    'seated_drinking': 'sip coffee and gesture while chatting',
    'talking': 'explain with a hand gesture and head nod',
    'listening': 'listen, nod, and briefly respond',
    'checking_terminal': 'type and check the terminal',
    'greeting': 'occasionally wave to arriving guests',
    'phone': 'tap phone and look up briefly',
    'leaning': 'rest on the rail and look around',
    'observing': 'look across the atrium',
    'pointing': 'point out the view and turn the head',
    'riding_escalator': 'hold the rail and look around',
}


def around(pivot, angle, axis):
    return Matrix.Translation(pivot) @ Matrix.Rotation(angle, 4, axis) @ Matrix.Translation(-pivot)


def body_regions(obj):
    """Authored particle order follows the body forms in build_lobby.person."""
    name = obj.name.removeprefix('Lobby • ')
    density = {'Visitor / walking toward entrance': 1.1,
               'Gallery / slow stroll': .8, 'Escalator / riding upstairs': .9}.get(name, 1)
    forms = [('hip', 190), ('torso', 480), ('neck', 65), ('head', 220), ('head', 35)]
    for side in (-1, 1):
        forms.extend([(f'{part}:{side}', count) for part, count in
                      [('thigh', 230), ('shin', 200), ('foot', 80),
                       ('upper', 185), ('forearm', 140), ('hand', 65)]])
    regions = [part for part, count in forms for _ in range(int(count*density))]
    assert len(regions) == len(obj.data.vertices), f'Unexpected body topology: {obj.name}'
    return regions


def activity_transforms(obj, regions):
    """Small joint rotations keep arms coherent and feet planted."""
    pose = obj['pose']
    seated = pose.startswith('seated_') or pose == 'sitting'
    hip = .64 if seated else 1.04
    # Use the center of the authored head particles (also respects person scale).
    heads = [v.co for v, region in zip(obj.data.vertices, regions) if region == 'head']
    head = sum(heads, Vector()) / len(heads)
    primary, secondary = {}, {'head': around(head, .12, 'X'), 'neck': Matrix.Identity(4)}
    for side in (-1, 1):
        elbow = Vector((side*.30, -.14, hip+.20)) if seated else Vector((side*.29, 0, 1.12))
        elbows = {
            'seated_reading': (side*.29, -.18, .91),
            'seated_phone': (side*.24, -.12, .88),
            'seated_relaxed': (side*.35, .07, .81),
            'talking': (side*.34, -.10, 1.19),
            'listening': (side*.29, .03, 1.17),
            'phone': (side*.27, -.07, 1.18),
            'checking_terminal': (side*.27, -.07, 1.48),
            'leaning': ((.31, -.14, 1.12) if side == 1 else (-.30, -.48, .98)),
            'observing': (side*.26, .15, 1.17),
        }
        elbow = Vector(elbows.get(pose, elbow))
        if pose == 'seated_drinking' and side == 1: elbow = Vector((.32, -.13, .99))
        if pose == 'greeting' and side == 1: elbow = Vector((.38, -.06, 1.65))
        if pose == 'pointing' and side == 1: elbow = Vector((.48, -.24, 1.55))
        pitch = -.22 if side == 1 else -.10
        if pose in ['phone', 'seated_phone']: pitch = -.14 if side == 1 else 0
        elif pose in ['seated_reading', 'checking_terminal']: pitch = -.065
        elif pose in ['leaning', 'observing', 'riding_escalator', 'walking', 'carrying_bag']: pitch = 0
        elif pose == 'greeting': pitch = 0
        first = around(elbow, pitch, 'X')
        second = Matrix.Identity(4)
        if pose == 'greeting' and side == 1:
            first = around(elbow, -.28, 'Y')
            second = around(elbow, .28, 'Y')
        elif pose == 'seated_relaxed' and side == -1:
            second = around(elbow, -.20, 'X')
        for part in ('forearm', 'hand'):
            primary[f'{part}:{side}'] = first
            secondary[f'{part}:{side}'] = second
        if pose == 'seated_relaxed':
            shoulder = Vector((side*.23, .08, 1.105))
            for part in ('upper', 'forearm', 'hand'):
                if side == 1:
                    primary[f'{part}:{side}'] = around(shoulder, -.85, 'X')
                else:
                    secondary[f'{part}:{side}'] = around(shoulder, -.55, 'X')
    if pose in ['observing', 'leaning', 'pointing', 'riding_escalator']:
        secondary['head'] = around(head, .22, 'Z')
    return primary, secondary


def activity_weights(t, index, pose):
    # Integer cycles make the loop seamless; offsets prevent synchronized crowds.
    phase = (t*(3+index%3) + index*.173) % 1
    envelope = math.sin(math.pi*min(1, phase/.55))**2 if phase < .55 else 0
    if pose == 'greeting':
        wave = math.sin(phase/.55*math.tau*2) if phase < .55 else 0
        return envelope*max(0, wave), envelope*max(0, -wave)
    return envelope, .5-.5*math.cos(math.tau*(t*(2+index%2)+index*.231))


def curves(owner):
    if not owner.animation_data or not owner.animation_data.action:
        return []
    return [c for layer in owner.animation_data.action.layers for strip in layer.strips
            for bag in strip.channelbags for c in bag.fcurves]


def install_npc_motion(scene):
    scene.frame_set(1); scene.view_layers[0].update()
    people = sorted((o for o in scene.objects if o.get('pose_origin') is not None), key=lambda o: o.name)
    for index, obj in enumerate(people):
        origin = Vector(obj['pose_origin']); angle = obj['facing_angle_rad']
        basis = Matrix.Translation(origin) @ Matrix.Rotation(angle,4,'Z')
        inverse = basis.inverted()
        installed = bool(obj.get('autonomous_npc'))
        if installed:
            obj.animation_data_clear()
            obj.shape_key_clear()
        else:
            for vertex in obj.data.vertices:
                vertex.co = inverse @ vertex.co
        obj.matrix_world = basis
        props = [p for p in scene.objects if p.get('npc_owner') == obj.name]
        for prop in props:
            if not installed:
                world = prop.matrix_world.copy(); prop.parent = obj
                prop.matrix_parent_inverse.identity(); prop.matrix_world = world
            if prop.animation_data:
                prop.animation_data_clear()
            if prop.get('activity_basis') is not None:
                prop.matrix_basis = Matrix([prop['activity_basis'][i:i+4] for i in range(0, 16, 4)])
            else:
                prop['activity_basis'] = [v for row in prop.matrix_basis for v in row]
        prop_bases = {prop: prop.matrix_basis.copy() for prop in props}
        regions = body_regions(obj)
        primary, secondary = activity_transforms(obj, regions)
        obj.shape_key_add(name='Basis')
        walk = obj.name.removeprefix('Lobby • ') in ROUTES
        gait = obj.shape_key_add(name='Stride forward')
        back = obj.shape_key_add(name='Stride backward')
        gesture = obj.shape_key_add(name='Activity gesture')
        attention = obj.shape_key_add(name='Attention and response')
        for vertex, region, a, b, g, h in zip(obj.data.vertices,regions,gait.data,back.data,gesture.data,attention.data):
            p = vertex.co; side = -1 if p.x < 0 else 1
            leg = max(0,1-p.z/1.05)**1.4 if walk else 0
            arm = min(1,max(0,(abs(p.x)-.18)/.12)) if walk and region.startswith(('upper:', 'forearm:', 'hand:')) else 0
            if obj['pose'] == 'carrying_bag' and region.endswith(':1'): arm = 0
            delta = Vector((0,side*(leg*.18-arm*.065),leg*.035))
            a.co = p+delta; b.co = p-delta
            g.co = primary.get(region, Matrix.Identity(4)) @ p
            h.co = secondary.get(region, Matrix.Identity(4)) @ p
        route = ROUTES.get(obj.name.removeprefix('Lobby • '))
        obj['autonomous_npc'] = True
        obj['activity_loop'] = 'walk, pause, look, return' if walk else ACTIVITIES.get(obj['pose'], 'idle and look around')
        if route: obj['predefined_route'] = [v for point in route for v in point]
        distance = 0; previous = None
        for frame in range(1,PERIOD+2):
            t = (frame-1)/PERIOD
            if route:
                moving = .10 < t < .40 or .60 < t < .90
                u = min(1,max(0,(t-.10)/.30)) if t < .50 else 1-min(1,max(0,(t-.60)/.30))
                u = u*u*(3-2*u)
                position = Vector(route[0]).lerp(Vector(route[1]),u)
                if previous is not None: distance += (position-previous).length
                previous = position.copy()
                obj.location = position
                turn = min(1,max(0,(t-.43)/.12)) if t < .9 else 1-min(1,max(0,(t-.90)/.10))
                direction = 1 if route[1][1] > route[0][1] else -1
                obj.rotation_euler.z = (math.pi if direction > 0 else 0)+math.pi*turn
                phase = math.sin(distance*math.tau/.72) if moving else 0
                gait.value = max(0,phase); back.value = max(0,-phase)
            else:
                obj.location = origin
                gait.value = back.value = 0
            gesture.value, attention.value = activity_weights(t, index, obj['pose'])
            # Accessories follow the same blended forearm deformation as the hand.
            for prop, base in prop_bases.items():
                side = -1 if obj['pose'] in ['phone', 'seated_phone', 'seated_reading'] else 1
                transform = primary.get(f'hand:{side}', Matrix.Identity(4))
                response = secondary.get(f'hand:{side}', Matrix.Identity(4))
                blended = Matrix.Identity(4)
                for row in range(4):
                    for col in range(4):
                        identity = 1 if row == col else 0
                        blended[row][col] += (transform[row][col]-identity)*gesture.value + (response[row][col]-identity)*attention.value
                prop.matrix_basis = blended @ base
                for path in ['location', 'rotation_euler', 'scale']:
                    prop.keyframe_insert(data_path=path, frame=frame)
            obj.keyframe_insert(data_path='location',frame=frame)
            obj.keyframe_insert(data_path='rotation_euler',frame=frame)
            for key in [gait,back,gesture,attention]: key.keyframe_insert(data_path='value',frame=frame)
        for owner in [obj,obj.data.shape_keys,*props]:
            for curve in curves(owner):
                for key in curve.keyframe_points: key.interpolation = 'LINEAR'
                curve.modifiers.new('CYCLES')
    scene['autonomous_npc_period'] = PERIOD
    scene.frame_set(1); scene.view_layers[0].update()
    return len(people)
