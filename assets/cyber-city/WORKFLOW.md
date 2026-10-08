# City workflow

Commands below run from the repository root. Inspect hardcoded `ROOT` values if using another checkout.

## Current reference-based main tower

### Native walkthrough playback view

If the production master opens in editor perspective rather than its animated camera, restore the saved Layout with:

```sh
blender --background assets/cyber-city/monochrome-city-solid-tower.blend --python-exit-code 1 --python assets/cyber-city/prepare_walkthrough_view.py
```

This focused authoring update saves a normal UI-bearing `.blend`, selects the walkthrough camera, starts at frame 1 and checks all 450 evaluated camera poses/lenses remain unchanged. Preserve a recovery copy first. Press Numpad 0 then Space when reviewing an already-open editor perspective; no embedded script needs to run.

```sh
python assets/cyber-city/prepare_reference_tower_artwork.py
blender --background assets/cyber-city/monochrome-city-solid-tower.blend --python-exit-code 1 --python assets/cyber-city/restyle_reference_tower.py
blender --background assets/cyber-city/monochrome-city-solid-tower.blend --python-exit-code 1 --python assets/cyber-city/verify_reference_tower.py
```

Version 2 follows the supplied cylindrical specification rather than the former block-tower arrangement. `reference_tower_spec.py` fits the radial scale and azimuths to the fixed entrance, tunes facade/crown heights, and derives each image aspect from actual arc length / panel height. The A bay retains its two stacked curved surfaces, now carrying coordinated slices of the supplied SANCTUM long banner with its original text/borders and no added captions. Three right-side screens contain the slogans, glass-like native hologram and eclipse/mountain/lake landscape. The rooftop has a drum, halo, full parapet and four paired masts. L1 and L2 have separate partial-ring slabs; L1 continues into the sweeping crescent fin. Glitch blocks, larger left luminous panels, vertical fins, storefront glazing, trees and the layered canopy complete the shape. Native Cycles materials/compositor and browser luminance/centerline proxies are authored together. `reference-tower.json` and `reference-tower-artwork.json` record geometry, framing and texture provenance.

This focused script hides the former block-tower solids, terraces, cage and foreground entrance-obscuring sign, retaining their recovery data. It restores the authored orbital sky, outdoor people and wireframe night skyline with sparse floor/window detail. It updates five existing display IDs and verifies unchanged existing transforms/camera at six route frames. Verification independently checks all 450 camera frames, packed texture hashes, UVs, mast/balcony presence and retired displays. On the master, the two export-cut skin objects are excluded from collision checks; repeat the same check on the generated city/lobby copy to test the evaluated doorway/atrium cuts. Reapplying the script replaces its own tower collection and refreshes the owned skyline detail.

Rebuild the connected city/lobby copy and export the city, then rebuild/verify the elevator handoff using the [integration sequence](../journey/WORKFLOW.md). The builder carves the front portal and rear atrium separately, hides the old flat podium, and recesses the sliding-door/pocket assemblies by 1.8 m without changing their timing. Reapply this redesign after a full styling/branding rebuild. The older banner sections below describe retained sources and the former layout; the current facade uses `reference-{logo,portrait,order,orbital,eclipse}.jpg`. Run the existing foreground/rear train verification after export.

`reference-tower-preview.png` is the current browser-rendered full-building view, captured with an isolated preview camera without editing the authored route. The city exporter also uses it as the loading-poster source when the reference redesign is active.

### Focused long-banner replacement

```sh
python3 assets/cyber-city/prepare_long_banner.py
blender --background assets/cyber-city/monochrome-city-solid-tower.blend --python-exit-code 1 --python assets/cyber-city/replace_long_banner.py
```

The source is `banner-artwork/long-banner-source.png`. This focused path updates only the two prepared A-bay images/metadata and packs them without rebuilding the tower. Rebuild the connected city/lobby copy, export the city, and rebuild the elevator handoff in the integration sequence. Check `verify_reference_tower.py` on production and the connected copy; review the browser banner and refresh browser-rendered building/sky previews. The city `assetHash` includes both JPEGs, while geometry and animation buffers remain unchanged for this texture-only edit.

### Clean long-banner border

```sh
blender --background assets/cyber-city/monochrome-city-solid-tower.blend --python-exit-code 1 --python assets/cyber-city/remove_long_banner_glitch.py
```

The focused update hides the 80 scattered rectangle meshes along the banner's right edge (2.5°–8.5° azimuth), retaining them for recovery. It preserves the artwork, thin frame, LED rails, receding-left facade decoration and all unrelated transforms/visibility/actions. Full generation omits this strip. Rebuild/export the connected city and elevator handoff; check the master/integration with `verify_reference_tower.py` and refresh browser previews. This geometry-visibility edit regenerates the city geometry/hash but preserves animation.

