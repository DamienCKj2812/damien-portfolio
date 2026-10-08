/* eslint react-hooks/immutability: "off" -- Hover fades update Three.js materials on finite demand frames. */
import { useEffect, useMemo, useRef } from 'react'
import { useFrame, useThree } from '@react-three/fiber'
import type { ThreeEvent } from '@react-three/fiber'
import { DoubleSide, MathUtils } from 'three'
import type { Group } from 'three'
import { LineSegmentsGeometry } from 'three/addons/lines/LineSegmentsGeometry.js'
import { LineSegments2 } from 'three/addons/lines/LineSegments2.js'
import { LineMaterial } from 'three/addons/lines/LineMaterial.js'
import { createSceneShaderMaterial } from './cityAssets'
import type { SceneGeometry } from '../../types/scene'

interface OfficePrinterProps {
  items: SceneGeometry[]; enabled: boolean; reducedMotion: boolean
  onInteract: (id: string) => void; onHover: (id: string | null) => void
}

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

export default function OfficePrinter({ items, enabled, reducedMotion, onInteract, onHover }: OfficePrinterProps) {
  const { invalidate, size } = useThree()
  const root = useRef<Group>(null)
  const hovered = useRef(false), held = useRef(false), brightness = useRef(0)
  const visuals = useMemo(() => {
    const solid = createSceneShaderMaterial({ vertexShader, fragmentShader, side: DoubleSide, toneMapped: false }, { gain: { value: 1 } })
    const lines = createSceneShaderMaterial({ vertexShader, fragmentShader, depthWrite: false, toneMapped: false }, { gain: { value: 1 } })
    const outline = new LineSegmentsGeometry()
    const positions: number[] = []
    for (const item of items.filter(item => item.kind === 'lines')) {
      const points = item.geometry.getAttribute('position')
      for (let i = 0; i < points.count; i++) positions.push(points.getX(i), points.getY(i), points.getZ(i))
    }
    outline.setPositions(positions)
    const halo = new LineMaterial({ color: 0xc9e1ff, linewidth: 5.5, transparent: true, opacity: 0, depthWrite: false, toneMapped: false })
    const edge = new LineMaterial({ color: 0xf1f7ff, linewidth: 1, transparent: true, opacity: 0, depthWrite: false, toneMapped: false })
    const wide = new LineSegments2(outline, halo), core = new LineSegments2(outline, edge)
    wide.renderOrder = 4;core.renderOrder = 5
    return { solid, lines, outline, halo, edge, wide, core }
  }, [items])
  useEffect(() => () => {
    for (const key of ['solid', 'lines', 'outline', 'halo', 'edge'] as const) visuals[key].dispose()
  }, [visuals])
  useEffect(() => {
    visuals.halo.resolution.set(size.width, size.height);visuals.edge.resolution.set(size.width, size.height);invalidate()
  }, [visuals, size.width, size.height, invalidate])
  useEffect(() => {
    const reset = () => {
      hovered.current = false;held.current = false;document.body.style.cursor = '';onHover(null);invalidate()
    }
    const release = () => { held.current = false;invalidate() }
    const visibility = () => { if (document.hidden) reset() }
    if (!enabled) reset()
    window.addEventListener('pointerup', release);window.addEventListener('pointercancel', reset);window.addEventListener('blur', reset)
    document.addEventListener('visibilitychange', visibility)
    return () => {
      window.removeEventListener('pointerup', release);window.removeEventListener('pointercancel', reset);window.removeEventListener('blur', reset)
      document.removeEventListener('visibilitychange', visibility)
      document.body.style.cursor = ''
    }
  }, [enabled, onHover, invalidate])
  useFrame((_, delta) => {
    const over = enabled && !document.hidden && hovered.current
    const target = over ? held.current ? 1 : .55 : 0
    brightness.current = reducedMotion ? target : MathUtils.damp(brightness.current, target, 22, Math.min(delta, .1))
    if (Math.abs(brightness.current - target) < .002) brightness.current = target
    const light = brightness.current
    visuals.solid.uniforms.gain.value = 1 + light * .75
    visuals.lines.uniforms.gain.value = 1 + light * 2
    visuals.halo.opacity = light * .14;visuals.edge.opacity = light * .3
    visuals.wide.visible = visuals.core.visible = light > 0
    if (root.current) Object.assign(root.current.userData, { hovered: over, brightness: light })
    if (light !== target) invalidate()
  })
  return <group ref={root} name="about-office-printer">
    {items.map(item => item.kind === 'solid' ? <mesh key={item.byteOffset} name="about-office-printer-pick" geometry={item.geometry} material={visuals.solid}
      {...(enabled ? {
        onPointerOver: (event: ThreeEvent<PointerEvent>) => { event.stopPropagation();if (event.pointerType === 'touch') return;hovered.current = true;document.body.style.cursor = 'pointer';onHover('printer');invalidate() },
        onPointerOut: () => { hovered.current = false;held.current = false;document.body.style.cursor = '';onHover(null);invalidate() },
        onPointerDown: (event: ThreeEvent<PointerEvent>) => { if (event.button === 0) { event.stopPropagation();held.current = true;invalidate() } },
        onClick: (event: ThreeEvent<MouseEvent>) => { event.stopPropagation();if (event.button === 0 && event.delta <= 5) onInteract('printer') },
      } : {})}
    /> : item.kind === 'lines' ? <lineSegments key={item.byteOffset} geometry={item.geometry} material={visuals.lines} renderOrder={1} /> : null)}
    <primitive object={visuals.wide} dispose={null} /><primitive object={visuals.core} dispose={null} />
  </group>
}
