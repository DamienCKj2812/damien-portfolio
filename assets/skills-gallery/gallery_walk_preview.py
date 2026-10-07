"""Run once in Blender's Text Editor. N sidebar → Gallery Walk → Start Guided Walk.

The saved rig moves on the timeline. Only user mouse input changes camera look.
"""
import json
import math

import bpy
from bpy.app.handlers import persistent

CAMERA_NAME = 'Gallery • Guided walk / free-look camera'
RUNTIME_KEY = 'gallery_guided_walk_runtime'


def apply_mouse_look(camera,yaw,pitch,dx,dy,sensitivity=.0035):
    yaw += dx*sensitivity
    pitch = max(-math.radians(75),min(math.radians(75),pitch+dy*sensitivity))
    camera.rotation_euler = (math.pi/2+pitch,0,-yaw)
    return yaw,pitch


def phase_label(scene):
    stops = json.loads(scene.get('Gallery tour stops','[]'))
    frame = scene.frame_current
    for stop in stops:
        if frame<=stop['end']:
            state = 'Viewing' if frame>=stop['start'] else 'Walking to'
            return f'{state} {stop["label"]} — {stop["hint"]}'
    return 'Returning to the gallery entrance'


class GALLERY_OT_guided_walk(bpy.types.Operator):
    bl_idname = 'gallery.guided_walk'
    bl_label = 'Start Guided Walk'
    bl_description = 'Follow the exhibit route with user-controlled camera look'

    @classmethod
    def poll(cls,context):
        return (context.area and context.area.type=='VIEW_3D'
                and CAMERA_NAME in context.scene.objects
                and not bpy.app.driver_namespace.get(RUNTIME_KEY))

    def invoke(self,context,event):
        self._window = context.window; self._area = context.area
        self._scene = context.scene; self._camera = context.scene.objects[CAMERA_NAME]
        self._old_camera = context.scene.camera
        self._space = context.space_data
        self._old_perspective = self._space.region_3d.view_perspective
        self._dragging = False; self._last_mouse = None
        self._finished = False
        self._yaw = -self._camera.rotation_euler.z
        self._pitch = self._camera.rotation_euler.x-math.pi/2
        self._scene.camera = self._camera; self._scene.frame_set(1)
        self._space.region_3d.view_perspective = 'CAMERA'
        self._space.lock_camera = False
        self._timer = context.window_manager.event_timer_add(.04,window=context.window)
        bpy.app.driver_namespace[RUNTIME_KEY] = self
        context.window_manager.modal_handler_add(self)
        if not context.screen.is_animation_playing:
            bpy.ops.screen.animation_play()
        self._area.header_text_set('Guided movement / hold RMB or MMB to look / Space pause / R reset / Esc stop')
        return {'RUNNING_MODAL'}

    def finish(self,context):
        if getattr(self,'_finished',False):
            return {'CANCELLED'}
        self._finished = True
        if getattr(self,'_timer',None):
            context.window_manager.event_timer_remove(self._timer); self._timer = None
        try:
            if self._window.screen.is_animation_playing:
                bpy.ops.screen.animation_cancel(restore_frame=False)
            self._area.header_text_set(None)
        except (ReferenceError,RuntimeError):
            pass
        if self._old_camera and self._old_camera.name in self._scene.objects:
            self._scene.camera = self._old_camera
        bpy.app.driver_namespace.pop(RUNTIME_KEY,None)
        return {'CANCELLED'}

    def modal(self,context,event):
        if bpy.app.driver_namespace.get(RUNTIME_KEY) is not self:
            return self.finish(context)
        if context.window!=self._window or not any(area==self._area for area in self._window.screen.areas):
            return self.finish(context)
        if event.type=='ESC' and event.value=='PRESS':
            return self.finish(context)
        if event.type=='TIMER':
            if self._scene.frame_current>=self._scene.frame_end and self._window.screen.is_animation_playing:
                bpy.ops.screen.animation_cancel(restore_frame=False)
            self._area.header_text_set(phase_label(self._scene)+' | RMB/MMB look · Space pause · R reset · Esc stop')
            self._area.tag_redraw()
            return {'PASS_THROUGH'}
        inside = (self._area.x<=event.mouse_x<self._area.x+self._area.width
                  and self._area.y<=event.mouse_y<self._area.y+self._area.height)
        if event.type in {'RIGHTMOUSE','MIDDLEMOUSE'} and (inside or self._dragging):
            self._dragging = event.value=='PRESS'
            self._last_mouse = (event.mouse_x,event.mouse_y)
            return {'RUNNING_MODAL'}
        if event.type=='MOUSEMOVE' and self._dragging:
            if self._last_mouse:
                dx,dy = event.mouse_x-self._last_mouse[0],event.mouse_y-self._last_mouse[1]
                self._yaw,self._pitch = apply_mouse_look(self._camera,self._yaw,self._pitch,dx,dy)
            self._last_mouse = (event.mouse_x,event.mouse_y)
            self._area.tag_redraw()
            return {'RUNNING_MODAL'}
        if event.type=='R' and event.value=='PRESS' and inside:
            self._yaw,self._pitch = apply_mouse_look(self._camera,0,0,0,0)
            self._area.tag_redraw(); return {'RUNNING_MODAL'}
        return {'PASS_THROUGH'}

    def cancel(self,context):
        self.finish(context)


class GALLERY_OT_stop_guided_walk(bpy.types.Operator):
    bl_idname = 'gallery.stop_guided_walk'
    bl_label = 'Stop Preview'

    def execute(self,context):
        active = bpy.app.driver_namespace.get(RUNTIME_KEY)
        if active:
            active.finish(context)
        return {'FINISHED'}


class GALLERY_PT_walk(bpy.types.Panel):
    bl_label = 'Guided movement / free look'
    bl_idname = 'GALLERY_PT_walk'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Gallery Walk'

    @classmethod
    def poll(cls,context):
        return CAMERA_NAME in context.scene.objects

    def draw(self,context):
        layout = self.layout
        active = bpy.app.driver_namespace.get(RUNTIME_KEY)
        layout.operator('gallery.stop_guided_walk' if active else 'gallery.guided_walk')
        layout.label(text='Movement follows the timeline.')
        layout.label(text='Camera direction stays yours.')
        layout.separator()
        layout.label(text='Hold RMB / MMB + drag: look')
        layout.label(text='Space: play / pause')
        layout.label(text='R: reset look   Esc: stop')
        layout.label(text=f'Frame {context.scene.frame_current} / {context.scene.frame_end}')


CLASSES = (GALLERY_OT_guided_walk,GALLERY_OT_stop_guided_walk,GALLERY_PT_walk)


@persistent
def gallery_walk_load_pre(_):
    active = bpy.app.driver_namespace.get(RUNTIME_KEY)
    if active:
        active.finish(bpy.context)


def unregister():
    active = bpy.app.driver_namespace.get(RUNTIME_KEY)
    if active:
        active.finish(bpy.context)
    for handler in list(bpy.app.handlers.load_pre):
        if getattr(handler,'__name__','')=='gallery_walk_load_pre':
            bpy.app.handlers.load_pre.remove(handler)
    for cls in reversed(CLASSES):
        existing = getattr(bpy.types,cls.__name__,None)
        if existing:
            bpy.utils.unregister_class(existing)


def register():
    unregister()
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.app.handlers.load_pre.append(gallery_walk_load_pre)


if __name__=='__main__':
    register()
    print('Gallery Walk controls installed. In a 3D View: N → Gallery Walk → Start Guided Walk.')