## Restore the wireframe night skyline

```sh
blender --background assets/cyber-city/monochrome-city-solid-tower.blend --python-exit-code 1 --python assets/cyber-city/restore_wireframe_skyline.py
```

This focused production update restores the retained skyline outlines and sparse white windows, adds floor bands from the original building bounds and hides the two opaque replacement blocks. It preserves existing poses, camera, tower, sky and traffic; `wireframe-skyline.json` records the building/source details. The tower builder also reapplies it during future rebuilds. Rebuild/export the connected city and elevator handoff using the [integration sequence](../journey/WORKFLOW.md), then check:

```sh
blender --background assets/cyber-city/monochrome-city-solid-tower.blend --python-exit-code 1 --python assets/cyber-city/verify_wireframe_skyline.py
```

## Refresh the configured crowd

```sh
blender --background assets/cyber-city/monochrome-city-solid-tower.blend --python-exit-code 1 --python assets/cyber-city/apply_lobby_npc_reference.py
blender --background assets/cyber-city/monochrome-city-solid-tower.blend --python-exit-code 1 --python assets/cyber-city/animate_city_npcs.py
```

These scripts save production atomically; reopen between processes. The reference refresh reads `assets/kaze-lobby/kaze-lobby-walkthrough.blend` without saving it and folds/removes prior walker rigs. The walker builder rejects existing rigs, so don't rerun it alone to duplicate the crowd.

For the connected website, rebuild the city/lobby integration and export from that copy; see [the integration command sequence](../journey/WORKFLOW.md).

Standalone export only:

```sh
blender --background assets/cyber-city/monochrome-city-solid-tower.blend --python-exit-code 1 --python assets/cyber-city/export_browser_city.py
```

Both export modes write `public/models/city/{scene.json,geometry.bin,animation.bin}` and `ads/`; neither saves the open master. Actor counts come from the exported manifest, not older prose about eight roots.

## Remove the small night banner

The narrow `THE NIGHT LIVES ON` banner beside the portrait is retired from production. Its screen, dedicated glow border and four edges in the shared billboard-frame network are removed by:

```sh
blender --background assets/cyber-city/monochrome-city-solid-tower.blend --python-exit-code 1 --python assets/cyber-city/remove_night_banner.py
```

`solidify_main_tower.py` and `simplify_environment.py` omit it during future production rebuilds. Rebuild the connected city/journey and re-export afterward; `night.png` must no longer appear in the city texture manifest.

## Replace the largest portrait banner

The production target is `Hero display • KAZE • cyborg campaign • LED display` (5.6 × 28.5 m). The owner's image is preserved as `banner-artwork/portrait-source.png`; preparation details/hashes are in `banner-artwork/portrait-banner.json`.

```sh
python assets/cyber-city/prepare_portrait_banner.py
blender --background assets/cyber-city/monochrome-city-solid-tower.blend --python-exit-code 1 --python assets/cyber-city/replace_portrait_banner.py
```

The image is center-cropped to the existing panel aspect ratio, resized to 402 × 2048, and compressed as quality-92 grayscale progressive JPEG (`textures-monochrome/portrait.jpg`). The focused update packs it into production and verifies unchanged geometry, UVs, camera and all object/actor poses at route frames 1/90/245/383/450.

Rebuild/export the connected city using the [integration sequence](../journey/WORKFLOW.md), including the elevator handoff builder afterward to restore the complete published journey metadata. The city exporter copies the JPEG to `public/models/city/ads/portrait.jpg` and includes its bytes in `assetHash`. The browser already renders native textured screens. Full monochrome-ad/solid-tower generation preserves this custom portrait override; original architecture artwork remains in the original-motion master.

## Replace NEW HORIZONS with Selangor

The curved landscape display uses the owner's `banner-artwork/selangor-source.png`:

```sh
python assets/cyber-city/prepare_selangor_banner.py
blender --background assets/cyber-city/monochrome-city-solid-tower.blend --python-exit-code 1 --python assets/cyber-city/replace_selangor_banner.py
```

The source's outer black background is trimmed, then the artwork fills the arc's surface edge-to-edge with a proportional center crop and no padding, as requested by the owner. It is compressed to `textures-monochrome/selangor.jpg` and packed into production. Rebuild/export the connected city using the [integration sequence](../journey/WORKFLOW.md), including the elevator handoff follow-up. The city exporter copies `ads/selangor.jpg` and derives the new texture hash. Full styling preserves this override.

## Replace SYNTHETIC REALITIES with the black-hole artwork

The curved portal display uses `banner-artwork/black-hole-source.png`:

