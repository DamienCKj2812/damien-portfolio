import { MathUtils } from 'three'
import type { AxisNavigation, HallwayCategory } from '../../types/scene'

export function hallwayCategoryAt(navigation: { categories?: HallwayCategory[] } | null | undefined, y: number) {
  return [...(navigation?.categories || [])].reverse().find(category => y >= category.startY) || navigation?.categories?.[0]
}

export function hallwayMaxY(navigation: Pick<AxisNavigation, 'maxY'>): number
export function hallwayMaxY(navigation: Pick<AxisNavigation, 'maxY'> | null | undefined): number | undefined
export function hallwayMaxY(navigation: Pick<AxisNavigation, 'maxY'> | null | undefined) {
  return navigation?.maxY
}

export function clampHallwayY(navigation: Pick<AxisNavigation, 'minY' | 'maxY'>, value: number) {
  return MathUtils.clamp(value, navigation.minY, hallwayMaxY(navigation))
}
