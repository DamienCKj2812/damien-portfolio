"""Complete the rounded wall frame's light without rebuilding the office."""
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
scene = bpy.data.scenes['ABOUT / Skyline Office']
fine = scene.objects['Office • Feature wall / fine rounded frame']
name = 'Office • Feature wall / continuous rounded frame light'
light = scene.objects.get(name) or scene.objects['Office • Feature wall / upper and side frame light']
assert fine.type == light.type == 'CURVE'
assert light.data.users == 1, 'Do not modify shared curve data.'
points = [tuple(point.co) for point in fine.data.splines[0].points]
assert len(points) > 48 and (Vector(points[0][:3])-Vector(points[-1][:3])).length < 1e-6
light.name = name
light.data.splines.clear()
spline = light.data.splines.new('POLY')
spline.points.add(len(points)-1)
for point, (_, y, z, _) in zip(spline.points, points):
    point.co = (5.802, y, z, 1)
assert all(abs(point.co.y-y) < 1e-6 and abs(point.co.z-z) < 1e-6
           for point, (_, y, z, _) in zip(spline.points, points))
assert (spline.points[0].co-spline.points[-1].co).length < 1e-6
assert len(light.data.splines) == 1
bpy.context.preferences.filepaths.save_version = 1
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'about-office.blend'))
print({'frame_light': name, 'closed_outline': True, 'segments': len(points)-1,
       'bevel_radius_m': light.data.bevel_depth})
