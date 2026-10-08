import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

// Optional: run after a production build (or VIDEO_TEST_DEV=1 for the video check).
export const checks = [
  'scripts/verify_portfolio_modes.mts',
  'scripts/verify_skills_focus.mts',
  'scripts/verify_project_directory.mts',
  'scripts/verify_project_detail_v2.mts',
  'scripts/verify_project_video_browser.mts',
  'scripts/verify_audio_consent.mts',
  'scripts/verify_music_autoplay.mts',
  'scripts/verify_door_audio_browser.mts',
  'scripts/verify_category_portal_audio_browser.mts',
  'assets/journey/verify_city_entrance.mts',
] as const

const root = fileURLToPath(new URL('..', import.meta.url))
const failures: string[] = []
for (const script of checks) {
  console.log(`\nVERIFY BROWSER ${script}`)
  const result = spawnSync(process.execPath, ['--import', 'tsx', script], { cwd: root, stdio: 'inherit', env: process.env })
  if (result.error) console.error(result.error)
  if (result.error || result.status !== 0) failures.push(script)
}
if (failures.length) {
  console.error(`\nFailed ${failures.length}/${checks.length} browser checks:\n${failures.join('\n')}`)
  process.exitCode = 1
} else console.log(`\nPASS all ${checks.length} browser checks`)
