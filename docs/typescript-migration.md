# TypeScript migration plan

## Baseline and scope

**Status: implemented and verified on 7 October 2026.**

All 61 original application modules are now `.ts` / `.tsx`, and all 31 original
Node tools are `.mts`. The canonical profile is `src/data/portfolio.json`, with a
validated `portfolio.ts` facade. TypeScript 6.0.3, typed ESLint, `tsx`, and
Playwright 1.61.1 are declared and locked. CI runs lint, strict typecheck, build,
and 19 non-browser checks; nine browser checks are available locally.

Application checking also enables `noUncheckedIndexedAccess` and
`exactOptionalPropertyTypes`, with dependency declaration checks retained.
Declaration-only patches resolve compatibility issues in `three-stdlib` and
`@types/three`; runtime package code is untouched. An independent review found
and fixed legacy stride-12 lobby classification and invalid shared loop periods;
the room verifier now covers both regressions.

Catalogue content/provenance was regenerated through the existing tools. Only
this portfolio's TypeScript/source references changed in Projects. The authored
hallway master, geometry, animation and all other model packages remained
byte-identical. The baseline audit and staged sequence below are retained as a
record of the migration decisions, rather than current filename instructions.

### Final implementation verification

```sh
npm ci
npm run lint
npm run typecheck
npm run build
npm run verify
npm run verify:browser
VIDEO_TEST_DEV=1 node --import tsx scripts/verify_project_video_browser.mts
npm run assets:check -- --dist
pnpm install --lockfile-only --ignore-scripts --frozen-lockfile
```

All commands passed. The clean install applied both declaration patches; the
dependency tree has coherent React/Three/Node types. The 19 non-browser checks
include current and legacy manifest validation, native motion, public-link/NDA
policy, canonical content provenance, responsive focus, audio lifecycle and BVH
equivalence. All nine browser checks passed against the final production build,
and the extra video run passed in Vite development/StrictMode. The Python contact
reader also passed against the canonical JSON with all seven printed lines.

The final BVH check retained the acceleration: 40 identical queries took about
270 ms with detailed scans versus 6.6 ms indexed. The existing Vite large-chunk
notice remains a baseline build advisory, not a failed check.

Two pre-existing verifier assumptions were corrected against the committed
baseline: lobby autonomous channels now distinguish people/accessories/fish,
and the hallway ceiling envelope follows the authored width. Their substantive
motion, loop, rib, light-clearance and geometry checks remain enforced.

Audited on 7 October 2026 against baseline commit **`caa19ef` — `feat: establish immersive portfolio baseline`**. The working tree was clean before adding this plan.

The tracked migration inventory is:

| Area | Current files | Intended treatment |
| --- | --- | --- |
| Application `src/` | 25 `.js`, 36 `.jsx` | Convert incrementally to `.ts` / `.tsx`, including unmounted components. |
| `scripts/` | 24 `.mjs` | Keep executable while application helpers change; type tooling in the final phase. |
| `assets/` Node tooling | 7 `.mjs` | Same execution strategy, preserving model-local entrypoints. |
| Vite / ESLint configuration | 2 root `.js` files | Type Vite configuration; ESLint's executable flat configuration can remain JavaScript. |
| Asset authoring | 153 `.py` files | Preserve Python/Blender ownership; adapt shared-data readers where necessary. |

The migration should retain the current experience: one demand-rendered Canvas, four floors (`about`, `skills`, `projects`, `experience`), stable model IDs, reversible camera handoffs, responsive card focus, click-only effects, and exclusive video playback. Keep migration changes separate from redesigns, dependency upgrades unrelated to typing, and model rebuilds.

## Audit findings

### 1. Shared profile data is also a build interface

`src/data/portfolio.js` is not only a React import:

