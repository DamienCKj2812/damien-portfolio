"""Refresh only approved exhibit text/metadata in the existing Skills master."""
import hashlib
import json
from array import array
from pathlib import Path

import bpy

ROOT=Path(__file__).resolve().parent
MODEL=ROOT/'skills-gallery.blend'
content=json.loads((ROOT/'skills.json').read_text())
if Path(bpy.data.filepath)!=MODEL:
    bpy.ops.wm.open_mainfile(filepath=str(MODEL))
scene=bpy.context.scene
scene.frame_set(1);scene.view_layers[0].update()


def curves(owner):
    if not owner.animation_data or not owner.animation_data.action:
        return []
    return [curve for layer in owner.animation_data.action.layers for strip in layer.strips
            for bag in strip.channelbags for curve in bag.fcurves]


def structural_fingerprint():
    digest=hashlib.sha256()
    for obj in sorted(scene.objects,key=lambda obj:obj.name):
        digest.update(repr((obj.name,obj.type,obj.parent.name if obj.parent else None,
            list(obj.location),list(obj.rotation_euler),list(obj.rotation_quaternion),list(obj.scale),obj.hide_render,
            [(constraint.name,constraint.type) for constraint in obj.constraints],
            [(modifier.name,modifier.type,getattr(getattr(modifier,'node_group',None),'name',None)) for modifier in obj.modifiers])).encode())
        if obj.type=='MESH':
            digest.update(array('f',(value for vertex in obj.data.vertices for value in vertex.co)).tobytes())
            digest.update(repr([tuple(polygon.vertices) for polygon in obj.data.polygons]).encode())
        elif obj.type=='CURVE' and not (obj.name.startswith('Gallery • Exhibit ') and obj.name.endswith(' / taxonomy branches')):
            digest.update(repr([(spline.type,[(tuple(point.co)) for point in spline.points]) for spline in obj.data.splines]).encode())
        elif obj.type=='CAMERA':
            digest.update(repr((obj.data.lens,obj.data.clip_start,obj.data.clip_end)).encode())
        for curve in curves(obj):
            digest.update(repr((curve.data_path,curve.array_index,[(tuple(point.co),point.interpolation) for point in curve.keyframe_points],[(modifier.type) for modifier in curve.modifiers])).encode())
    return digest.hexdigest()


before=structural_fingerprint()
roots=[obj for obj in scene.objects if obj.get('category')]
assert len(roots)==len(content['entries'])==9
assert len([obj for obj in scene.objects if obj.get('activity')])==6
assert any(obj.get('centre_exhibit_id')=='atat' for obj in scene.objects)
assert not any(obj.get('dots_only') for obj in scene.objects)


def update_text(name,body,size,width):
    obj=scene.objects[name]
    assert obj.type=='FONT'
    obj.data.body=body;obj.data.size=size
    scene.view_layers[0].update()
    actual=max(point[0] for point in obj.bound_box)-min(point[0] for point in obj.bound_box)
    if actual>width:
        obj.data.size*=width/actual


for entry in content['entries']:
    index=entry['number']
    root=next(obj for obj in roots if obj.name.startswith(f'Gallery • Exhibit {index:02d} /'))
    surface=next(obj for obj in root.children if obj.name.endswith(' / content surface'))
    width=max(vertex.co.x for vertex in surface.data.vertices)-min(vertex.co.x for vertex in surface.data.vertices)+.16
    root['category']=entry['title']
    root['concept_items']=' / '.join(entry['displayItems'])
    root['content_status']=entry['contentStatus']
    root['skill_id']=entry['id']
    root['skill_metadata']=json.dumps(entry)
    update_text(f'Gallery • Exhibit {index:02d} / heading',entry['title'].upper(),.17,width*.88)
    update_text(f'Gallery • Exhibit {index:02d} / subheading','APPLIED / PROJECT EVIDENCE',.058,width*.84)
    assert 1 <= len(entry['displayItems']) <= 5
    for item,label in enumerate(entry['displayItems']):
        update_text(f'Gallery • Exhibit {index:02d} / item {item:02d}',label,.115,width*.66)
    for item in range(len(entry['displayItems']), 5):
        name = f'Gallery • Exhibit {index:02d} / item {item:02d}'
        if scene.objects.get(name):
            update_text(name,'',.115,width*.66)
    branches = scene.objects[f'Gallery • Exhibit {index:02d} / taxonomy branches']
    while len(branches.data.splines) > len(entry['displayItems']) + 1:
        branches.data.splines.remove(branches.data.splines[-1])
    assert len(branches.data.splines) == len(entry['displayItems']) + 1, 'Card rows and branch markers must match'
    update_text(f'Gallery • Exhibit {index:02d} / footer',f'ABOUT + PROJECTS / {index:02d}',.056,width*.84)
if 'Gallery • Rear gallery subtitle' in scene.objects:
    scene.objects['Gallery • Rear gallery subtitle'].data.body='PROJECT-BACKED TOOLKIT\nFULL-STACK / DELIVERY / CONTINUOUS LEARNING'
scene['Skills content source']=' + '.join(content['source'])
scene.view_layers[0].update()
after=structural_fingerprint()
assert before==after,'Unexpected architecture, sculpture, animation or camera change; master not saved.'
bpy.context.preferences.filepaths.save_version=1
bpy.ops.wm.save_as_mainfile(filepath=str(MODEL),compress=True)
manifest=json.loads((ROOT/'gallery-manifest.json').read_text())
manifest['categories']=[entry['title'] for entry in content['entries']]
manifest['skillContentSource']=content['source']
(ROOT/'gallery-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(ROOT/'skill-content-verification.json').write_text(json.dumps({'exhibits':9,'structuralFingerprint':after,'architectureSculptureVisitorsAndRoutePreserved':True,'sources':content['source'],'validation':'passed'},indent=2)+'\n')
print('SKILLS CONTENT REFRESH: 9 approved exhibits; architecture, AT-AT, six visitor performances and guided route unchanged')
