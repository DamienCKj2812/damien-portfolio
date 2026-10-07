# Cyber city

| Master | Purpose |
| --- | --- |
| **`cyber-city-walkthrough.blend`** | Editable architecture, original materials, entrance shell, doors, camera and traffic routes |
| **`monochrome-city-solid-tower.blend`** | Browser production model: cylindrical reference tower, five curved display surfaces, emissive crown/halo, traffic, sparse background and fairy-light trees |

The reference animation is 1–450 at 30 FPS. The production master opens in the **Mono • Walkthrough • camera** view. Hover over the 3D viewport and press **Space** to play/pause. If you have orbited into an editor perspective, press **Numpad 0** (View → Cameras → Active Camera) first. The first 90 frames are the stationary-position look-up/look-down phase; walking starts afterward. Solid shading is useful for playback, while Rendered shading gives the final material review. If your personal Space shortcut opens Search or Tools instead, use the Timeline Play button.

The main KAJU tower follows the owner's cylindrical building specification. A continuous curved skin carries separate logo and portrait panels and three stacked right-side displays. The rooftop has a setback crown drum, a floating bright halo and four paired masts; the right flank has two balcony levels and a descending crescent fin. Glitch panels, vertical LED fins, sparkle trees and a layered atrium canopy complete the facade. `reference_tower_spec.py` fits the proportions to the existing entrance and owns all screen aspects. See [design details](DESIGN.md) and the [reference-tower workflow](WORKFLOW.md#current-reference-based-main-tower).

In the browser, the flying/road vehicles and ten outdoor walkers repeat their authored routes on a separate clock. Eight stationary street people retain their conversation/phone/bag poses and accessories. Scrolling controls the camera, foreground maglev and entrance journey; the rear-highway train has its own one-way clock. A layered wireframe skyline restores the original background towers, stepped crowns and spires, with restrained floor bands and tiny window lights. Motion pauses offscreen, while the page is hidden or with reduced motion. A separate **Reference tower • Reference inspection camera** supplies the low-angle portrait review pose without changing the walkthrough.

Three occasional shooting stars cross distinct world-space sky routes with staggered timing and fading trails. They use the same scroll-independent visible-city clock and are suppressed by reduced-motion preferences.

Nine world-fixed bright stars use white cores and soft optical flare sprites. The original `Orbital sky • bright star optical shine` sits at opening-camera sky coordinates `(0.730, 0.313)` (upper-right); eight smaller companions are scattered across the sky. `bright_star_layout.py` owns their positions and sizes. Apply only this star update with `blender --background assets/cyber-city/monochrome-city-solid-tower.blend --python-exit-code 1 --python assets/cyber-city/add_bright_stars.py`, then regenerate the connected city package following the journey workflow. Full sky authoring uses the same layout.

- [Agent instructions](AGENTS.md)
- [Design, crowd, motion and source data](DESIGN.md)
- [Authoring order and exports](WORKFLOW.md)
- [Connected journey](../journey/README.md)

[Restored orbital sky preview](restored-sky-preview.png) shows the preserved arcs, constellations, crescents and optical highlights without annotation labels.

[Restored outdoor NPC preview](restored-outdoor-npcs.png) shows the 18-person exterior crowd.

[Wireframe skyline preview](wireframe-skyline-preview.png) shows the layered night-city backdrop restored behind the tower.

The source and production masters are self-contained. Intermediate styling/optimization files are reproducible outputs, not additional authoritative models.