- `scripts/build_skills_catalogue.mjs` extracts its declaration, evaluates it with `vm.runInNewContext`, substitutes an empty portrait manifest, and hashes the source text.
- `assets/timeline-observatory/build_timeline_content.mjs` rewrites the import/export text and evaluates the result in a VM.
- `assets/about-office/contact_card_content.py` reads the file and extracts contact literals with regular expressions.
- `scripts/verify_skills_content.mjs` checks the exact profile-source hash.
- `scripts/verify_media_assets.mjs` checks a JavaScript source substring for the music path.

Renaming this file or adding type annotations would break those contracts. Address the data interface before converting it.

**Recommended replacement:** a canonical plain-data `src/data/portfolio.json`, plus a typed `portfolio.ts` facade that combines that content with the generated portrait manifest. Node and Python read the JSON directly. Keep computed portrait URLs/hashes in the facade, not duplicated in authored JSON. Validate the JSON shape at the shared-data boundary and compare the resolved profile with the old profile before removing the old declaration.

Change generator input paths, provenance/hash checks, media checks, and source-location documentation together. Hash the canonical JSON bytes for content provenance; changing a TypeScript annotation should not make Skills content stale. Preserve approved wording and IDs. Source-path/hash metadata changes are expected; content changes are not.

### 2. Node verifiers import application modules directly

Room, focus, public-link, audio, and BVH verifiers import `src/**/*.js`. Asset-local NPC/fish/ceiling checks do this too. Browser automation also consumes Vite configuration and generated scene manifests.

Node 22.13+ is the documented minimum. Do not depend on newer Node releases' automatic TypeScript stripping or on Vite transpilation for Node scripts. Introduce a declared `tsx` runner before migrating a directly imported helper, and update its consumers/commands in the same change.

Browser-only modules using `import.meta.env.BASE_URL` must remain out of Node verifier import graphs. Load shared plain data directly rather than importing the browser media registry.

### 3. Type tooling is absent, and the local install is not a clean npm tree

- No TypeScript compiler, `tsconfig`, or typecheck script is configured.
- ESLint currently targets `.js` / `.jsx` with browser globals; `.mjs` tooling does not have an explicit Node lint scope.
- React/Three types are present transitively, but must become deliberate development dependencies.
- `npm ls` reports extraneous/invalid type-package entries in a local tree containing pnpm paths. Existing application checks nevertheless pass. A clean npm installation must establish reproducibility before any dependency changes.
- CI uses Node 22, `npm ci`, lint, and Vite build. It consumes checked-in model packages and does not run Blender.

Registry metadata checked during this audit:

| Package | Observed version / compatibility | Decision for the first migration phase |
| --- | --- | --- |
| `typescript` | Latest `7.0.2`; `6.0.3` also published | Start with `6.0.3`, subject to installation/typecheck verification. |
| `typescript-eslint` | `8.71.1`; ESLint `^8.57.0 \|\| ^9.0.0 \|\| ^10.0.0`; TypeScript `>=4.8.4 <6.1.0` | Compatible peer range with current ESLint 10 and TS 6.0, not TS 7. |
| `tsx` | `4.23.15`; Node `>=18` | Suitable for the documented Node 22.13+ minimum. |

These are peer-metadata checks, not proof that the complete typed application already compiles. Recheck and lock compatible versions during implementation. Preserve current React 19 / Three 0.186 / Fiber / Drei versions while introducing typing.

### 4. Generated manifests need explicit runtime contracts

`cityAssets.js` currently checks versions, group kinds, buffer sizes, morph ranges, route length, and texture load failures. Scene JSON contains different city/lobby/elevator/room shapes, and animation channel strides differ (10, 12, 16). Geometry descriptors carry their own strides; route XYZ data is separate.

Treat fetched JSON as `unknown`, validate it once at load time, and then expose typed assets. A cast such as `response.json() as SceneManifest` is not validation. Preserve existing rejection/Retry behavior and cache-busting. Do not change offsets, byte layout, generated hashes, coordinate conversion, or per-frame algorithms to simplify types.

### 5. State and resource ownership are the high-risk application areas

