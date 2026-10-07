# Integration geometry and behavior

## City → lobby

The city camera reaches the threshold at 383. Lobby frames blend for 60 frames, then continue through reception/escalator/R1 to global 1403. Lobby entrance `(0,-12,0)` translates by `(-1.5,6.45,0)` to the city threshold `(-1.5,-5.55,0)`.

The integration-only portal is 5.75 m wide, 7.65 m high, with opaque sliding leaves, white trims, safety details, access panels, canopy/lettering and concealed pockets. Leaves overlap at seam/jamb/header when closed. A mobility display is raised and a support pier relocated to clear the entrance.

The old blockout is removed, a larger cavity/podium envelope fitted, and `geometry_clearance.py` subtracts the same voids from native city points/lines. The city export must use this integration geometry, not the smaller authored blockout. Inputs remain unchanged.

## Lobby → cabin

The cabin translates by approximately `(2.55,30.615,6.12)`, including a 0.20 m recess behind R1. Integration trims its redundant approach to local 62 and blends entry without stepping backward. Global 1521 equals cabin 180, the user-choice stop.

R1's original portal/display remain visible; fitted leaves/outlines seal the opening and retreat into pockets without motion scaling. The black placeholder and backing/shell opening are removed/fitted in the export copy. `geometry_clearance.py` owns these corrections.

Four floor switches ascend 01→04. Face/label/border groups share 6 mm press travel, hover/focus, spring and selected illumination. Keyboard choices are visually hidden; portrait views ease toward actual switches. Choosing a floor uses local 181–510 close/turn/open/walk-out, with the selected room replacing generic review landing geometry. The final 414–510 interval blends into the authored room pose. Return/cancel restores selection and input ownership.

## Staged loading

- City/journey config at startup.
- Lobby preload 100; reveal/hold 245, covering the portal before crossing.
- City geometry hides 383 independently of camera blending.
- Cabin preload 893; reveal/hold 1283 before R1 opens; lobby hides 1483.
- Room loads on floor selection; departure holds at 296, before door opening. Failed requests offer Retry/cancel; buffers remain cached on repeat visits.

Direct jumps and startup must respect holds, not briefly render an unloaded open interior. Full initial preloading remains a [planned feature](../../docs/roadmap.md).

## Packages and clocks

Point/line meshes become GPU primitives; dark surfaces/typography become triangles; native floor reflections are approximated in the browser. Cabin stipple meshes become points. Camera/actor strides: city 10, lobby/cabin/Skills 12, other rooms 16. Morph slots and route offsets belong to descriptors, not hardcoded consumers.

Projects uses 1200-frame native morph/transform animation independent of walking. Skills samples all 2940 tour frames for 90 parts and pauses movement/visitors together. Observatory uses a looping 2400-frame XYZ route with an independent six-channel celestial clock and no NPCs. About is static except authored focus views; Observer opens a camera-preserving React dialog.

Room entrance +Y rotates by π toward the cabin exit and translates to its threshold. Guided jumps preserve look, with explicit look/reset/detail controls. Live clocks run only for active/visible rooms and respect pause/reduced motion.

Verification reports: `handoff-verification.json` (city/lobby poses/clearance/door coverage), `elevator-handoff-verification.json` (selection continuity/forward progress/display rays), and source motion reports `room-motion-verification.json`, `room-skills-verification.json`, `room-experience-verification.json`.
