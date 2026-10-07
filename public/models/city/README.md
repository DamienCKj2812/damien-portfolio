# Browser city assets

Generated from the city portion of `assets/journey/city-lobby-walkthrough.blend` by
`assets/cyber-city/export_browser_city.py` inside Blender.

- `scene.json`: draw groups, camera information, and animation channel names.
- `geometry.bin`: little-endian Float32 points, thin lines, bright vehicle outlines,
  solid vehicle surfaces, and black-backing geometry.
- `animation.bin`: evaluated world transforms for the camera and 18 moving roots.
- `preview.png`: static fallback image.
- `ads/`: eight grayscale textures for the main tower's advertising displays.

Coordinates use Blender's Z-up system. The browser rotates the scene to Three.js
Y-up and applies the same conversion to the camera. Point surfaces and lines are
rendered directly; no Geometry Nodes support is required in the browser.

Manifest version 2 adds `outline` and `solid` draw groups. Outline groups become
screen-space thick line segments, and solid groups carry baked grayscale face
brightness. Traffic actors have `style: "outlined_vehicle"` and no particle groups.

Version 3 adds UV-mapped `screen` groups and selective `glow` outlines. The
manifest lists texture paths and hashes texture content along with the binary
buffers. Glow is limited to the hero tower rather than applied to the scene.

Ten actors have `style: "walking_npc"` and `walk` metadata. Their positions are
baked, while the renderer computes stepping from scroll-controlled travel distance
so no separate clock or animation loop moves people when scrolling stops.

The combined integration copy adds the grand doorway and larger atrium cavity.
The authored city master remains `assets/cyber-city/monochrome-city-solid-tower.blend`.
Journey alignment and the lobby package live outside this city buffer set.
