"""Rebuild all stages, retaining only the final Blender source and its backup.

Run: blender --background --factory-startup --python assets/kaze-elevator/rebuild_elevator.py
"""
import json
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
FINAL = 'kaze-elevator-journey.blend'
STAGES = ['build_elevator.py', 'build_entrance.py', 'build_dialogs.py', 'build_journey.py', 'update_floor_panel.py']
INTERMEDIATE_FILES = [
    'kaze-elevator.blend', 'kaze-elevator.blend1',
    'kaze-elevator-entrance.blend', 'kaze-elevator-entrance.blend1',
    'kaze-elevator-interactive.blend', 'kaze-elevator-interactive.blend1',
]


def clean_intermediate_files():
    """Delete only the known generated staging files after verifying the final scene."""
    import bpy

    if not (ROOT / FINAL).is_file():
        raise RuntimeError('Final journey file is missing; intermediate files were retained.')
    if not bpy.data.objects.get('Elevator / Full journey camera'):
        raise RuntimeError('Load the final journey scene before cleaning intermediate files.')
    if bpy.data.libraries:
        raise RuntimeError('Linked library dependencies detected; intermediate files were retained.')
    removed = []
    for name in INTERMEDIATE_FILES:
        path = ROOT / name
        if path.is_file():
            size = path.stat().st_size
            path.unlink()
            removed.append({'name': name, 'bytes': size})
    for name in ['elevator-manifest.json', 'elevator-levels.json', 'entrance-camera.json']:
        path = ROOT / name
        data = json.loads(path.read_text())
        if name == 'elevator-manifest.json':
            data['files']['source'] = FINAL
        else:
            data['source'] = FINAL
        data['rebuild'] = 'rebuild_elevator.py'
        path.write_text(json.dumps(data, indent=2) + '\n')
    return removed


if __name__ == '__main__':
    for stage in STAGES:
        runpy.run_path(str(ROOT / stage), run_name='__main__')
    clean_intermediate_files()
