"""Run this embedded Blender text once; then F3 > Project Hallway: Walk.

Mouse: look around. W/S or Up/Down: move along the fixed hallway axis.
Shift: faster movement. Tab: release/recapture mouse. Esc: stop controller.
NPC time always advances while this controller is active, including at rest.
"""
import math
import time

import bpy
from mathutils import Vector


class HallwayState:
    """Keep navigation separate from the wall-clock NPC animation timeline."""

    def __init__(self, y=-7.8, end=98.8, yaw=0, pitch=0, now=None):
        self.y = y
        self.end = end
        self.yaw = yaw
        self.pitch = pitch
        self.started = time.perf_counter() if now is None else now
        self.last_tick = self.started

    def look(self, dx, dy):
        self.yaw = (self.yaw + dx * .0025) % math.tau
        self.pitch = max(-math.radians(85), min(math.radians(85), self.pitch + dy * .0025))

    def tick(self, now, forward=0, fast=False, fps=30):
        dt = max(0, min(.1, now - self.last_tick))
        self.last_tick = now
        self.y = max(-7.8, min(self.end, self.y + forward * (8 if fast else 3) * dt))
        # Absolute elapsed time: even slow redraws or no movement keep NPCs live.
        return 1 + ((now - self.started) * fps) % 1200

    def direction(self):
        return Vector((math.sin(self.yaw) * math.cos(self.pitch),
                       math.cos(self.yaw) * math.cos(self.pitch), math.sin(self.pitch)))


class HALLWAY_OT_walk(bpy.types.Operator):
    bl_idname = 'hallway.walk'
    bl_label = 'Project Hallway: Walk'
    bl_description = 'Free mouse-look, straight-line walking, continuously animated NPCs'
    _running = None

    @classmethod
    def poll(cls, context):
        return (context.area is not None and context.area.type == 'VIEW_3D'
                and 'Project Hallway / free-look camera' in context.scene.objects
                and cls._running is None)

    def invoke(self, context, event):
        self.window = context.window
        self.area = context.area
        self.region = next(r for r in self.area.regions if r.type == 'WINDOW')
        self.wm = context.window_manager
        self.scene = context.scene
        self.camera = self.scene.objects['Project Hallway / free-look camera']
        if context.screen.is_animation_playing:
            bpy.ops.screen.animation_cancel(restore_frame=False)
        self.scene.camera = self.camera
        direction = self.camera.rotation_quaternion @ Vector((0, 0, -1))
        self.state = HallwayState(y=self.camera.location.y, end=self.scene['hallway_length_m'] - 3,
                                 yaw=math.atan2(direction.x, direction.y),
                                 pitch=math.asin(max(-1, min(1, direction.z))))
        self.keys = set()
        self.captured = True
        self.request_stop = False
        self.center = (self.region.x + self.region.width // 2, self.region.y + self.region.height // 2)
        space = self.area.spaces.active
        space.region_3d.view_perspective = 'CAMERA'
        space.region_3d.view_camera_zoom = 0
        space.region_3d.view_camera_offset = (0, 0)
        space.lock_camera = False
        self.window.cursor_modal_set('NONE')
        self.window.cursor_warp(*self.center)
        self.timer = self.wm.event_timer_add(1 / 30, window=self.window)
        self.wm.modal_handler_add(self)
        type(self)._running = self
        self.area.header_text_set('HALLWAY LIVE | Mouse: look | W/S: forward/back | Shift: faster | Tab: release mouse | Esc: exit')
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        try:
            if self.request_stop or (event.type == 'ESC' and event.value == 'PRESS'):
                self.finish()
                return {'FINISHED'}
            if event.type == 'WINDOW_DEACTIVATE':
                self.keys.clear()
            if event.type == 'TAB' and event.value == 'PRESS':
                self.captured = not self.captured
                self.keys.clear()
                if self.captured:
                    self.window.cursor_modal_set('NONE')
                    self.window.cursor_warp(*self.center)
                else:
                    self.window.cursor_modal_restore()
                return {'RUNNING_MODAL'}
            if self.captured and event.type in {'W', 'S', 'UP_ARROW', 'DOWN_ARROW', 'LEFT_SHIFT', 'RIGHT_SHIFT'}:
                if event.value == 'PRESS':
                    self.keys.add(event.type)
                elif event.value == 'RELEASE':
                    self.keys.discard(event.type)
                return {'RUNNING_MODAL'}
            if self.captured and event.type == 'MOUSEMOVE':
                dx, dy = event.mouse_x - self.center[0], event.mouse_y - self.center[1]
                if dx or dy:
                    self.state.look(dx, dy)
                    self.window.cursor_warp(*self.center)
                return {'RUNNING_MODAL'}
            if event.type == 'TIMER':
                forward = int(bool(self.keys & {'W', 'UP_ARROW'})) - int(bool(self.keys & {'S', 'DOWN_ARROW'}))
                frame = self.state.tick(time.perf_counter(), forward, bool(self.keys & {'LEFT_SHIFT', 'RIGHT_SHIFT'}),
                                        self.scene.render.fps / self.scene.render.fps_base)
                self.scene.frame_set(int(frame), subframe=frame % 1)
                self.camera.location = (0, self.state.y, 2.45)
                self.camera.rotation_quaternion = self.state.direction().to_track_quat('-Z', 'Y')
                self.area.tag_redraw()
                return {'RUNNING_MODAL'}
            return {'RUNNING_MODAL'} if self.captured else {'PASS_THROUGH'}
        except (ReferenceError, RuntimeError):
            self.finish()
            return {'CANCELLED'}

    def finish(self):
        if self.timer is not None:
            self.wm.event_timer_remove(self.timer)
            self.timer = None
        self.window.cursor_modal_restore()
        try:
            self.area.header_text_set(None)
        except ReferenceError:
            pass
        type(self)._running = None

    def cancel(self, context):
        self.finish()


class HALLWAY_OT_stop(bpy.types.Operator):
    bl_idname = 'hallway.stop'
    bl_label = 'Stop Hallway Controls'

    def execute(self, context):
        if HALLWAY_OT_walk._running:
            HALLWAY_OT_walk._running.request_stop = True
        return {'FINISHED'}


class HALLWAY_PT_controls(bpy.types.Panel):
    bl_label = 'Project Hallway'
    bl_idname = 'HALLWAY_PT_controls'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Hallway'

    def draw(self, context):
        layout = self.layout
        layout.operator('hallway.stop' if HALLWAY_OT_walk._running else 'hallway.walk',
                        text='Stop Controls' if HALLWAY_OT_walk._running else 'Start Walking', icon='PLAY')
        for label in ('Mouse: look freely', 'W/S or Up/Down: walk straight', 'Shift: faster walking',
                      'Tab: release/capture mouse', 'Esc: exit controls', 'NPCs animate even while standing still'):
            layout.label(text=label)


CLASSES = (HALLWAY_OT_walk, HALLWAY_OT_stop, HALLWAY_PT_controls)


def register():
    for cls in CLASSES:
        old = getattr(bpy.types, cls.__name__, None)
        if old:
            if cls is HALLWAY_OT_walk and old._running:
                old._running.finish()
            bpy.utils.unregister_class(old)
        bpy.utils.register_class(cls)


def unregister():
    if HALLWAY_OT_walk._running:
        HALLWAY_OT_walk._running.finish()
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)


if __name__ == '__main__':
    register()
