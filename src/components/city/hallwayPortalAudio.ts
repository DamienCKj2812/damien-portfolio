// Track stable sides of authored portal planes. The small dead band prevents
// hovering/micro-movement on the threshold from repeatedly starting the effect.
export function createHallwayPortalAudio(navigation?: PortalAudioNavigation | null, tolerance = .3) {
  const portals = (navigation?.categories || []).flatMap(category => category.door ? [{ id: category.id, y: category.door.y }] : [])
  const sides = new Map<string, -1 | 0 | 1>()
  let previousY: number | undefined
  const side = (y: number, plane: number): -1 | 0 | 1 => y < plane - tolerance ? -1 : y > plane + tolerance ? 1 : 0
  function reset(y?: number) {
    sides.clear()
    previousY = Number.isFinite(y) ? y : undefined
    if (previousY !== undefined) for (const portal of portals) sides.set(portal.id, side(previousY, portal.y))
  }
  function update(y: number, active = true): PortalCrossing[] {
    if (!Number.isFinite(y)) { reset();return [] }
    if (!active || previousY === undefined) { reset(y);return [] }
    const direction = y >= previousY ? 1 : -1
    const crossed: PortalCrossing[] = []
    for (const portal of portals) {
      const current = side(y, portal.y)
      const previous = sides.get(portal.id) || 0
      if (!current) continue
      if (previous && current !== previous) crossed.push({ ...portal, direction: current > 0 ? 'enter' : 'exit' })
      sides.set(portal.id, current)
    }
    previousY = y
    return crossed.sort((a, b) => direction * (a.y - b.y))
  }
  return { reset, update }
}
import type { PortalAudioNavigation, PortalCrossing } from '../../types/audio'
