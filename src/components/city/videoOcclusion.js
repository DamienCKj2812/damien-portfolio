import { Mesh } from 'three'
import { MeshBVH, acceleratedRaycast } from 'three-mesh-bvh/src/index.js'

export function createVideoOccluder(geometry, material) {
  // All video boards share these static geometries. Build once per geometry,
  // with indirect storage so authored vertex/index order is not rearranged.
  if (!geometry.boundsTree) {
    geometry.boundsTree = new MeshBVH(geometry, { indirect: true, maxLeafTris: 16 })
    // Geometry.dispose releases GPU buffers, not immutable CPU positions.
    // Retain the CPU index through StrictMode's GPU cleanup/replay; it is
    // collected with its geometry when the scene itself is released.
  }
  const mesh = new Mesh(geometry, material)
  mesh.raycast = acceleratedRaycast
  return mesh
}

export function videoIsOccluded(raycaster, meshes, hits) {
  raycaster.firstHitOnly = true
  for (const mesh of meshes) {
    hits.length = 0
    raycaster.intersectObject(mesh, false, hits)
    if (hits.length) return true
  }
  return false
}
