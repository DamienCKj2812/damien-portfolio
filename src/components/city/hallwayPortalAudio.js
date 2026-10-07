// Track stable sides of authored portal planes. The small dead band prevents
// hovering/micro-movement on the threshold from repeatedly starting the effect.
export function createHallwayPortalAudio(navigation, tolerance = .3) {
  const portals = (navigation?.categories || []).filter(category => category.door).map(category => ({ id: category.id, y: category.door.y }))
  const sides = new Map()
  let previousY
  const side = (y, plane) => y < plane - tolerance ? -1 : y > plane + tolerance ? 1 : 0
  function reset(y) {
    sides.clear()
    previousY = Number.isFinite(y) ? y : undefined
    if (previousY !== undefined) for (const portal of portals) sides.set(portal.id, side(y, portal.y))
  }
  function update(y, active = true) {
    if (!Number.isFinite(y)) { reset();return [] }
    if (!active || previousY === undefined) { reset(y);return [] }
    const direction = y >= previousY ? 1 : -1
    const crossed = []
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
