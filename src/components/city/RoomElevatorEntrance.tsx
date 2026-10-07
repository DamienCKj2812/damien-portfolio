/* eslint react-hooks/immutability: "off" -- The entrance projects its label using mutable Three.js resources on existing camera frames. */
import { useEffect, useMemo, useRef, useState } from 'react'
import { useFrame, useThree } from '@react-three/fiber'
import type { ThreeEvent } from '@react-three/fiber'
import { Html } from '@react-three/drei'
import { BufferGeometry, DoubleSide, Float32BufferAttribute, Vector3 } from 'three'
import './roomElevatorEntrance.css'
import './aboutOfficeTargets.css'
import useSoundEffects from '../../audio/useSoundEffects'
import type { RefObject } from 'react'
import type { Group } from 'three'
import type { Vec3 } from '../../types/scene'
import type { NavigationState } from '../../types/navigation'

export interface RoomElevatorEntranceProps {
  entrance: Vec3; active: boolean; interactive: boolean; navigationRef: RefObject<NavigationState>; onReturn: () => void
}

const CALL_PANEL: Vec3 = [-1.58, .125, 1.55]
const CALL_CORNERS = Array.from({ length: 8 }, (_, index) => new Vector3(
  CALL_PANEL[0] + (index & 1 ? .21 : -.21),
  CALL_PANEL[1] + (index & 2 ? .09 : -.09),
  CALL_PANEL[2] + (index & 4 ? .30 : -.30),
))

