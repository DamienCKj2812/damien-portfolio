# Observatory workflow

## Build and native verification

For qualification labels and source-backed board logos, use the focused path:

```sh
python assets/timeline-observatory/prepare_timeline_logos.py
node --import tsx assets/timeline-observatory/build_timeline_content.mts
blender --background assets/timeline-observatory/timeline-observatory.blend --python-exit-code 1 --python assets/timeline-observatory/update_timeline_content.py
```

The updater preserves existing room transforms/actions and route, changing only copy and the intentionally replaced board symbols. Original qualification records remain in About data; card display fields supply the requested label wording. APU/LYJ/COS inputs stay unchanged; original-color copies are packed into Blender and exported with the Experience package. After the browser export below, run `verify_board_art.py` against the master and `node --import tsx scripts/verify_timeline_focus.mts`.

For content-only changes, preserve the completed room and route:

```sh
node --import tsx assets/timeline-observatory/build_timeline_content.mts
blender --background assets/timeline-observatory/timeline-observatory.blend --python-exit-code 1 --python assets/timeline-observatory/update_timeline_content.py
```

For a full authored rebuild:

```sh
blender --background --python-exit-code 1 --python assets/timeline-observatory/build_timeline_observatory.py -- --no-render
blender --background --python-exit-code 1 --python assets/timeline-observatory/validate_timeline_observatory.py
blender --background --python-exit-code 1 --python assets/timeline-observatory/verify_observatory_walk.py
```

`-- --all-previews` builds/renders everything; `-- --preview-only --all-previews` renders the saved file. The full builder resets factory data and disables numbered save versions. Preserve manual edits/recovery before replacing the master.

Confirmed content comes directly from canonical `src/data/portfolio.json` and the project catalogue, without VM evaluation of app source; `milestones.json` is generated. `src/data/portfolio.ts` is the validated browser facade, not the generator's content input. `observatory-layout.json`, `validation.json` and `walking-validation.json` are generated reports. Embedded controls add input preview; native animation needs no handlers/cache.

## Browser export

```sh
blender --background assets/timeline-observatory/timeline-observatory.blend --python-exit-code 1 --python assets/journey/export_browser_room.py -- --level experience
node --import tsx assets/journey/verify_rooms.mts
node --import tsx scripts/verify_timeline_focus.mts
node --import tsx scripts/verify_project_card_focus.mts
blender --background assets/timeline-observatory/timeline-observatory.blend --python-exit-code 1 --python assets/journey/verify_room_source.py -- --level experience
```

The semantic `experience` package has a separate looping XYZ route, stride-16 globe/planet channels, six cards/nodes and no NPC actors. Export is read-only.

Verify native-source agreement, exact route wrapping, player look preservation, all card/node picks, detail cameras, walking pause versus celestial pause, keyboard/touch equivalents, reduced motion, route-load Retry and demand-render cleanup.
