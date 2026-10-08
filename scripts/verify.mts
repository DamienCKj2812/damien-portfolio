import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

export const checks = [
  'scripts/verify_media_assets.mts',
  'scripts/verify_public_links.mts',
  'scripts/verify_cv.mts',
  'scripts/verify_skills_content.mts',
  'scripts/verify_project_categories.mts',
  'scripts/verify_spacious_hallway.mts',
  'scripts/verify_project_video.mts',
  'scripts/verify_project_card_focus.mts',
  'scripts/verify_timeline_focus.mts',
  'scripts/verify_video_occlusion.mts',
  'scripts/verify_lobby_portal.mts',
  'scripts/verify_contact_card_dismissal.mts',
  'scripts/verify_interaction_audio.mts',
  'scripts/verify_category_portal_audio.mts',
  'scripts/verify_door_audio.mts',
  'assets/journey/verify_rooms.mts',
  'assets/journey/verify_npc_motion.mts',
  'assets/kaze-lobby/verify_browser_npcs.mts',
  'assets/kaze-lobby/verify_fish_motion.mts',
  'assets/project-hallway/verify_browser_ceiling.mts',
] as const

const root = fileURLToPath(new URL('..', import.meta.url))
const failures: string[] = []
for (const script of checks) {
  console.log(`\nVERIFY ${script}`)
  const result = spawnSync(process.execPath, ['--import', 'tsx', script], { cwd: root, stdio: 'inherit', env: process.env })
  if (result.error) console.error(result.error)
  if (result.error || result.status !== 0) failures.push(script)
}
if (failures.length) {
  console.error(`\nFailed ${failures.length}/${checks.length} checks:\n${failures.join('\n')}`)
  process.exitCode = 1
} else console.log(`\nPASS all ${checks.length} non-browser checks`)
