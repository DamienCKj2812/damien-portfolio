"""Own the monochrome Malaysia map on the existing office monitor screen."""
import hashlib
import json
import math
from pathlib import Path
import urllib.request

import bpy
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'map-data/malaysia-context.geojson'
SOURCE_URL = 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson'
PREFIX = 'Office • Malaysia screen / '
OLD_CONTENT = ['Screen navigation', 'Screen signature', 'Screen layout panels', 'Screen original idea network',
               'Screen network nodes', 'Screen profile caption', 'Screen globe diagram', 'Screen right caption', 'Screen activity chart']
BOUNDS = (98, .5, 120.2, 8.5)


def geography():
    if not SOURCE.is_file():
        request = urllib.request.Request(SOURCE_URL, headers={'User-Agent': 'Damien-portfolio-asset-authoring'})
        with urllib.request.urlopen(request, timeout=60) as response:
            data = response.read()
        original = json.loads(data)
        countries = {'Malaysia', 'Thailand', 'Indonesia', 'Brunei', 'Singapore'}
        features = [feature for feature in original['features'] if feature['properties'].get('ADMIN') in countries]
        assert any(feature['properties']['ADMIN'] == 'Malaysia' for feature in features)
        SOURCE.write_text(json.dumps({'type': 'FeatureCollection', 'sourceUrl': SOURCE_URL,
                                     'sourceSha256': hashlib.sha256(data).hexdigest(), 'features': features}, separators=(',', ':')) + '\n')
    return json.loads(SOURCE.read_text())


def paint(name, value):
    mat = bpy.data.materials.get(PREFIX + name) or bpy.data.materials.new(PREFIX + name)
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


def clip_segment(a, b):
    x0, y0, x1, y1 = BOUNDS
    dx, dy = b[0] - a[0], b[1] - a[1]
    low, high = 0, 1
    for p, q in [(-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])]:
        if abs(p) < 1e-12:
            if q < 0:
                return None
        else:
            value = q / p
            if p < 0:
                low = max(low, value)
            else:
                high = min(high, value)
        if low > high:
            return None
    return [(a[0] + t * dx, a[1] + t * dy) for t in (low, high)]


