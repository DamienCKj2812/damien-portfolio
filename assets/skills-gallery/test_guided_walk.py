"""Blender regression checks for translation-only walking and mouse-look controls."""
import importlib.util
import math
from pathlib import Path
from types import MethodType, SimpleNamespace

import bpy

ROOT = Path(__file__).resolve().parent
scene = bpy.data.scenes['SKILLS / Technology Gallery']
bpy.context.window.scene = scene
spec = importlib.util.spec_from_file_location('gallery_preview_test',ROOT/'gallery_walk_preview.py')
preview = importlib.util.module_from_spec(spec); spec.loader.exec_module(preview)
camera = scene.objects[preview.CAMERA_NAME]
rig = camera.parent
assert not camera.animation_data and not camera.data.animation_data and not camera.constraints
assert rig and rig.animation_data
start_rotation = camera.rotation_euler.copy()
scene.frame_set(1); bpy.context.view_layer.update()
start = camera.matrix_world.translation.copy()
for frame in [300,770,900,1100,1300,1450,1650,1850,2050]:
    scene.frame_set(frame); bpy.context.view_layer.update()
    assert max(abs(a-b) for a,b in zip(camera.rotation_euler,start_rotation))<.00001
assert (camera.matrix_world.translation-start).length>2
eye = camera.location.copy()
yaw,pitch = preview.apply_mouse_look(camera,0,0,140,80)
assert yaw>.45 and pitch>.25
assert (camera.location-eye).length<.00001
scene.frame_set(1450); bpy.context.view_layer.update()
assert abs(camera.rotation_euler.z+yaw)<.00001
assert abs(camera.rotation_euler.x-(math.pi/2+pitch))<.00001
_,pitch = preview.apply_mouse_look(camera,yaw,pitch,0,100000)
assert abs(pitch-math.radians(75))<.00001
preview.apply_mouse_look(camera,0,0,0,0)
preview.register()
assert hasattr(bpy.types,'GALLERY_PT_walk')
assert len([h for h in bpy.app.handlers.load_pre if h.__name__=='gallery_walk_load_pre'])==1
preview.register()
assert len([h for h in bpy.app.handlers.load_pre if h.__name__=='gallery_walk_load_pre'])==1
view = next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D')
region = next(r for r in view.regions if r.type=='WINDOW')
with bpy.context.temp_override(area=view,region=region):
    # Background Blender has no native input event loop. Exercise the registered
    # modal methods with real camera/area/timer resources and synthetic events.
    if bpy.app.background:
        operator = SimpleNamespace(_window=bpy.context.window,_area=view,_scene=scene,
            _camera=camera,_old_camera=camera,_space=view.spaces.active,
            _finished=False,_dragging=False,_last_mouse=None,_yaw=0.0,_pitch=0.0,
            _timer=bpy.context.window_manager.event_timer_add(.04,window=bpy.context.window))
        operator.finish = MethodType(preview.GALLERY_OT_guided_walk.finish,operator)
        operator.modal = MethodType(preview.GALLERY_OT_guided_walk.modal,operator)
        bpy.app.driver_namespace[preview.RUNTIME_KEY] = operator
    else:
        result = bpy.ops.gallery.guided_walk('INVOKE_DEFAULT')
        assert result=={'RUNNING_MODAL'}
        operator = bpy.app.driver_namespace[preview.RUNTIME_KEY]
    x,y = view.x+view.width//2,view.y+view.height//2
    def event(kind,value='NOTHING',dx=0,dy=0):
        return SimpleNamespace(type=kind,value=value,mouse_x=x+dx,mouse_y=y+dy)
    operator.modal(bpy.context,event('RIGHTMOUSE','PRESS'))
    operator.modal(bpy.context,event('MOUSEMOVE',dx=100,dy=40))
    assert abs(camera.rotation_euler.z)>.3
    operator.modal(bpy.context,event('RIGHTMOUSE','RELEASE',dx=view.width))
    assert not operator._dragging
    operator.modal(bpy.context,event('R','PRESS'))
    assert abs(camera.rotation_euler.z)<.00001
    operator.modal(bpy.context,event('ESC','PRESS'))
    assert preview.RUNTIME_KEY not in bpy.app.driver_namespace
    assert operator._timer is None
preview.unregister()
assert not hasattr(bpy.types,'GALLERY_PT_walk')
print({'checks':'passed','movement_only':True,'mouse_look':True,
       'pitch_clamp':True,'modal_drag_and_escape':True,'registration_cleanup':True})
