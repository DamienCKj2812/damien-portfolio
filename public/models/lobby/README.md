# Lobby browser assets

Generated from `assets/kaze-lobby/kaze-lobby-walkthrough.blend` by the journey
exporter. Geometry and animation remain separate from the city asset package.

`scene.json` describes Float32 buffers and camera/door channels. Lobby channels
have stride 12: XYZ position, XYZW quaternion, XYZ scale, camera vertical FOV,
and visibility. This preserves the authored lens animation and hiding door seam.
Coordinates remain local Blender Z-up; the journey applies the entrance offset.
