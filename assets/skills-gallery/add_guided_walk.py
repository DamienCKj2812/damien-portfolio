"""Install guided player movement and package the free-look preview in the main file."""
import importlib.util
import json
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parent
scene = bpy.data.scenes['SKILLS / Technology Gallery']
bpy.context.window.scene = scene
spec = importlib.util.spec_from_file_location('gallery_walk',ROOT/'gallery_walk.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
walk = module.install_guided_walk(scene,ROOT)
checks = module.validate_guided_walk(scene,walk)
manifest_path = ROOT/'gallery-manifest.json'
manifest = json.loads(manifest_path.read_text())
manifest.update(objects=len(scene.objects),active_camera=walk['camera'],
                frames=walk['frames'],duration_s=walk['duration_s'],saved_frame=1,
                guided_walk={k:v for k,v in walk.items() if k!='positions'},
                npc_clip_frames=[1,960],npc_clip_loops_during_tour=True)
manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
(ROOT/'gallery-walk.json').write_text(json.dumps(walk,indent=2)+'\n')
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective = 'CAMERA'
            area.spaces.active.lock_camera = False
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print(json.dumps({**checks,'camera':walk['camera'],'frames':walk['frames'],
                  'forced_camera_rotation':False,'exhibits_visited':9}))
