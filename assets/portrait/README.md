# Pixel-grid About portrait

The About profile displays `Chong Kah Jun - Bg remove.png` as a **soft monochrome raster portrait**. Its existing transparent background is preserved against the black frame. A single tonal curve grades the whole photo and compresses highlights, with no selective clothing darkening or lower fade. A faint fine grid overlays continuous greyscale samples; there are no isolated checkerboard dots or aggressive sharpening.

## Build

```bash
python3 assets/portrait/build_pixel_portrait.py \
  --source "$HOME/Pictures/Chong Kah Jun - Bg remove.png"
```

Requires Pillow and NumPy. The source photograph is read-only. Background-removed PNGs use their supplied alpha; opaque studio photographs use the fallback background matte. The build writes:

- `public/portraits/damien-pixel.png`: 640 × 800 RGBA portrait with a 128 × 160 raster grid (5px cells) over gently blurred photographic detail.
- `public/portraits/damien-original.png`: original photographic color/detail, with matching 640 × 800 transparent subject framing and no tonal curve, grid or photographic blur.
- `assets/portrait/image-manifest.json`: source filename, dimensions, cell size, and both image hashes.

`src/data/portfolio.js` imports both generated image hashes for cache-busting. `PixelPortrait.jsx` displays normally scaled HTML images in a black frame. A restrained 1.1px softness and the grid are baked into the default PNG; the original-color image has neither treatment. The source studio background is masked out and framing is shared so revealing the photo does not shift the subject. There is no portrait model or rotation UI.

Fine-pointer movement reveals original colour through an SVG pixel-cell trail. Leaving releases the active brush and continues fading the remaining cells for up to 700 ms, then hides the original-colour SVG layer to prevent stale patches. Re-entry starts a fresh brush without connecting to the previous position. Keyboard focus reveals the full photograph with a visible focus outline. Touch does not latch a simulated hover. Hidden/offscreen/window-blur/closing clear the reveal immediately, and unmount removes listeners and cancels pending frames. Reduced motion keeps a local brush and clears it immediately on leave. The custom portrait cursor is a transparent outlined square, without contrast inversion. Animation frames run only while trail cells fade; idle portraits stop completely, and the interaction never invalidates WebGL. If the original image fails to load, the default portrait remains visible.

## Retired 3D experiment

The previous Blender master, generator, surface helper, and review renders are retained as authoring/recovery artifacts. The GLB and model textures have been removed from the public website, and the 3D portrait React components have been removed. Rebuilding the retired model is not part of the current image workflow.
