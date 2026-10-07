# Planned media and startup features

These decisions are recorded for later implementation. Current runtime behavior is described in [architecture](architecture.md).

## Video banners

Use Three.js **`VideoTexture`** on separate named, UV-mapped lobby screen meshes; keep their frames and transforms. Load videos independently of native geometry. Blender movie-texture playback is not transferred by a GLB.

- Prefer short, compressed portrait clips with muted, looping, inline playback.
- Match the banner aspect ratio; monochrome footage or animated typography fits the scene.
- Use poster images until playback is ready or autoplay is unavailable.
- Play only when visible; pause offscreen and dispose video resources when the viewer is removed.

**Status:** planned. The current runtime uses static image textures; banner video selection/preparation and playback are not implemented.

## Startup preloading and further warmup

The branded loading screen prepares city/journey, lobby/cabin, all four destination packages and their textures, both portrait layers, project posters and silent audio buffers. It stays mounted through the lazy runtime import and first city draw, then hands off to the sound choice or the remembered playback settings. Scene data is reused on floor selection; video recordings retain their visibility/selection-driven loading.

**Status:** package/image/audio preparation and first-city-frame handoff are implemented. Additional GPU/shader warmup for every offscreen destination remains a profiling task; those rooms' geometry/materials are mounted when selected. Measure memory/network budgets before extending warmup further. Prepared packages remove later download waits but do not guarantee a fixed startup time or frame rate on every device.
