/* eslint react-hooks/immutability: "off" -- Shooting-star geometry and uniforms update on the existing visible-city clock. */
import { useEffect, useLayoutEffect, useMemo, useRef } from 'react'
import { useFrame, useThree } from '@react-three/fiber'
import { AdditiveBlending, BufferGeometry, DoubleSide, DynamicDrawUsage, Float32BufferAttribute, Vector3 } from 'three'
import { sampleShootingStar, shootingStarRoutes } from './shootingStarRoutes'
import { createSceneShaderMaterial } from './cityAssets'
import type { RefObject } from 'react'
import type { Group } from 'three'
import type { JourneyConfig } from '../../types/scene'
import type { ShootingStarSample } from '../../types/navigation'

export interface CityShootingStarsProps { clock: RefObject<number>; fps: number; frameRef: RefObject<number>; journey: JourneyConfig; reducedMotion: boolean }
const TRAIL_VERTICES: [number, boolean, number][] = [[0, false, -1], [1, false, 1], [2, true, 1], [3, false, -1], [4, true, 1], [5, true, -1]]

export default function CityShootingStars({ clock, fps, frameRef, journey, reducedMotion }: CityShootingStarsProps) {
  const root = useRef<Group>(null)
  const objects = useRef(new Map<string, Group>())
  const { camera, gl, size, viewport } = useThree()
  const scratch = useMemo(() => ({ head: new Vector3(), tail: new Vector3(), view: new Vector3(), width: new Vector3(), point: new Vector3(), motion: { active: false, progress: 0, opacity: 0 } satisfies ShootingStarSample }), [])
  const stars = useMemo(() => shootingStarRoutes.map(route => {
    const start = new Vector3().fromArray(route.start), end = new Vector3().fromArray(route.end)
    const delta = end.clone().sub(start), length = delta.length(), direction = delta.clone().normalize()
    const trail = new BufferGeometry()
    const trailPosition = new Float32BufferAttribute(new Float32Array(18), 3).setUsage(DynamicDrawUsage)
    trail.setAttribute('position', trailPosition)
    trail.setAttribute('uv', new Float32BufferAttribute([0, 1, 1, 1, 1, 0, 0, 1, 1, 0, 0, 0], 2))
    const head = new BufferGeometry()
    const headPosition = new Float32BufferAttribute(new Float32Array(3), 3).setUsage(DynamicDrawUsage)
    head.setAttribute('position', headPosition)
    const trailMaterial = createSceneShaderMaterial({
      transparent: true, depthWrite: false, side: DoubleSide, blending: AdditiveBlending, toneMapped: false,
      vertexShader: 'varying vec2 streakUv; void main() { streakUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
      fragmentShader: `uniform float opacity; varying vec2 streakUv;
        void main() {
          float edge = pow(max(0.0, 1.0 - abs(streakUv.x * 2.0 - 1.0)), 1.5);
          float fade = pow(streakUv.y, 1.5);
          gl_FragColor = vec4(vec3(0.85), opacity * edge * fade);
          #include <colorspace_fragment>
        }`,
    }, { opacity: { value: 0 } })
    const headMaterial = createSceneShaderMaterial({
      transparent: true, depthWrite: false, blending: AdditiveBlending, toneMapped: false,
      vertexShader: `uniform float viewportHeight;
        void main() {
          vec4 view = modelViewMatrix * vec4(position, 1.0);
          gl_PointSize = clamp(0.13 * viewportHeight * projectionMatrix[1][1] / max(0.01, -view.z), 1.4, 8.0);
          gl_Position = projectionMatrix * view;
        }`,
      fragmentShader: `uniform float opacity;
        void main() {
          float radius = length(gl_PointCoord - vec2(0.5)) * 2.0;
          gl_FragColor = vec4(vec3(1.0), opacity * (1.0 - smoothstep(0.15, 1.0, radius)));
          #include <colorspace_fragment>
        }`,
    }, { opacity: { value: 0 }, viewportHeight: { value: 900 } })
    return { route, start, delta, length, direction, trail, head, trailPosition, headPosition, trailMaterial, headMaterial }
  }), [])
  useLayoutEffect(() => { for (const star of stars) star.headMaterial.uniforms.viewportHeight.value = size.height * gl.getPixelRatio() }, [stars, size.height, viewport.dpr, gl])
  useEffect(() => () => {
    for (const star of stars) { star.trail.dispose();star.head.dispose();star.trailMaterial.dispose();star.headMaterial.dispose() }
  }, [stars])

  useFrame(() => {
    if (!root.current) return
    const active = !reducedMotion && frameRef.current < (journey.cityHideFrame ?? journey.cityEnd)
    root.current.visible = active
    if (!active || document.hidden) return
    root.current.updateWorldMatrix(true, false)
    for (const star of stars) {
      const object = objects.current.get(star.route.id)
      if (!object) continue
      const motion = sampleShootingStar(star.route, clock.current / fps, scratch.motion)
      object.visible = motion.active
      if (!motion.active) continue
      scratch.head.copy(star.start).addScaledVector(star.delta, motion.progress)
      scratch.tail.copy(scratch.head).addScaledVector(star.direction, -Math.min(star.route.trail, star.length * motion.progress))
      scratch.view.copy(camera.position);root.current.worldToLocal(scratch.view)
      scratch.view.sub(scratch.head).normalize()
      scratch.width.crossVectors(star.direction, scratch.view).normalize().multiplyScalar(star.route.width)
      const position = star.trailPosition
      for (const [index, tail, side] of TRAIL_VERTICES) {
        scratch.point.copy(tail ? scratch.tail : scratch.head).addScaledVector(scratch.width, side)
        position.setXYZ(index, scratch.point.x, scratch.point.y, scratch.point.z)
      }
      position.needsUpdate = true;star.trail.computeBoundingSphere()
      star.headPosition.setXYZ(0, scratch.head.x, scratch.head.y, scratch.head.z)
      star.headPosition.needsUpdate = true;star.head.computeBoundingSphere()
      star.trailMaterial.uniforms.opacity.value = motion.opacity * .72
      star.headMaterial.uniforms.opacity.value = motion.opacity
    }
  }, -.1)

  return <group ref={root} name="city-shooting-stars" visible={false}>
    {stars.map(star => <group key={star.route.id} name={`city-shooting-star-${star.route.id}`} visible={false}
      ref={object => { if (object) objects.current.set(star.route.id, object);else objects.current.delete(star.route.id) }}>
      <mesh geometry={star.trail} material={star.trailMaterial} raycast={() => null} renderOrder={3} />
      <points geometry={star.head} material={star.headMaterial} raycast={() => null} renderOrder={4} />
    </group>)}
  </group>
}
