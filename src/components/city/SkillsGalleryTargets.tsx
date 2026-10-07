/* eslint react-hooks/immutability: "off" -- Projected hints reuse mutable Three.js resources on existing camera frames. */
import { useEffect, useMemo, useRef, useState } from 'react'
import { useFrame, useThree } from '@react-three/fiber'
import { Html } from '@react-three/drei'
import { BufferGeometry, DoubleSide, Float32BufferAttribute, Matrix4, Mesh, MeshBasicMaterial, Raycaster, Vector3 } from 'three'
import type { Box3, Group, Intersection } from 'three'
import type { SyntheticEvent } from 'react'
import type { ExhibitMetadata, SceneGeometry } from '../../types/scene'

export interface SkillsGalleryTargetsProps {
  groups: SceneGeometry[]; exhibits: ExhibitMetadata[]; enabled: boolean; hovered: string | null; onInteract: (id: string, source?: 'label') => void
}
import './aboutOfficeTargets.css'
import './skillsGalleryTargets.css'

// Keep the action in the screen's interface area, independent of the card face.
const screenOrigin = (): [number, number] => [0, 0]

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

export default function SkillsGalleryTargets({ groups, exhibits, enabled, hovered, onInteract }: SkillsGalleryTargetsProps) {
  const root = useRef<Group>(null)
  const selected = useRef<string | null>(null)
  const held = useRef<string | null>(null)
  const dirty = useRef(true)
  const [focused, setFocused] = useState<string | null>(null)
  const { camera, size, pointer, invalidate } = useThree()
  const scratch = useMemo(() => ({
    camera: new Vector3(), localCamera: new Vector3(), center: new Vector3(), projected: new Vector3(),
    corner: new Vector3(), facing: new Vector3(), direction: new Vector3(),
    cameraMatrix: new Matrix4(), projectionMatrix: new Matrix4(), rootMatrix: new Matrix4(), inverse: new Matrix4(),
    raycaster: new Raycaster(), hits: new Array<Intersection>(),
  }), [])
  const resources = useMemo(() => {
    const material = new MeshBasicMaterial({ side: DoubleSide })
    const targets = groups.filter(item => item.kind === 'solid' && item.role === 'exhibit' && item.id?.startsWith('skill-')).map(item => {
      const exhibit = exhibits.find(exhibit => exhibit.id === item.id)
      if (!exhibit) return null
      item.geometry.computeBoundingBox()
      if (!item.geometry.boundingBox) return null
      const bounds = item.geometry.boundingBox.clone()
      const center = bounds.getCenter(new Vector3())
      const positions = item.geometry.getAttribute('position')
      const a = new Vector3().fromBufferAttribute(positions, 0)
      const b = new Vector3().fromBufferAttribute(positions, 1).sub(a)
      const c = new Vector3().fromBufferAttribute(positions, 2).sub(a)
      const normal = b.cross(c).normalize()
      return { ...exhibit, center, normal, corners: cornersOf(bounds),
        geometry: cornerGeometry(bounds.expandByScalar(.045)) }
    }).filter(target => target !== null)
    const occluders = groups.filter(item => item.actor === 0 && item.kind === 'solid' && (item.opacity ?? 1) >= 1)
      .map(item => new Mesh(item.geometry, material))
    return { targets, occluders, material }
  }, [groups, exhibits])
  useEffect(() => () => {
    for (const target of resources.targets) target.geometry.dispose()
    resources.material.dispose()
  }, [resources])
  useEffect(() => { dirty.current = true;invalidate() }, [enabled, hovered, resources, size.width, size.height, invalidate])

  useFrame(() => {
    if (!enabled || document.hidden || !root.current) {
      held.current = null
      dirty.current = true
      if (selected.current !== null) { selected.current = null;setFocused(null) }
      return
    }
    root.current.updateWorldMatrix(true, false)
    // The cards and architecture are static: moving visitors must not cause
    // repeated hint/raycast work while the camera and hover remain idle.
    if (!dirty.current && scratch.cameraMatrix.equals(camera.matrixWorld) &&
        scratch.projectionMatrix.equals(camera.projectionMatrix) && scratch.rootMatrix.equals(root.current.matrixWorld)) return
    dirty.current = false
    scratch.cameraMatrix.copy(camera.matrixWorld)
    scratch.projectionMatrix.copy(camera.projectionMatrix)
    scratch.rootMatrix.copy(root.current.matrixWorld)
    scratch.inverse.copy(root.current.matrixWorld).invert()
    scratch.camera.copy(camera.position)
    scratch.localCamera.copy(camera.position).applyMatrix4(scratch.inverse)
    camera.getWorldDirection(scratch.direction)
    for (const mesh of resources.occluders) mesh.matrixWorld.copy(root.current.matrixWorld)

    let next: string | null = null
    let best = Infinity
    for (const target of resources.targets) {
      scratch.facing.subVectors(scratch.localCamera, target.center).normalize()
      if (scratch.facing.dot(target.normal) < .08) continue
      scratch.center.copy(target.center).applyMatrix4(root.current.matrixWorld)
      scratch.projected.copy(scratch.center).project(camera)
      if (scratch.projected.z < -1 || scratch.projected.z > 1 || Math.abs(scratch.projected.y) > .95) continue
      const score = Math.abs(scratch.projected.x) + Math.abs(scratch.projected.y) * .04
      let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity
      let behindCamera = false
      for (const corner of target.corners) {
        scratch.corner.copy(corner).applyMatrix4(root.current.matrixWorld)
        scratch.facing.subVectors(scratch.corner, scratch.camera)
        if (scratch.facing.dot(scratch.direction) <= camera.near) { behindCamera = true;break }
        scratch.corner.project(camera)
        minX = Math.min(minX, scratch.corner.x);maxX = Math.max(maxX, scratch.corner.x)
        minY = Math.min(minY, scratch.corner.y);maxY = Math.max(maxY, scratch.corner.y)
      }
      if (behindCamera) continue
      const toleranceX = 2 * Math.min(44, size.width * .055) / size.width
      const toleranceY = 2 * Math.min(44, size.height * .055) / size.height
      const pointing = hovered === target.id && pointer.x >= minX && pointer.x <= maxX && pointer.y >= minY && pointer.y <= maxY
      const labelHeld = held.current === target.id
      const centred = minX <= toleranceX && maxX >= -toleranceX && minY <= toleranceY && maxY >= -toleranceY
      if (!pointing && !labelHeld && !centred) continue
      const rank = score + (pointing || labelHeld ? 0 : 2)
      if (rank >= best) continue

      // A rear-wall label must not appear through the AT-AT or another card.
      const distance = scratch.center.distanceTo(scratch.camera)
      scratch.raycaster.set(scratch.camera, scratch.facing.subVectors(scratch.center, scratch.camera).normalize())
      scratch.raycaster.near = camera.near
      scratch.raycaster.far = Math.max(camera.near, distance - .05)
      scratch.hits.length = 0
      scratch.raycaster.intersectObjects(resources.occluders, false, scratch.hits)
      if (scratch.hits.length) continue
      next = target.id
      best = rank
    }
    if (next !== selected.current) { selected.current = next;setFocused(next) }
  }, -.25)

  const hold = (id: string) => { held.current = id;dirty.current = true;invalidate() }
  const release = (event: SyntheticEvent<HTMLButtonElement>) => {
    if (event.currentTarget.matches(':hover, :focus')) return
    held.current = null;dirty.current = true;invalidate()
  }
  return <group ref={root} name="skills-gallery-target-hints">
    {enabled && resources.targets.filter(target => target.id === focused).map(target => <group key={target.id}>
      <lineSegments geometry={target.geometry} renderOrder={8} raycast={() => null}>
        <lineBasicMaterial color="#ffffff" transparent opacity={.85} depthWrite={false} depthTest={false} toneMapped={false} />
      </lineSegments>
      <Html position={target.center.toArray()} calculatePosition={screenOrigin} zIndexRange={[20, 10]}
        className="skills-target-dock" style={{ pointerEvents: 'none', width: size.width, height: size.height }}>
        <button className="about-target-label skills-target-label" data-sound-effect="environment" data-target={target.id}
          aria-label={`Focus ${target.title} skill card`} onPointerEnter={() => hold(target.id)} onPointerLeave={release}
          onFocus={() => hold(target.id)} onBlur={release} onClick={() => onInteract(target.id, 'label')}>
          <span className="about-target-title">{target.title}</span>
          <span className="about-target-action">Focus skill card <span aria-hidden="true">↗</span></span>
        </button>
      </Html>
    </group>)}
  </group>
}
