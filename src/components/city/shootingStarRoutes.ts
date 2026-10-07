import { MathUtils } from 'three'
import type { Vec3 } from '../../types/scene'
import type { ShootingStarSample } from '../../types/navigation'

export interface ShootingStarRoute {
  id: string; start: Vec3; end: Vec3; duration: number; period: number; delay: number; trail: number; width: number
}

// Fixed Blender Z-up routes in the open sky above the city, independent of the
// camera/scroll timeline. Separate periods and delays keep the sky intermittent.
export const shootingStarRoutes: ShootingStarRoute[] = [
  { id: '01', start: [-35, -8, 110], end: [48, 5, 55], duration: 1.55, period: 11, delay: .30, trail: 7, width: .055 },
  { id: '02', start: [36, 12, 115], end: [-32, -4, 68], duration: 1.85, period: 14, delay: 4.60, trail: 9, width: .065 },
  { id: '03', start: [-10, -14, 96], end: [18, -2, 72], duration: 1.20, period: 17, delay: 8.20, trail: 5, width: .045 },
]

export function sampleShootingStar(route: ShootingStarRoute, seconds: number, result: Partial<ShootingStarSample> = {}): ShootingStarSample {
  const age = MathUtils.euclideanModulo(seconds - route.delay, route.period)
  const progress = Math.min(1, age / route.duration)
  result.active = age < route.duration
  result.progress = progress
  result.opacity = result.active ? MathUtils.smoothstep(progress, 0, .10) * (1 - MathUtils.smoothstep(progress, .70, 1)) : 0
  return result as ShootingStarSample
}
