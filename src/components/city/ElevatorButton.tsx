/* eslint react-hooks/immutability: "off" -- Switch travel, light materials, and Three.js geometry are mutable GPU resources. */
import { useEffect, useMemo, useRef } from 'react'
import { useFrame, useThree } from '@react-three/fiber'
import type { ThreeEvent } from '@react-three/fiber'
import { DoubleSide, MathUtils, Vector4 } from 'three'
import { createSceneShaderMaterial } from './cityAssets'
import { LineSegmentsGeometry } from 'three/addons/lines/LineSegmentsGeometry.js'
import { LineSegments2 } from 'three/addons/lines/LineSegments2.js'
import { LineMaterial } from 'three/addons/lines/LineMaterial.js'
import useSoundEffects from '../../audio/useSoundEffects'
import type { Group } from 'three'
import type { ElevatorLevel, LevelId, SceneGeometry } from '../../types/scene'

export interface ElevatorButtonProps {
  level: ElevatorLevel; items: SceneGeometry[]; selected: boolean; focused: boolean; keyboardPressed: boolean
  interactive: boolean; reducedMotion: boolean; onSelect: (level: LevelId) => void
}

const TRAVEL = .006
const vertexShader = `
  attribute float luminance;
  varying float brightness;
  void main() {
    brightness = luminance;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`
const fragmentShader = `
  varying float brightness;
  uniform float gain;
  void main() {
    gl_FragColor = vec4(vec3(brightness * gain), 1.0);
    #include <colorspace_fragment>
  }
`
const faceVertexShader = `
  varying vec2 panelPosition;
  void main() {
    panelPosition = position.yz;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`
const faceFragmentShader = `
  varying vec2 panelPosition;
  uniform vec4 bounds;
  uniform float light;
  void main() {
    vec2 uv = (panelPosition - bounds.xy) / (bounds.zw - bounds.xy);
    float sheen = pow(clamp(uv.y, 0.0, 1.0), 2.0) * exp(-pow((uv.x - .32) * 1.9, 2.0));
    float shade = .002 + .016 * sheen + .008 * light;
    gl_FragColor = vec4(vec3(shade), 1.0);
    #include <colorspace_fragment>
  }
`