export default function RoomElevatorEntrance({ entrance, active, interactive, navigationRef, onReturn }: RoomElevatorEntranceProps) {
  const { environmentClick: playClick } = useSoundEffects()
  const root = useRef<Group>(null)
  const labelVisible = useRef(false)
  const [showLabel, setShowLabel] = useState(false)
  const { camera, size, invalidate } = useThree()
  const scratch = useMemo(() => new Vector3(), [])
  const outline = useMemo(() => {
    const paths: [Vec3, ...Vec3[]][] = [
      [[-1.30, .105, 0], [-1.30, .105, 3.20], [1.30, .105, 3.20], [1.30, .105, 0]],
      [[-1.20, .121, .05], [-1.20, .121, 3.12], [1.20, .121, 3.12], [1.20, .121, .05]],
      [[0, .107, 0], [0, .107, 3.20]],
    ]
    const points = paths.flatMap(path => {
      let previous = path[0]
      return path.slice(1).flatMap(point => {
        const segment = [...previous, ...point]
        previous = point
        return segment
      })
    })
    return new BufferGeometry().setAttribute('position', new Float32BufferAttribute(points, 3))
  }, [])
  const callOutline = useMemo(() => {
    const points: number[] = []
    for (const x of [-1, 1]) {
      for (const z of [-1, 1]) {
        const corner: Vec3 = [CALL_PANEL[0] + x * .18, .15, CALL_PANEL[2] + z * .27]
        points.push(...corner, corner[0] - x * .07, corner[1], corner[2])
        points.push(...corner, corner[0], corner[1], corner[2] - z * .09)
      }
    }
    return new BufferGeometry().setAttribute('position', new Float32BufferAttribute(points, 3))
  }, [])
  useEffect(() => () => { outline.dispose();callOutline.dispose() }, [outline, callOutline])
  useEffect(() => {
    if (!interactive) document.body.style.cursor = ''
    invalidate()
  }, [active, interactive, entrance, invalidate])

  useFrame(() => {
    let next = false
    if (active && interactive && root.current && !document.hidden) {
      root.current.updateWorldMatrix(true, false)
      scratch.copy(camera.position);root.current.worldToLocal(scratch)
      const insideRoom = scratch.y > .12
      scratch.fromArray(CALL_PANEL).applyMatrix4(root.current.matrixWorld).project(camera)
      if (insideRoom && scratch.z >= -1 && scratch.z <= 1 && Math.abs(scratch.y) < .95) {
        let minX = Infinity, maxX = -Infinity
        for (const corner of CALL_CORNERS) {
          scratch.copy(corner).applyMatrix4(root.current.matrixWorld).project(camera)
          minX = Math.min(minX, scratch.x);maxX = Math.max(maxX, scratch.x)
        }
        const tolerance = 2 * Math.min(44, size.width * .055) / size.width
        next = minX <= tolerance && maxX >= -tolerance
      }
    }
    if (next !== labelVisible.current) { labelVisible.current = next;setShowLabel(next) }
  }, -.25)

  return <group ref={root} name="room-elevator-entrance" position={entrance} visible={active}>
    <mesh position={[0, 0, 1.60]} raycast={() => null}>
      <boxGeometry args={[2.42, .14, 3.22]} />
      <meshBasicMaterial color="#080808" toneMapped={false} />
    </mesh>
    {[-1, 1].map(side => <mesh key={side} name={`room-elevator-door-${side}`} position={[side * .60, .077, 1.60]} raycast={() => null}>
      <boxGeometry args={[1.199, .04, 3.22]} />
      <meshBasicMaterial color="#151515" toneMapped={false} />
    </mesh>)}
    {[-1, 1].map(side => <mesh key={`jamb-${side}`} position={[side * 1.25, .06, 1.60]} raycast={() => null}>
      <boxGeometry args={[.10, .11, 3.22]} />
      <meshBasicMaterial color="#444444" toneMapped={false} />
    </mesh>)}
    <mesh position={[0, .06, 3.17]} raycast={() => null}>
      <boxGeometry args={[2.60, .11, .10]} />
      <meshBasicMaterial color="#444444" toneMapped={false} />
    </mesh>
    <mesh position={[0, .06, .02]} raycast={() => null}>
      <boxGeometry args={[2.60, .11, .06]} />
      <meshBasicMaterial color="#333333" toneMapped={false} />
    </mesh>
    <lineSegments geometry={outline} raycast={() => null} renderOrder={3}>
      <lineBasicMaterial color="#d2d2d2" toneMapped={false} />
    </lineSegments>
    <mesh position={[-1.58, .075, 1.55]} raycast={() => null}>
      <boxGeometry args={[.28, .05, .45]} />
      <meshBasicMaterial color="#555555" toneMapped={false} />
    </mesh>
    <mesh position={[-1.58, .112, 1.55]} raycast={() => null}>
      <sphereGeometry args={[.035, 16, 12]} />
      <meshBasicMaterial color="#eeeeee" toneMapped={false} />
    </mesh>
    <mesh name="room-elevator-return-pick" position={[0, .10, 1.60]}
      {...(interactive ? {
        onClick: (event: ThreeEvent<MouseEvent>) => { event.stopPropagation();if (event.delta <= 5 && navigationRef.current.dragDistance <= 5) { playClick();onReturn() } },
        onPointerOver: (event: ThreeEvent<PointerEvent>) => { event.stopPropagation();document.body.style.cursor = 'pointer' },
        onPointerOut: () => { document.body.style.cursor = '' },
      } : {})}>
      <boxGeometry args={[2.62, .24, 3.22]} />
      <meshBasicMaterial transparent opacity={0} depthWrite={false} side={DoubleSide} />
    </mesh>
    <mesh name="room-elevator-call-pick" position={CALL_PANEL}
      {...(interactive ? {
        onClick: (event: ThreeEvent<MouseEvent>) => { event.stopPropagation();if (event.delta <= 5 && navigationRef.current.dragDistance <= 5) { playClick();onReturn() } },
        onPointerOver: (event: ThreeEvent<PointerEvent>) => { event.stopPropagation();document.body.style.cursor = 'pointer' },
        onPointerOut: () => { document.body.style.cursor = '' },
      } : {})}>
      <boxGeometry args={[.84, .24, 1.00]} />
      <meshBasicMaterial transparent opacity={0} depthWrite={false} side={DoubleSide} />
    </mesh>
    {showLabel && interactive && <lineSegments geometry={callOutline} raycast={() => null} renderOrder={8}>
      <lineBasicMaterial color="#ffffff" transparent opacity={.85} depthWrite={false} depthTest={false} toneMapped={false} />
    </lineSegments>}
    <Html position={[CALL_PANEL[0], CALL_PANEL[1] + .02, CALL_PANEL[2] + .45]} center zIndexRange={[20, 10]} style={{ pointerEvents: 'none' }}>
      <button className="about-target-label room-elevator-label" data-sound-effect="environment" hidden={!showLabel || !active || !interactive} disabled={!interactive}
        aria-label="Return to elevator" title="Return to the elevator and choose another floor" onClick={onReturn}>
        <span className="about-target-title">ELEVATOR</span>
        <span className="about-target-action">Return to elevator <span aria-hidden="true">↗</span></span>
      </button>
    </Html>
  </group>
}
