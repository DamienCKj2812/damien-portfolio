import { Plane, Vector3 } from 'three'

// Clip only the preloaded interior to the real street aperture. Otherwise the
// much wider lobby shell covers outdoor scenery before the visitor enters it.
export function createLobbyPortalClip(portal, basis) {
  const [x, y, z] = portal.center
  const corners = [[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([sx, sz]) =>
    new Vector3(x + sx * portal.width / 2, y, z + sz * portal.height / 2).applyQuaternion(basis))
  const center = new Vector3(x, y, z).applyQuaternion(basis)
  const forward = new Vector3(0, 1, 0).applyQuaternion(basis)
  return { corners, center, forward, planes: Array.from({ length: 4 }, () => new Plane()), delta: new Vector3() }
}

export function updateLobbyPortalClip(clip, eye, near = .05) {
  const outside = clip.delta.subVectors(eye, clip.center).dot(clip.forward) < -near * 2
  for (let i = 0; i < clip.planes.length; i++) {
    const plane = clip.planes[i]
    if (outside) {
      plane.setFromCoplanarPoints(eye, clip.corners[i], clip.corners[(i + 1) % 4])
      if (plane.distanceToPoint(clip.center) < 0) plane.negate()
    } else {
      // Keep the plane count stable when crossing/reversing at the threshold,
      // avoiding shader recompilation and an idle invalidation loop.
      plane.set(clip.forward, 1e6)
    }
  }
  return outside
}
