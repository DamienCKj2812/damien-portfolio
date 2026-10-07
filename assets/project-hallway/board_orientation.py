"""Fixed approach-facing yaw for the left/right project displays."""
import math

APPROACH_ANGLE_DEGREES = 45


def project_board_yaw(x):
    inward = math.pi / 2 - math.radians(APPROACH_ANGLE_DEGREES)
    return inward if x < 0 else -inward


def orient_project_board(root):
    root.rotation_euler.z = project_board_yaw(root.location.x)
    root['approach_angle_degrees'] = APPROACH_ANGLE_DEGREES
    root['display_facing'] = 'east-entrance' if root.location.x < 0 else 'west-entrance'


def stabilize_projector(root):
    """Keep the floor equipment in its original lanes; retarget only the beam."""
    from mathutils import Matrix
    unit = next((obj for obj in root.children if obj.get('holographic_projector')), None)
    if unit is None:
        return
    baseline = math.pi / 2 if root.location.x < 0 else -math.pi / 2
    angle = root.rotation_euler.z - baseline
    unit.rotation_euler.z = -angle
    delta = angle - unit.get('beam_board_angle', 0.0)
    rotation = Matrix.Rotation(delta, 3, 'Z')
    for obj in unit.children:
        if obj.type == 'CURVE' and 'frustum rays' in obj.name:
            for spline in obj.data.splines:
                for point in spline.points:
                    if point.co.z > 1:
                        point.co.xyz = rotation @ point.co.xyz
        elif obj.type == 'MESH' and obj.name.endswith(' / subtle projected light field'):
            for vertex in obj.data.vertices:
                if vertex.co.z > 1:
                    vertex.co = rotation @ vertex.co
    unit['beam_board_angle'] = angle
    unit['fixed_walkway_base'] = True
