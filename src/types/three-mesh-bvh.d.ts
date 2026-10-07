import 'three-mesh-bvh/src/index.js'

// 0.8.3 implements indirect CPU indices but omits the option from its types.
// Keep the runtime's ESM entry and the package's own Three.js augmentations.
declare module 'three-mesh-bvh/src/index.js' {
  interface MeshBVHOptions {
    indirect?: boolean
  }
}