- `CityWalkthrough.jsx`: nullable async load state, partial room caches, elevator status/level, profile/detail views, and modal-derived paused state.
- `RoomNavigator.jsx`: a navigation object initialized with a few fields and subsequently extended with routes, springs, positions, camera/focus flags, and return state.
- `CityScene.jsx` / `ReflectiveFloor.jsx`: geometry/material ownership, camera selection, renderer state restoration, and resource disposal.
- `ProjectVideoBoards.jsx` / `ProjectVideoBoard.jsx`: player registry, preview/full handoff, decoded VideoTexture creation, timers/frame callbacks, audio focus, and StrictMode replay.
- Audio modules: nullable contexts, injected test doubles, trusted gestures, optional browser APIs, finite door timers, and cleanup races.

Types should describe these lifecycles without adding render-state updates or allocations to existing frame loops.

### 6. BVH declarations contain a specific gap

The installed `three-mesh-bvh@0.8.3` provides `src/index.d.ts` and already augments Three's `BufferGeometry.boundsTree` and `Raycaster.firstHitOnly`. Its `MeshBVHOptions` declaration omits the supported runtime `indirect` option used by this application.

Check declaration resolution for the intentional ESM import `three-mesh-bvh/src/index.js`. If needed, add a narrow `MeshBVHOptions` augmentation for `indirect?: boolean`, importing the real package declarations. Do not replace the package with an untyped ambient module, duplicate its existing Three augmentations, or switch back to a CJS runtime import just to satisfy the compiler. Keep indirect storage, unchanged authored buffers, and StrictMode-safe CPU cache retention.

## Toolchain and execution strategy

### Compiler configuration

Introduce separate application and tooling checks, with a root configuration coordinating their commands:

- **Application:** `module: ESNext`, `moduleResolution: Bundler`, `jsx: react-jsx`, `lib: [ES2022, DOM, DOM.Iterable]`, Vite client types, `resolveJsonModule`, `strict`, `noEmit`, `isolatedModules`, `verbatimModuleSyntax`, and `erasableSyntaxOnly`.
- **Transition:** `allowJs: true`, `checkJs: false`, so converted files are checked while remaining JS is migrated in bounded batches. This does not certify unconverted JS; track the inventory explicitly.
- **Tooling:** explicit Node types and a separate include list for Vite configuration and converted tooling. Use the same bundler-style resolution where scripts are executed through `tsx`, not emitted for bare Node. Verifiers that transitively import browser-typed application modules need the relevant DOM/JSX types; keep Node/browser lint globals separately scoped. Do not assume a DOM-free Node config will check those imports unchanged.
- Use `import type` for erased dependencies. Prefer string unions to TypeScript enums and ordinary fields to parameter properties.
- Start with dependency declaration checking enabled; document and narrowly address third-party issues before considering `skipLibCheck`. Do not hide errors in application declarations.
- Add `noUncheckedIndexedAccess` and `exactOptionalPropertyTypes` in a separate hardening pass after strict conversion is green. Binary-index guards belong at parsing/validated helper boundaries, not new checks or allocations on every animation frame.

Declare `@types/react`, `@types/react-dom`, `@types/three`, and `@types/node` explicitly with compatible React/Three releases and Node 22 APIs. Ensure React/Fiber/Three resolve a single coherent type identity; preserve Vite's existing runtime dedupe and prebundling.

Vite continues to build browser code. Add `npm run typecheck` independently, and put it before `npm run build` in CI. A Vite build alone does not check TypeScript types.

### Imports and script execution

- Use extensionless relative imports for browser application modules under Vite/TypeScript bundler resolution; retain explicit JSON, CSS, URL assets and Three addon/package paths.
- For Node verifiers importing migrated helpers, use explicit `.ts` module paths and `node --import tsx <existing-script.mjs>` during transition. Enable TypeScript-extension imports in the no-emit tooling check where required.
- Document a grouped npm verification entrypoint so users do not need to remember which verifiers require the runner. Update documented commands as helper imports migrate, including scoped asset guides.
- Convert Node tooling to `.mts` only after the application is stable; continue executing it through the declared runner. Update command paths, CI/documentation, and `import.meta.url`-relative asset paths together.
- Keep `predev`, `prebuild`, and media synchronization functioning throughout. Do not require Blender for npm install, dev, build, or deploy.
- Treat npm / `package-lock.json` as the CI authority. Resolve support for the existing pnpm lockfile before modifying dependencies: synchronize it if retained, or make its retirement an explicit maintenance decision. Do not leave two silently divergent dependency graphs.

