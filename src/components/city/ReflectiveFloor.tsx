/* eslint react-hooks/immutability: "off" -- Planar reflections temporarily mutate and restore shared Three.js renderer resources. */
import { useEffect, useLayoutEffect, useMemo } from 'react'
import { useThree } from '@react-three/fiber'
import { CircleGeometry, Color, Mesh, PlaneGeometry, ShaderMaterial, Vector2, Vector4 } from 'three'
import type { IUniform, Material, Object3D, Plane } from 'three'
import type { Vec3 } from '../../types/scene'
import { Reflector } from 'three/addons/objects/Reflector.js'

let reflectionPass = false

export interface ReflectiveFloorProps {
  name: string; width?: number; depth?: number; radius?: number; position: Vec3; strength?: number; paving?: boolean; clippingPlanes?: Plane[]
}

const glassShader = {
  name: 'DarkGlassFloor',
  uniforms: {
    color: { value: new Color('#030303') },
    tDiffuse: { value: null }, textureMatrix: { value: null },
    texel: { value: new Vector2() }, strength: { value: .34 },
     circular: { value: 0 },
     paving: { value: 0 },
  },
  vertexShader: `
    #include <clipping_planes_pars_vertex>
    uniform mat4 textureMatrix;
    varying vec4 reflectionUv;
    varying vec3 worldPosition;
    varying vec3 worldNormal;
    varying vec2 floorUv;
    void main() {
      reflectionUv = textureMatrix * vec4(position, 1.0);
      worldPosition = (modelMatrix * vec4(position, 1.0)).xyz;
      worldNormal = normalize(mat3(modelMatrix) * normal);
      floorUv = uv;
      vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
      gl_Position = projectionMatrix * mvPosition;
      #include <clipping_planes_vertex>
    }
  `,
  fragmentShader: `
    #include <clipping_planes_pars_fragment>
    uniform vec3 color;
    uniform sampler2D tDiffuse;
    uniform vec2 texel;
    uniform float strength;
    uniform float circular;
    uniform float paving;
    varying vec4 reflectionUv;
    varying vec3 worldPosition;
    varying vec3 worldNormal;
    varying vec2 floorUv;
    void main() {
      #include <clipping_planes_fragment>
      vec2 coord = reflectionUv.xy / reflectionUv.w;
      // Static stone grain breaks up wet street reflections without an idle clock.
      vec2 stone = worldPosition.xz;
      float grain = fract(sin(dot(floor(stone * 90.0), vec2(12.9898, 78.233))) * 43758.5453);
      float ripple = sin(stone.x * 71.0 + sin(stone.y * 43.0)) * sin(stone.y * 57.0);
      coord += paving * vec2(ripple, grain - 0.5) * texel * 0.65;
      vec3 reflected = texture2D(tDiffuse, coord).rgb * 0.4;
      reflected += texture2D(tDiffuse, coord + vec2(texel.x, 0.0)).rgb * 0.15;
      reflected += texture2D(tDiffuse, coord - vec2(texel.x, 0.0)).rgb * 0.15;
      reflected += texture2D(tDiffuse, coord + vec2(0.0, texel.y)).rgb * 0.15;
      reflected += texture2D(tDiffuse, coord - vec2(0.0, texel.y)).rgb * 0.15;
      vec3 viewDirection = normalize(cameraPosition - worldPosition);
      float grazing = 1.0 - clamp(dot(viewDirection, normalize(worldNormal)), 0.0, 1.0);
      float fresnel = 0.35 + 0.65 * grazing * grazing;
      float edge = min(min(floorUv.x, 1.0 - floorUv.x), min(floorUv.y, 1.0 - floorUv.y));
      edge = mix(edge, 0.5 - length(floorUv - vec2(0.5)), circular);
      float fade = smoothstep(0.0, 0.012, edge);
      vec3 surface = color + paving * vec3(0.0015 + grain * 0.002);
      gl_FragColor = vec4(surface + reflected * strength * fresnel * fade * (1.0 - paving * grain * 0.14), 1.0);
      #include <colorspace_fragment>
    }
  `,
}

