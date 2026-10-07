# Development and deployment

Use Node.js **22.13+ in Node 22 LTS**, matching the CI major version. Both lockfiles currently contain the Three.js dependencies; CI uses **npm and `package-lock.json`**.

| Task | Command |
| --- | --- |
| Install the locked dependencies | `npm ci` |
| Develop | `npm run dev` |
| CI checks, in order | `npm run lint && npm run build` |
| Lint one changed component | `npx eslint src/components/CityWalkthrough.jsx` |
| Serve the production build | `npm run preview` |
| Validate room packages/alignment | `node assets/journey/verify_rooms.mjs` |
| Validate sound-effect lifecycle/races | `node scripts/verify_interaction_audio.mjs` |

There is no configured unit-test runner, formatter, or typecheck script. Blender/source validators are model-specific; see [integration workflow](../assets/journey/WORKFLOW.md) and the relevant model guide. Some Blender preview validators use synthetic events in background mode rather than a native GUI event loop.

## Vite and browser review

- Dev/preview are served under **`/damien-portfolio/`**. `import.meta.env.BASE_URL` must prefix public asset URLs for GitHub Pages.
- `vite.config.js` dedupes React, React DOM, and Three.js and prebundles both renderers. Preserve these settings when changing lazy loading or dependencies.
- Tailwind v4 uses `@tailwindcss/vite` and the CSS import. Unlayered custom selectors can override utility classes.
- `.city-stage` exposes requested/rendered frame and loading/room state. Verify gesture reversal and jumps, then enter each floor through the actual elevator controls.
- For interaction changes, test actual 3D clicks/taps plus accessible controls, Escape/focus return, reduced motion, and a portrait viewport. Loading changes also need delayed/failing assets, Retry, cancel/reselect, and cached returns.
- Animation changes need demand-render settling, pause/offscreen handling, held-key/pointer cleanup, and independent room look/movement.

Browser automation is not an npm script or declared Playwright dependency. Previous local smoke scripts/screenshots in `/tmp/opencode` are session artifacts, not repository tests; don't assume they exist in a fresh checkout.

## Deployment

`.github/workflows/deploy.yml` runs `npm ci`, lint, and build on Node 22, then deploys `dist/` to GitHub Pages on pushes to `main` or manual dispatch. Configure Pages to use **GitHub Actions**.

The workflow consumes checked-in generated model packages; it does not run Blender. Export and verify packages locally before deployment. The repository base URL is configured in Vite and must be reconciled when renaming the repository or using a custom domain.
