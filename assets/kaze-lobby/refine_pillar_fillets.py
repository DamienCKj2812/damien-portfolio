"""Match the existing pillar junction to structural edges without rebuilding."""
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parent
scene = bpy.data.scenes['KAZE / Monochrome Atrium']
original_frame = scene.frame_current
fillets = scene.objects['Lobby • Ceiling / continuous pillar fillets']
collar = scene.objects['Lobby • Ceiling / integrated pillar collar']
material = bpy.data.materials['Lobby • Fine silver edges']
assert fillets.type == 'CURVE'
principled = material.node_tree.nodes.get('Principled BSDF')
assert principled.inputs['Emission Strength'].default_value < 2, 'Structural edges must not export as glow.'


def geometry():
    return (
        tuple(tuple(point.co) for spline in fillets.data.splines for point in spline.points),
        tuple(tuple(vertex.co) for vertex in collar.data.vertices),
        tuple(tuple(face.vertices) for face in collar.data.polygons),
    )


def motion():
    channels = sorted((obj for obj in scene.objects
                       if obj.animation_data and obj.animation_data.action), key=lambda obj: obj.name)
    result = []
    for frame in [1, 320, 510, 690, 840, 900, 990, 1020]:
        scene.frame_set(frame)
        scene.view_layers[0].update()
        for obj in channels:
            result.append((obj.name, tuple(value for row in obj.matrix_world for value in row)))
    return result


before_geometry, before_motion = geometry(), motion()
fillets.data.materials.clear()
fillets.data.materials.append(material)
fillets.data.bevel_depth = .004
assert geometry() == before_geometry, 'Pillar junction geometry changed.'
assert motion() == before_motion, 'Animated transforms changed.'
scene.frame_set(original_frame)
scene.view_layers[0].update()
bpy.context.preferences.filepaths.save_version = 1
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'kaze-lobby-walkthrough.blend'))
print({'pillar_fillets_material': material.name, 'radius_m': fillets.data.bevel_depth,
       'junction_geometry_preserved': True, 'motion_preserved': True})
