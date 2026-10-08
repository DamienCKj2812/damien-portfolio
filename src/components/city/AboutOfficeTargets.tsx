/* eslint react-hooks/immutability: "off" -- Projected target positions and Three.js matrices update on demand-rendered frames. */
import { useEffect, useMemo, useRef, useState } from 'react'
import { useFrame, useThree } from '@react-three/fiber'
import { Html } from '@react-three/drei'
import { Box3, BufferGeometry, Float32BufferAttribute, Vector3 } from 'three'
import { portfolio } from '../../data/portfolio'
import type { Group } from 'three'
import type { SceneGeometry } from '../../types/scene'

export interface AboutOfficeTargetsProps {
  groups: SceneGeometry[]; enabled: boolean; hovered: string | null; onInteract: (id: string, source?: 'label') => void
}
import './aboutOfficeTargets.css'

function cornersOf(box: Box3) {
  return Array.from({ length: 8 }, (_, index) => new Vector3(
    index & 1 ? box.max.x : box.min.x,
    index & 2 ? box.max.y : box.min.y,
    index & 4 ? box.max.z : box.min.z,
  ))
}

function cornerGeometry(box: Box3) {
  const points = []
  const size = box.getSize(new Vector3())
  for (const corner of cornersOf(box)) {
    for (const axis of ['x', 'y', 'z'] as const) {
      const end = corner.clone()
      end[axis] += (corner[axis] === box.min[axis] ? 1 : -1) * Math.min(.16, size[axis] * .28)
      points.push(...corner.toArray(), ...end.toArray())
    }
  }
  return new BufferGeometry().setAttribute('position', new Float32BufferAttribute(points, 3))
}

export default function AboutOfficeTargets({ groups, enabled, hovered, onInteract }: AboutOfficeTargetsProps) {
  const root = useRef<Group>(null)
  const selected = useRef<string | null>(null)
  const [focused, setFocused] = useState<string | null>(null)
  const { camera, size, pointer, invalidate } = useThree()
  const scratch = useMemo(() => new Vector3(), [])
  const targets = useMemo(() => groups.filter(item => item.role === 'contactPick' || item.role === 'observerPick' || item.role === 'printer' && item.kind === 'solid').flatMap(item => {
    item.geometry.computeBoundingBox()
    if (!item.id || !item.geometry.boundingBox) return []
    const bounds = item.geometry.boundingBox.clone()
    const center = bounds.getCenter(new Vector3())
    let outline = bounds.clone().expandByScalar(.035)
    if (item.id === 'card') {
      const face = groups.find(group => group.role === 'contact' && group.id === 'card')
      if (!face) return []
      face.geometry.computeBoundingBox()
      if (!face.geometry.boundingBox) return []
      face.geometry.boundingBox.getCenter(center)
      outline = new Box3().setFromCenterAndSize(center.clone().add(new Vector3(0, 0, .025)), new Vector3(.28, .19, .045))
    }
    return [{
      id: item.id,
      title: item.id === 'card' ? 'Contact' : item.id === 'printer' ? 'Printer' : portfolio.name,
      action: item.id === 'card' ? 'View business card' : item.id === 'printer' ? 'Print CV' : `Meet ${portfolio.name}`,
      ariaLabel: item.id === 'printer' ? 'Print CV' : `Open ${item.id === 'card' ? 'contact card' : `${portfolio.name} profile`}`,
      center,
      corners: cornersOf(bounds),
      label: new Vector3(center.x, center.y, outline.max.z + (item.id === 'card' ? .25 : .18)),
      geometry: cornerGeometry(outline),
    }]
  }), [groups])
  useEffect(() => () => { for (const target of targets) target.geometry.dispose() }, [targets])
  useEffect(() => { invalidate() }, [enabled, hovered, invalidate])

  useFrame(() => {
    let next: string | null = null
    let best = Infinity
    if (enabled && !document.hidden && root.current) {
      root.current.updateWorldMatrix(true, false)
      for (const target of targets) {
        scratch.copy(target.center).applyMatrix4(root.current.matrixWorld).project(camera)
        if (scratch.z < -1 || scratch.z > 1 || Math.abs(scratch.y) > .95) continue
        const score = Math.abs(scratch.x) + Math.abs(scratch.y) * .04
        let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity
        for (const corner of target.corners) {
          scratch.copy(corner).applyMatrix4(root.current.matrixWorld).project(camera)
          minX = Math.min(minX, scratch.x);maxX = Math.max(maxX, scratch.x)
          minY = Math.min(minY, scratch.y);maxY = Math.max(maxY, scratch.y)
        }
        const tolerance = 2 * Math.min(44, size.width * .055) / size.width
        if (hovered === target.id && pointer.x >= minX && pointer.x <= maxX && pointer.y >= minY && pointer.y <= maxY) { next = target.id;break }
        if (minX <= tolerance && maxX >= -tolerance && score < best) { next = target.id;best = score }
      }
    }
    if (next !== selected.current) { selected.current = next;setFocused(next) }
  }, -.25)

  return <group ref={root} name="about-office-target-hints">
    {enabled && targets.filter(target => target.id === focused).map(target => <group key={target.id}>
      <lineSegments geometry={target.geometry} renderOrder={8} raycast={() => null}>
        <lineBasicMaterial color="#ffffff" transparent opacity={.85} depthWrite={false} depthTest={false} toneMapped={false} />
      </lineSegments>
      <Html position={target.label.toArray()} center zIndexRange={[20, 10]} style={{ pointerEvents: 'none' }}>
        <button className="about-target-label" data-sound-effect="environment" data-target={target.id} aria-label={target.ariaLabel} onClick={() => onInteract(target.id, 'label')}>
          <span className="about-target-title">{target.title}</span>
          <span className="about-target-action">{target.action}<span aria-hidden="true">↗</span></span>
        </button>
      </Html>
    </group>)}
  </group>
}
