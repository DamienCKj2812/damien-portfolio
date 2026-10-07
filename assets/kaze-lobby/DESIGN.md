# Lobby design and navigation

## Room

The 20 × 36.5 × 18 m atrium uses dark occluding meshes, fine white curves, reflective stone, particle foliage/people, and selective architectural glow. Collections separate furniture, stairs/escalators, signage, gardens, people, atmosphere, cameras, navigation, and upper foyer.

- Reception island with monitors, motto, and luminous plinth.
- KAJU structural pillar, 3.5 × 2.2 × 16 m, at `(0,6.9,8)`; front Y=5.8, 1.2 m behind the countertop. Its cap sits below the branching roof shoulders, keeping the outlined rectangular header visible beneath the canopy. The triangular reference logo and KAJU wordmark share the canonical branding source in `assets/branding/kaju_brand.py`.
- Four-metre-wide carpet from entrance Y=-12 to beneath reception Y=4.75.
- Sculpted overhead canopy: a continuous black branching soffit has five individually shaped openings—a left sweep, narrow central slit, larger diagonal right sweep and two rear forks. Rounded recessed returns carry bright lower lips and two fine inner contours; paired diagonal silver grid members sit above them. A closed collar connects the identity pillar to sampled roof-lip vertices, with two continuous fillets tangent to the vertical pillar edges and roof contours. The left campaign banner has no thin floor-to-roof support beside it. There are no ceiling vines. The roof has its own `16 Sculpted ceiling` collection, and the `Sculpted ceiling detail camera` provides the wide, upward reference view.
- Two simplified escalators with 34 steps each, closed side skirts, rounded handrail loops, and flat plates. Entries start at Y=8.45, 3.85 m behind the countertop.
- Upper walking surface Z=6.12, foyer Y=19–24.5. Left L1/L2 and right R1/R2 elevator entrances have editable door leaves, call panels, indicators and a directory.
- Waiting sofas face inward: left +X, right -X. Their opaque bases are removed; fine support frames remain.
- Behind the identity pillar, a holographic goldfish floats over a circular illuminated pedestal at `(0,15.55,0)`. Native surface particles, outlined fins/rays, eye/gill curves, horizontal halos and broken projection columns recreate the monochrome reference. A rear display wall, low benches, faceted stone plinths, vertical light channels and a wall light matrix frame the exhibit between the escalators. The space above the fish is open, with no sub-ceiling canopy.
- `fish_motion.py` gives the hologram a seamless hovering swim: a gently bobbing/turning body and head, a two-stage swishing tail, and separate fin flutter. Native parent rigs carry points and outlines together. It shares the independent visible-lobby clock with the people, so stopping or reversing scroll does not stop or reverse the fish; hidden/reduced-motion views suspend playback.
- Varied static particle poses include reading, phones, coffee, conversation, bags, handrail resting and an escalator rider. The walkthrough moves that rider to the descending flight to keep its own path clear.

Pillar outlines, handrails, lift portals and gallery underside strips use separate Cyber hero/architectural/secondary materials with restrained compositor glow. Use Rendered shading or F12.

## Cameras and previews

`lobby-concept.png` and `lobby-wide.png` show portrait/wide compositions. Upper views are `upper-landing-elevators.png`, `escalator-arrival.png`, and `upper-landing-back-view.png`; select the corresponding Upper elevator foyer, Escalator arrival, or Upper foyer back toward escalators camera in Scene Properties.

`ceiling-detail.png` shows the sculpted canopy from the upward-facing Sculpted ceiling detail camera.

`pillar-ceiling-junction.png` shows the continuous roof collar from the Pillar ceiling junction camera.

`holographic-fish-exhibit.png` shows the rear installation from the Holographic fish exhibit camera, standing behind the identity pillar.

`holographic-fish-walkthrough.png` shows the installation from navigation frame 420 on the existing approach to the right escalator.

`holographic-fish-swimming.gif` shows the autonomous tail/body/fin loop with a fixed exhibit camera.

## Navigation timeline

1–1020 at 30 FPS / 34 seconds, using **Lobby • Navigation / walkthrough camera**:

| Frames | Phase |
| --- | --- |
| 1–60 | Entrance view |
| 61–509 | Carpet approach, then pass reception on the right |
| 510–690 | Right escalator ride, six seconds |
| 691–840 | Approach R1 |
| 840–899 | Hold outside |
| 900–990 | Door leaves slide open |
| 991–1020 | Open-door handoff hold |

The camera stops at `(4.05,21.45,7.82)`, about 2.3 m before the threshold; it does not enter the authored black placeholder. Monotone interpolation, animated look target, lens keys (16 mm entrance, 15 mm ride, 14 mm approach) and enlarged viewport framing support review.

Preview frames: `navigation-start.png`, `navigation-escalator.png`, `navigation-elevator-arrival.png`, `navigation-elevator-open.png`.

## Anchors

- Floor X=-10…10, Y=-12…24.5, Z=0; +Y points inward.
- Entrance `(0,-12,0)`; reception focus `(0,3.7,1.5)`.
- Upper landing `(0,19.5,6.12)`; R1 door centre `(4.05,23.965,7.66)`.
- `lobby-manifest.json` records geometry/anchors; `navigation-handoff.json` records the final pose; `navigation-camera.json` stores all sampled frames.
