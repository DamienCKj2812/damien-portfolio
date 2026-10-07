# Repository guidance

## Commands
- Use Node 22 LTS, version 22.13+. CI uses npm: `npm ci`, then `npm run lint && npm run build`; deployment consumes `dist/` and does not run Blender.
- Focused lint: `npx eslint src/components/CityWalkthrough.jsx` (replace with changed JS/JSX paths). There is no configured unit-test runner or typecheck script.
- After browser-package changes, run `node assets/journey/verify_rooms.mjs`; source/export checks and model-specific commands are in the scoped asset guides.
- Dev and preview use `/damien-portfolio/`. Public URLs must use `import.meta.env.BASE_URL`; preserve Vite's React/React DOM/Three dedupe and prebundling settings.

## App boundaries
- `src/main.jsx` uses StrictMode; `src/App.jsx` mounts the lazy full-viewport `CityWalkthrough` and persistent `BackgroundMusic` controls. `PortfolioSections.jsx`, `Section.jsx`, and `KeyboardViewer.jsx` are not mounted.
- Portfolio/Observer/contact text belongs in `src/data/portfolio.js`; project and observatory exhibit content has separate JSON sources in its model directory.
- Amplifii / AMPLYFII (Ampress) is NDA-covered. Publish only its general influencer-marketing purpose, unreleased status and broad product-development/teamwork contribution. Do not add specifications, implementation details, detailed features, source references or project-specific technical skills evidence. Keep catalogue, timeline, native card text and browser exports aligned; `node scripts/verify_public_links.mjs` checks this boundary.
- The document does not scroll. `useScrollTimeline.js` maps viewport-local gestures to a reversible journey and yields input during departure/room visits.
- Keep the shared Canvas demand-rendered with capped DPR. Animate only active/visible areas, invalidate while changing, and settle when idle; see [runtime guidance](src/components/city/AGENTS.md).
- Tailwind v4 coexists with unlayered custom CSS. Check `src/index.css` and `city/city.css` when utilities appear ineffective.
- Interaction audio is click-only; hover/focus are silent. DOM controls default to `system-click.mp3` via `SoundEffectsProvider`; environment labels/accessibility controls use `data-sound-effect="environment"`. Native environment picks use `useSoundEffects().environmentClick()`, with room scene clicks centralized after the drag guard; system shortcuts use `click()`. Avoid double-playing, keep disabled/drag/continuous movement silent, and preserve gesture unlocking, saved effects mute/volume and cleanup. See [sound-effect convention](docs/sound-effects.md); check with `node scripts/verify_interaction_audio.mjs`.

## Model ownership
- `assets/*/AGENTS.md` contains scoped instructions beside each model. Read [asset rules](assets/AGENTS.md) and the affected model's guide before modifying Blender files or generated exports.
- Authored masters, integration copies, and browser packages are different outputs. Routing is defined by `assets/journey/room-destinations.json`; loading/alignment metadata is generated in `public/models/journey.json`.
- Do not hand-edit binary offsets, strides, or hashes in generated packages. Regenerate related files together; standard GLB export does not preserve the point/line representation.
- Keep model redesigns scoped: preserve previously completed surroundings, NPC visibility/actions and journey connections unless their replacement is explicitly requested. In the city, tower rebuilds must retain the detailed orbital sky, 18 outdoor NPCs, geographic Earth hologram and sealed working entrance; ownership and regression commands are in `assets/cyber-city/AGENTS.md` and `assets/journey/AGENTS.md`.
- Human-facing documentation is indexed by [README.md](README.md): [development](docs/development.md), [architecture](docs/architecture.md), and [planned features](docs/roadmap.md).