export default function ElevatorButton({ level, items, selected, focused, keyboardPressed, interactive, reducedMotion, onSelect }: ElevatorButtonProps) {
  const { environmentClick: playClick } = useSoundEffects()
  const { invalidate, size } = useThree()
  const root = useRef<Group>(null)
  const hovered = useRef(false)
  const held = useRef(false)
  const pulseUntil = useRef(0)
  const brightness = useRef(0)
  const available = level.available !== false
  const body = items.find(item => item.role === 'button')
  const visuals = useMemo(() => {
    if (!body) throw new Error(`Elevator floor ${level.id} has no button face.`)
    body.geometry.computeVertexNormals()
    body.geometry.computeBoundingBox()
    const bounds = body.geometry.boundingBox
    if (!bounds) throw new Error(`Elevator floor ${level.id} has no button bounds.`)
    const { min, max } = bounds
    const front = min.x - .004
    const outline = new LineSegmentsGeometry()
    const positions = body.geometry.getAttribute('position')
    const corners = new Map<string, [number, number]>()
    for (let i = 0; i < positions.count; i++) {
      if (Math.abs(positions.getX(i)-min.x) > .00001) continue
      const y = positions.getY(i), z = positions.getZ(i)
      corners.set(`${y.toFixed(6)}:${z.toFixed(6)}`, [y, z])
    }
    const centerY = (min.y+max.y)/2, centerZ = (min.z+max.z)/2
    const perimeter = [...corners.values()].sort((a, b) => Math.atan2(a[1]-centerZ,a[0]-centerY)-Math.atan2(b[1]-centerZ,b[0]-centerY))
    const segments = []
    for (let i = 0; i < perimeter.length; i++) {
      const a = perimeter[i], b = perimeter[(i+1)%perimeter.length]
      if (!a || !b) throw new Error(`Elevator floor ${level.id} has an incomplete button perimeter.`)
      segments.push(front, ...a, front, ...b)
    }
    outline.setPositions(segments)
    const face = createSceneShaderMaterial({ vertexShader: faceVertexShader, fragmentShader: faceFragmentShader,
      side: DoubleSide, toneMapped: false }, { bounds: { value: new Vector4(min.y, min.z, max.y, max.z) }, light: { value: 0 } })
    const lettering = createSceneShaderMaterial({ vertexShader, fragmentShader, side: DoubleSide, polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1, toneMapped: false }, { gain: { value: 1 } })
    const border = createSceneShaderMaterial({ vertexShader, fragmentShader, depthWrite: false, toneMapped: false }, { gain: { value: 1 } })
    const halo = new LineMaterial({ color: 0xc9e1ff, linewidth: 5.5, transparent: true, opacity: .055, depthWrite: false, toneMapped: false })
    const edge = new LineMaterial({ color: 0xf1f7ff, linewidth: 1, transparent: true, opacity: .65, depthWrite: false, toneMapped: false })
    const wide = new LineSegments2(outline, halo), core = new LineSegments2(outline, edge)
    wide.renderOrder = 4;core.renderOrder = 5
    return { face, lettering, border, halo, edge, outline, wide, core }
  }, [body, level.id])
  useEffect(() => () => {
    for (const key of ['face', 'lettering', 'border', 'halo', 'edge', 'outline'] as const) visuals[key].dispose()
  }, [visuals])
  useEffect(() => {
    visuals.halo.resolution.set(size.width, size.height);visuals.edge.resolution.set(size.width, size.height);invalidate()
  }, [visuals, size.width, size.height, invalidate])
  useEffect(() => {
    if (selected && !reducedMotion) pulseUntil.current = performance.now() + 140
    invalidate()
  }, [selected, reducedMotion, invalidate])
  useEffect(() => {
    if (!interactive) { hovered.current = false;held.current = false;document.body.style.cursor = '' }
    invalidate()
  }, [interactive, focused, keyboardPressed, invalidate])
  useEffect(() => {
    const release = () => { if (held.current) { held.current = false;invalidate() } }
    window.addEventListener('pointerup', release);window.addEventListener('pointercancel', release);window.addEventListener('blur', release)
    return () => {
      window.removeEventListener('pointerup', release);window.removeEventListener('pointercancel', release);window.removeEventListener('blur', release)
      document.body.style.cursor = ''
    }
  }, [invalidate])
  useFrame((_, delta) => {
    if (!root.current) return
    const over = available && interactive && (hovered.current || focused)
    const pulse = selected && !reducedMotion && performance.now() < pulseUntil.current
    const down = available && (interactive && (held.current || keyboardPressed) || pulse)
    const targetLight = selected ? 1 : over ? .55 : 0
    const targetDepth = down ? TRAVEL : 0
    const blend = Math.min(delta, .1)
    brightness.current = reducedMotion ? targetLight : MathUtils.damp(brightness.current, targetLight, 22, blend)
    root.current.position.x = reducedMotion ? targetDepth : MathUtils.damp(root.current.position.x, targetDepth, down ? 42 : 30, blend)
    if (Math.abs(brightness.current - targetLight) < .002) brightness.current = targetLight
    if (Math.abs(root.current.position.x - targetDepth) < .00002) root.current.position.x = targetDepth
    const light = brightness.current
    visuals.face.uniforms.light.value = light
    visuals.lettering.uniforms.gain.value = available ? 1 + light * .75 : .45
    visuals.border.uniforms.gain.value = available ? 1 + light * 2 : .45
    visuals.halo.opacity = .055 + light * .14;visuals.edge.opacity = .65 + light * .3
    visuals.wide.visible = available;visuals.core.visible = available
    Object.assign(root.current.userData, { hovered: over, selected, pressed: down, pressDepth: root.current.position.x, brightness: light })
    if (pulse || brightness.current !== targetLight || root.current.position.x !== targetDepth) invalidate()
  })
  if (!body) return null
  const enabled = interactive && available
  return <group ref={root} name={`elevator-floor-${level.id}`}>
    <mesh name={`elevator-floor-${level.id}-face`} geometry={body.geometry} material={visuals.face}
      {...(enabled ? {
        onPointerOver: (event: ThreeEvent<PointerEvent>) => { event.stopPropagation();hovered.current = true;document.body.style.cursor = 'pointer';invalidate() },
        onPointerOut: () => { hovered.current = false;held.current = false;document.body.style.cursor = '';invalidate() },
        onPointerDown: (event: ThreeEvent<PointerEvent>) => { if (event.button === 0) { event.stopPropagation();held.current = true;invalidate() } },
        onPointerUp: () => { held.current = false;invalidate() },
        onClick: (event: ThreeEvent<MouseEvent>) => { event.stopPropagation();if (event.delta <= 5) { playClick();onSelect(level.id) } },
      } : {})}
    />
    {items.filter(item => item.role === 'buttonDetail').map(item => item.kind === 'lines' ?
      <lineSegments key={item.byteOffset} geometry={item.geometry} material={visuals.border} renderOrder={1} /> :
      <mesh key={item.byteOffset} geometry={item.geometry} material={visuals.lettering} renderOrder={0} />
    )}
    <primitive object={visuals.wide} dispose={null} /><primitive object={visuals.core} dispose={null} />
  </group>
}