```sh
python assets/cyber-city/prepare_black_hole_banner.py
blender --background assets/cyber-city/monochrome-city-solid-tower.blend --python-exit-code 1 --python assets/cyber-city/replace_black_hole_banner.py
```

The full square image and caption are fitted to the curved surface aspect ratio with black side padding, compressed to `textures-monochrome/black-hole.jpg`, and packed into production. Follow the connected [integration/export sequence](../journey/WORKFLOW.md), including the elevator handoff follow-up, to publish `ads/black-hole.jpg` and its updated cache hash. Full ad/tower builds preserve the override.

## Replace DRIVE A CLEANER TOMORROW

The clean-mobility display uses `banner-artwork/drive-the-next-horizon-source.png`:

```sh
python assets/cyber-city/prepare_drive_banner.py
blender --background assets/cyber-city/monochrome-city-solid-tower.blend --python-exit-code 1 --python assets/cyber-city/replace_drive_banner.py
```

The artwork fills the existing 8.4 × 6.5 m panel edge-to-edge with a proportional cover crop biased toward its headline/logo, without padding or stretching. It is compressed to `textures-monochrome/drive-the-next-horizon.jpg` and packed into production. Follow the connected [integration/export sequence](../journey/WORKFLOW.md), including the elevator handoff follow-up, to publish the JPEG and new cache hash. Preserve the integration's existing banner lift above the grand doorway. Full ad/tower generation retains the override.

## Replace NEXUS with Shaping a Brighter Tomorrow

The curved NEXUS display uses `banner-artwork/shaping-a-brighter-tomorrow-source.png`:

```sh
python assets/cyber-city/prepare_nexus_banner.py
blender --background assets/cyber-city/monochrome-city-solid-tower.blend --python-exit-code 1 --python assets/cyber-city/replace_nexus_banner.py
```

The artwork fills the curved surface edge-to-edge with a proportional center crop and no padding, as requested by the owner. The focused update packs `textures-monochrome/shaping-a-brighter-tomorrow.jpg` and preserves geometry/UVs/motion. Follow the connected [integration/export sequence](../journey/WORKFLOW.md), including the elevator handoff follow-up, to publish the replacement JPEG and new cache hash. Full ad/tower generation preserves the override.

## Reference orbital sky

```sh
blender --background assets/cyber-city/monochrome-city-solid-tower.blend --python-exit-code 1 --python assets/cyber-city/add_orbital_sky.py -- --preview
```

This replaces only `City • Reference orbital sky` and saves production. The opening-camera composition follows the monochrome reference: continuous/dotted orbital arcs, a shallow S-shaped diagonal orbit with three tracking stars, constellation links, two shaded crescent bodies and technical annotations. There is no overhead construction grid or registration crosshair. All geometry is world-fixed behind the city; only sky point groups receive the existing subtle twinkle. The bright star core exports separately as `sky-shine`, with an authored optical flare radius for the browser's transparent, smoothly fading halo/rays. The optional native preview shows its point core and uses the reference's wide aspect without changing the saved camera or route. `orbital-sky.json` records generated counts.

Rebuild the connected city/lobby integration and export the city from that copy using the [integration sequence](../journey/WORKFLOW.md), then run:

```sh
blender --background assets/cyber-city/monochrome-city-solid-tower.blend --python-exit-code 1 --python assets/cyber-city/verify_orbital_sky.py
node --import tsx assets/journey/verify_rooms.mts
```

Reapply the sky step after a full styling rebuild.

## Illuminated street plaza

```sh
blender --background assets/cyber-city/monochrome-city-solid-tower.blend --python-exit-code 1 --python assets/cyber-city/restyle_street_plaza.py -- --preview
```

This focused authoring step replaces only `Street plaza • Illuminated precinct` and the ground material. It adds two-metre stone joints, broken inset light strips, dotted pedestrian guides, crosswalk inlays, pavement directions, three wayfinding pylons, framed benches, garden rims and illuminated bollards. The source camera, crowd, sky and architecture transforms are checked at six route frames before an atomic production save. Reapply after a full styling rebuild.

`street-plaza.json` records counts and the browser reflection footprint. The connected city exporter publishes this as `streetPlaza` in its manifest; the runtime uses the shared, capped, demand-rendered floor reflector with static wet-stone grain. The optional `street-plaza-preview.png` is a native street-level preview, rendered with export-aligned ground after saving, without altering the authored route or anchors. Rebuild and verify the connected city and elevator handoffs using the [integration sequence](../journey/WORKFLOW.md), then run the package check, lint and build.

## Left-side train corridor

```sh
blender --background assets/cyber-city/monochrome-city-solid-tower.blend --python-exit-code 1 --python assets/cyber-city/reroute_train_left.py -- --preview
```

