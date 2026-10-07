"""Remove the exhibit's sub-ceiling without rebuilding or changing the fish rig."""
import json
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parent
scene = bpy.data.scenes['KAZE / Monochrome Atrium']
names = ['Lobby • Exhibit / bridge-connected canopy',
         'Lobby • Exhibit / bridge-connected canopy / feature edges',
         'Lobby • Exhibit / canopy front light']
removed = []
for name in names:
    obj = scene.objects.get(name)
    if obj:
        bpy.data.objects.remove(obj, do_unlink=True)
        removed.append(name)
assert all(name not in scene.objects for name in names)
bpy.context.preferences.filepaths.save_version = 1
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'kaze-lobby-walkthrough.blend'))
path = ROOT/'lobby-manifest.json'
manifest = json.loads(path.read_text())
manifest['rear_exhibit'].pop('canopy_underside_z', None)
manifest['rear_exhibit']['sub_ceiling'] = False
manifest['objects'] = len(scene.objects)
path.write_text(json.dumps(manifest, indent=2))
print({'removed': removed, 'fish_exhibit_sub_ceiling': False})
