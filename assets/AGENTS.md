# Asset authoring rules

- Each model directory owns its authored master and local `AGENTS.md`; `journey/` owns integration copies and browser exporters. The routing/authoring boundary is `journey/room-destinations.json`.
- Asset-local Node tools use MTS: run `node --import tsx <path>.mts` from the repository root. `npm run verify` includes 19 non-browser checks; after a build, `npm run verify:browser` runs nine browser checks with declared Playwright 1.61.1. Chrome/output overrides and Python/Pillow requirements are in [development](../docs/development.md).
- Shared profile/contact content is canonical `src/data/portfolio.json`, read directly by Node and Python; `src/data/portfolio.ts` validates it and adds generated portrait metadata for the app. Hash canonical JSON bytes for content provenance, not TypeScript source text.
- Projects owns its video originals in `project-hallway/videos/originals/<project>/` (local, Git-ignored), with prepared browser recordings/compatibility copies/posters tracked in `public/videos/`. Keep original bytes intact, keep video uploads out of the repository root, and follow [video ownership](project-hallway/videos/README.md). Normal builds consume prepared files without transcoding or requiring originals.
- Use background Blender processes; full generators replace manual edits. Use the model's rebuild entrypoint rather than replaying historical patch scripts on a finished animated scene.
- Run Blender with `--python-exit-code 1` so Python exceptions fail the command. `--factory-startup` is required by the lobby/office/gallery fresh-scene generators.
- Preserve authored masters. Integration and browser exporters operate on in-memory copies; explicit authoring updates are the scripts allowed to save a master. Numbered `.blend1` files are local recovery copies, ignored by Git.
- Geometry is in meters, Blender Z-up. Browser groups and camera poses must use the same Three.js basis conversion; no independent floor/doorway translations.
- Point-source meshes and curve centerlines export natively; do not realize thousands of sphere instances or substitute a standard GLB for the browser packages.
- Re-export manifest, geometry, animation, route/textures together. `assetHash`, offsets, group strides, and frame counts must agree; see [integration workflow](journey/WORKFLOW.md).
- Embedded Blender controllers run only after explicit Text Editor execution. Website picking/dialogs belong to React/Three.js, not automatic `.blend` Python execution.
- Some city/journey scripts hardcode this checkout's absolute `ROOT`; check it before running in another checkout. Blender 5.2 scripts use layered-action channel bags and `scene.compositing_node_group`; don't assume older API properties exist.
