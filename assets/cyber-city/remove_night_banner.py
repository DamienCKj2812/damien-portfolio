"""Remove the narrow night campaign and its duplicate frame from production."""
import json
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parent
MASTER = ROOT/'monochrome-city-solid-tower.blend'
scene = bpy.context.scene
assert scene.name=='MONO / Wire & Particle City'
assert Path(bpy.data.filepath).resolve()==MASTER
scene.frame_set(1);scene.view_layers[0].update()
names = ['Hero display • THE NIGHT LIVES ON • LED display',
         'Hero glow • THE NIGHT LIVES ON • LED display']
before = {o.name:tuple(value for row in o.matrix_world for value in row)
          for o in scene.objects if o.name not in names}
removed = []
for name in names:
    obj = scene.objects.get(name)
    if obj:
        bpy.data.objects.remove(obj,do_unlink=True);removed.append(name)

# simplify_environment.py also generated a rectangle in this shared network.
# Remove only edges on this banner's plane and within its exact authored bounds.
obj = scene.objects['Clean outlines • Billboard frames']
original = obj.data
vertices,edges,radii = [],[],[]
removed_edges = 0
for edge in original.edges:
    points = [obj.matrix_world@original.vertices[index].co for index in edge.vertices]
    on_banner = all(-6.276<=p.x<=-4.224 and abs(p.y+5.92)<.001 and 10.999<=p.z<=28.001 for p in points)
    if on_banner:
        removed_edges+=1
        continue
    start = len(vertices)
    vertices.extend([tuple(original.vertices[index].co) for index in edge.vertices])
    edges.append((start,start+1))
    radii.extend([original.attributes['radius'].data[index].value for index in edge.vertices])
if removed_edges:
    assert removed_edges==4, f'Unexpected night-banner outline count: {removed_edges}'
    mesh = bpy.data.meshes.new('Billboard frames • night campaign removed')
    mesh.from_pydata(vertices,edges,[]);mesh.update()
    radius = mesh.attributes.new('radius','FLOAT','POINT')
    radius.data.foreach_set('value',radii)
    obj.data = mesh
scene.view_layers[0].update()
assert before=={o.name:tuple(value for row in o.matrix_world for value in row)
                for o in scene.objects}, 'An unrelated object transform changed'
portrait = scene.objects['Hero display • KAZE • cyborg campaign • LED display']
assert portrait.get('city_texture')=='portrait.jpg'
assert not any(o.get('city_texture')=='night.png' for o in scene.objects)
scene['removed_night_banner']=True
bpy.context.preferences.filepaths.save_version=1
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER))
print(json.dumps({'checks':'passed','removedObjects':removed,'removedSharedFrameEdges':removed_edges,
                  'portraitAndOtherObjectTransformsPreserved':True}))
