import { Plane, Vector3 } from 'three'
import type { Quaternion } from 'three'
import type { PortalMetadata } from '../../types/scene'

export interface LobbyPortalClip {
  corners: [Vector3, Vector3, Vector3, Vector3]
  center: Vector3
  forward: Vector3
  planes: [Plane, Plane, Plane, Plane]
  delta: Vector3
}

// Clip only the preloaded interior to the real street aperture. Otherwise the
// much wider lobby shell covers outdoor scenery before the visitor enters it.
export function createLobbyPortalClip(portal: PortalMetadata, basis: Quaternion): LobbyPortalClip {
  const [x, y, z] = portal.center
  const corner = (sx: number, sz: number) => new Vector3(x + sx * portal.width / 2, y, z + sz * portal.height / 2).applyQuaternion(basis)
  const corners: LobbyPortalClip['corners'] = [corner(-1, -1), corner(1, -1), corner(1, 1), corner(-1, 1)]
  const center = new Vector3(x, y, z).applyQuaternion(basis)
  const forward = new Vector3(0, 1, 0).applyQuaternion(basis)
  return { corners, center, forward, planes: [new Plane(), new Plane(), new Plane(), new Plane()], delta: new Vector3() }
}

function updatePlane(plane: Plane, start: Vector3, end: Vector3, clip: LobbyPortalClip, eye: Vector3, outside: boolean) {
  if (outside) {
    plane.setFromCoplanarPoints(eye, start, end)
    if (plane.distanceToPoint(clip.center) < 0) plane.negate()
  } else {
    // Keep the plane count stable when crossing/reversing at the threshold,
    // avoiding shader recompilation and an idle invalidation loop.
    plane.set(clip.forward, 1e6)
  }
}

export function updateLobbyPortalClip(clip: LobbyPortalClip, eye: Vector3, near = .05) {
  const outside = clip.delta.subVectors(eye, clip.center).dot(clip.forward) < -near * 2
  // Fixed four-wide tuples encode the same clockwise wrap. Explicit edges
  // avoid uncertain array reads, per-frame guards and iterator allocations.
  updatePlane(clip.planes[0], clip.corners[0], clip.corners[1], clip, eye, outside)
  updatePlane(clip.planes[1], clip.corners[1], clip.corners[2], clip, eye, outside)
  updatePlane(clip.planes[2], clip.corners[2], clip.corners[3], clip, eye, outside)
  updatePlane(clip.planes[3], clip.corners[3], clip.corners[0], clip, eye, outside)
  return outside
}
