# Gallery design and behavior

The 12 × 16 × 5.4 m monochrome gallery has portrait skill frames, numbered wire symbols/lists, separate `ExhibitUV` content surfaces, reflective tiles, ceiling grid/perimeter light, skirting and three benches. Nine approved areas are Languages, Frameworks, Backend & APIs, Databases, Data & AI, Security, DevOps & CI/CD, Microservices and Linux. `skills.json` is generated from the completed About profile/toolkit and the approved Projects catalogue. Five fitted card rows summarize each area; the detailed toolkit also includes project-backed Go, R, Rust, Supabase, Redis Streams, 3D web tooling and ML/data libraries.

Each area retains project evidence and repository links plus explicit profile-only/learning scope. About-only C/PHP, Spring Boot, MySQL and distribution/tool claims are not relabelled as implemented catalogue projects. The Microservices card has four rows—Redis Streams/OTLP, REST/WebSockets, Metrics/traces and Queues/resilience—with the removed Kafka/gateways row and its branch marker absent. AI/ML/3D modeling remain stated learning areas; FYP results keep their recorded-evaluation context, and DWMLight/AMPLYFII collaboration attribution is preserved. Pinecone/RAG evidence comes from the completed About experience at COS Great Trading. No proficiency percentage or unprovided certification is added.

## AT-AT walker

The static left-facing AT-AT replaces the T-Rex and follows the supplied three-quarter white-outline reference. A uniform 0.72 display scale makes it about 4.47 × 1.83 × 3.46 m on the existing 7.4 × 3.2 m illuminated plinth. Its roof sits around 3.80 m above the floor, leaving about 1.6 m below the gallery ceiling. Black occluding armor and fine white native curves create a clean technical-illustration silhouette.

The taller beveled body has large inset armor panels, access hatches, fasteners, roof rails, side ladders and belly ribs. A flexible ringed neck connects the faceted visor/head, concentric side turrets and twin chin/side cannons. Four separate legs have circular hip/knee drums, exposed upper struts, paired hydraulic rods, flared ankle armor and broad toe-tab feet.

`atat_walker.py` owns editable model construction. `replace_trex_with_atat.py` is the narrow master-saving replacement, verifying other gallery/visitor/camera transforms across the tour. `render_atat.py` renders the master read-only, with an optional isolated reference view. Prior dinosaur scripts/images are construction history, not the current build.

## Visitors

Six slim lobby-style point humans use 90 editable articulated meshes, with distance-based planted/swinging feet, knee placement, arm counter-swing, breathing and gaze:

1. Explore left displays, skirt the plinth, study the AT-AT and return.
2. View the walker from rear/right, inspect right displays and return.
3. Walk between left exhibits; hands-behind-back during viewing pauses.
4. Walk between Linux/DevOps; thinking hand near chin during pauses.
5. Explain the sculpture with a pointing gesture.
6. Listen and alternate attention between figure/sculpture.

The native clip is 1–960 / 32 seconds, with frame 960 duplicating frame 1 and 959 unique browser frames. Cycles modifiers repeat it throughout the tour. Explorers use front-left and rear-right reserved lanes; the side readers stay in wall-side lanes. Clearance is checked across every player/NPC time combination, so stopping or jumping the tour does not cause collisions. Root paths and transforms stay editable.

## Guided route and look

The authored 1–2940 / 98-second route visits all nine skill exhibits and the AT-AT, then returns to the entrance. Browser traversal is reparameterized by travel distance for continuous walking without checkpoint holds. The location-only player rig carries a 1.70 m-eye-height camera with no rotation keys or auto-aim. Static review cameras are separate.

For Blender mouse look, run **Gallery Walk Preview.py** once in the Text Editor; return to Layout, press N and choose **Gallery Walk → Start Guided Walk**. Hold RMB/MMB and drag to look; Space pauses; R resets look; Esc/Stop exits. Native Space playback moves without the script. No embedded Python auto-runs.

The browser's Level 02 retains Start/resume, Space, previous/next, Home and route progress controls; these route jumps preserve look. Clicking a skill card or selecting its sidebar entry opens the same v2 case-file presentation as Projects: full 3D card in the middle, source-backed content on the left and a section menu/progress rail on the right, with fading side backgrounds and shared typography/controls. Eight sections cover summary, toolkit, project evidence, workflow, decisions/trade-offs, collaboration, learning/scope and sources. Wheel, arrow keys, previous/next and mobile selection navigate the sections.

Focus uses the exported card normal/right vectors and dimensions, covering both side walls and the rear wall. The saved route, yaw/pitch and original tour running/paused state remain intact. Visitors and the AT-AT temporarily hide and their clock suspends while reading, preventing sculpture/visitor occlusion and idle rendering. Back/Escape restores the gallery and resumes the original tour state. The outlined AT-AT still has its real pick, guided stop and existing close-up camera; it is not repurposed as a skill card. Visitors retain their independent playback in normal gallery view, including with the tour paused or at its endpoint. Reduced motion, explicit animation pause and offscreen controls still suspend playback.

## Review and anchors

`gallery-atat.png` and `gallery-atat-reference.png` show the current walker and its isolated outline view. Earlier gallery/T-Rex previews document construction history. Walk examples are `gallery-walk-start.png`, `gallery-walk-languages.png` and `gallery-walk-databases.png`; their illustrative look angles are not saved/keyed by the rendering helper.

Floor X=-6…6, Y=-7…9, Z=0. Entrance `(0,-7,0)`, inward +Y. Walker root `(0,3.85,.34)`; sculpture anchor targets its scaled mid-height, around `(0,3.85,2.07)`. Plinth X=-3.9…3.5, Y=2.25…5.45. `gallery-manifest.json`/`gallery-walk.json` record the native layout, stages and guided positions.
