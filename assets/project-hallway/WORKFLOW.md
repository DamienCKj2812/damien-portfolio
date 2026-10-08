# Hallway workflow

## Build and native checks

```sh
blender --background --python-exit-code 1 --python assets/project-hallway/build_project_hallway.py -- --no-render
blender --background --python-exit-code 1 --python assets/project-hallway/validate_project_hallway.py
blender --background --python-exit-code 1 --python assets/project-hallway/verify_hallway_controls.py
```

Full generation replaces manual edits and resets the process's scene data. The builder disables numbered save versions; preserve recovery separately before a rebuild. It reads the production city NPC source without modifying it.

Full builds first regenerate `projects.json` from `docs/project-catalogue.md` using `build_project_catalogue.py`. Change approved long-form content in the catalogue; fitted physical-card titles/summaries/tags and explicit exhibit mapping live in the generator. Do not hand-edit the generated JSON.

Options:

- `-- --all-previews`: full build plus scene/detail/ceiling renders.
- `-- --preview-only --all-previews`: render the saved master.
- `-- --ceiling-only --no-render`: replace only ceiling; verify the rest of the room fingerprint.
- `-- --preview-only --ceiling-previews`: only the two ceiling views.
- `-- --preview-only --category-previews`: only the Academic and Personal doorway views.

`render_motion_preview.py` creates the native NPC excerpts. `validation.json`, `hallway-layout.json`, and `ceiling-refresh.json` report authored state; instance costs are not equivalent to evaluated triangle counts.

## Browser export

```sh
blender --background assets/project-hallway/project-hallway.blend --python-exit-code 1 --python assets/journey/export_browser_room.py -- --level projects
node --import tsx assets/journey/verify_rooms.mts
node --import tsx scripts/verify_project_categories.mts
node --import tsx scripts/verify_project_card_focus.mts
blender --background assets/project-hallway/project-hallway.blend --python-exit-code 1 --python assets/journey/verify_room_source.py -- --level projects
```

After ceiling edits also run:

```sh
node --import tsx assets/project-hallway/verify_browser_ceiling.mts
```

This focused check verifies the package hash, sculpted rib depth/bounds, curved integrated light geometry, full hallway/entrance coverage and absence of ceiling dots independently of the other floors. Pass the previous animation-buffer SHA-256 as an optional argument to verify that a ceiling-only update leaves NPC motion byte-identical.

Test all project picks/jumps/links, fixed-axis movement versus look, keyboard/touch hold release, scroll ownership, independent NPC pause/reduced motion, delayed/failing load/cancel/reselect, cached returns and offscreen cleanup.

Also verify Client → Academic → Personal ordering, no first-section portal, reveal only after preceding displays, uninterrupted keyboard/touch/scroll/progress crossing with no activation buttons or click sounds, reverse traversal and top-right category text with the menu shown/hidden. Check all 16 catalogue entries, grouped DSTR, omitted empty TXSA Part 2, RTS, client links/attribution, featured FYP links and recorded-evaluation qualifiers in expanded details. Pause visitors and confirm the scene settles after walking stops.

Verify native card clicks and sidebar focus, full-card corner bounds on both walls and after resize, Explore readiness, translucent description/navigation panels, all ten case-file sections and keyboard/mobile selection, visitor suspension/idle settling, isolated guide Escape, and two-stage Back restoring the original walking position/look. The focus verifier projects actual authored card bounds through the computed cameras across seven viewport sizes and both UI modes.

For the entrance/category presentation, use `refresh_directory_board.py`, `refresh_category_titles.py` and `refresh_category_wall_numbers.py` against the existing master. They guard unrelated transforms, text and animation. Re-export Projects afterward. `node --import tsx scripts/verify_project_directory.mts` checks the authored top-projector framing, native board click, sidebar-free zoom, resizing and saved-view return. `-- --preview-only --category-previews` refreshes the portal/number views without rebuilding.

After a browser build, `node --import tsx scripts/verify_project_detail_v2.mts` checks the v2 panel widths/fades, fixed header/scroll body, numbered rows, previous/next limits, progress rail, responsive framing and toggle-only audio. `node --import tsx scripts/verify_audio_consent.mts` separately verifies consent, remembered choices, trusted activation, preset levels and hidden-page playback cleanup. Both use declared Playwright 1.61.1, with `PLAYWRIGHT_MODULE` retained as an external-module override. `CHROME_EXECUTABLE` overrides `/usr/bin/google-chrome`, and `VERIFY_OUTPUT_DIR` overrides temporary screenshot output. Run `npm run verify` for all 20 non-browser checks and `npm run verify:browser` for all nine browser checks; video/Python/Pillow prerequisites are in [development](../../docs/development.md).
