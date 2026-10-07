"""Focused master-saving NPC update using the canonical generator functions."""
import ast
import json
import math
from pathlib import Path
import bpy
from mathutils import Euler, Vector

ROOT = Path(__file__).resolve().parent
scene = bpy.data.scenes['SKILLS / Technology Gallery']
source = ROOT/'build_gallery.py'
names = {'smooth_keys','configure_gallery_visitors','gaze_target','solve_knee',
         'set_segment','gait_foot','pose_visitor','bake_gallery_visitors','validate_gallery_visitors'}
tree = ast.parse(source.read_text())
module = ast.Module(body=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names],type_ignores=[])
exec(compile(module,str(source),'exec'),globals())
roots = sorted([obj for obj in scene.objects if obj.get('activity')],key=lambda obj:obj.name)
assert len(roots)==6
people = [{'root':root,'parts':{obj['joint']:obj for obj in root.children if obj.get('joint')},
           'phase':phase,'activity':root['activity']} for root,phase in zip(roots,[.11,.47,.27,.61,.83,.39])]
configure_gallery_visitors(people)
positions = bake_gallery_visitors(people)
validate_gallery_visitors(people,positions)
import sys
sys.path.insert(0,str(ROOT))
from gallery_walk import curves, validate_guided_walk
for root in roots:
    root['guided_walk_phase_offset']=0
    for obj in [root,*root.children]:
        for curve in curves(obj):
            if not any(m.type=='CYCLES' for m in curve.modifiers): curve.modifiers.new('CYCLES')
walk = json.loads((ROOT/'gallery-walk.json').read_text())
validate_guided_walk(scene,walk)
scene['autonomous_npc_period']=959
bpy.context.preferences.filepaths.save_version=1
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print({'checks':'passed','autonomous_visitors':6,'loop_frames':959})
