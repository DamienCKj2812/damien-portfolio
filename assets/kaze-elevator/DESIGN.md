# Cabin design and flow

Black metal panels, silver seams, illuminated corner reveals, reflective floor, chrome rails, inset ceiling, KAJU branding, and a stippled human-profile campaign use native geometry/typography. There are four floor meshes; door-operation icons and 05 Contact are removed.

## Blender review

Run embedded **KAZE_Elevator_Controls.py** once in the Text Editor. In the 3D View open **N → KAJU Elevator**:

1. **Replay entry / stop at selection** enters, turns toward the panel, and stops at 180.
2. Choose a sidebar destination or enable viewport button clicks in Object Mode. Selecting a modeled face/number/label starts departure at 181.
3. The floor highlights/display update, doors close, camera turns toward the exit, doors reopen, and the camera walks out to the review landing.
4. Replay selected departure or reset to entry. Escape disables viewport click mode.

Preview Python is embedded but not automatically executed. Native camera/door animation plays independently. Retained Dialog collections/cards are design review material, hidden during direct departure; the browser reveals actual destination packages instead of review signs/cards.

## Authored timing

| Frames at 30 FPS | Phase |
| --- | --- |
| 1–180 | Entry and user-choice stop |
| 181–220 | Selected floor illuminates; doors close |
| 221–296 | Turn toward exit |
| 300–350 | Doors open |
| 351–370 | Pause |
| 370–510 | Walk through threshold and stop |

The Full journey camera stays at 1.65 m with a constant 21 mm lens. Clamped position curves and unwrapped Euler yaw avoid overshoot/flips. The older entrance camera/path remains review history. `journey-camera.json` holds sampled phases; `journey-selection.png`, `journey-facing-doors.png`, `journey-doors-open.png`, `journey-walkout.png`, and `journey-arrival.png` are key views.

## Website selection

The modeled switches are the visible interface. Hover/focus brightens the rim/text; press moves the face, label and border inward 6 mm, then springs back. Selected illumination stays latched. Equivalent keyboard choices remain visually hidden; Tab/Enter/Space and direct mobile touch select the same floors. Portrait views ease toward the panel. Departure/cancel status is compact, not a left overlay covering switches.

The floor panel follows the clipped-corner reference: four graphite plates ordered 04–01 from top to bottom, white/cool luminous chamfered rims, a larger left number separated by a fine vertical rule, widely tracked captions, and right chevrons. Idle outlines remain softly illuminated. The upper display shows two dashes; the lower alarm circle and three-line future statement complete the composition. Browser rim geometry follows the authored eight-corner face rather than drawing a rectangular bounding box. All lettering/divider/chevron/rim geometry travels with its switch.

## Coordinates

- Cabin clear dimensions 2.6 × 2.8 × 3.2 m; entrance `(0,0,0)`, back Y=2.8, Blender Z-up.
- Local `(x,y,z)` converts to Three.js `(x,z,-y)`. Entrances align only in integration/export copies.
- Named anchors use the `Elevator / ` prefix. Left/Right sliding door meshes retain local X open/closed values and interaction extras; don't merge them into the shell.
- Clear opening is about 2.32 m; open pockets need about 3.85 m overall width. Browser cabin recess is 0.20 m behind R1.

Local GLBs, dialog renders, levels/manifest JSON, and entrance samples remain supporting review outputs. They do not replace the point/line browser package.
