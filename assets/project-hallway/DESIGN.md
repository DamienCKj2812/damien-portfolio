# Hallway design and interaction

The 104.7 m corridor is 10 m wide and 6.2 m high. Sixteen reviewed projects form three ordered sections: Client / real world project (4), Academic Assignment (10), and Personal Project (2). Bays have 7.8 m spacing within each category and a 2 m right-side stagger, with one entrance Projects directory and an end message. The Selected Work exhibition-guide board and its projector have been removed. Cards face east (+X) on the left and west (-X) on the right.

Each of the 17 cards has a floor projector with twin luminous rings, emitter housing, brackets and a faint transparent/emissive frustum rather than volume simulation. Both side walls are continuous opaque matte-black surfaces (nonmetallic, roughness 0.92); there are no window panes, mirrors or window frames. Benches sit between displays.

The world strength is 0.025 and overhead softboxes use only 5 W, leaving the environment dark while luminous card outlines and typography stand out. There are no individual card spotlights or baked spotlight pools.

The 1.1 m pure-dot pillars have no solid cores/collars; lower rows and footprints emit seven times the shafts. The ceiling follows the flowing-rib reference: 41 continuous charcoal louvers curve in a shared S-wave field, with subtly sculpted depth and dark side/underside/bevel materials. Five selected ribs carry white integrated light strips; two quiet perimeter lights frame the ceiling. The 18 m wave rhythm continues through the entire 101.8 m hallway and covers the entrance. Top height is 6.18 m and the lowest light is 5.878 m. No ceiling grid, dots, coffer boxes, junction blocks or recessed circular lights are intended. The browser exports ribs and lighting as separate `ceilingRib`/`ceilingLight` groups, and the glass floor reflects their real geometry.

The Projects browser floor uses a restrained reflection strength of 0.15, keeping panels and visitors subtly visible in the polished surface rather than making the long corridor a bright mirror.

Floor seams form broad 2.5 m × 7.8 m polished slabs, aligned to the project-bay rhythm, with subdued luminance 0.055 instead of a dense bright grid.

## Content

`docs/project-catalogue.md` is the approved source for descriptions, contribution attribution, technologies, evidence and repository links. `build_project_catalogue.py` generates `projects.json` with fitted card text plus verbatim full sections. The original 2026-10-04 public snapshot is preserved separately. FYP leads Academic as one featured exhibit with three repositories. Data Structures groups both parts; TXSA's empty Part 2 is omitted; RTS includes the confirmed GCS contribution. Client links and DWMLight/ANVA CMS and AMPLYFII attribution come from the catalogue. FYP numerical results retain their recorded-offline-evaluation context, never relabelled as live production performance.

There is no entrance door for Client / real world project. Two open holographic portals appear at Y=27.3 m (Academic) and Y=78 m (Personal). Satin caps/jambs, white light rails, inset tunnel contours, hanging filaments, transparent/smoked veils and fine dust follow the reference. Their lights and lettering reveal after preceding displays (Y=19.5 m and Y=70.2 m). Veils soften around the approaching camera. There are no sliding leaves, entry buttons or blocking thresholds: keyboard, touch, scrolling and progress seeking pass through continuously and silently. Top-right current-category text follows actual camera position in both directions, including with the sidebar hidden. Sidebar categories unlock automatically on crossing.

The builder copies NPC geometry from the production city as local data, not a linked library. Fifteen performances include conversation/listening, viewing, phone/thinking, and three walkers (one with a bag). Accessories stay aligned.

Native transforms, shape keys and Cycles modifiers animate without scripts/caches. Walk loops are 300 frames; interaction cycles 120/150/200 with staggered phases. The global 1200-frame/40-second cycle wraps all performances. Walkers follow closed oval routes with distance-based strides, turns, arm swing and foot lifts; idle visitors gesture, nod, glance or shift weight.

## Blender control

Run embedded **hallway_controls.py** once, then **F3 → Project Hallway: Walk** or **N → Hallway → Start Walking**. Mouse looks freely; W/S or arrows walk the fixed +Y/-Y axis; Shift increases speed 3→8 m/s; Tab releases/captures mouse; Esc exits. Motion stays X=0, Z=2.45 and respects corridor bounds. NPC time runs even when walking stops.

Review cameras include Conversation, Walking, Thinking, east/west display detail, Ceiling review and Ceiling perspective. The optional 1–1200 walkthrough camera is separate from the free-look camera.

## Website / Level 03

W/S/arrows, drag look, scene-local scroll, hold-to-move touch/keyboard controls, and a project selector expose the corridor. A real display click shows metadata/repository links. Pause visitors/reduced motion freeze their independent clock; inactive/offscreen states settle. Escape/Return restores elevator selection; cached packages support repeat visits.

Project selection shows the full catalogue title, overview, repository links and expandable source-backed sections: purpose, role/contribution, features, architecture, technologies, challenges, evidence, lessons and source references. Tables/code diagrams are retained, including FYP's recorded results. Only the selected project's rich details mount. The former meeting-room scene remains retired; its authored model is retained as an archived source asset.

The first entrance board is now a raised Category 01 introduction for Client / Real-world Projects, listing the four client projects rather than all category names. It remains off the center walking lane and faces the entrance camera. Its projector is overhead and points downward; the complete optical rings and frustum are regenerated for the new position. Clicking it opens a zoom-only view of the board and device, with no description/navigation panels. Back/Escape restores the saved hallway view.

The two portals display `02 Academic Assignment Projects` and `03 Personal Projects`. Large thin luminous 02/03 outline digits appear on the left partition, with a vertical upper light, short underline and three small dot accents matching the reference. They use native curve centerlines and the existing category-frame rendering policy, without new animation loops or click targets.

Clicking a modeled card or selecting its sidebar entry moves into a dedicated front-facing view. Camera distance and projection offset fit the authored mesh and its corner brackets into the available screen area, including portrait/mobile/landscape sizes. The complete card stays visible instead of cropping its top/bottom. Walking position/look remain saved. Nearby visitors hide and their clock suspends while reading, then resumes on return.

Once framed, **Explore** reveals the case-file presentation: the actual 3D card in the middle, the selected catalogue section on the left, and a ten-section menu on the right. Panels use transparent fading gradients and subtle backdrop softening, not solid black slabs. Arrow Up/Down changes sections. Mobile uses a compact selector above the card and a scrolling description dock below. Back/Escape returns first to the focused card, then to the original hallway view; guide-dialog Escape remains isolated from this hierarchy.

The current Explore layout follows `Project Detail v2.dc.html`: full-height wide edge fades, a fixed left header and source-backed type/role metadata, separately scrolling/masked section content, numbered feature/challenge rows, and previous/next controls that stop at Start/End. The right index has a proportional illuminated progress rail and visited/active text states. Keyboard navigation is clamped rather than wrapping. The middle-stage fit uses the reference's responsive gutters; mobile keeps the selector and reading dock. Global audio is the reference's toggle-only Music/SFX row at fixed mix levels. Reference sample years, deployment claims and live URLs are not copied into the approved catalogue content.

## Previews and cost

Entrance/interior/end, east/west projector, and ceiling images document the scene. Four-second conversation/walking/thinking GIF excerpts cut at replay; the complete native cycle is seamless. Layout/validation/ceiling reports hold measured data.

Three shared particle groups instance low-poly spheres without realization; morphs deform only source points. Outline curves and architecture are low-complexity. There are no external textures/fonts/libraries or simulation caches. Cycles uses adaptive 32-sample rendering; AgX falls back to Standard when unavailable locally.
