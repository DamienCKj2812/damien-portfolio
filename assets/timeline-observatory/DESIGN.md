# Observatory design and controls

The 25 m-diameter chamber has curved satin-black panel walls, entry opening, reflective floor and a glazed roof oculus with architectural light rings and a smooth black ceiling fascia. Six cards cover the APU diploma, LYJ Events & Marketing, COS Great Trading, freelance work, the APU bachelor's degree and current focus. `build_timeline_content.mts` generates `milestones.json` directly from confirmed About data in `src/data/portfolio.json` and the Level 03 project catalogue. Focused entries share the Projects left-info/right-section-menu layout, with the authored card framed in the centre.

Four real curved wall windows have thin frames/clear glazing and replace former flat cosmic banners. Five 3D exterior planets include ringed, geodesic, banded, cratered and overhead worlds. Opaque planet bodies mask far-side contours; a spatial starfield gives real depth/parallax.

Eight shallow black wall ribs have slender recessed white LED strips and brighter lower lights, replacing the former dotted pillars to match the architectural reference. Wall panel joints are dark and recessed; a subtle procedural microtexture gives satin-black surfaces a fine physical finish without patterned decoration. A central geodesic globe, dais/orbits and Same person / Bigger possibilities inscription connect the chronology. Further ahead constellation, Past/Present/Future captions and two benches complete the room. No NPCs or humanoids are included.

## Native review

The diploma board reads **DIPLOMA IN IT (Software Engineer Specialism)** and the bachelor's board reads **Bachelor of Degree in Computer Science (Data Analytics Specialism)**. Primary headings and smaller specialism lines are fitted independently. The first three boards use owner-supplied APU, LYJ Events & Marketing and COS Great Trading artwork, prepared as proportional original-color PNGs on separate UV quads, without grayscale filtering or browser color tint. The replaced procedural icons stay hidden for recovery. PNG alpha is preserved for transparent marks; logo image bytes are included in the browser package's cache hash.

### Black-glass interface floor

The floor has a recessed charcoal foundation and level 70 mm smoked-black 3 × 3 m square slabs. Only the perimeter panels are clipped to the circular room. Recessed 8 mm joints contain single hairline white centrelines, matching the supplied architectural reference rather than a dense luminous tile grid. A low-roughness, coated obsidian material reflects architecture and white illumination.

Twenty-four selected square slabs carry evenly spaced, very tiny white dots (13 × 13 points per slab, 6 mm diameter), distributed across the entry, both central aisles and the rear floor. About 56% of the room area remains plain black glass apart from its seams. No dot panels are hidden under the central dais. Four tiny diamond joints, two short rounded corner brackets and one small stacked TRAIN / EVOLVE / REPEAT inscription provide the only additional floor decoration. There are no floor HUD circles or scanning arcs. These are visual embedded markings; milestone interactions remain in the timeline.

The curved charcoal walls are opaque 160 mm architectural shells with no luminous wireframe grid. Wall/ceiling base values are .003/.002, with low metallic reflectance and a restrained satin finish. Architectural wall LEDs are softened, ceiling rings use a dedicated dim-white material, and native ceiling bounce is 12 W per softbox. Exhibit outlines, typography and floor-dot materials retain their readable contrast. Thickness extends outward to retain interior floor/route clearance; the four real observation windows and entrance remain open.

`timeline-observatory-floor.png` uses the **Interface floor** camera for a close architectural review. Inlays are placed 1.2 mm above the level slab surface to avoid z-fighting and read as embedded light; no thick bars, raised tiles, external decals or texture dependencies are used. Native glass reflections are Cycles material effects; the existing browser exporter retains its native point/curve representation.

Space plays the 1–2400 / 80-second movement route: entry, all six milestones with six-second viewing stops, then return. Only position is keyed; camera/rig rotation remains free. Eye height is 2.45 m, with stops about 2.8 m from the cards and clear of dais/benches. Globe and planets animate natively on the tour cycle.

Run embedded **observatory_controls.py** once, then **F3 → Timeline Observatory: Guided Walk** or **N → Observatory → Start Guided Walk**. Mouse gives free 360° look; Space pauses walking while the globe continues; ←/→ visits nodes; Home returns to entrance; Tab releases/captures mouse; Esc exits. Jumps/loops preserve look. No Python auto-runs when the file opens.

Review cameras include Main gallery, Globe detail, Star oculus, Space window and Node detail. Preview/layout/native walking reports document the scene.

## Browser / Level 04

The separate `rooms/experience/` package loads on selection, caches on repeat visits and holds closed doors while unavailable. Guided controls include Start/resume, Space, station arrows/Home, route slider and explicit look/reset/detail actions. Cards/luminous nodes are clickable; node pick volumes are enlarged invisibly.

Walking can pause while celestial motion continues. Pause animation, reduced motion, inactivity/offscreen states stop live invalidation. Globe, Roof window and Observation window use authored cameras. Return/Escape restores the cabin.

## Cost and source independence

Curves use low-resolution bevels; planets modest sphere segments; stars/floor dots share instanced low-poly spheres without realization. Glazing is mostly transparent with a small reflection layer, not thick refraction. Native typography and procedural wall microtexture require no external fonts/textures. The builder reads no city/lobby/hallway master. Cycles uses adaptive 32-sample rendering; AgX falls back to Standard when unavailable.
