"""Read-only first-three-logo and qualification-label checks."""
import hashlib
import json
from pathlib import Path

import bpy
from mathutils import Vector

OUT = Path(__file__).resolve().parent
scene = bpy.context.scene
content = json.loads((OUT / 'milestones.json').read_text())
logos = json.loads((OUT / 'logos/logo-manifest.json').read_text())
package = OUT.parents[1] / 'public/models/rooms/experience'
manifest = json.loads((package / 'scene.json').read_text())
expected = {'diploma-information-technology': 'apu', 'lyj-events-marketing': 'lyj', 'cos-great-trading': 'cos'}
for item in content['milestones']:
    root = next(obj for obj in scene.objects if obj.get('milestone_id') == item['id'])
    title = next(obj for obj in root.children if obj.name.endswith(' / title'))
    assert title.data.body == item.get('cardHeading', item['cardTitle'])
    if item.get('cardSpecialism'):
        subtitle = next(obj for obj in root.children if obj.get('timeline_specialism'))
        assert subtitle.data.body == item['cardSpecialism']
    if item['id'] in expected:
        identity = expected[item['id']]
        logo = next(obj for obj in root.children if obj.get('milestone_logo'))
        assert logo.data.uv_layers.get('LogoUV') and not logo.hide_render
        assert all(abs(vertex.co.x) < .95 and 1.55 < vertex.co.z < 3.95 for vertex in logo.data.vertices)
        image = next(node.image for node in logo.data.materials[0].node_tree.nodes if node.type == 'TEX_IMAGE')
        assert image.packed_file
        assert logos[identity]['palette'] == 'original-color RGBA'
        assert any(max(image.pixels[index:index+3]) - min(image.pixels[index:index+3]) > .05
                   for index in range(0, len(image.pixels)-3, 4*997)), f'Logo was unintentionally desaturated: {identity}'
        texture = logos[identity]['texture']
        assert hashlib.sha256((package / texture).read_bytes()).hexdigest() == logos[identity]['outputSha256']
        source = OUT.parents[1] / logos[identity]['source']
        assert hashlib.sha256(source.read_bytes()).hexdigest() == logos[identity]['sourceSha256']
        assert all(obj.hide_render for obj in root.children if obj.name.startswith('Milestone icon / '))
    for obj in root.children:
        if obj.type == 'FONT':
            bounds = [obj.matrix_local @ Vector(point) for point in obj.bound_box]
            assert all(abs(point.x) < .95 and 1.55 < point.z < 3.95 for point in bounds), f'Board text outside frame: {obj.name}'
assert len([group for group in manifest['groups'] if group.get('role') == 'milestoneLogo']) == 3
assert set(manifest['textures']) == {value['texture'] for value in logos.values()}
digest = hashlib.sha256()
for field in ['geometry', 'animation', 'navigation']:
    if field == 'navigation':
        digest.update((package / manifest['navigation']['route']['file']).read_bytes())
    else:
        digest.update((package / manifest[field]).read_bytes())
for texture in sorted(manifest['textures']):
    digest.update((package / texture).read_bytes())
assert digest.hexdigest()[:12] == manifest['assetHash'], 'Logo bytes must participate in the package hash'
print(json.dumps({'checks': 'passed', 'qualificationLabels': 2, 'suppliedOriginalColorLogos': 3,
                  'packedNativeImages': True, 'boardBounds': True, 'sourceFilesUnchanged': True, 'browserHashIncludesLogos': True}))
