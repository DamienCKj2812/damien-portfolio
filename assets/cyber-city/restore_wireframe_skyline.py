"""Restore the authored night skyline without rebuilding the tower or motion."""
import json
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
MASTER = ROOT / 'monochrome-city-solid-tower.blend'
PREFIX = 'Wireframe skyline • '


def emission(name, value):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    shader = nodes.new('ShaderNodeEmission')
    shader.inputs['Color'].default_value = (value, value, value, 1)
    shader.inputs['Strength'].default_value = 1
    mat.node_tree.links.new(shader.outputs[0], output.inputs['Surface'])
    mat.diffuse_color = (value, value, value, 1)
    return mat


def restore_skyline(scene):
    silhouette = scene.objects.get('Clean outlines • Skyline silhouettes')
    assert silhouette and len(silhouette.data.edges) > 500, 'The retained skyline source is missing.'
    silhouette.hide_render = False
    silhouette.hide_set(False)
    silhouette['city_render_kind'] = 'lines'
    silhouette['city_skyline'] = True
    silhouette['city_browser_luminance'] = .16
    modifier = next(m for m in silhouette.modifiers if m.type == 'NODES')
    group = bpy.data.node_groups.get(PREFIX + 'silhouette network') or modifier.node_group.copy()
    group.name = PREFIX + 'silhouette network'
    group.nodes.get('Set Material').inputs['Material'].default_value = emission(PREFIX + 'dim white silhouette', .16)
    modifier.node_group = group

    # Restore selected authored window/antenna lights, not the dense facade cloud.
    point_count = 0
    for suffix in (1, 2, 3):
        obj = scene.objects.get(f'Mono • 04 Skyline • particles {suffix}')
        if not obj:
            continue
        obj.hide_render = False
        obj.hide_set(False)
        obj['city_render_kind'] = 'points'
        obj['city_skyline'] = True
        obj['city_browser_luminance'] = .22
        mod = next(m for m in obj.modifiers if m.type == 'NODES')
        name = PREFIX + f'window points {suffix}'
        nodes = bpy.data.node_groups.get(name) or mod.node_group.copy()
        nodes.name = name
        nodes.nodes.get('Set Material').inputs['Material'].default_value = emission(PREFIX + 'small white windows', .22)
        mod.node_group = nodes
        point_count += len(obj.data.vertices)

    # The two opaque replacement blocks mask the recovered distant buildings.
    for obj in scene.objects:
        if obj.name.startswith(('Reference tower • Left background', 'Reference tower • Right background')):
            obj.hide_render = True
            obj.hide_set(True)
    dense = scene.objects.get('Mono • 04 Skyline • particles 0')
    if dense:
        dense.hide_render = True
        dense.hide_set(True)

    # Read only the original tower bodies to recover real architectural bounds.
    # Do not append their scene, lights, cameras, characters or materials to ours.
    with bpy.data.libraries.load(str(ROOT / 'cyber-city-walkthrough.blend'), link=False) as (available, loaded):
        loaded.objects = [name for name in available.objects if
                          name.startswith('Skyline ') and name.endswith('• tower') or
                          name.startswith('Flanking skyline • stepped shaft')]
    specs = []
    segments = []
    def source_world(obj):
        # Unlinked library objects have no evaluated matrix_world yet. Recover
        # the authored transform from their local basis/parent hierarchy.
        assert not obj.constraints and not obj.animation_data
        return source_world(obj.parent) @ obj.matrix_parent_inverse @ obj.matrix_basis if obj.parent else obj.matrix_basis
    for obj in loaded.objects:
        world = source_world(obj)
        corners = [world @ Vector(p) for p in obj.bound_box]
        low = [min(p[i] for p in corners) for i in range(3)]
        high = [max(p[i] for p in corners) for i in range(3)]
        assert low[1] > 0 and low[2] > -.1, f'Invalid recovered skyline placement: {obj.name}'
        specs.append({'name': obj.name, 'bounds': [low, high]})
        # Sparse horizontal belts on the front and one side establish floor
        # scale, while the restored outline retains the original crowns/spires.
        for z in range(5, int(high[2]) - 2, 5):
            segments.extend([((low[0], low[1], z), (high[0], low[1], z)),
                             ((high[0], low[1], z), (high[0], high[1], z))])
        data = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if data.users == 0:
            bpy.data.meshes.remove(data)
    assert len(specs) >= 30, 'Expected the original layered skyline buildings.'
    col = bpy.data.collections.get(PREFIX + 'Architectural detail')
    if not col:
        col = bpy.data.collections.new(PREFIX + 'Architectural detail')
        scene.collection.children.link(col)
    name = PREFIX + 'sparse floor bands'
    obj = scene.objects.get(name)
    vertices = [p for segment in segments for p in segment]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [(2*i, 2*i+1) for i in range(len(segments))], [])
    mesh.update()
    mesh.attributes.new('radius', 'FLOAT', 'POINT').data.foreach_set('value', [.005] * len(vertices))
    if obj:
        previous = obj.data
        obj.data = mesh
        if previous.users == 0:
            bpy.data.meshes.remove(previous)
    else:
        obj = bpy.data.objects.new(name, mesh)
        col.objects.link(obj)
    obj['city_render_kind'] = 'lines'
    obj['city_skyline'] = True
    obj['city_browser_luminance'] = .075
    bands = bpy.data.node_groups.get(PREFIX + 'floor band network') or group.copy()
    bands.name = PREFIX + 'floor band network'
    bands.nodes.get('Set Material').inputs['Material'].default_value = emission(PREFIX + 'faint floor bands', .075)
    mod = next((m for m in obj.modifiers if m.type == 'NODES'), None) or obj.modifiers.new('Sparse architectural bands', 'NODES')
    mod.node_group = bands
    obj.hide_render = False
    obj.hide_set(False)
    report = {'version': 1, 'source': 'cyber-city-walkthrough.blend', 'buildingCount': len(specs),
              'silhouetteSegments': len(silhouette.data.edges), 'floorBandSegments': len(segments),
              'windowPoints': point_count, 'denseFacadeCloud': False, 'palette': 'black / dim white',
              'replacedOpaqueBackgroundBlocks': 2, 'buildings': specs}
    scene['wireframe_skyline'] = json.dumps(report)
    return report


if __name__ == '__main__':
    scene = bpy.context.scene
    assert Path(bpy.data.filepath).resolve() == MASTER
    assert scene.name == 'MONO / Wire & Particle City'
    camera = scene.camera
    snapshots = {}
    for frame in (1, 90, 180, 245, 383, 450):
        scene.frame_set(frame)
        scene.view_layers[0].update()
        snapshots[frame] = {obj.name: obj.matrix_world.copy() for obj in scene.objects}
    scene.frame_set(1)
    report = restore_skyline(scene)
    for frame, snapshot in snapshots.items():
        scene.frame_set(frame)
        scene.view_layers[0].update()
        assert all(scene.objects[name].matrix_world == matrix for name, matrix in snapshot.items()), f'Authored pose changed at {frame}'
    assert scene.camera == camera
    scene.frame_set(1)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(MASTER), compress=True)
    (ROOT / 'wireframe-skyline.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'buildings'}))
