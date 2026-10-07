"""Run once, then F3 > Timeline Observatory: Guided Walk.

Only the walking position follows the route. Mouse-look is never auto-aimed.
Space pauses movement; the globe keeps rotating. Tab releases mouse; Esc exits.
"""
import json
import math
import time

import bpy
from mathutils import Vector

ROOT_NAME = 'Timeline Observatory / guided movement rig'
CAMERA_NAME = 'Timeline Observatory / guided free-look camera'


def location_curves(root):
    return [curve for layer in root.animation_data.action.layers for strip in layer.strips
            for bag in strip.channelbags for curve in bag.fcurves if curve.data_path == 'location']


def route_position(curves, frame):
    position = Vector((0, 0, 0))
    for curve in curves:
        position[curve.array_index] = curve.evaluate(frame)
    return position


class JourneyClock:
    def __init__(self, fps=30, frame=1, now=None, period=2400):
        self.fps = fps
        self.started = time.perf_counter() if now is None else now
        self.previous = self.started
        self.start_frame = frame
        self.walk_seconds = (frame - 1) / fps
        self.paused = False
        self.period = period

    def tick(self, now):
        if not self.paused:
            self.walk_seconds += max(0, now - self.previous)
        self.previous = now
        global_frame = 1 + (self.start_frame - 1 + (now - self.started) * self.fps) % self.period
        walk_frame = 1 + self.walk_seconds * self.fps % self.period
        return global_frame, walk_frame

    def jump(self, frame):
        self.walk_seconds = (frame - 1) / self.fps


class OBSERVATORY_OT_guided_walk(bpy.types.Operator):
    bl_idname = 'observatory.guided_walk'
    bl_label = 'Timeline Observatory: Guided Walk'
    bl_description = 'Visit the journey nodes in order, with unrestricted mouse-look'
    _running = None

    @classmethod
    def poll(cls, context):
        return (context.area is not None and context.area.type == 'VIEW_3D'
                and CAMERA_NAME in context.scene.objects and cls._running is None)

    def invoke(self, context, event):
        self.window, self.area, self.scene = context.window, context.area, context.scene
        self.wm = context.window_manager
        self.region = next(r for r in self.area.regions if r.type == 'WINDOW')
        self.root = self.scene.objects[ROOT_NAME]
        self.camera = self.scene.objects[CAMERA_NAME]
        self.curves = location_curves(self.root)
        self.stations = json.loads(self.scene['guided_walk_stations'])
        if context.screen.is_animation_playing:
            bpy.ops.screen.animation_cancel(restore_frame=False)
        self.scene.camera = self.camera
        self.clock = JourneyClock(self.scene.render.fps / self.scene.render.fps_base,
                                  self.scene.frame_current_final, period=self.scene['guided_walk_period'])
        direction = self.camera.rotation_quaternion @ Vector((0, 0, -1))
        self.yaw = math.atan2(direction.x, direction.y)
        self.pitch = math.asin(max(-1, min(1, direction.z)))
        self.captured, self.request_stop = True, False
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
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        try:
            if self.request_stop or (event.type == 'ESC' and event.value == 'PRESS'):
                self.finish()
                return {'FINISHED'}
            if event.type == 'TAB' and event.value == 'PRESS':
                self.captured = not self.captured
                if self.captured:
                    self.window.cursor_modal_set('NONE')
                    self.window.cursor_warp(*self.center)
                else:
                    self.window.cursor_modal_restore()
                return {'RUNNING_MODAL'}
            if self.captured and event.type == 'SPACE' and event.value == 'PRESS':
                self.clock.paused = not self.clock.paused
                return {'RUNNING_MODAL'}
            if self.captured and event.type in {'RIGHT_ARROW', 'LEFT_ARROW', 'HOME'} and event.value == 'PRESS':
                current = 1 + self.clock.walk_seconds * self.clock.fps % self.clock.period
                if event.type == 'HOME':
                    self.clock.jump(1)
                elif event.type == 'RIGHT_ARROW':
                    next_station = next((s for s in self.stations if s['arrivalFrame'] > current + 1), self.stations[0])
                    self.clock.jump(next_station['arrivalFrame'])
                else:
                    previous = [s for s in self.stations if s['arrivalFrame'] < current - 1]
                    self.clock.jump((previous[-1] if previous else self.stations[-1])['arrivalFrame'])
                return {'RUNNING_MODAL'}
            if self.captured and event.type == 'MOUSEMOVE':
                dx, dy = event.mouse_x - self.center[0], event.mouse_y - self.center[1]
                if dx or dy:
                    self.yaw = (self.yaw + dx * .0025) % math.tau
                    self.pitch = max(-math.radians(85), min(math.radians(85), self.pitch + dy * .0025))
                    self.window.cursor_warp(*self.center)
                return {'RUNNING_MODAL'}
            if event.type == 'TIMER':
                global_frame, walk_frame = self.clock.tick(time.perf_counter())
                self.scene.frame_set(int(global_frame), subframe=global_frame % 1)
                # Movement only: neither the rig nor the camera is auto-rotated.
                self.root.location = route_position(self.curves, walk_frame)
                direction = Vector((math.sin(self.yaw) * math.cos(self.pitch),
                                    math.cos(self.yaw) * math.cos(self.pitch), math.sin(self.pitch)))
                self.camera.rotation_quaternion = direction.to_track_quat('-Z', 'Y')
                self.camera.location = (0, 0, 2.45)
                stage = next((s['title'] for s in self.stations if s['arrivalFrame'] <= walk_frame <= s['leaveFrame']), 'Walking to the next node')
                state = 'PAUSED' if self.clock.paused else 'GUIDED WALK'
                self.area.header_text_set(f'{state} | {stage} | Mouse: look | Space: pause walk | Arrows: nodes | Tab: release | Esc: exit')
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


class OBSERVATORY_OT_stop(bpy.types.Operator):
    bl_idname = 'observatory.stop'
    bl_label = 'Stop Guided Walk'

    def execute(self, context):
        if OBSERVATORY_OT_guided_walk._running:
            OBSERVATORY_OT_guided_walk._running.request_stop = True
        return {'FINISHED'}


class OBSERVATORY_PT_controls(bpy.types.Panel):
    bl_label = 'Timeline Observatory'
    bl_idname = 'OBSERVATORY_PT_controls'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Observatory'

    def draw(self, context):
        layout = self.layout
        layout.operator('observatory.stop' if OBSERVATORY_OT_guided_walk._running else 'observatory.guided_walk',
                        text='Stop Guided Walk' if OBSERVATORY_OT_guided_walk._running else 'Start Guided Walk')
        for line in ('Mouse: look freely', 'Space: pause/resume walking', 'Arrows: previous/next node',
                     'Home: restart route', 'Tab: release/capture mouse', 'Esc: stop controls'):
            layout.label(text=line)


CLASSES = (OBSERVATORY_OT_guided_walk, OBSERVATORY_OT_stop, OBSERVATORY_PT_controls)


def register():
    for cls in CLASSES:
        old = getattr(bpy.types, cls.__name__, None)
        if old:
            if cls is OBSERVATORY_OT_guided_walk and old._running:
                old._running.finish()
            bpy.utils.unregister_class(old)
        bpy.utils.register_class(cls)


def unregister():
    if OBSERVATORY_OT_guided_walk._running:
        OBSERVATORY_OT_guided_walk._running.finish()
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)


if __name__ == '__main__':
    register()
