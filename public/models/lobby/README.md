# Lobby browser assets

Generated from `assets/kaze-lobby/kaze-lobby-walkthrough.blend` by the journey
exporter. Geometry and animation remain separate from the city asset package.

`scene.json` describes Float32 buffers and camera/door channels. Current lobby
channels have stride 16: XYZ position, XYZW quaternion, XYZ scale, camera vertical
FOV, visibility, and four native morph weights. Legacy non-morph lobby packages
use stride 12. Read the authored descriptor; lobby and cabin packages are
distinguished by their metadata rather than stride alone. This preserves the
authored lens animation, hiding door seam, and independent NPC performances.
Coordinates remain local Blender Z-up; the journey applies the entrance offset.
