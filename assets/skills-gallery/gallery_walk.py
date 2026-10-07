"""Guided movement only: a translated player rig and an unanimated look camera."""
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

RIG_NAME = 'Gallery • Guided walk / player movement'
CAMERA_NAME = 'Gallery • Guided walk / free-look camera'
END_FRAME = 2940
ROUTE = [
    (1,(0,-6.6,0)),(140,(-2.65,-4.6,0)),
    (300,(-2.4,-.3,0)),(480,(-2.4,-.3,0)),
    (580,(-4.4,1.7,0)),(710,(-4.45,5.85,0)),
    (770,(-3.85,6.65,0)),(860,(-3.85,6.65,0)),
    (900,(-3.3,6.45,0)),(990,(-3.3,6.45,0)),
    (1100,(0,6.45,0)),(1190,(0,6.45,0)),
    (1300,(3.3,6.45,0)),(1390,(3.3,6.45,0)),
    (1450,(4.3,6.9,0)),(1540,(4.3,6.9,0)),
    (1650,(4.25,3.7,0)),(1740,(4.25,3.7,0)),
    (1790,(4.15,1.7,0)),(1850,(3.0,.65,0)),(1940,(3.0,.65,0)),
    (2050,(3.0,-2.7,0)),(2140,(3.0,-2.7,0)),
    (2290,(0,.65,0)),(2380,(0,.65,0)),
    (2470,(0,-1.75,0)),(2610,(2.6,-2.65,0)),
    (2680,(2.65,-4.65,0)),(2810,(0,-6.6,0)),(END_FRAME,(0,-6.6,0)),
]
STOPS = [
    (300,480,'Languages','Look left and slightly up',1),
    (770,860,'Frameworks','Look left',2),
    (900,990,'Backend & APIs','Look toward the rear wall',3),
    (1100,1190,'Databases','Look toward the rear wall',4),
    (1300,1390,'Data & AI','Look toward the rear wall',5),
    (1450,1540,'Security','Look right',6),
    (1650,1740,'DevOps & CI/CD','Look right',7),
    (1850,1940,'Microservices','Look right',8),
    (2050,2140,'Linux','Look right',9),
    (2290,2380,'AT-AT walker','Look ahead and around the mechanical walker',0),
]


def curves(owner):
    if not owner.animation_data or not owner.animation_data.action:
        return []
    return [curve for layer in owner.animation_data.action.layers for strip in layer.strips
            for bag in strip.channelbags for curve in bag.fcurves]


