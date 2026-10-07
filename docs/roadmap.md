# Planned media and startup features

These decisions are recorded for later implementation. Current runtime behavior is described in [architecture](architecture.md).

## Video banners

Use Three.js **`VideoTexture`** on separate named, UV-mapped lobby screen meshes; keep their frames and transforms. Load videos independently of native geometry. Blender movie-texture playback is not transferred by a GLB.

- Prefer short, compressed portrait clips with muted, looping, inline playback.
- Match the banner aspect ratio; monochrome footage or animated typography fits the scene.
- Use poster images until playback is ready or autoplay is unavailable.
- Play only when visible; pause offscreen and dispose video resources when the viewer is removed.

**Status:** planned. The current runtime uses static image textures; banner video selection/preparation and playback are not implemented.

## Complete startup preloading

Before enabling **Enter**, show branded loading progress, load/decode the city/lobby/cabin and essential textures, upload GPU resources, and warm shaders. Retain the areas while drawing only visible geometry. Buffer video separately rather than waiting for entire clips.

**Status:** planned. Current loading is staged, and destination rooms load on floor selection. Extending the startup preload to room packages needs a measured memory/network budget. Preloading avoids later download waits but does not guarantee frame rate or a fixed few-second startup on every device.
