"""Reference-style desktop inkjet, with native silver curve outlines."""
import math


def build_printer(link, box, lines, ellipse, graphite, black, edge, quiet):
    import bpy

    root = link('Printer / desktop assembly', None, '03')
    root.location = (2.35, .68, .895)
    root.rotation_euler.z = math.radians(-40)
    root['design'] = 'Faceted inkjet with rear paper feeder and front output tray'

    def block(name, center, size, mat=graphite, **kwargs):
        obj = box('Printer / ' + name, center, size, mat, '03', **kwargs)
        obj.parent = root
        return obj

    def contour(name, paths, mat=edge, radius=.0017):
        obj = lines('Printer / ' + name, paths, mat, radius, '03')
        obj.parent = root
        return obj

    # A chamfered top shell, rather than a stack of rectangular boxes.
    profile = [(-.45, .03), (.45, .03), (.45, .34),
               (.39, .405), (-.36, .405), (-.45, .35)]
    verts = [(x, y, z) for y in [-.27, .27] for x, z in profile]
    n = len(profile)
    faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
    faces += [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    mesh = bpy.data.meshes.new('Office • Printer / faceted casing')
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(graphite)
    body = link('Printer / faceted casing', mesh, '03')
    body.parent = root
    contour('casing silhouette',
            [[verts[i] for i in list(range(n)) + [0]],
             [verts[i] for i in list(range(n, 2 * n)) + [n]]] +
            [[verts[i], verts[i + n]] for i in range(n)])
    contour('scanner lid seam', [[(-.34, -.22, .407), (.32, -.22, .407),
                                 (.37, .20, .407), (-.34, .20, .407),
                                 (-.34, -.22, .407)]], quiet)
    contour('front upper seam', [[(-.45, -.272, .305), (.45, -.272, .305)]])

    # Dark recessed output, side cheeks and a projecting two-stage catch tray.
    block('output recess', (0, -.274, .16), (.55, .008, .23), black,
          edge_mat=quiet)
    block('left front cheek', (-.365, -.283, .17), (.17, .035, .27))
    block('right control cheek', (.365, -.283, .17), (.17, .035, .27))
    block('paper exit slot', (0, -.286, .105), (.50, .01, .028), black,
          edge_mat=quiet)
    block('output tray', (0, -.36, .042), (.56, .24, .018))
    block('telescoping tray lip', (0, -.475, .062), (.57, .025, .042))
    contour('output tray guides', [[(x, -.46, .054), (x, -.25, .054)]
                                  for x in [-.235, .235]], quiet)

    # Rear support and one plain sheet, tilted slightly away from the viewer.
    block('rear feeder support', (0, .245, .49), (.53, .025, .30),
          rotation=(-.16, 0, 0))
    paper = block('upright paper sheet', (0, .224, .54), (.38, .006, .29),
                  rotation=(-.16, 0, 0), edge_mat=edge)
    paper['detail'] = 'Plain unprinted paper in rear input feeder'
    for x in [-.235, .235]:
        block('feeder paper guide', (x, .215, .428), (.036, .065, .055),
              edge_mat=quiet)

    block('control panel', (.354, -.306, .283), (.158, .014, .068),
          edge_mat=quiet)
    contour('power button', [ellipse((.322, -.315, .282), .013, .013, 'XZ', 24)], quiet)
    contour('power glyph', [[(.322, -.317, .282), (.322, -.317, .299)]], edge, .0012)
    contour('second button', [ellipse((.385, -.315, .282), .013, .013, 'XZ', 24)], quiet)
    contour('status light', [[(.416, -.316, .28), (.422, -.316, .28)]], edge, .0015)
    for x in [-.45, .45]:
        contour('side ventilation', [[(x * 1.002, y, .10), (x * 1.002, y, .18)]
                                     for y in [.06, .095, .13, .165]], quiet, .001)
    for x in [-.35, .35]:
        for y in [-.18, .18]:
            block('rubber foot', (x, y, .015), (.065, .065, .03), black,
                  outline=False)
    return root
