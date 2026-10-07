/* eslint react-hooks/immutability: "off" -- Planar reflections temporarily mutate and restore shared Three.js renderer resources. */
import { useEffect, useLayoutEffect, useMemo } from 'react'
import { useThree } from '@react-three/fiber'
import { CircleGeometry, Color, PlaneGeometry, Vector2, Vector4 } from 'three'
import { Reflector } from 'three/addons/objects/Reflector.js'

let reflectionPass = false

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

export default function ReflectiveFloor({ name, width, depth, radius, position, strength = .34, paving = false, clippingPlanes }) {
  const { size, invalidate } = useThree()
  const resolution = size.width <= 600 ? 256 : 512
  const mirror = useMemo(() => {
    const geometry = radius ? new CircleGeometry(radius, 128) : new PlaneGeometry(width, depth)
    const floor = new Reflector(geometry, {
      textureWidth: resolution, textureHeight: resolution, multisample: 0,
      color: '#030303', clipBias: .0003, shader: glassShader,
    })
    floor.name = name
    floor.material.toneMapped = false
    floor.material.uniforms.circular.value = radius ? 1 : 0
    floor.material.uniforms.texel.value.set(1.2 / resolution, 1.2 / resolution)
    floor.raycast = () => null
    const reflect = floor.onBeforeRender
    const viewport = new Vector4(), scissor = new Vector4()
    floor.onBeforeRender = function (renderer, scene, camera) {
      if (reflectionPass) return
      reflectionPass = true
      const target = renderer.getRenderTarget()
      const face = renderer.getActiveCubeFace(), mip = renderer.getActiveMipmapLevel()
      const scissorTest = renderer.getScissorTest()
      const xr = renderer.xr.enabled, shadows = renderer.shadowMap.autoUpdate
      renderer.getViewport(viewport);renderer.getScissor(scissor)
      const mirrors = [], heights = [], visited = new Set()
      scene.traverse(object => {
        if (object.isReflector) { mirrors.push([object, object.visible]);object.visible = false }
        for (const material of Array.isArray(object.material) ? object.material : [object.material]) {
          const height = material?.uniforms?.viewportHeight
          if (height && !visited.has(material)) { visited.add(material);heights.push([height, height.value]);height.value = resolution }
        }
      })
      try {
        reflect.call(floor, renderer, scene, camera)
      } finally {
        for (const [uniform, value] of heights) uniform.value = value
        for (const [object, visible] of mirrors) object.visible = visible
        renderer.xr.enabled = xr;renderer.shadowMap.autoUpdate = shadows
        renderer.setRenderTarget(target, face, mip)
        renderer.setViewport(viewport);renderer.setScissor(scissor);renderer.setScissorTest(scissorTest)
        reflectionPass = false
      }
    }
    return floor
  }, [name, width, depth, radius, resolution])
  useEffect(() => { invalidate();return () => { mirror.geometry.dispose();mirror.dispose() } }, [mirror, invalidate])
  useLayoutEffect(() => {
    mirror.material.uniforms.strength.value = strength
    mirror.material.uniforms.paving.value = paving ? 1 : 0
    invalidate()
  }, [mirror, strength, paving, invalidate])
  useLayoutEffect(() => {
    mirror.material.clipping = Boolean(clippingPlanes)
    mirror.material.clippingPlanes = clippingPlanes || null
    mirror.material.needsUpdate = true
    invalidate()
  }, [mirror, clippingPlanes, invalidate])
  return <primitive object={mirror} position={position} dispose={null} />
}
