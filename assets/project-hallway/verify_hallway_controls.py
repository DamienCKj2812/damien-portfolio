"""Verify navigation, operator event handling, and idle NPC time in Blender."""
import importlib.util
import math
from pathlib import Path
from types import SimpleNamespace

import bpy
from mathutils import Vector

OUT = Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(OUT / 'project-hallway.blend'))
spec = importlib.util.spec_from_file_location('hallway_control_checks', OUT / 'hallway_controls.py')
controls = importlib.util.module_from_spec(spec)
spec.loader.exec_module(controls)
controls.register()
assert hasattr(bpy.ops.hallway, 'walk') and hasattr(bpy.ops.hallway, 'stop')
assert bpy.context.scene.camera.name == 'Project Hallway / free-look camera'
assert bpy.context.scene.camera.animation_data is None
assert bpy.data.texts['hallway_controls.py'].as_string() == (OUT / 'hallway_controls.py').read_text()

state = controls.HallwayState(y=10, end=98.8, now=100)
assert state.tick(101) == 31 and state.y == 10
state.yaw = math.pi
state.tick(101.1, forward=1)
assert abs(state.y - 10.3) < 1e-6, 'Forward motion follows gaze instead of hallway axis'
state.tick(101.2, forward=-1)
assert abs(state.y - 10) < 1e-6
state.tick(101.3, forward=1, fast=True)
assert abs(state.y - 10.8) < 1e-6
state.y = 98.7
state.tick(101.4, forward=1)
assert state.y == 98.8
state.y = -7.7
state.tick(101.5, forward=-1)
assert state.y == -7.8
state.look(50000, 50000)
assert 0 <= state.yaw < math.tau and abs(state.pitch - math.radians(85)) < 1e-6
state.look(0, -100000)
assert abs(state.pitch + math.radians(85)) < 1e-6
assert abs(state.tick(140) - 1) < 1e-6, 'NPC clock does not wrap'


class Harness:
    _running = None


session = Harness()
session.request_stop = False
session.scene = bpy.context.scene
session.camera = session.scene.camera
session.state = controls.HallwayState(now=100)
session.keys = set()
session.captured = True
session.center = (500, 500)
session.timer = object()
events = []
session.window = SimpleNamespace(cursor_warp=lambda *args: events.append('warp'),
                                 cursor_modal_set=lambda *args: events.append('capture'),
                                 cursor_modal_restore=lambda: events.append('release'))
session.wm = SimpleNamespace(event_timer_remove=lambda timer: events.append('remove timer'))
session.area = SimpleNamespace(tag_redraw=lambda: events.append('redraw'),
                              header_text_set=lambda text: events.append('header'))
session.finish = lambda: controls.HALLWAY_OT_walk.finish(session)
clock = [100.0]
original_clock = controls.time.perf_counter
controls.time.perf_counter = lambda: clock[0]


def event(kind, value='NOTHING', **kwargs):
    return controls.HALLWAY_OT_walk.modal(session, None, SimpleNamespace(type=kind, value=value, **kwargs))


try:
    session.scene.frame_set(1)
    walker = next(o for o in session.scene.objects if o.get('npc_animation') == 'walking_loop')
    initial = walker.location.copy()
    clock[0] = 101
    event('TIMER')
    assert session.camera.location == Vector((0, -7.8, 2.45))
    assert (walker.location - initial).length > .05, 'NPC waits for user movement'
    event('W', 'PRESS')
    event('MOUSEMOVE', mouse_x=700, mouse_y=550)
    clock[0] = 101.1
    event('TIMER')
    assert abs(session.camera.location.x) < 1e-6 and session.camera.location.y > -7.8
    forward = session.camera.rotation_quaternion @ Vector((0, 0, -1))
    assert forward.x > .4 and forward.z > .1, 'Mouse look does not turn the camera'
    event('TAB', 'PRESS')
    assert not session.captured and not session.keys
    idle_y = session.camera.location.y
    clock[0] = 102
    event('TIMER')
    assert session.scene.frame_current == 61 and session.camera.location.y == idle_y
    event('TAB', 'PRESS')
    assert session.captured
    event('ESC', 'PRESS')
    assert session.timer is None and 'remove timer' in events and 'release' in events
finally:
    controls.time.perf_counter = original_clock
    controls.unregister()
print('HALLWAY CONTROLS PASSED: registration, free look, axis constraints, speed, limits, idle NPC clock, mouse release, cleanup')
