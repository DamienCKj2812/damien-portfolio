"""Render a fixed-camera GIF proving the hologram swims without camera movement.

blender --background assets/kaze-lobby/kaze-lobby-walkthrough.blend \
  --python-exit-code 1 --python assets/kaze-lobby/render_fish_preview.py
"""
from pathlib import Path
import tempfile

import bpy
from PIL import Image

ROOT = Path(__file__).resolve().parent
scene = bpy.data.scenes['KAZE / Monochrome Atrium']
bpy.context.window.scene = scene
scene.camera = scene.objects['Lobby • Holographic fish exhibit camera']
camera_pose = scene.camera.matrix_world.copy()
scene.render.resolution_x = 640
scene.render.resolution_y = 426
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.cycles.samples = 4
frames = 48
period = scene['autonomous_fish_period']/6
images = []
with tempfile.TemporaryDirectory(prefix='lobby-fish-',dir='/tmp/opencode') as directory:
    for index in range(frames):
        frame = 1+period*index/frames
        scene.frame_set(int(frame),subframe=frame-int(frame))
        scene.view_layers[0].update()
        assert max(abs(a-b) for ra,rb in zip(camera_pose,scene.camera.matrix_world)
                   for a,b in zip(ra,rb))<1e-6
        filename = Path(directory)/f'frame-{index:03}.png'
        scene.render.filepath = str(filename)
        bpy.ops.render.render(write_still=True)
        with Image.open(filename) as image:
            images.append(image.convert('L').convert('P'))
    duration = period/scene.render.fps*1000
    durations = [10*(round((i+1)*duration/(frames*10))-round(i*duration/(frames*10)))
                 for i in range(frames)]
    images[0].save(ROOT/'holographic-fish-swimming.gif',save_all=True,
                   append_images=images[1:],duration=durations,loop=0,optimize=True)
print({'preview':str(ROOT/'holographic-fish-swimming.gif'),
       'duration_seconds':sum(durations)/1000,'camera_fixed':True})
