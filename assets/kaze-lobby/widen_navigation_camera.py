"""Widen only the saved navigation lens; preserve camera route and door timing."""
import ast
import bisect
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
scene = bpy.data.scenes['KAZE / Monochrome Atrium']
bpy.context.window.scene = scene
camera = scene.objects['Lobby • Navigation / walkthrough camera']
source = ast.parse((ROOT/'add_navigation.py').read_text())
helpers = ast.Module(body=[n for n in source.body if
    (isinstance(n,ast.FunctionDef) and n.name in {'pchip','key_interpolation'}) or
    (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='LENS' for t in n.targets))],type_ignores=[])
exec(compile(helpers,str(ROOT/'add_navigation.py'),'exec'),globals())
payload = json.loads((ROOT/'navigation-camera.json').read_text())
for frame in range(1,scene.frame_end+1):
    camera.data.lens = pchip(LENS,frame)[0]
    camera.data.keyframe_insert(data_path='lens',frame=frame)
    payload['samples'][frame-1]['lens_mm'] = camera.data.lens
key_interpolation(camera.data,'LINEAR')
payload['handoff']['camera']['lens_mm'] = payload['samples'][-1]['lens_mm']
payload['navigation_fov_note'] = 'Wide 16mm entrance, 15mm escalator, 14mm elevator approach.'
(ROOT/'navigation-camera.json').write_text(json.dumps(payload,indent=2)+'\n')
(ROOT/'navigation-handoff.json').write_text(json.dumps({k:v for k,v in payload.items() if k!='samples'},indent=2)+'\n')
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective = 'CAMERA'
            area.spaces.active.region_3d.view_camera_zoom = 18
            area.spaces.active.region_3d.view_camera_offset = (0,0)
scene.camera = camera
scene.frame_set(1); bpy.context.view_layer.update()
assert abs(camera.data.lens-16)<.001
scene.frame_set(scene.frame_end); bpy.context.view_layer.update()
assert abs(camera.data.lens-14)<.001
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'kaze-lobby-walkthrough.blend'))
if '--render' in sys.argv:
    for frame,filename in [(1,'navigation-start.png'),(600,'navigation-escalator.png'),
                           (840,'navigation-elevator-arrival.png'),(scene.frame_end,'navigation-elevator-open.png')]:
        scene.frame_set(frame)
        scene.render.filepath = str(ROOT/filename)
        bpy.ops.render.render(write_still=True)
print(json.dumps({'checks':'passed','start_lens_mm':16,'escalator_lens_mm':15,
                  'final_lens_mm':14,'viewport_camera_zoom':18}))
