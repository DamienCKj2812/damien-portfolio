# Office workflow

## Authoring

```sh
blender --background --factory-startup --python-exit-code 1 --python assets/about-office/build_office.py -- --render
```

Omit `-- --render` for geometry only. The fresh-scene generator saves the single main file and one prior-save backup. Normal edits belong directly in the master; full generation replaces them. Earlier standing-card/zoom patch scripts are historical, not a sequence for the finished file.

To center the existing authored presentation camera on the computer without rebuilding the room:

```sh
blender --background assets/about-office/about-office.blend --python-exit-code 1 --python assets/about-office/center_presentation_camera.py
```

This narrow authoring update preserves all other object/camera transforms and keeps one previous-save backup. Re-export the browser package afterward.

## Read-only browser export

To update only the computer's Malaysia map in the existing master:

```sh
blender --background assets/about-office/about-office.blend --python-exit-code 1 --python assets/about-office/update_malaysia_screen.py
```

The focused update retains the UV target and verifies surrounding transforms/actions at five aquarium-cycle frames, then saves one `.blend1` backup. The builder calls the same `malaysia_screen.py` function for reproducible full builds. Re-export About below, then run `verify_malaysia_screen.py` against the master to check both native map regions, monochrome materials, bounds and browser groups. Native screen/presentation previews can render the existing **Screen detail camera** and **About office presentation camera** without saving camera changes.

To complete the rounded wall frame's bright outline in an existing master without rebuilding the office:

```sh
blender --background assets/about-office/about-office.blend --python-exit-code 1 --python assets/about-office/complete_frame_outline.py
```

This replaces the two partial light strips with one closed perimeter following the existing fine frame, preserving its light material and thickness. `office_environment.py` uses the same complete outline on future builds. Re-export below afterward.

```sh
blender --background assets/about-office/about-office.blend --python-exit-code 1 --python assets/journey/export_browser_room.py -- --level about
node assets/journey/verify_rooms.mjs
blender --background assets/about-office/about-office.blend --python-exit-code 1 --python assets/about-office/verify_malaysia_screen.py
```

The exporter writes native points/lines/triangles and static stride-16 camera data to `public/models/rooms/about/`; it adds memory-side card-pick and Observer-pick geometry. The About master supplies its own solid entry surround; flush entry panels export with the `officeDoor` role, which the browser hides in favor of the shared clickable `RoomElevatorEntrance`. It never saves the Blender master. Routing/main/entry/focus names are in `assets/journey/room-destinations.json`.

## Interaction checks

Enter About through floor 01. Confirm the computer center is centered in the viewport; test mouse/touch turns, 360° yaw, arrow-key look, R/Reset look, and idle settling. Test actual Observer clicks/taps, Meet the Observer, native dialog focus/Tab/Escape, and background-look suspension. Then test real card picks, View business card and a smooth Back to office preserving the previous look direction. Clicking outside the focused card also smoothly returns to the saved office look; card clicks, dragging, multi-touch and contact links must not dismiss it. Reduced motion skips the camera easing. Scrolling backward at the office home view opens the elevator-return confirmation and walking transition.

Focused contact-card dismissal checks: `node scripts/verify_contact_card_dismissal.mjs`; audio checks: `node scripts/verify_interaction_audio.mjs`.

Observer implementation is `ObserverProfile.jsx` / `observerProfile.css`, with picking in `CityScene.jsx` and state in `CityWalkthrough.jsx`. `profileOpen` suspends room input and picks; it must not change the camera target. Content edits need lint/build, while model/export edits also need room-package validation.
