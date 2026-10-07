"""Fit requested headings and source-backed logo artwork to existing cards."""
import json
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parent


def apply_board_art(scene, root, item):
    title = next(obj for obj in root.children if obj.name.endswith(' / title'))
    title.data.body = item.get('cardHeading', item.get('cardTitle', item['title']))
    title.data.size = .19
    scene.view_layers[0].update()
    if title.dimensions.x > 1.60:
        title.data.size *= 1.60 / title.dimensions.x
    specialism = item.get('cardSpecialism')
    if specialism:
        obj = next((obj for obj in root.children if obj.get('timeline_specialism')), None)
        if not obj:
            data = bpy.data.curves.new(root.name + ' / specialism', 'FONT')
            data.align_x = 'CENTER'
            data.space_character = 1.2
            data.materials.append(title.data.materials[0])
            obj = bpy.data.objects.new(data.name, data)
            root.users_collection[0].objects.link(obj)
            obj.parent = root
            obj.rotation_euler = title.rotation_euler.copy()
            obj.location = (0, -.036, 3.35 if '\n' not in title.data.body else 3.08)
            obj['timeline_specialism'] = True
        obj.data.body = specialism
        obj.data.size = .078
        scene.view_layers[0].update()
        if obj.dimensions.x > 1.64:
            obj.data.size *= 1.64 / obj.dimensions.x
    logo = item.get('logo')
    if not logo:
        return
    for obj in root.children:
        if obj.name.startswith('Milestone icon / '):
            obj.hide_render = True
            obj.hide_set(True)
            obj['timeline_retired_icon'] = True
    metadata = json.loads((ROOT / 'logos/logo-manifest.json').read_text())[logo['id']]
    image = bpy.data.images.get(f'Timeline logo / {logo["id"]}')
    if image:
        bpy.data.images.remove(image)
    image = bpy.data.images.load(str(ROOT / logo['texture']), check_existing=False)
    image.name = f'Timeline logo / {logo["id"]}'
    image.pack()
    width = min(1.42, 1.12 * image.size[0] / image.size[1])
    height = width * image.size[1] / image.size[0]
    obj = next((obj for obj in root.children if obj.get('milestone_logo')), None)
    if not obj:
        data = bpy.data.meshes.new(root.name + ' / supplied logo')
        data.from_pydata([(-width/2, -.052, 2.62-height/2), (width/2, -.052, 2.62-height/2),
                         (width/2, -.052, 2.62+height/2), (-width/2, -.052, 2.62+height/2)], [], [(0, 1, 2, 3)])
        uv = data.uv_layers.new(name='LogoUV')
        for point, value in zip(uv.data, [(0, 0), (1, 0), (1, 1), (0, 1)]):
            point.uv = value
        obj = bpy.data.objects.new(data.name, data)
        root.users_collection[0].objects.link(obj)
        obj.parent = root
    mat = bpy.data.materials.get(f'Timeline logo / {logo["id"]}') or bpy.data.materials.new(f'Timeline logo / {logo["id"]}')
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    output, texture, emission, transparent, mix = (nodes.new(kind) for kind in
        ['ShaderNodeOutputMaterial', 'ShaderNodeTexImage', 'ShaderNodeEmission', 'ShaderNodeBsdfTransparent', 'ShaderNodeMixShader'])
    texture.image = image
    emission.inputs['Strength'].default_value = 1
    mat.node_tree.links.new(texture.outputs['Color'], emission.inputs['Color'])
    mat.node_tree.links.new(texture.outputs['Alpha'], mix.inputs[0])
    mat.node_tree.links.new(transparent.outputs[0], mix.inputs[1])
    mat.node_tree.links.new(emission.outputs[0], mix.inputs[2])
    mat.node_tree.links.new(mix.outputs[0], output.inputs['Surface'])
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    obj['milestone_logo'] = True
    obj['milestone_logo_texture'] = logo['texture']
    obj['milestone_logo_metadata'] = json.dumps(metadata)
    obj.hide_render = False
    obj.hide_set(False)
