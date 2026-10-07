import type { ExhibitMetadata, LoadedSceneAssets, SceneManifest } from '../../types/scene'
import { packedNumber } from '../../types/packedNumbers'

// Reparameterize guided room paths by distance, removing inspection holds while
// keeping their paths, look directions, loop/end behavior, and coupled clocks.
export function prepareLinearRoomRoute<M extends SceneManifest>(assets: LoadedSceneAssets<M>): LoadedSceneAssets<M>
export function prepareLinearRoomRoute(assets: LoadedSceneAssets): LoadedSceneAssets {
  if (!(assets.manifest.level === 'skills' || assets.manifest.level === 'experience') || !assets.route) return assets
  const descriptor = assets.manifest.navigation.route
  const count = descriptor.frameEnd - descriptor.frameStart + 1
  const stride = descriptor.stride
  const distances = new Float64Array(count)
  // Loading validates an integer route count >= 2 and count * XYZ stride
  // floats. This loop visits adjacent in-range vertices and distance slots.
  for (let index = 1; index < count; index++) {
    const a = (index - 1) * stride, b = index * stride
    distances[index] = packedNumber(distances, index - 1) + Math.hypot(packedNumber(assets.route, b) - packedNumber(assets.route, a), packedNumber(assets.route, b + 1) - packedNumber(assets.route, a + 1), packedNumber(assets.route, b + 2) - packedNumber(assets.route, a + 2))
  }
  const total = packedNumber(distances, count - 1)
  if (total <= 0) throw new Error('The guided walking path has no travel distance.')
  const steps = descriptor.loop ? count : count - 1
  const route = new Float32Array(count * stride)
  let segment = 1
  // segment remains in [1, count - 1], so both endpoints and all stride axes
  // below are in the validated input buffer and newly allocated distance array.
  for (let index = 0; index < count; index++) {
    const distance = total * index / steps
    while (segment < count - 1 && packedNumber(distances, segment) <= distance) segment++
    const before = packedNumber(distances, segment - 1), span = packedNumber(distances, segment) - before
    const blend = span > 0 ? (distance - before) / span : 0
    const a = (segment - 1) * stride, b = segment * stride
    for (let axis = 0; axis < stride; axis++) route[index * stride + axis] = packedNumber(assets.route, a + axis) + (packedNumber(assets.route, b + axis) - packedNumber(assets.route, a + axis)) * blend
  }
  const remap = (item: ExhibitMetadata) => {
    // Native station/exhibit starts are validated integer frame coordinates;
    // clamping their relative index keeps it in the count-slot distance array.
    const index = Math.min(count - 1, Math.max(0, item.start - descriptor.frameStart))
    const start = Math.min(descriptor.frameEnd, descriptor.frameStart + packedNumber(distances, index) / total * steps)
    return { ...item, start, end: Math.min(descriptor.frameEnd, start + 2) }
  }
  return {
    ...assets,
    route,
    manifest: {
      ...assets.manifest,
      exhibits: assets.manifest.exhibits.map(remap),
      navigation: { ...assets.manifest.navigation, pacing: 'linear-distance' as const, travelDistance: total, stations: assets.manifest.navigation.stations.map(remap) },
    },
  }
}