def install_guided_walk(scene,source_dir):
    assert scene.name=='SKILLS / Technology Gallery'
    col = bpy.data.collections.get('Gallery • 09 Guided movement')
    if col is None:
        col = bpy.data.collections.new('Gallery • 09 Guided movement')
        scene.collection.children.link(col)
    for obj in list(col.objects):
        bpy.data.objects.remove(obj,do_unlink=True)
    rig = bpy.data.objects.new(RIG_NAME,None); col.objects.link(rig)
    rig.empty_display_type = 'ARROWS'; rig.empty_display_size = .25
    rig['role'] = 'Timeline-controlled translation only; camera look is independent'
    for frame,position in ROUTE:
        rig.location = position; rig.keyframe_insert(data_path='location',frame=frame,group='Guided walking position')
    for curve in curves(rig):
        for key in curve.keyframe_points:
            key.interpolation = 'BEZIER'
            key.handle_left_type = 'AUTO_CLAMPED'; key.handle_right_type = 'AUTO_CLAMPED'
    data = bpy.data.cameras.new(CAMERA_NAME)
    camera = bpy.data.objects.new(CAMERA_NAME,data); col.objects.link(camera)
    camera.parent = rig; camera.location = (0,0,1.70)
    camera.rotation_euler = (math.pi/2,0,0)
    data.lens = 18; data.clip_start = .04; data.clip_end = 100
    camera['look_control'] = 'Unkeyed orientation; mouse look via Gallery Walk Preview.py'
    camera['default_yaw'] = 0.0; camera['default_pitch'] = 0.0
    assert not camera.constraints and not camera.animation_data and not data.animation_data
    assert all(curve.data_path=='location' for curve in curves(rig))
    # Existing 32-second NPC clips keep running for the entire tour.
    for obj in scene.objects:
        if obj.get('activity') or obj.get('joint'):
            for curve in curves(obj):
                if not any(m.type=='CYCLES' for m in curve.modifiers):
                    cycle = curve.modifiers.new('CYCLES')
                    cycle.mode_before = 'REPEAT'; cycle.mode_after = 'REPEAT'
    # Visitors use reserved lanes; their timing is independent of this route.
    for marker in list(scene.timeline_markers):
        if marker.name.startswith('Tour /'):
            scene.timeline_markers.remove(marker)
    for frame,_,label,_,index in STOPS:
        scene.timeline_markers.new('Tour / %02d / %s' % (index,label),frame=frame)
    scene.timeline_markers.new('Tour / Exit',frame=2810)
    scene.frame_start = 1; scene.frame_end = END_FRAME; scene.render.fps = 30
    scene.camera = camera
    scene['Gallery tour stops'] = json.dumps([{'start':a,'end':b,'label':label,'hint':hint,'index':index}
                                            for a,b,label,hint,index in STOPS])
    scene['Gallery movement control'] = 'Guided position; no camera rotation keys or aiming constraints'
    # The script is embedded for offline use, but is never auto-executed.
    text = bpy.data.texts.get('Gallery Walk Preview.py') or bpy.data.texts.new('Gallery Walk Preview.py')
    text.clear(); text.write((Path(source_dir)/'gallery_walk_preview.py').read_text())
    text.use_module = False
    script = bpy.data.texts.get('Gallery Walk - START HERE.txt') or bpy.data.texts.new('Gallery Walk - START HERE.txt')
    script.clear(); script.write('GUIDED MOVEMENT, FREE LOOK\n\n'
        'Normal Space playback moves the player through all nine exhibits.\n'
        'For mouse look: run Gallery Walk Preview.py once from the Text Editor.\n'
        'Then return to Layout, press N, open Gallery Walk, and click Start Guided Walk.\n'
        'Hold right or middle mouse and drag to look. Space pauses. R resets look.\n'
        'Escape stops the preview. The camera direction is never keyed or auto-aimed.\n')
    scene.frame_set(1); bpy.context.view_layer.update()
    points = []
    for frame in range(1,END_FRAME+1):
        scene.frame_set(frame); bpy.context.view_layer.update()
        points.append(list(rig.location))
    guide_data = bpy.data.curves.new('Gallery • Guided walk / route guide','CURVE')
    guide_data.dimensions = '3D'
    spline = guide_data.splines.new('POLY'); spline.points.add(len(points[::10])-1)
    for point,position in zip(spline.points,points[::10]):
        point.co = (*position,1)
    guide = bpy.data.objects.new(guide_data.name,guide_data); col.objects.link(guide)
    guide.hide_render = True; guide.show_in_front = True
    scene.frame_set(1)
    return {'camera':camera.name,'rig':rig.name,'frames':[1,END_FRAME],'fps':30,
            'duration_s':END_FRAME/30,'camera_rotation_animated':False,'camera_auto_aim':False,
            'stops':[{'start':a,'end':b,'label':label,'hint':hint,'index':index} for a,b,label,hint,index in STOPS],
            'positions':points}


def validate_guided_walk(scene,walk):
    roots = [o for o in scene.objects if o.get('activity')]
    obstacles = [(-.20,3.85,7.4,3.2),(0,-3.65,3.45,.70),(-4.65,-1.10,.72,2.15),(4.65,-1.10,.72,2.15)]
    issues = []; closest = 100
    for frame,position in enumerate(walk['positions'],1):
        x,y,_ = position
        assert abs(x)<5.6 and -6.8<y<8.3
        for cx,cy,w,d in obstacles:
            assert not (abs(x-cx)<w/2+.20 and abs(y-cy)<d/2+.20), f'Player obstacle collision at {frame}'
        scene.frame_set(frame); bpy.context.view_layer.update()
        for root in roots:
            distance = math.hypot(x-root.location.x,y-root.location.y)
            closest = min(closest,distance)
            if distance<.48:
                issues.append({'frame':frame,'visitor':root.name,'distance':distance})
    if issues:
        summary = {}
        for issue in issues:
            item = summary.setdefault(issue['visitor'],{'first':issue['frame'],'last':issue['frame'],'minimum':1})
            item['last'] = issue['frame']; item['minimum'] = min(item['minimum'],issue['distance'])
        raise AssertionError(f'Player/NPC route conflicts: {summary}')
    scene.frame_set(1)
    # Independent clocks require clearance for EVERY combination of player and
    # visitor time. Bin the complete clip, then check the complete player route.
    bins = {}
    cell = .48
    for frame in range(1,961):
        scene.frame_set(frame); scene.view_layers[0].update()
        for root in roots:
            x,y = root.location.x,root.location.y
            bins.setdefault((math.floor(x/cell),math.floor(y/cell)),[]).append((x,y,root.name))
    for x,y,_ in walk['positions']:
        bx,by = math.floor(x/cell),math.floor(y/cell)
        for dx in [-1,0,1]:
            for dy in [-1,0,1]:
                for nx,ny,name in bins.get((bx+dx,by+dy),[]):
                    assert math.hypot(x-nx,y-ny)>=cell, f'Independent player/NPC conflict: {name}'
    scene.frame_set(1)
    return {'checks':'passed','minimum_player_npc_distance_m':closest}
