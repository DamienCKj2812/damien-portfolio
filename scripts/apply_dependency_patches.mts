import { execFileSync, spawnSync } from 'node:child_process'
import { createRequire } from 'node:module'
import { dirname, relative, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = fileURLToPath(new URL('..', import.meta.url))
const require = createRequire(import.meta.url)
// pnpm resolves transitive dependencies beside their consumer, which can differ
// from the flat copy patch-package found after switching package managers.
const dreiRequire = createRequire(require.resolve('@react-three/drei'))
const packages = [
  { directory: dirname(dreiRequire.resolve('three-stdlib')), patch: 'three-stdlib+2.36.1.patch', strip: 3 },
  { directory: dirname(require.resolve('@types/three/package.json')), patch: '@types+three+0.186.0.patch', strip: 4 },
]

const pnpm = packages.some(({ directory }) => directory.includes('/node_modules/.pnpm/'))
if (!pnpm) execFileSync(process.execPath, [require.resolve('patch-package'), '--error-on-fail'], { cwd: root, stdio: 'inherit' })

for (const { directory, patch, strip } of pnpm ? packages : []) {
  const args = ['apply', `-p${strip}`, `--directory=${relative(root, directory)}`]
  const patchPath = resolve(root, 'patches', patch)
  const applied = spawnSync('git', [...args, '--reverse', '--check', patchPath], { cwd: root, encoding: 'utf8' })
  if (applied.status === 0) continue
  execFileSync('git', [...args, patchPath], { cwd: root, stdio: 'inherit' })
  console.log(`Applied declaration patch to pnpm dependency: ${patch}`)
}
