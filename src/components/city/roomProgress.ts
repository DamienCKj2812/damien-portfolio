import type { RoomNavigation } from '../../types/scene'
import type { RoomProgress } from '../../types/navigation'

// Walking progress follows the camera route, independently of exhibit animation.
export function getRoomProgress(navigation: RoomNavigation | null | undefined, y: number, walkFrame: number | null | undefined): RoomProgress | null {
  const guided = navigation?.type === 'guided'
  if (!guided && navigation?.type !== 'axis') return null
  const min = guided ? navigation.route?.frameStart : navigation.minY
  const max = guided ? navigation.route?.frameEnd : navigation.maxY
  if (!Number.isFinite(min) || !Number.isFinite(max) || max <= min) return null
  const position = guided ? walkFrame : y
  const value = Math.max(min, Math.min(max, Number.isFinite(position) ? position! : min))
  return { min, max, value, percent: (value - min) / (max - min) * 100 }
}

export function updateRoomProgress(input: HTMLInputElement | null | undefined, progress: RoomProgress | null | undefined, label: string | undefined) {
  if (!input || !progress) return
  // Preserve the user's thumb position while dragging or using arrow keys.
  if (document.activeElement !== input) input.value = String(progress.value)
  input.setAttribute('aria-valuetext', `${Math.round(progress.percent)}% · ${label}`)
  input.style.setProperty('--timeline-progress', `${progress.percent}%`)
}