type FloorMaterial = ShaderMaterial & { uniforms: typeof glassShader.uniforms }

export default function ReflectiveFloor({ name, width, depth, radius, position, strength = .34, paving = false, clippingPlanes }: ReflectiveFloorProps) {
  const { size, invalidate } = useThree()
  const resolution = size.width <= 600 ? 256 : 512
  const { mirror, material } = useMemo(() => {
    const geometry = radius ? new CircleGeometry(radius, 128) : new PlaneGeometry(width, depth)
    const floor = new Reflector(geometry, {
      textureWidth: resolution, textureHeight: resolution, multisample: 0,
      color: '#030303', clipBias: .0003, shader: glassShader,
    })
    floor.name = name
    const shaderMaterial = floor.material
    if (!(shaderMaterial instanceof ShaderMaterial)) throw new Error('The floor reflector requires a shader material.')
    // Reflector creates this material by cloning the supplied shader's uniforms.
    const material = shaderMaterial as FloorMaterial
    material.toneMapped = false
    material.uniforms.circular.value = radius ? 1 : 0
    material.uniforms.texel.value.set(1.2 / resolution, 1.2 / resolution)
    floor.raycast = () => null
    const reflect = floor.onBeforeRender
    const viewport = new Vector4(), scissor = new Vector4()
    floor.onBeforeRender = function (renderer, scene, camera, geometry, material, group) {
      if (reflectionPass) return
      reflectionPass = true
      const target = renderer.getRenderTarget()
      const face = renderer.getActiveCubeFace(), mip = renderer.getActiveMipmapLevel()
      const scissorTest = renderer.getScissorTest()
      const xr = renderer.xr.enabled, shadows = renderer.shadowMap.autoUpdate
      renderer.getViewport(viewport);renderer.getScissor(scissor)
      const mirrors: [Object3D, boolean][] = [], heights: [IUniform<number>, number][] = [], visited = new Set<Material>()
      scene.traverse(object => {
        if ('isReflector' in object && object.isReflector) { mirrors.push([object, object.visible]);object.visible = false }
        if (!(object instanceof Mesh) && !('material' in object)) return
        const objectMaterial = object.material
        for (const material of Array.isArray(objectMaterial) ? objectMaterial : [objectMaterial]) {
          const height = material instanceof ShaderMaterial ? material.uniforms.viewportHeight : undefined
          if (height && !visited.has(material)) { visited.add(material);heights.push([height, height.value]);height.value = resolution }
        }
      })
      try {
        reflect.call(floor, renderer, scene, camera, geometry, material, group)
      } finally {
        for (const [uniform, value] of heights) uniform.value = value
        for (const [object, visible] of mirrors) object.visible = visible
        renderer.xr.enabled = xr;renderer.shadowMap.autoUpdate = shadows
        renderer.setRenderTarget(target, face, mip)
        renderer.setViewport(viewport);renderer.setScissor(scissor);renderer.setScissorTest(scissorTest)
        reflectionPass = false
      }
    }
    return { mirror: floor, material }
  }, [name, width, depth, radius, resolution])
  useEffect(() => { invalidate();return () => { mirror.geometry.dispose();mirror.dispose() } }, [mirror, invalidate])
  useLayoutEffect(() => {
    material.uniforms.strength.value = strength
    material.uniforms.paving.value = paving ? 1 : 0
    invalidate()
  }, [material, strength, paving, invalidate])
  useLayoutEffect(() => {
    material.clipping = Boolean(clippingPlanes)
    material.clippingPlanes = clippingPlanes || null
    material.needsUpdate = true
    invalidate()
  }, [material, clippingPlanes, invalidate])
  return <primitive object={mirror} position={position} dispose={null} />
}