### ESLint

Add TypeScript flat-config support compatible with ESLint 10. Keep React Hooks and Refresh checks for application components. Replace core `no-unused-vars` with its TypeScript-aware equivalent only in TS scopes; do not apply React Refresh to generators or verification scripts.

Introduce an explicit Node scope for converted tooling. Audit the impact of newly linting existing `.mjs` files separately, rather than mixing a repository-wide lint cleanup into the first component conversion. Introduce type-aware lint rules after the compiler/config boundaries are stable.

## Type boundaries

Use small colocated contracts or a focused `src/types/` directory. Avoid a single catch-all type file and avoid annotating every local value when inference is sufficient.

| Boundary | Types / constraints to establish |
| --- | --- |
| Shared content | `PortfolioContent`, resolved `Portfolio`, contact links, music track, skill groups, education/experience records, portrait metadata, typed media keys. Preserve optional fields and sample labels. |
| Journey configuration | `LevelId`, room destinations, frame ranges/bookmarks, handoff/alignment configuration. A room cache is partial, not a complete record of loaded floors. |
| Scene manifests | Common animation/buffer contract plus city, lobby, elevator and level-specific manifests; geometry kind union; actor/morph/texture descriptors; camera records; explicit optional versioned fields. |
| Navigation | `look`, `axis`, and `guided` descriptors; route/station metadata; mutable navigation ref and spring state. Retain pre-mount/cleanup absence where fields are genuinely not available. |
| Loaded assets | Typed `ArrayBuffer`, `Float32Array`, prepared route, texture lookup and geometry descriptors. Distinguish authored tuples from Three objects and preserve mutability where required. |
| Application state | Typed async result/error and elevator status; nullable floor selection; room view union; saved return snapshots. Narrow a manifest by room/view before accessing project, skill or timeline fields. |
| Exhibits | Shared sections/links/card axes plus project/video, skill/evidence, and timeline variants. Preserve NDA-limited and source-restricted variants; do not assume fixed section counts. |
| React and DOM | Concrete nullable element/resource refs, component props, `ReactNode` children, typed error boundaries, React events versus native events, and guarded `EventTarget` narrowing. |
| Three/Fiber | Camera narrowing where perspective-only methods are used; renderer/material/geometry refs; shader uniforms; `ThreeEvent` picks. Respect React 19 ref typing and Fiber's JSX declarations. |
| Browser compatibility | Narrow optional capabilities for autoplay-policy detection and legacy Web Audio only where lib.dom lacks them; feature-detect before use. Check existing video-frame callback types before adding declarations. |
| Audio and media | Engine/context interface, effect-kind union, injected environment/test contracts, timer return types, player controller registry and cleanup callbacks. Avoid importing Node timer types into browser code. |

Keep IDs driven by actual catalogue/configuration data. Do not reinterpret string-based section headings as a fixed ten-section enum: restricted projects and timeline entries legitimately have different sections.

Use `unknown` for external JSON, stored settings, and caught errors, then narrow or normalize at boundaries. Avoid blanket `any`, `as unknown as`, permissive ambient module stubs, or mass non-null assertions. When strict typing reveals a real bug, fix it in a small independently verified change.

## Migration phases

Each phase must leave a runnable, verified application. Make reviewable checkpoints; do not bulk-rename the whole tree before resolving the first compiler errors.

### Phase 0 — Reproducible baseline

1. Establish a clean `npm ci` installation from the locked baseline; reconcile the local mixed package-manager state without changing application versions.
2. Record lint/build, generated package/content, focus/audio, and video browser results.
3. Record production output and representative demand-render/BVH behavior for comparison. Treat chunk-size notices as the existing baseline, not a migration target.

