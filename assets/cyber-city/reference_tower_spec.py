"""Reference dimensions fitted to the existing metre-scale city/lobby site."""
import math

SCALE = .43
FACADE_HEIGHT_SCALE = .36
BASE_RAISE = 3.0
RADIUS = 22 * SCALE
ENTRANCE = (-1.5, -5.55)
ENTRANCE_AZIMUTH = math.radians(-15)
CENTER = (ENTRANCE[0] - RADIUS * math.sin(ENTRANCE_AZIMUTH),
          ENTRANCE[1] + RADIUS * math.cos(ENTRANCE_AZIMUTH))


def height(reference_z):
    if reference_z == 0:
        return 0
    # Overlay tuning: compress the facade relative to the crown so the logo,
    # portrait head and lower balcony land at the reference's frame heights.
    if reference_z <= 106:
        return reference_z * FACADE_HEIGHT_SCALE + BASE_RAISE
    if reference_z <= 118:
        return 41.16 + (reference_z - 106) * .8
    return 50.76 + (reference_z - 118) * ((66.45 - 50.76) / 32)


def surface(radius, azimuth, z):
    angle = math.radians(azimuth)
    return (CENTER[0] + radius * math.sin(angle), CENTER[1] - radius * math.cos(angle), z)


SCREENS = {
    'logo': {'azimuth': [-40, 9], 'z': [height(72), height(101)], 'radius': RADIUS + .30},
    'portrait': {'azimuth': [-40, 9], 'z': [height(15), height(70)], 'radius': RADIUS + .30},
    'order': {'azimuth': [15, 58], 'z': [height(55), height(78)], 'radius': RADIUS + .045},
    'orbital': {'azimuth': [15, 58], 'z': [height(35), height(54)], 'radius': RADIUS + .045},
    'eclipse': {'azimuth': [15, 58], 'z': [height(4), height(33)], 'radius': RADIUS + .045},
}
for spec in SCREENS.values():
    spec['arcLength'] = spec['radius'] * math.radians(spec['azimuth'][1] - spec['azimuth'][0])
    spec['aspect'] = spec['arcLength'] / (spec['z'][1] - spec['z'][0])
for key in ['order', 'orbital', 'eclipse']:
    SCREENS[key]['z'] = [z - 1.6 for z in SCREENS[key]['z']]

PREVIEW_CAMERA = {
    'position': [CENTER[0], CENTER[1] - 46, .86],
    'target': [CENTER[0], CENTER[1], .86 + math.tan(math.radians(28)) * 46],
    'verticalFov': 23,
    'sourceAspect': 1.6,
    'resolution': [1428, 2439],
}
