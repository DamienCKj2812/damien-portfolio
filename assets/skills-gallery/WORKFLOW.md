# Skills workflow

## Full build

```sh
node --import tsx scripts/build_skills_catalogue.mts
blender --background --factory-startup --python-exit-code 1 --python assets/skills-gallery/build_gallery.py -- --render
```

Omit `-- --render` to skip previews. The generator includes the outlined AT-AT and guided rig; full generation replaces manual edits and retains one previous save. Normal work belongs in the master. Older dinosaur/card/crowd patches are history rather than a finished-scene update sequence.

## Approved content-only update

```sh
node --import tsx scripts/build_skills_catalogue.mts
blender --background assets/skills-gallery/skills-gallery.blend --python-exit-code 1 --python assets/skills-gallery/refresh_skill_content.py
```

This changes only card typography and approved metadata, verifies the non-content structural fingerprint and leaves the architecture, AT-AT, all six articulated visitor performances and the full guided route untouched. `skill-content-verification.json` records the preservation check. The JSON generator reads About's current toolkit/focus/strengths directly from `src/data/portfolio.json` and Projects' explicit catalogue evidence; fitted rows/skill-specific narrative structure are curated in the generator. Profile provenance hashes canonical JSON bytes rather than evaluating or hashing the typed app wrapper.

The targeted AT-AT replacement and read-only previews are:

```sh
blender --background assets/skills-gallery/skills-gallery.blend --python-exit-code 1 --python assets/skills-gallery/replace_trex_with_atat.py
blender --background assets/skills-gallery/skills-gallery.blend --python-exit-code 1 --python assets/skills-gallery/render_atat.py
blender --background assets/skills-gallery/skills-gallery.blend --python-exit-code 1 --python assets/skills-gallery/render_atat.py -- --isolated
```

Guided rig/look checks:

For a focused NPC-only update preserving the existing room, exhibits and camera:

```sh
blender --background assets/skills-gallery/skills-gallery.blend --python-exit-code 1 --python assets/skills-gallery/update_autonomous_visitors.py
```

Walking/pause destinations and gaze targets live in `configure_gallery_visitors()` in `build_gallery.py`. This update validates clearance across every player/NPC time combination before saving; re-export afterward.

```sh
blender --background assets/skills-gallery/skills-gallery.blend --python-exit-code 1 --python assets/skills-gallery/test_guided_walk.py
```

This exercises actual rig/camera data, mouse-look math, limits, registration and synthetic modal events in background mode; manual GUI preview remains the native event-loop check.

## Browser export and source comparison

```sh
blender --background assets/skills-gallery/skills-gallery.blend --python-exit-code 1 --python assets/journey/export_browser_room.py -- --level skills
node --import tsx assets/journey/verify_rooms.mts
node --import tsx scripts/verify_skills_content.mts
blender --background assets/skills-gallery/skills-gallery.blend --python-exit-code 1 --python assets/journey/verify_room_source.py -- --level skills
```

Export is read-only and writes `public/models/rooms/skills/`. It samples 959 unique visitor frames for 90 part channels at stride 12, preserves closest animated-root world poses, and writes the separate 2940-frame XYZ `route.bin`. The `atat` exhibit retains native black surface triangles and white contour curves; do not substitute realized point spheres or a line-free standard GLB.

## Runtime checks

Enter floor 02; test real exhibit/AT-AT picks, close-up views, route jumps preserving look, player/NPC clearance, independent visitor playback with the tour paused/at its endpoint, animation pause/resume, ←/→/Home/Space/R, touch alternatives, reduced motion, route-load Retry and offscreen/unmount cleanup. Guides and collision validation are not a reason to bake camera orientation into movement.

After `npm run lint && npm run typecheck && npm run build`, run `node --import tsx scripts/verify_skills_focus.mts` for actual card picking, all nine full-card focuses, evidence/learning content, shared v2 sections, mobile rear-wall framing, saved route and original tour-state return, hidden visitor suspension and idle cleanup. Playwright 1.61.1 is a declared dev dependency; `PLAYWRIGHT_MODULE` remains an external-module override. Chrome defaults to `/usr/bin/google-chrome` (`CHROME_EXECUTABLE` override), and screenshots use temporary output (`VERIFY_OUTPUT_DIR` override). This check is also in `npm run verify:browser`; non-browser content/package checks are in `npm run verify`. Keep cross-time clearance validation in `gallery_walk.validate_guided_walk`, not just synchronized phase checks.
