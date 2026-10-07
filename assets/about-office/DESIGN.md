# Office design and interactions

The 12 × 12 × 4.6 m room is a complete 360° interior with skyline-facing panoramic frames, an original 45-tower backdrop, reflective black tiles, fine seams, luminous ceiling strips and soft monochrome bloom.

The workstation includes a drawer pedestal/open support frame, ultrawide monitor, keyboard, mouse contours, lamp, pens, notebook, books and a wire globe. A turned adjustable chair has cloth panels, open arms, piston, five-star base and casters. Two outlined plants and a hands-behind-back particle Observer complete the room.

## Surrounding walls

- **Right (+X):** a quiet solid feature wall following the updated reference: a large softly rounded, luminous orbital-art panel with the architectural caption **A QUIETER TOMORROW**, a long low console with four plain doors and recessed plinth lighting, a delicate plant and two captioned book stacks. One narrow end bookshelf has three illuminated display compartments, 10 standing books, small horizontal stacks and one framed original mountain illustration. Tall dark divider/end pillars complete the wall.
- **Left (−X):** a solid wall around a recessed 6.2 × 2.0 m aquarium, composed to match the clean aquarium reference: a slim double-outline frame, one concealed upper light strip, three small fish, two restrained bubble trails and a gently contoured substrate. Smooth tapered aquatic leaves and rounded stones cluster at the ends, leaving generous open water in the center. Fish follow smooth preset routes with gentle vertical motion and end turns. Sixteen staggered bubbles rise, grow slightly and shrink away before recycling at the bottom. Native animation repeats over 720 frames / 24 seconds, with four-second bubble cycles. Plants, stones and the enclosure are static.
- **Behind the visitor (−Y):** a plain solid wall around the elevator passage. The Blender master includes flush dark panels tagged `officeDoor`; the browser hides them and uses the shared, recognizable elevator entrance found on every floor. Full-height leaves fit flush inside its surround, and a wall-mounted call panel sits beside the doors. Clicking either starts the return trip directly; the entrance clears while the camera enters the cabin.
- **Skyline-facing (+Y):** the original panoramic glazing remains.

`office_environment.py` owns these additions and is called by `build_office.py`. Its local random generator preserves the existing workstation, skyline, Observer, card and camera geometry when rebuilding.

Materials use near-black walls, cabinetry and recessed backing; darker charcoal shelves, varied dark book covers and muted aquarium surfaces provide tonal depth. Silver picture details, book-spine bands and recessed lighting carry the brighter accents rather than filling every surface with medium gray.

The browser advances the aquarium's native actor clock only while its bounds intersect the camera view in the active office. Looking away, opening the profile or card view, hiding the page, pausing the room or enabling reduced motion freezes playback; returning to the aquarium resumes it without a time jump. The shared Canvas continues to settle when the aquarium is outside the view.

The monitor's **About content screen / web texture target** remains a separate `ScreenUV` mesh, aspect 2.259:1. `malaysia_screen.py` replaces its abstract network/navigation/globe/chart with a black-and-white geographic display: white Malaysia land shapes, fine coastlines, faint regional context, MALAYSIA heading, and labelled Brunei/Singapore markers. Both Peninsular Malaysia and Sabah/Sarawak share one geographic scale. The Natural Earth 1:50m source is public domain; cached country geometry and source hashes are recorded in `map-data/` and `malaysia-screen.json`. The map exports natively as triangles/curve centerlines/text under the `officeScreenMap` role, without a screenshot texture or generated UV-offset edits. Old content stays hidden for recovery; the workstation, camera, Observer, contact card and aquarium are preserved. The decorative Floor 32 label is not an imposed physical altitude or completed elevator destination.

## Review cameras

| Image | Camera suffix (all prefixed `Office • `) |
| --- | --- |
| `office-preview.png` | About office presentation camera |
| `office-screen.png` | Screen detail camera |
| `office-overview.png` | Office architectural overview camera |
| `office-name-card.png` | Contact card focus camera |

Choose a camera in Scene Properties, press Numpad 0 and use Rendered/F12. The office arrival camera is an eye-level integration reference.

The presentation camera is aligned horizontally with the monitor and looks at its exact screen center. In the website, drag to turn through a full 360° from that fixed viewpoint; arrow keys look horizontally/vertically, and R/Reset look returns to the computer. Touch drags beginning horizontally turn the view; vertical swipes keep the entrance-return gesture. The contact view returns smoothly to the previous office look direction.

## Flat card

The 90 × 55 × 0.8 mm paper card lies near `(1.82,-.16,.8962)`, slightly rotated. Its top mesh **Name card / contact face** has `CardUV` and click metadata. Contact text matches the existing GitHub link.

There is no standing base or automatic close-up playback. The 180-frame/6-second idle timeline pulses only a thin luminous rim and corner glint; shine peaks at 46/136. Hidden review/controller metadata does not implement website clicking by itself.

The browser card pick uses a forgiving 0.70 × 0.48 × 0.135 m invisible 3D volume so oblique views can activate it without changing the physical card. **View business card** is its keyboard/touch alternative. The authored focus camera exposes contact links; Back/Escape returns to the prior room view.

In the main office view, looking left/right until the camera's central vertical line crosses the card or Observer highlights the closest aligned target with luminous corner brackets and a small floating **CONTACT** or **OBSERVER** label. Hovering also reveals a visible target. Labels are anchored above their objects and can be clicked or keyboard-activated. They disappear while viewing the card, showing the profile, returning to the elevator, or looking away. Projection updates follow existing demand-rendered camera frames and settle when idle; no independent animation loop is added.

## Observer dialog

**Observer / looking out at city** opens the React **Identity / Portrait / Record** sheet through an exported invisible pick volume. It leaves the office/card camera unchanged. Close/Return/Escape dismiss it; focus trapping/restoration and scroll locking keep background room input inactive. The fading floor sidebar can collapse to its Info tab while looking around.

The sheet uses nearly the full viewport and opens with a monochrome adaptation of [Jitter's Glitch 01 text reveal](https://jitter.video/template/glitch-01-text-reveal/): staggered rectangular signal masks, displaced duplicate text slices, and per-line clipping that resolves into clean lettering in about a second. Closing reuses this staggered, stepped language with mirrored slice offsets, progressively dissolving text and advancing block masks, then fades out over roughly 960 ms while retaining focus trapping and blocking room input until dismissal completes. An 82%-opaque dark background, light backdrop dimming and subtle blur let the office remain visible behind the sheet. Visual duplicates are accessibility-hidden; close controls stay usable throughout. Reduced-motion preferences disable these effects and dismiss immediately. Portrait sizing adapts to available height; shorter screens scroll internally, with a sticky close header and reachable footer instead of clipped content.

Canonical `src/data/portfolio.json` supplies identity, About description, skill groups and records through the validated `src/data/portfolio.ts` facade. That facade attaches generated portrait paths/hashes from `assets/portrait/image-manifest.json`; authored portrait alt text stays in JSON. Python contact-card tooling reads the same JSON directly. Development records remain labelled as samples.

## Anchors

Floor X=-6…6, Y=-7…5, Z=0; inward +Y. Entrance `(0,-6.8,0)` and screen `(0.35,1.07,1.49)` are recorded in `office-manifest.json`. Source remains standalone; export aligns it with Level 01's cabin exit.