def apply_malaysia_screen(scene):
    display = scene.objects['Office • About content screen / web texture target']
    assert display.data.uv_layers.get('ScreenUV')
    for suffix in OLD_CONTENT:
        obj = scene.objects.get('Office • ' + suffix)
        if obj:
            obj.hide_render = True
            obj.hide_set(True)
    col = bpy.data.collections.get(PREFIX + 'Map content')
    if col:
        for obj in list(col.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
    else:
        col = bpy.data.collections.new(PREFIX + 'Map content')
        scene.collection.children.link(col)
    geo = geography()
    white, contour, quiet = paint('white Malaysian land', .56), paint('white coastline and labels', .85), paint('faint regional borders', .16)
    center_lon, center_lat = (BOUNDS[0] + BOUNDS[2]) / 2, (BOUNDS[1] + BOUNDS[3]) / 2
    longitude_scale = math.cos(math.radians(center_lat))
    scale = min(2.22 / ((BOUNDS[2] - BOUNDS[0]) * longitude_scale), .80 / (BOUNDS[3] - BOUNDS[1]))

    def project(point, depth=-.014):
        lon, lat = point[:2]
        return Vector(((lon - center_lon) * longitude_scale * scale, depth, (lat - center_lat) * scale - .06))

    def link(name, data):
        obj = bpy.data.objects.new(PREFIX + name, data)
        col.objects.link(obj)
        obj.parent = display
        obj['office_screen_map'] = True
        return obj

    def strokes(name, segments, mat, width=.001):
        data = bpy.data.curves.new(PREFIX + name, 'CURVE')
        data.dimensions = '3D'
        data.bevel_depth = width
        data.bevel_resolution = 0
        for a, b in segments:
            spline = data.splines.new('POLY')
            spline.points.add(1)
            spline.points[0].co = (*a, 1)
            spline.points[1].co = (*b, 1)
        data.materials.append(mat)
        return link(name, data)

    def label(name, body, position, size, mat=contour):
        data = bpy.data.curves.new(PREFIX + name, 'FONT')
        data.body = body
        data.align_x = 'CENTER'
        data.align_y = 'CENTER'
        data.size = size
        data.space_character = 1.25
        data.materials.append(mat)
        obj = link(name, data)
        obj.location = position
        obj.rotation_euler = (math.pi / 2, 0, 0)
        return obj

    land_vertices, land_faces, malaysia_lines, neighbor_lines = [], [], [], []
    malaysia_polygons = 0
    for feature in geo['features']:
        country = feature['properties']['ADMIN']
        geometry = feature['geometry']
        polygons = [geometry['coordinates']] if geometry['type'] == 'Polygon' else geometry['coordinates']
        for polygon in polygons:
            ring = polygon[0]
            target = malaysia_lines if country == 'Malaysia' else neighbor_lines
            for a, b in zip(ring, ring[1:]):
                segment = clip_segment(a, b)
                if segment:
                    target.append([project(point, -.016) for point in segment])
            if country != 'Malaysia':
                continue
            points = [project(point, -.013) for point in ring[:-1]]
            triangles = tessellate_polygon([points])
            for triangle in triangles:
                start = len(land_vertices)
                land_vertices.extend(tuple(points[point] if isinstance(point, int) else point) for point in triangle)
                land_faces.append((start, start + 1, start + 2))
            malaysia_polygons += 1
    assert malaysia_polygons >= 2
    mesh = bpy.data.meshes.new(PREFIX + 'Malaysia filled geography')
    mesh.from_pydata(land_vertices, [], land_faces)
    mesh.materials.append(white)
    mesh.update()
    country = link('Malaysia filled geography', mesh)
    country['country_code'] = 'MYS'
    strokes('Malaysia coastline', malaysia_lines, contour, .0009)
    strokes('Neighbor country outlines', neighbor_lines, quiet, .00065)
    label('Title', 'M A L A Y S I A', (0, -.017, .445), .062)
    label('Region caption', 'PENINSULAR  +  EAST MALAYSIA', (0, -.017, -.492), .027, quiet)
    for name, point, text_point in [('BRUNEI', (114.94, 4.54), (113.45, 7.45)),
                                   ('SINGAPORE', (103.82, 1.35), (105.0, .88))]:
        target, caption = project(point, -.019), project(text_point, -.019)
        label(name, name, caption, .033)
        strokes(name + ' leader', [(caption + Vector((0, 0, -.025)), target)], contour, .0007)
        delta = .006
        strokes(name + ' marker', [(target + Vector((-delta, 0, 0)), target + Vector((delta, 0, 0))),
                                  (target + Vector((0, 0, -delta)), target + Vector((0, 0, delta)))], contour, .0009)
    scene.view_layers[0].update()
    report = {'country': 'Malaysia', 'countryCode': 'MYS', 'regions': ['Peninsular Malaysia', 'Sabah and Sarawak'],
              'sourceUrl': SOURCE_URL, 'sourceLicense': 'Natural Earth public domain', 'sourceSha256': geo['sourceSha256'],
              'cacheSha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(), 'mapBoundsLonLat': list(BOUNDS),
              'polygons': malaysia_polygons, 'triangles': len(land_faces), 'coastlineSegments': len(malaysia_lines),
              'contextSegments': len(neighbor_lines), 'objects': len(col.objects), 'palette': 'black / white',
              'screen': display.name, 'nativeRepresentation': 'planar meshes / thin curves / text'}
    scene['office_malaysia_map'] = json.dumps(report)
    scene['Screen note'] = 'Monochrome Malaysia geography: Peninsular Malaysia, Sabah and Sarawak; Natural Earth public-domain map data.'
    display['screen_content'] = 'Monochrome Malaysia geography: Peninsula, Sabah and Sarawak'
    return report
