"""One-time verified binary cleanup: keep the main lobby and one recovery copy.

Run in background Blender with kaze-lobby-walkthrough.blend opened.
Only removes the two obsolete lobby files explicitly listed below.
"""
import hashlib
import json
from pathlib import Path
import shutil

import bpy

ROOT = Path(__file__).resolve().parent
main = ROOT/'kaze-lobby-walkthrough.blend'
assert Path(bpy.data.filepath).resolve()==main
scene = bpy.data.scenes['KAZE / Monochrome Atrium']
bpy.context.window.scene = scene
assert scene.frame_end==1020 and scene.render.fps==30
assert scene.objects.get('Lobby • Navigation / walkthrough camera')
assert scene.compositing_node_group
old = ROOT/'kaze-lobby.blend'
if old.exists():
    with bpy.data.libraries.load(str(old),link=False) as (source,target):
        old_objects = {n for n in source.objects if n.startswith('Lobby • ')}
    assert old_objects <= {o.name for o in scene.objects}, 'Main file is missing static lobby objects.'
scene.frame_set(1020); bpy.context.view_layer.update()
assert abs(scene.objects['Lobby • Elevator R1 / left door leaf'].location.x-2.455)<.001
assert abs(scene.objects['Lobby • Elevator R1 / right door leaf'].location.x-5.645)<.001
backup = ROOT/'kaze-lobby-walkthrough.blend1'
shutil.copy2(main,backup)
assert hashlib.sha256(main.read_bytes()).digest()==hashlib.sha256(backup.read_bytes()).digest()
removed = []
for path in [old,ROOT/'kaze-lobby.blend1']:
    if path.exists():
        path.unlink()
        removed.append(path.name)
manifest_path = ROOT/'lobby-manifest.json'
manifest = json.loads(manifest_path.read_text())
manifest.update(blend=main.name,recovery_backup=backup.name,objects=len(scene.objects),
                camera=scene.camera.name,frames=[1,1020],fps=30,duration_s=34)
manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'checks':'passed','kept':[main.name,backup.name],'removed':removed,
                  'backup_matches_verified_main':True}))
