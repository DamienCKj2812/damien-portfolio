// Reparameterize guided room paths by distance, removing inspection holds while
// keeping their paths, look directions, loop/end behavior, and coupled clocks.
export function prepareLinearRoomRoute(assets) {
  if (!['skills', 'experience'].includes(assets.manifest.level) || !assets.route) return assets
  const descriptor = assets.manifest.navigation.route
  const count = descriptor.frameEnd - descriptor.frameStart + 1
  const stride = descriptor.stride
  const distances = new Float64Array(count)
  for (let index = 1; index < count; index++) {
    const a = (index - 1) * stride, b = index * stride
    distances[index] = distances[index - 1] + Math.hypot(assets.route[b] - assets.route[a], assets.route[b + 1] - assets.route[a + 1], assets.route[b + 2] - assets.route[a + 2])
  }
  const total = distances[count - 1]
  if (total <= 0) throw new Error('The guided walking path has no travel distance.')
  const steps = descriptor.loop ? count : count - 1
  const route = new Float32Array(count * stride)
  let segment = 1
  for (let index = 0; index < count; index++) {
    const distance = total * index / steps
    while (segment < count - 1 && distances[segment] <= distance) segment++
    const before = distances[segment - 1], span = distances[segment] - before
    const blend = span > 0 ? (distance - before) / span : 0
    const a = (segment - 1) * stride, b = segment * stride
    for (let axis = 0; axis < stride; axis++) route[index * stride + axis] = assets.route[a + axis] + (assets.route[b + axis] - assets.route[a + axis]) * blend
  }
  const remap = item => {
    const index = Math.min(count - 1, Math.max(0, item.start - descriptor.frameStart))
    const start = Math.min(descriptor.frameEnd, descriptor.frameStart + distances[index] / total * steps)
    return { ...item, start, end: Math.min(descriptor.frameEnd, start + 2) }
  }
  return {
    ...assets,
    route,
    manifest: {
      ...assets.manifest,
      exhibits: assets.manifest.exhibits.map(remap),
      navigation: { ...assets.manifest.navigation, pacing: 'linear-distance', travelDistance: total, stations: assets.manifest.navigation.stations.map(remap) },
    },
  }
}
