"""Native, seamless hologram swimming; playback uses the independent lobby clock.

The rig moves point sources and their curve outlines together. Nested tail/fin
actions are baked by the browser exporter from the closest animated ancestor,
so no evaluated sphere meshes or renderer-only deformations are needed.
"""
import math

import bpy
from mathutils import Matrix, Vector

from npc_motion import PERIOD

FISH_PARTS = {
    'body': ['holographic fish body', 'fish luminous silhouette',
             'fish body contour traces', 'fish eye and gill'],
    'upper tail': ['upper tail outline', 'upper tail fin rays', 'upper tail translucent membrane'],
    'lower tail': ['lower tail outline', 'lower tail fin rays', 'lower tail translucent membrane'],
    'dorsal': ['dorsal outline', 'dorsal fin rays', 'dorsal translucent membrane'],
    'near pectoral': ['near pectoral outline', 'near pectoral fin rays', 'near pectoral translucent membrane'],
    'lower ventral': ['lower ventral outline', 'lower ventral fin rays', 'lower ventral translucent membrane'],
}


def install_fish_motion(scene):
    """Install only on a freshly generated exhibit; never save a master here."""
    group = bpy.data.collections['Lobby • 17 Holographic fish exhibit']
    if scene.objects.get('Lobby • Exhibit / swim / body'):
        raise RuntimeError('Fish motion already exists. Use rebuild_lobby.py for a fresh rig.')
    cy = 15.55
    scene.frame_set(1)
    scene.view_layers[0].update()

    def parent_at_rest(obj,parent):
        world = obj.matrix_world.copy()
        obj.parent = parent
        obj.matrix_parent_inverse = Matrix.Identity(4)
        obj.matrix_world = world
        scene.view_layers[0].update()

    def root(part,pivot,parent=None):
        obj = bpy.data.objects.new('Lobby • Exhibit / swim / '+part,None)
        group.objects.link(obj)
        obj.location = Vector(pivot)
        obj.empty_display_type = 'PLAIN_AXES'
        obj.empty_display_size = .12
        obj['autonomous_lobby'] = True
        obj['fish_part'] = part
        obj['loop_frames'] = PERIOD
        obj['activity_loop'] = 'Seamless hovering swim: tail swish, head/body sway and fin flutter'
        scene.view_layers[0].update()
        if parent is not None:
            parent_at_rest(obj,parent)
        return obj

    body = root('body',(.35,cy,3.45))
    tail = root('tail joint',(-1.03,cy,3.445),body)
    parts = {
        'body': body,
        'upper tail': root('upper tail',(-1.03,cy-.03,3.49),tail),
        'lower tail': root('lower tail',(-1.03,cy-.03,3.40),tail),
        'dorsal': root('dorsal',(-.25,cy+.10,4.175),body),
        'near pectoral': root('near pectoral',(.15,cy-.27,3.22),body),
        'lower ventral': root('lower ventral',(1.08,cy-.05,3.02),body),
    }
    for part,names in FISH_PARTS.items():
        for name in names:
            parent_at_rest(scene.objects['Lobby • Exhibit / '+name],parts[part])

    rests = {obj:obj.location.copy() for obj in [body,tail,*list(parts.values())[1:]]}
    for frame in range(1,PERIOD+2):
        phase = math.tau*(frame-1)/PERIOD
        body.location = rests[body]+Vector((0,.018*math.sin(6*phase+.30),.045*math.sin(6*phase)))
        body.rotation_euler = (0,.025*math.sin(6*phase),.045*math.sin(6*phase+.35))
        tail.rotation_euler = (0,.075*math.sin(18*phase+.70),.36*math.sin(18*phase))
        parts['upper tail'].rotation_euler = (0,.065*math.sin(18*phase+.90),.14*math.sin(18*phase-.35))
        parts['lower tail'].rotation_euler = (0,-.065*math.sin(18*phase+.40),.13*math.sin(18*phase+.25))
        parts['dorsal'].rotation_euler = (.085*math.sin(18*phase+.80),.04*math.sin(12*phase),0)
        parts['near pectoral'].rotation_euler = (
            .18*math.sin(24*phase+1.30),.11*math.sin(12*phase+.60),.07*math.sin(24*phase))
        parts['lower ventral'].rotation_euler = (
            .13*math.sin(24*phase-.80),.05*math.sin(12*phase),.06*math.sin(24*phase+.20))
        for obj in rests:
            obj.keyframe_insert(data_path='location',frame=frame)
            obj.keyframe_insert(data_path='rotation_euler',frame=frame)

    for obj in rests:
        for layer in obj.animation_data.action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        for key in curve.keyframe_points:
                            key.interpolation = 'LINEAR'
                        curve.modifiers.new('CYCLES')
    scene['autonomous_fish_period'] = PERIOD
    scene.frame_set(1)
    scene.view_layers[0].update()
    return {'loop_frames':PERIOD,'scroll_independent':True,
            'tail_cycle_seconds':PERIOD/(18*30),'animated_parts':list(parts)}
