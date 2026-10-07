"""Check the native guided route and free-look/pause operator in Blender."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import bpy
from mathutils import Vector

OUT = Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(OUT / 'timeline-observatory.blend'))
scene = bpy.context.scene
spec = importlib.util.spec_from_file_location('observatory_walk_checks', OUT / 'observatory_controls.py')
controls = importlib.util.module_from_spec(spec)
spec.loader.exec_module(controls)
controls.register()
root = scene.objects[controls.ROOT_NAME]
camera = scene.objects[controls.CAMERA_NAME]
curves = controls.location_curves(root)
stations = json.loads(scene['guided_walk_stations'])
assert scene.camera == camera and scene.frame_end == scene['guided_walk_period'] == 2400
assert len(stations) == 6 and len(curves) == 3
assert not camera.animation_data and not camera.constraints and not root.constraints
assert all(curve.data_path == 'location' for curve in curves)
assert bpy.data.texts['observatory_controls.py'].as_string() == (OUT / 'observatory_controls.py').read_text()
assert [s['id'] for s in stations] == [m['id'] for m in json.loads((OUT / 'milestones.json').read_text())['milestones']]
for station in stations:
    for frame in (station['arrivalFrame'], station['arrivalFrame'] + 90, station['leaveFrame']):
        assert (controls.route_position(curves, frame) - Vector(station['viewPosition'])).length < .001
    card = next(o for o in scene.objects if o.get('milestone_id') == station['id'])
    assert abs((Vector(station['viewPosition']) - card.location).length - 2.8) < .001
benches = [o for o in scene.objects if 'viewing bench' in o.name and o.type == 'MESH']
boxes = [[o.matrix_world @ Vector(corner) for corner in o.bound_box] for o in benches]
min_clearance = 100
for frame in range(1, 2401, 10):
    position = controls.route_position(curves, frame)
    min_clearance = min(min_clearance, position.xy.length)
    assert 3.1 < position.xy.length < 12, 'Route crosses dais or leaves floor'
    assert abs(position.z) < .001
    for corners in boxes:
        assert any(position[axis] + .28 < min(v[axis] for v in corners)
                   or position[axis] - .28 > max(v[axis] for v in corners) for axis in (0, 1)), 'Route intersects a bench'
assert (controls.route_position(curves, 1) - controls.route_position(curves, 2401)).length < .001
camera.rotation_quaternion = Vector((.5, -.8, .2)).to_track_quat('-Z', 'Y')
user_view = camera.rotation_quaternion.copy()
for frame in (1, 451, 991, 1801, 2401):
    scene.frame_set(frame)
    assert abs(abs(user_view.dot(camera.rotation_quaternion)) - 1) < .001, 'Route overrides camera orientation'
clock = controls.JourneyClock(now=100)
assert clock.tick(101) == (31, 31)
clock.paused = True
assert clock.tick(102) == (61, 31), 'Pausing movement stops globe time'
clock.jump(451)
assert clock.tick(103) == (91, 451)


class Harness:
    _running = None


session = Harness()
session.request_stop, session.captured = False, True
session.scene, session.root, session.camera = scene, root, camera
session.curves, session.stations = curves, stations
session.clock = controls.JourneyClock(now=100)
session.clock.jump(451)
session.yaw, session.pitch, session.center = .4, .1, (500, 500)
session.timer = object()
events = []
session.window = SimpleNamespace(cursor_warp=lambda *args: events.append('warp'),
                                 cursor_modal_set=lambda *args: events.append('capture'),
                                 cursor_modal_restore=lambda: events.append('release'))
session.wm = SimpleNamespace(event_timer_remove=lambda timer: events.append('remove timer'))
session.area = SimpleNamespace(tag_redraw=lambda: events.append('redraw'), header_text_set=lambda text: events.append('header'))
session.finish = lambda: controls.OBSERVATORY_OT_guided_walk.finish(session)
now = [100.0]
original_clock = controls.time.perf_counter
controls.time.perf_counter = lambda: now[0]


def event(kind, value='NOTHING', **kwargs):
    return controls.OBSERVATORY_OT_guided_walk.modal(session, None, SimpleNamespace(type=kind, value=value, **kwargs))


try:
    event('TIMER')
    event('SPACE', 'PRESS')
    held_position = root.location.copy()
    event('MOUSEMOVE', mouse_x=700, mouse_y=570)
    now[0] = 105
    event('TIMER')
    bpy.context.view_layer.update()
    assert (root.matrix_world.translation - held_position).length < .001, 'Walking pause is overwritten by native animation'
    assert scene.frame_current == 151, 'Globe clock paused with the walking route'
    direction = camera.rotation_quaternion @ Vector((0, 0, -1))
    assert direction.x > .7 and direction.z > .2, 'Mouse-look is not independent'
    view_before_jump = camera.rotation_quaternion.copy()
    event('RIGHT_ARROW', 'PRESS')
    event('TIMER')
    bpy.context.view_layer.update()
    assert (root.matrix_world.translation - Vector(stations[1]['viewPosition'])).length < .001
    assert abs(abs(view_before_jump.dot(camera.rotation_quaternion)) - 1) < .001, 'Node jump auto-aims camera'
    event('TAB', 'PRESS')
    assert not session.captured
    event('ESC', 'PRESS')
    assert session.timer is None and 'remove timer' in events
finally:
    controls.time.perf_counter = original_clock
    controls.unregister()
report = {'nativeRouteFrames': 2400, 'nodeOrder': [s['id'] for s in stations], 'nodeDwellSeconds': 6,
          'minimumDistanceFromRoomCenterMeters': min_clearance, 'orientationForced': False,
          'pauseKeepsGlobeAnimating': True, 'controlsValidation': 'passed'}
(OUT / 'walking-validation.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
