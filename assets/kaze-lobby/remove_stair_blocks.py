"""Remove the three projecting solid blocks at the toe of each staircase."""
import json
from pathlib import Path
import sys

import bpy

ROOT = Path(__file__).resolve().parent
scene = bpy.data.scenes['KAZE / Monochrome Atrium']
bpy.context.window.scene = scene
targets = {f'Lobby • Stair {side} / tread {index:02d}' for side in ['L','R'] for index in [1,2,3]}
retained = {o.name:o.matrix_world.copy() for o in scene.objects if o.name not in targets}
removed = []
for name in sorted(targets):
    obj = scene.objects.get(name)
    if obj:
        mesh = obj.data
        bpy.data.objects.remove(obj,do_unlink=True)
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
        removed.append(name)
assert not any(scene.objects.get(name) for name in targets)
assert sum('/ tread ' in o.name for o in scene.objects)==74
for name,matrix in retained.items():
    assert scene.objects[name].matrix_world == matrix, f'Unexpected change to {name}'
manifest = json.loads((ROOT/'lobby-manifest.json').read_text())
manifest.update(objects=len(scene.objects),stair_solid_treads=74,stair_outline_only_treads=6)
(ROOT/'lobby-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
if '--render' in sys.argv:
    original = (scene.camera,scene.render.resolution_x,scene.render.resolution_y,
                scene.render.resolution_percentage,scene.render.filepath)
    scene.render.resolution_percentage = 100
    for camera_name,width,height,filename in [
        ('Lobby • Concept portrait camera',720,1120,'lobby-concept.png'),
        ('Lobby • Wide lobby activity camera',1280,800,'lobby-wide.png')]:
        scene.camera = scene.objects[camera_name]
        scene.render.resolution_x = width; scene.render.resolution_y = height
        scene.render.filepath = str(ROOT/filename)
        bpy.ops.render.render(write_still=True)
    (scene.camera,scene.render.resolution_x,scene.render.resolution_y,
     scene.render.resolution_percentage,scene.render.filepath) = original
print(json.dumps({'checks':'passed','removed_blocks':removed,'preserved_objects':len(retained)}))