**Exit:** baseline reproducible under npm and documented Node 22.13+; no unresolved application regressions attributed to migration.

### Phase 1 — Type toolchain, without mass conversion

1. Add compatible compiler/linter/runner/type dependencies and lockfile updates.
2. Add application/tooling configurations, Vite client declarations, a typecheck command, and the CI typecheck step.
3. Convert Vite configuration, preserving the base, plugins, React/Three dedupe and optimizeDeps exactly.
4. Prove lint, typecheck, build, and a verifier executed with the runner work together.

**Exit:** mixed JS/TS tooling is green and the existing app still runs. Unconverted JS is explicitly tracked.

### Phase 2 — Canonical data and manifest contracts

1. Move static profile content to JSON and replace VM/regex/source-substring readers with structured reads. Keep the existing JS facade until the new data path is verified, then convert the facade.
2. Update Skills source hashing and timeline/contact/media readers atomically; compare generated output semantically before accepting provenance-only differences. Update source-location guidance.
3. Type media/public-link helpers and establish validated journey/manifest/loaded-asset contracts. Validate at fetch boundaries, preserving existing loader behavior.
4. Resolve the BVH declaration gap narrowly, without changing BVH runtime behavior.

**Exit:** profile/contact/Skills/timeline content and public-link/NDA checks match the baseline. Ordinary type edits require no model rebuild. If an actual browser package change is necessary, regenerate related outputs together through the existing read-only exporter and run the scoped source/package checks.

### Phase 3 — Pure helpers and shared navigation contracts

Convert small helpers first: `cameraMotion`, `elevatorTiming`, `roomProgress`, `hallwayCategories`, `shootingStarRoutes`, then `journeyTimeline`, `roomJourney`, `linearRoomRoute`, `cityActorMotion`, `projectCardFocus`, `lobbyPortal`, and `videoOcclusion`.

Introduce the navigation ref contract from all writers/readers rather than only its initial object. Update importing verifiers to the runner alongside each rename. Preserve tuple order, shader/geometry buffers, coordinate transforms, interpolation and mutable scratch objects.

**Exit:** package/alignment, responsive focus, category/directory, portal and exact BVH-equivalence checks pass; accelerated behavior and geometry order remain intact.

### Phase 4 — Audio and DOM interface

Type the audio engines/context/hooks and components, then dialogs, topline/guide, profile/portrait, detail panels, sidebars, elevator controls, progress controls, and other DOM-focused components. Preserve existing settings, gesture activation, focus containment/restoration and input ownership.

**Exit:** audio lifecycle/race checks and browser interaction checks pass. Escape, long-content scrolling, mobile layouts, reduced motion, and modal pause/resume work as before.

### Phase 5 — Scene, camera and media lifecycle

Convert asset-loading/geometry implementations and runtime hooks against the contracts established earlier. Migrate pick targets, shared entrance/return journey and reflectors, then `RoomNavigator`, `CityScene`, video board/player coordination and `CityWalkthrough` in bounded changes.

Give class error boundaries, lazy imports, refs and callbacks explicit contracts. Retain derived modal state and saved return state; do not rewrite the state machine or add a new Canvas/reducer solely for migration.

**Exit:** all four actual floor journeys work; delayed/failing loads, Retry, cancel/reselect, cached returns, reverse navigation and actual native picks remain correct. Full/preview video pixels, exclusivity, fixed walking FOV, audio focus and StrictMode resource replay pass. Hidden/paused/reduced-motion scenes settle without held input or idle loops.

### Phase 6 — Finish application and harden

Convert `App`, `main`, and any remaining leaf files as their dependencies become ready. Update `index.html`'s entry path with the `main.tsx` rename. Convert the currently unmounted `PortfolioSections`, `Section`, and `KeyboardViewer` without mounting or deleting them.

Remove transition allowances once `src/` has no `.js` / `.jsx`. Enable indexed/optional-property hardening in small checked batches. Review every suppression/declaration and ensure no converted file escapes the compiler include lists.

