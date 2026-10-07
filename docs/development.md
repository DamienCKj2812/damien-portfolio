# Development and deployment

Use Node.js **22.13+ in Node 22 LTS**, matching the CI major version. Both npm and pnpm lockfiles are maintained; CI uses **npm and `package-lock.json`** as the authority for reproducible installation.

| Task | Command |
| --- | --- |
| Install the locked dependencies | `npm ci` |
| Develop | `npm run dev` |
| CI checks, in order | `npm run lint && npm run typecheck && npm run build && npm run verify` |
| Lint one changed component | `npx eslint src/components/CityWalkthrough.tsx` |
| Check app and Node tool types | `npm run typecheck` |
| Run 19 non-browser checks | `npm run verify` |
| Run nine actual-browser checks after build | `npm run verify:browser` |
| Serve the production build | `npm run preview` |
| Validate room packages/alignment | `node --import tsx assets/journey/verify_rooms.mts` |
| Validate sound-effect lifecycle/races | `node --import tsx scripts/verify_interaction_audio.mts` |

There is no configured unit-test runner or formatter. Blender/source validators are model-specific; see [integration workflow](../assets/journey/WORKFLOW.md) and the relevant model guide. Some Blender preview validators use synthetic events in background mode rather than a native GUI event loop.

## TypeScript and shared data

All 61 original application modules are now TS/TSX, including unmounted components, alongside shared type modules. The 31 existing Node tools are MTS, alongside `scripts/verify.mts`, `scripts/verify_browser.mts`, `scripts/node_json.mts` and `scripts/browser_tools.mts`. Run individual tools from the repository root with `node --import tsx <path>.mts`; the declared runner supports the Node 22.13 minimum without relying on newer Node versions' automatic type stripping.

`npm run typecheck` uses TypeScript **6.0.3** for both `tsconfig.app.json` and `tsconfig.node.json`. The shared configuration is strict, no-emit and keeps `skipLibCheck: false`; the application also enables `noUncheckedIndexedAccess` and `exactOptionalPropertyTypes`. Vite builds separately and does not replace compiler checks. ESLint uses TypeScript-aware rules for browser TS/TSX and a separate Node scope for MTS tooling/Vite config, retaining React Hooks/Refresh checks for app components. Keep application source free of JS/JSX.

Installation runs `scripts/apply_dependency_patches.mts` via `postinstall`: npm uses `patch-package --error-on-fail`, while pnpm applies the same checked-in patches to the packages resolved by the application, including Drei's nested `three-stdlib` dependency. The patches for `three-stdlib@2.36.1` and `@types/three@0.186.0` fix SVG `userData`, TGA parser returns, and exact optional-property compatibility in line materials/motion-controller declarations. They change no runtime code; preserve them rather than disabling dependency declaration checks. Keep the same package manager for installation and the running dev session. After changing the dependency layout, restart Vite so hot reload does not reference removed package paths.

Edit profile/Observer/contact/music copy in canonical `src/data/portfolio.json`. The typed `src/data/portfolio.ts` facade validates it and attaches generated portrait URLs/hashes. Node generators use the shared JSON reader and Python contact tooling reads JSON directly, replacing VM evaluation and regex extraction of application declarations. Profile provenance hashes the canonical JSON bytes, so TypeScript-only edits do not invalidate Skills content.

## Vite and browser review

- Dev/preview are served under **`/damien-portfolio/`**. `import.meta.env.BASE_URL` must prefix public asset URLs for GitHub Pages.
- `vite.config.ts` dedupes React, React DOM, and Three.js and prebundles both renderers. Preserve these settings when changing lazy loading or dependencies.
- Tailwind v4 uses `@tailwindcss/vite` and the CSS import. Unlayered custom selectors can override utility classes.
- `.city-stage` exposes requested/rendered frame and loading/room state. Verify gesture reversal and jumps, then enter each floor through the actual elevator controls.
- For interaction changes, test actual 3D clicks/taps plus accessible controls, Escape/focus return, reduced motion, and a portrait viewport. Loading changes also need delayed/failing assets, Retry, cancel/reselect, and cached returns.
- Animation changes need demand-render settling, pause/offscreen handling, held-key/pointer cleanup, and independent room look/movement.

Playwright **1.61.1** is a declared, locked development dependency installed by `npm ci`; no separate `/tmp` installation is needed. `npm run verify:browser` runs nine browser checks sequentially after a current production build. Chrome defaults to `/usr/bin/google-chrome`; set `CHROME_EXECUTABLE` for another compatible executable. `PLAYWRIGHT_MODULE` remains an optional external-module override. Screenshots go to a fresh system temporary directory unless `VERIFY_OUTPUT_DIR` selects an output directory; the helper reports the path.

The video browser check needs `python3` with Pillow for rendered-pixel scoring and available project video/poster assets. Run `VIDEO_TEST_DEV=1 node --import tsx scripts/verify_project_video_browser.mts` to cover Vite development/StrictMode effect replay. Audio and Skills preview checks support `VITE_TEST_OUT_DIR` for an isolated build. Previous local smoke artifacts are not prerequisites for these checked-in verifiers.

Project video uploads are organized in `assets/project-hallway/videos/originals/<project>/` and remain local/Git-ignored. Browser-ready recordings, compatibility copies and posters are tracked in `public/videos/` and copied into `dist/videos/` by Vite. See [project video ownership](../assets/project-hallway/videos/README.md); builds do not require the original uploads or video transcoding.

`scripts/browser_tools.mts` centralizes SDK/Chrome/output selection and browser instrumentation. Use `installBrowserHelpers` when serializing instrumented callbacks: it installs the `__name` helper introduced by `tsx` in the same init script, avoiding missing module scope and unordered init-script execution.

## Deployment

`.github/workflows/deploy.yml` runs `npm ci`, lint, typecheck, build and the 19 non-browser checks on Node 22, then deploys `dist/` to GitHub Pages on pushes to `main` or manual dispatch. Configure Pages to use **GitHub Actions**.

The workflow consumes checked-in generated model packages; Blender and browser automation are local checks rather than CI jobs. Export and verify packages locally before deployment. The repository base URL is configured in Vite and must be reconciled when renaming the repository or using a custom domain.