This focused production update rotates the original foreground corridor into a longitudinal route beside the tower's left flank: deck center X = −14 m, maglev rail center X = −14.65 m. It moves the train and shared-deck commuter curves together with their foreground deck outlines, guide rails, piers and stipple points. It also removes the disconnected upper-left interchange's deck outlines, supports and stipple points; the background highway retains its original geometry. The native carriage models, original follow-path timing and walkthrough camera remain authored as before. `Left transit • Source • …` datablocks retain the source knots and network vertices for repeatable updates. Hidden objects in `Left transit • Source recovery` reference these baselines so scene-only library saves preserve them; none of the recovery objects export. Legacy missing baselines can be recovered from the local production `.blend1` copy without replacing the current scene.

The update checks the complete three-car envelope across all 450 frames and unrelated object poses at six route frames before saving production atomically. `left-transit-route.json` records the corridor and clearance checks; `left-transit-preview.png` shows the pass at frame 145. Reapply after a full styling rebuild. Rebuild/export the connected city and elevator handoffs using the [integration sequence](../journey/WORKFLOW.md), then verify:

```sh
blender --background assets/cyber-city/monochrome-city-solid-tower.blend --python-exit-code 1 --python assets/cyber-city/verify_left_transit.py
node --import tsx assets/journey/verify_rooms.mts
```

The read-only check compares every published train pose to the native follow-path motion, verifies the left-side rail placement and checks the full source envelope/timing. `traffic-animation.json` belongs to the original architecture/motion workflow; the connected browser uses freshly exported city motion.

## Autonomous rear-highway train

```sh
blender --background assets/cyber-city/monochrome-city-solid-tower.blend --python-exit-code 1 --python assets/cyber-city/add_background_train.py -- --preview
```

This replaces only `Background transit • Autonomous train`, cloning the three-car native maglev hierarchy and shared model data onto the rear highway. The extended route is X −1000…1000 m, Y 7 m, Z 7.6 m, with a native 1–450-frame linear action. `city_autonomous` and `city_motion` publish the independent visible-city clock policy: a fixed-heading one-way pass sampled over 2000 clock frames, followed by a 60-frame hidden reset. The stable phase starts the train at X 20 m. Both endpoints, including the entire carriage envelope, are checked against all 450 camera poses at viewport aspects 0.5, 1.6, 4.5 and 8.0. There is no visible turn-around or spin. Scrolling controls the foreground train and camera but does not seek this rear train. Reduced motion and hidden/offscreen city suspension use the existing clock lifecycle.

`background-train-route.json` records the route, and `transit-network-preview.png` shows both lanes with the retired upper interchange absent. Rebuild/export the connected city and elevator handoffs, then run:

```sh
blender --background assets/cyber-city/monochrome-city-solid-tower.blend --python-exit-code 1 --python assets/cyber-city/verify_background_train.py
blender --background assets/cyber-city/monochrome-city-solid-tower.blend --python-exit-code 1 --python assets/cyber-city/verify_left_transit.py
node --import tsx assets/journey/verify_rooms.mts
npm run lint && npm run typecheck && npm run build && npm run verify
```

The rear-train verifier checks all 450 native/exported motion frames, fixed heading, lateral fit within the rear deck, one-way/hidden-reset metadata, foreground timing ownership, removed interchange counts and scene-linked recovery baselines. Reapply this step after a full styling rebuild, following the left-corridor update.

## Full styling rebuild

Start in an isolated copy/session of `cyber-city-walkthrough.blend`, with the original neon scene active:

1. `restyle_monochrome.py`: create the separate monochrome scene.
2. `improve_humans.py`: initial crowd and stable IDs.
3. `simplify_environment.py`: structural outline replacement.
4. `optimize_camera_scene.py`: requires the full source scene; checks every sampled frame and writes the optimized stage.
5. Reopen `monochrome-city-optimized.blend`; run `polish_traffic_models.py` to write the traffic-polished stage.
6. Run `python assets/cyber-city/make_monochrome_ads.py` with Pillow installed.
7. Reopen `monochrome-city-traffic-polished.blend`; run `solidify_main_tower.py`, which reads the original tower source and writes production.
8. Apply the crowd refresh and walker build above, then rebuild integration/export.

The temporary monochrome walkthrough, optimized, and traffic-polished `.blend` files are ignored derived stages. Verify production before removing them; keep the two masters.

Original architecture can be reconstructed with `make_posters.py` (Python/Pillow), then `build_scene.py`, `polish_scene.py`, `detail_pass.py`, `finalize_scene.py`, `add_walkthrough.py`, `retime_walkthrough.py`, and `add_traffic.py`. These are construction stages, not updates to the finished production model. Route edits require fresh camera sampling and optimization.
                                                                                                                                                                                                                         