**Exit:** all 61 original application files have typed replacements; strict typecheck, lint and build pass without masking application errors.

### Phase 7 — Type Node tooling and finalize guidance

Convert the 31 Node generator/verifier files to `.mts` in groups: shared-data/media tooling, pure/source-package checks, then browser automation. Type Node buffers/filesystem data, browser-test callbacks and fixtures with honest interfaces. Preserve test assertions and generated-file paths; update tooling lint/typecheck scopes and commands as each group moves.

Make Playwright setup reproducible rather than relying on `/tmp/opencode`; document Chrome, Python/Pillow and video-test requirements. A declared browser-test dependency can remain development-only. Native Python/Blender files stay in their existing language.

Make browser verification screenshots configurable or temporary by default. The current directory verifier overwrites the tracked `assets/project-hallway/project-directory-zoom.png`; ordinary verification should not replace the approved reference image.

**Exit:** application and intended Node tooling are checked, all command paths are current, CI passes, and repository documentation describes the new data/toolchain boundaries. ESLint's JS configuration is an intentional executable configuration exception.

## Verification and completion criteria

### Baseline planning audit results (original command paths)

The following passed during this planning audit using the existing local install:

```sh
npm run lint && npm run build
node scripts/verify_media_assets.mjs
node scripts/verify_public_links.mjs
node scripts/verify_project_categories.mjs
node scripts/verify_project_card_focus.mjs
node scripts/verify_project_directory.mjs
node scripts/verify_skills_content.mjs
node scripts/verify_skills_focus.mjs
node scripts/verify_timeline_focus.mjs
node scripts/verify_spacious_hallway.mjs
node scripts/verify_project_video.mjs
node scripts/verify_video_occlusion.mjs
node scripts/verify_lobby_portal.mjs
node scripts/verify_contact_card_dismissal.mjs
node scripts/verify_interaction_audio.mjs
node scripts/verify_music_autoplay.mjs
node scripts/verify_category_portal_audio.mjs
node scripts/verify_door_audio.mjs
node assets/journey/verify_rooms.mjs
VIDEO_TEST_DEV=1 node scripts/verify_project_video_browser.mjs
```

Skills focus includes real browser picks, mobile framing, smooth focus, saved route/tour resume and idle cleanup. The video test checks actual rendered pixels for MyRumawip, MyReport and DWMLight, exclusive playback, fixed walking FOV, mobile/reduced motion and non-persistent audio focus.

The BVH verifier compared 40 identical detailed queries: approximately **265.6 ms standard versus 6.5 ms indexed**, with unchanged geometry and retained CPU cache. Timing is environment-dependent; correctness, shared cache and bounded active-frame work are the regression requirements.

These results do not replace Phase 0's clean-install check or future strict typechecking. Browser/native checks not listed above were not rerun during this audit. Existing production bundle-size and browser-test Pillow deprecation notices do not indicate a failed check.

The directory verifier's generated screenshot was restored to the committed reference after the audit; the resulting changes are this plan and its README link only.

### Gates during implementation

- Every application batch: focused lint, typecheck, build, and the existing checks for the affected behavior. Run room validation after browser-package changes.
- Shared focus/math contracts: project, directory, Skills and timeline checks together.
- Audio/input changes: lifecycle checks plus the existing browser consent, category-portal and door-audio checks as applicable.
- Scene/video changes: verify rendered pixels in production and development StrictMode; verify actual input, offscreen/hidden suspension and resource cleanup. Do not rely only on media `currentTime` or passing types.
- Native/package changes: read the relevant asset guides; use their export/source/alignment commands. Preserve authored masters, surrounding geometry, NPC visibility/actions, routes and model provenance.
- Release gate: clean install, strict application/tooling typecheck, lint/build, content/public-link checks, package/focus/audio/BVH suite and the four-floor/browser regression matrix.

The migration is complete only when the compiler includes all intended source files, the executable verification commands work from a fresh checkout, and visual/interaction/performance behavior matches the baseline. Conversion counts alone are not completion evidence.
