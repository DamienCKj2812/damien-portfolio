"""Render short GIF excerpts of the native Blender NPC animation.

blender --background --python-exit-code 1 --python assets/project-hallway/render_motion_preview.py
Requires Pillow in Blender's Python environment. Does not save the model.
"""
from pathlib import Path
import sys
import tempfile

import bpy
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'assets/project-hallway'
bpy.ops.wm.open_mainfile(filepath=str(OUT / 'project-hallway.blend'))
scene = bpy.context.scene
scene.render.resolution_x = 480
scene.render.resolution_y = 270
scene.cycles.samples = 8
scene.cycles.adaptive_threshold = .1
scene.cycles.use_denoising = True
for camera, filename in (('Conversation review', 'npc-conversation-preview.gif'),
                         ('Walking review', 'npc-walking-preview.gif'),
                         ('Thinking review', 'npc-thinking-preview.gif')):
    if '--walking-only' in sys.argv and camera != 'Walking review':
        continue
    scene.camera = scene.objects['Project Hallway / ' + camera]
    images = []
    with tempfile.TemporaryDirectory(prefix='hallway-motion-', dir='/tmp/opencode') as temporary:
        for frame in range(1, 121, 10):
            scene.frame_set(frame)
            scene.render.filepath = str(Path(temporary) / f'{frame:04d}.png')
            bpy.ops.render.render(write_still=True)
            with Image.open(scene.render.filepath) as image:
                images.append(image.convert('RGB').quantize(colors=128))
        images[0].save(OUT / filename, save_all=True, append_images=images[1:],
                       duration=333, loop=0, disposal=2)
    print('MOTION PREVIEW:', OUT / filename)
