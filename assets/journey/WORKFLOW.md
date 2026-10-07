# Integration and browser-export workflow

All commands run from the repository root. Models/export directories must exist; Blender exports are local prerequisites for deployment.

## Connected core, in order

```sh
blender --background assets/cyber-city/monochrome-city-solid-tower.blend --python-exit-code 1 --python assets/journey/build_city_lobby_handoff.py
blender --background assets/journey/city-lobby-walkthrough.blend --python-exit-code 1 --python assets/journey/verify_handoff.py
blender --background assets/journey/city-lobby-walkthrough.blend --python-exit-code 1 --python assets/cyber-city/export_browser_city.py
blender --background assets/kaze-lobby/kaze-lobby-walkthrough.blend --python-exit-code 1 --python assets/journey/export_browser_lobby.py
blender --background assets/kaze-elevator/kaze-elevator-journey.blend --python-exit-code 1 --python assets/journey/export_browser_elevator.py
blender --background assets/journey/city-lobby-walkthrough.blend --python-exit-code 1 --python assets/journey/build_elevator_handoff.py
blender --background assets/journey/portfolio-journey.blend --python-exit-code 1 --python assets/journey/verify_elevator_handoff.py
```

The cabin export precedes `build_elevator_handoff.py` because that builder reads the generated cabin motion. The first builder reads the lobby master and writes a derived copy. Both integration stages preserve authored inputs.

Room routing/panel changes require publishing `room-destinations.json` through the elevator handoff builder and re-exporting cabin availability; source-panel layout edits use the [elevator's explicit authoring workflow](../kaze-elevator/WORKFLOW.md).

## Export changed rooms

```sh
blender --background assets/about-office/about-office.blend --python-exit-code 1 --python assets/journey/export_browser_room.py -- --level about
blender --background assets/skills-gallery/skills-gallery.blend --python-exit-code 1 --python assets/journey/export_browser_room.py -- --level skills
blender --background assets/project-hallway/project-hallway.blend --python-exit-code 1 --python assets/journey/export_browser_room.py -- --level projects
blender --background assets/timeline-observatory/timeline-observatory.blend --python-exit-code 1 --python assets/journey/export_browser_room.py -- --level experience
```

Export only the affected packages unless routing/shared handoff changed. Exporters close cutaways, fit portals and derive picks in memory; they do not save masters. `geometry.bin`, `animation.bin`, scene metadata/hash and optional `route.bin` must be regenerated together.

## Focused verification

City entrance regression: `verify_handoff.py` checks 120 closed-vestibule sealing rays, 72 open-leaf casing-occlusion rays and 32 clear atrium-skin sightlines for the cylindrical tower. Clear the atrium cavity from both curved skins while retaining the exterior front band. Generate leaves, fitted pockets and enclosing jamb/header/floor returns together; avoid broad flat pockets across the neighboring curved storefront.

`node --import tsx scripts/verify_lobby_portal.mts` checks that the preloaded lobby stays inside the street aperture throughout the authored approach, releases its four clipping planes after crossing, and restores clipping during reverse navigation. Generated `lobbyPortal` dimensions must match the vestibule's real front opening, not the full lobby width.

After a build, `node --import tsx assets/journey/verify_city_entrance.mts` checks restored sky metadata, captures frames 245–450, reverses to the closed entrance and confirms elevator arrival. Playwright 1.61.1 is installed by `npm ci`; `PLAYWRIGHT_MODULE` remains an external-module override. `CHROME_EXECUTABLE` overrides `/usr/bin/google-chrome`, and `VERIFY_OUTPUT_DIR` overrides temporary screenshot output. `FIXED_APPROACH=1` holds only the test camera at frame 245 to isolate moving-door artifacts without editing authored/exported camera data.

```sh
node --import tsx assets/journey/verify_rooms.mts
blender --background assets/project-hallway/project-hallway.blend --python-exit-code 1 --python assets/journey/verify_room_source.py -- --level projects
blender --background assets/skills-gallery/skills-gallery.blend --python-exit-code 1 --python assets/journey/verify_room_source.py -- --level skills
blender --background assets/timeline-observatory/timeline-observatory.blend --python-exit-code 1 --python assets/journey/verify_room_source.py -- --level experience
```

The Node check validates current package bounds, frame/route sizes, all four floors, ascending switches, entrance alignment, forward arrival, Observer/card/node picks, guided stop/wrap and AT-AT surface/contour groups. Source checks compare sampled transforms/scales/morphs/points/routes read-only; there is no About option in that script.

After relevant UI changes, run `npm run lint && npm run typecheck && npm run build && npm run verify`, then `npm run verify:browser` for the nine actual-browser checks. Review real 3D plus accessible picks, all floors, press/release/drag-off, keyboard/touch controls, delayed/failing load/Retry/cancel, room caching, reverse/jump cleanup, reduced motion and offscreen/idle settling. Detailed input/clock ownership is in [runtime architecture](../../docs/architecture.md); browser prerequisites are in [development](../../docs/development.md).
