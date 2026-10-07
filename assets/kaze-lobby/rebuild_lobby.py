"""Rebuild the complete lobby and navigation, saving one authoritative blend.

blender --background --factory-startup --python assets/kaze-lobby/rebuild_lobby.py
Add -- --render for previews, or -- --output-dir /path for an isolated rebuild.
Existing manual edits are replaced during a full rebuild; Blender keeps one backup.
"""
import argparse
import json
from pathlib import Path
import sys

import bpy

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--output-dir',type=Path,default=ROOT)
parser.add_argument('--render',action='store_true')
args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
if bpy.data.filepath:
    raise RuntimeError('Run this full rebuild with --factory-startup, not an opened project file.')
output = args.output_dir.resolve()
output.mkdir(parents=True,exist_ok=True)
factory_scenes = list(bpy.data.scenes)
deferred = '--defer-save' not in sys.argv
if deferred:
    sys.argv.append('--defer-save')
try:
    source = ROOT/'build_lobby.py'
    namespace = {'__file__':str(output/source.name),'__name__':'__main__'}
    exec(compile(source.read_text(),str(source),'exec'),namespace)
finally:
    if deferred:
        sys.argv.remove('--defer-save')
# Discard only the factory scenes in this fresh process, retaining the new lobby.
for scene in factory_scenes:
    if scene != bpy.context.scene:
        bpy.data.scenes.remove(scene)
source = ROOT/'add_navigation.py'
sys.path.insert(0,str(ROOT))
from npc_motion import install_npc_motion
install_npc_motion(bpy.context.scene)
from fish_motion import install_fish_motion
fish_motion = install_fish_motion(bpy.context.scene)
manifest_path = output/'lobby-manifest.json'
manifest = json.loads(manifest_path.read_text())
manifest['rear_exhibit']['motion'] = fish_motion
manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
namespace = {'__file__':str(output/source.name),'__name__':'__main__'}
exec(compile(source.read_text(),str(source),'exec'),namespace)
assert bpy.data.filepath==str(output/'kaze-lobby-walkthrough.blend')
assert bpy.context.scene.frame_end==1020
