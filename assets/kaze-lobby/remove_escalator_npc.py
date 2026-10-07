"""Remove the escalator rider from the existing master without rebuilding."""
from pathlib import Path
import bpy

scene = bpy.data.scenes['KAZE / Monochrome Atrium']
name = 'Lobby • Escalator / riding upstairs'
rider = scene.objects.get(name)
if rider:
    for obj in list(scene.objects):
        if obj.get('npc_owner') == name:
            bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.objects.remove(rider, do_unlink=True)
assert name not in scene.objects
assert len([obj for obj in scene.objects if obj.get('pose_origin') is not None]) == 17
bpy.context.preferences.filepaths.save_version = 1
bpy.ops.wm.save_as_mainfile(filepath=str(Path(__file__).resolve().parent / 'kaze-lobby-walkthrough.blend'))
print({'escalator_npc_removed': True, 'remaining_npcs': 17})
