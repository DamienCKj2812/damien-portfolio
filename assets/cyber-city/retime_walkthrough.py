"""Update the existing camera: stationary tilt first, walking second."""
import bpy
from mathutils import Vector

scene=bpy.context.scene
if bpy.context.screen.is_animation_playing:
    bpy.ops.screen.animation_cancel(restore_frame=False)
camera=scene.objects['Walkthrough • camera']
target=scene.objects['Walkthrough • look target']
path=scene.objects['Walkthrough • editable travel path']
path.data.splines[0].bezier_points[0].co=(12,-35,1.7)
path.data.splines[0].bezier_points[1].co=(5,-22,1.7)
path.data.path_duration=450

def curves(obj):
    action=obj.animation_data.action
    if hasattr(action,'fcurves'):
        return list(action.fcurves)
    return [curve for layer in action.layers for strip in layer.strips for bag in getattr(strip,'channelbags',[]) for curve in bag.fcurves]

# Existing actions are unlinked, not deleted. New timing lives in fresh actions.
camera.animation_data_clear()
travel=camera.constraints['Travel • follow editable Bezier route']
for frame,progress in [(1,0),(90,0),(180,.30),(245,.55),(300,.70),(350,.84),(450,1)]:
    travel.offset_factor=progress
    travel.keyframe_insert(data_path='offset_factor',frame=frame)
for curve in curves(camera):
    for key in curve.keyframe_points:
        key.handle_left_type='AUTO_CLAMPED';key.handle_right_type='AUTO_CLAMPED'
        if key.co.x==1:key.interpolation='LINEAR'

target.animation_data_clear()
for frame,loc in [(1,(0,0,50)),(90,(-1.5,-5.3,1.7)),(180,(-1.5,-3,1.7)),(300,(-1.5,-1,1.7)),(380,(0,4.6,1.6)),(450,(0,4.6,1.6))]:
    target.location=loc;target.keyframe_insert(data_path='location',frame=frame)
for curve in curves(target):
    for key in curve.keyframe_points:
        key.handle_left_type='AUTO_CLAMPED';key.handle_right_type='AUTO_CLAMPED'

for side,name in [(-1,'Entrance • left sliding door'),(1,'Entrance • right sliding door')]:
    door=scene.objects[name];door.animation_data_clear()
    for frame,slide in [(1,0),(245,0),(300,1.65),(450,1.65)]:
        door.location.x=-1.5+side*(.81+slide);door.keyframe_insert(data_path='location',frame=frame)
scene.frame_start=1;scene.frame_end=450;scene.render.fps=30
labels=[('01 • Stationary rooftop view',1),('02 • Looking down / begin walking',90),('03 • Doors opening',245),('04 • Entrance',380),('05 • Inside lobby',410),('06 • Future lobby screen',450)]
for marker in list(scene.timeline_markers):
    if marker.name[:2] in ['01','02','03','04','05','06']:scene.timeline_markers.remove(marker)
for name,frame in labels:scene.timeline_markers.new(name,frame=frame)
scene.camera=camera
stationary=[]
for frame in [1,15,30,45,60,75,90]:
    scene.frame_set(frame);bpy.context.view_layer.update();stationary.append(list(camera.matrix_world.translation))
drift=max((Vector(p)-Vector(stationary[0])).length for p in stationary)
if drift>1e-5:raise RuntimeError(f'Opening camera drifts by {drift} meters')
scene.frame_set(1)
result={'opening_position':stationary[0],'stationary_frames':[1,90],'maximum_drift_m':drift,'walking_begins_after':90,'end_frame':450}
