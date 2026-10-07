import { MathUtils } from 'three'

export function hallwayCategoryAt(navigation, y) {
  return [...(navigation?.categories || [])].reverse().find(category => y >= category.startY) || navigation?.categories?.[0]
}

export function hallwayMaxY(navigation) {
  return navigation?.maxY
}

export function clampHallwayY(navigation, value) {
  return MathUtils.clamp(value, navigation.minY, hallwayMaxY(navigation))
}
