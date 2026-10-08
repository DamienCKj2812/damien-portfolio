/* eslint react-hooks/immutability: "off" -- Three.js cameras and GPU materials are intentionally mutable scene resources, not React state. */
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { useFrame, useThree } from '@react-three/fiber'
import type { ThreeEvent } from '@react-three/fiber'
import { DoubleSide, Material, MathUtils, Matrix4, MeshBasicMaterial, PerspectiveCamera, Quaternion, ShaderMaterial, Vector3, Vector4 } from 'three'
import type { BufferGeometry, Group, IUniform } from 'three'
import type { RefObject } from 'react'
import { LineSegmentsGeometry } from 'three/addons/lines/LineSegmentsGeometry.js'
import { LineMaterial } from 'three/addons/lines/LineMaterial.js'
import { LineSegments2 } from 'three/addons/lines/LineSegments2.js'
import { createCityGeometries, createSceneShaderMaterial } from './cityAssets'
import { createPoseScratch, readCameraPose, readPose } from './journeyTimeline'
import { advanceCameraSpring, interpolateCameraBridge } from './cameraMotion'
import { createRoomAlignment, sampleMorphWeights } from './roomJourney'
import RoomNavigator from './RoomNavigator'
import type { RoomNavigatorProps } from './RoomNavigator'
import RoomReturnJourney from './RoomReturnJourney'
import type { RoomReturnJourneyProps } from './RoomReturnJourney'
import { ELEVATOR_PLAYBACK_RATE } from './elevatorTiming'
import ElevatorButton from './ElevatorButton'
import AboutOfficeTargets from './AboutOfficeTargets'
import OfficePrinter from './OfficePrinter'
import ContactCardDismiss from './ContactCardDismiss'
import SkillsGalleryTargets from './SkillsGalleryTargets'
import ProjectVideoBoards from './ProjectVideoBoards'
import RoomElevatorEntrance from './RoomElevatorEntrance'
import useCityActorClock from './useCityActorClock'
import { isAutonomousCityActor, sampleCityActorMotion } from './cityActorMotion'
import ReflectiveFloor from './ReflectiveFloor'
import type { ReflectiveFloorProps } from './ReflectiveFloor'
import CityShootingStars from './CityShootingStars'
import useSoundEffects from '../../audio/useSoundEffects'
import { createLobbyPortalClip, updateLobbyPortalClip } from './lobbyPortal'
import { isElevatorManifest, isLobbyManifest } from '../../types/sceneValidation'
import type { CityManifest, ElevatorManifest, JourneyConfig, LevelId, LoadedRoomAssets, LoadedSceneAssets, LobbyManifest, SceneGeometry, Vec3 } from '../../types/scene'
import type { CityActorMotion, ElevatorState, NavigationState, RoomAlignment, RoomState, RoomView } from '../../types/navigation'

export interface CitySceneProps {
  assets: LoadedSceneAssets<CityManifest>; lobbyAssets: LoadedSceneAssets<LobbyManifest> | null
  elevatorAssets: LoadedSceneAssets<ElevatorManifest> | null; elevatorState: ElevatorState
  focusedLevel: LevelId | null; pressedLevel: LevelId | null; roomAssets: LoadedRoomAssets | null
  roomState: RoomState; navigationRef: RefObject<NavigationState>; journey: JourneyConfig; progress: number; reducedMotion: boolean
  onFrame: (frame: number) => void; onSelectLevel: (level: LevelId) => void; onElevatorFrame: (frame: number) => void
  onRoomFrame: RoomNavigatorProps['onFrame']; onRoomInteract: (id: string, source?: 'label' | 'scene') => void
  onArrival: () => void; onCancel: () => void; onRoomView: (view: RoomView) => void
  onToggleWalk: () => void; onSeekTour: RoomNavigatorProps['onSeekTour']; onStation: RoomNavigatorProps['onStation']
  onTourEnd: () => void; onRequestReturn: () => void; onEnterElevator: () => void
  onReturnProgress: RoomReturnJourneyProps['onProgress']; onReturnComplete: () => void
}
interface JourneyCameraProps {
  city: CitySceneProps['assets']; lobby: CitySceneProps['lobbyAssets']; elevator: CitySceneProps['elevatorAssets']
  elevatorState: ElevatorState; roomAssets: LoadedRoomAssets | null; roomAlignment: RoomAlignment | null
  journey: JourneyConfig; progress: number; reducedMotion: boolean; frameRef: RefObject<number>; elevatorFrameRef: RefObject<number>
  onFrame: CitySceneProps['onFrame']; onElevatorFrame: CitySceneProps['onElevatorFrame']; onArrival: () => void; onCancel: () => void
}
interface PointUniforms {
  viewportHeight: IUniform<number>; walkBlend: IUniform<number>; walkPhase: IUniform<number>; shapeWeights: IUniform<Vector4>
  sky: IUniform<number>; shine: IUniform<number>; twinkleTime: IUniform<number>; twinkleEnabled: IUniform<number>
}
type PointMaterial = ShaderMaterial & { uniforms: PointUniforms }
type OpacityMaterial = ShaderMaterial & { uniforms: { opacity: IUniform<number> } }
interface ZoneMaterials {
  points: PointMaterial; sky: PointMaterial; starShine: PointMaterial; walkers: Record<number, PointMaterial>
  lines: ShaderMaterial; outline: LineMaterial; glowWide: LineMaterial; glowNear: LineMaterial; glowCore: LineMaterial
  screens: Record<string, MeshBasicMaterial>; solid: ShaderMaterial; selectedButton: MeshBasicMaterial
  disabledButton: MeshBasicMaterial; pick: MeshBasicMaterial; translucent: Record<number, OpacityMaterial>
  portalVeils: Record<string, OpacityMaterial>; mask: MeshBasicMaterial
}
interface DrawGroupProps {
  item: SceneGeometry; materials: ZoneMaterials; selectedLevel?: LevelId | null | undefined; interactive?: boolean | undefined; cardFocused?: boolean | undefined
  onSelect?: CitySceneProps['onSelectLevel'] | undefined; onInteract?: CitySceneProps['onRoomInteract'] | undefined; onHover?: ((id: string | null) => void) | undefined
}

function materialFromRegistry<M extends Material>(registry: Record<string, M>, key: string | number): M {
  const material = registry[key]
  if (!material) throw new Error(`Missing authored scene material: ${key}`)
  return material
}
interface ZoneGeometryProps {
  assets: LoadedSceneAssets; frameRef: RefObject<number>; elevatorFrameRef?: RefObject<number>; roomFrameRef?: RefObject<number>
  destinationActive?: boolean; connectedRoom?: boolean; reducedMotion: boolean; journey: JourneyConfig
  zone: 'city' | 'lobby' | 'elevator' | `room-${LevelId}`; offset?: Vec3; rotation?: Vec3
  selectedLevel?: LevelId | null; focusedLevel?: LevelId | null; pressedLevel?: LevelId | null
  interactive?: boolean; showTargets?: boolean; cardFocused?: boolean; entryClosed?: boolean
  onSelect?: CitySceneProps['onSelectLevel']; onInteract?: CitySceneProps['onRoomInteract']; onView?: CitySceneProps['onRoomView']
  navigationRef?: RefObject<NavigationState>; projectFocused?: boolean; roomState?: RoomState; roomArrived?: boolean
}

const BASIS = new Quaternion().setFromAxisAngle(new Vector3(1, 0, 0), -Math.PI / 2)
const pointVertex = `
  #include <clipping_planes_pars_vertex>
  attribute float radius;
  attribute float luminance;
  attribute vec3 shape0;
  attribute vec3 shape1;
  attribute vec3 shape2;
  attribute vec3 shape3;
  uniform vec4 shapeWeights;
  uniform float viewportHeight;
  uniform float walkBlend;
  uniform float walkPhase;
  uniform float sky;
  uniform float shine;
  uniform float twinkleTime;
  uniform float twinkleEnabled;
  varying float brightness;
  varying float coverage;
  void main() {
    vec3 animatedPosition = position + shape0 * shapeWeights.x + shape1 * shapeWeights.y + shape2 * shapeWeights.z + shape3 * shapeWeights.w;
    if (walkBlend > 0.0) {
      float side = position.x < 0.0 ? -1.0 : 1.0;
      float leg = pow(clamp(1.0 - position.z / 1.1, 0.0, 1.0), 1.4);
      float swing = sin(walkPhase + (side < 0.0 ? 3.14159265 : 0.0));
      animatedPosition.y += swing * leg * 0.16 * walkBlend;
      animatedPosition.z += max(0.0, swing) * leg * 0.045 * walkBlend;
      float arm = smoothstep(0.17, 0.27, abs(position.x)) * smoothstep(0.6, 0.9, position.z) * (1.0 - smoothstep(1.3, 1.75, position.z));
      animatedPosition.y -= swing * arm * 0.09 * walkBlend;
    }
    vec4 view = modelViewMatrix * vec4(animatedPosition, 1.0);
    vec4 mvPosition = view;
    #include <clipping_planes_vertex>
    float scale = max(length(modelMatrix[0].xyz), max(length(modelMatrix[1].xyz), length(modelMatrix[2].xyz)));
    float diameter = 2.0 * radius * scale * viewportHeight * projectionMatrix[1][1] / max(0.01, -view.z);
    brightness = luminance;
    if (sky > 0.5) {
      float seed = fract(sin(dot(position, vec3(12.9898, 78.233, 37.719))) * 43758.5453);
      float speed = mix(0.6, 1.7, fract(seed * 13.37));
      float pulse = pow(0.5 + 0.5 * sin(twinkleTime * speed + seed * 6.283185), mix(2.0, 6.0, fract(seed * 7.91)));
      brightness *= (0.55 + seed * 0.9) * mix(1.0, 0.22 + pulse * 1.78, twinkleEnabled);
      diameter *= 0.75 + fract(seed * 5.73) * 0.8;
    }
    gl_PointSize = clamp(diameter, 1.0, shine > 0.5 ? 192.0 : 14.0);
    coverage = clamp(diameter * diameter, 0.035, 1.0);
    gl_Position = projectionMatrix * view;
  }
`
const pointFragment = `
  #include <clipping_planes_pars_fragment>
  varying float brightness;
  varying float coverage;
  void main() {
    #include <clipping_planes_fragment>
    float distanceToCenter = length(gl_PointCoord - vec2(0.5)) * 2.0;
    float alpha = (1.0 - smoothstep(0.55, 1.0, distanceToCenter)) * coverage;
    if (alpha < 0.005) discard;
    gl_FragColor = vec4(vec3(brightness), alpha);
    #include <colorspace_fragment>
  }
`
const starShineFragment = `
  #include <clipping_planes_pars_fragment>
  varying float brightness;
  void main() {
    #include <clipping_planes_fragment>
    vec2 p = (gl_PointCoord - vec2(0.5)) * 2.0;
    float r2 = dot(p, p);
    float core = exp(-r2 / 0.00045);
    float halo = exp(-r2 / 0.009) * 0.14;
    float vertical = exp(-abs(p.x) * 180.0 - abs(p.y) * 6.0) * 0.24;
    float horizontal = exp(-abs(p.y) * 180.0 - abs(p.x) * 19.0) * 0.22;
    float fade = 1.0 - smoothstep(0.65, 0.98, length(p));
    float alpha = clamp((core + halo + vertical + horizontal) * fade, 0.0, 1.0);
    if (alpha < 0.001) discard;
    gl_FragColor = vec4(vec3(brightness), alpha);
    #include <colorspace_fragment>
  }
`
const lineVertex = `
  #include <clipping_planes_pars_vertex>
  attribute float luminance;
  varying float brightness;
  void main() {
    brightness = luminance;
    vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
    gl_Position = projectionMatrix * mvPosition;
    #include <clipping_planes_vertex>
  }
`
const lineFragment = `
  #include <clipping_planes_pars_fragment>
  varying float brightness;
  void main() {
    #include <clipping_planes_fragment>
    gl_FragColor = vec4(vec3(brightness), 1.0);
    #include <colorspace_fragment>
  }
`
const transparentFragment = `
  #include <clipping_planes_pars_fragment>
  varying float brightness;
  uniform float opacity;
  void main() {
    #include <clipping_planes_fragment>
    gl_FragColor = vec4(vec3(brightness), opacity);
    #include <colorspace_fragment>
  }
`

function VehicleOutline({ geometry, material, order = 3 }: { geometry: BufferGeometry; material: LineMaterial; order?: number }) {
  const object = useMemo(() => {
    if (!(geometry instanceof LineSegmentsGeometry)) throw new Error('An authored outline requires line-segment geometry.')
    return new LineSegments2(geometry, material)
  }, [geometry, material])
  object.renderOrder = order
  return <primitive object={object} dispose={null} />
}

function DrawGroup({ item, materials, selectedLevel, interactive, cardFocused, onSelect, onInteract, onHover }: DrawGroupProps) {
  const { environmentClick: playClick } = useSoundEffects()
  if (item.kind === 'points') return <points {...(item.role === 'sky-shine' ? { name: 'city-star-optical-shine' } : item.role === 'sky' ? { name: 'city-sky-dots' } : {})} geometry={item.geometry} material={item.role === 'sky-shine' ? materials.starShine : item.role === 'sky' ? materials.sky : materials.walkers[item.actor] || materials.points} renderOrder={2}
    {...(interactive && item.role === 'exhibit' ? {
      onClick: (event: ThreeEvent<MouseEvent>) => { event.stopPropagation();if (event.delta <= 5 && item.id) onInteract?.(item.id) },
      onPointerOver: (event: ThreeEvent<PointerEvent>) => { event.stopPropagation();document.body.style.cursor = 'pointer' },
      onPointerOut: () => { document.body.style.cursor = '' },
    } : {})}
  />
  if (item.kind === 'lines') return <lineSegments geometry={item.geometry} material={materials.lines} renderOrder={1} />
  if (item.kind === 'outline') return <VehicleOutline geometry={item.geometry} material={materials.outline} />
  if (item.kind === 'glow') return <>
    <VehicleOutline geometry={item.geometry} material={materials.glowWide} order={4} />
    <VehicleOutline geometry={item.geometry} material={materials.glowNear} order={5} />
    <VehicleOutline geometry={item.geometry} material={materials.glowCore} order={6} />
  </>
  if (item.kind === 'screen') {
    const material = materials.screens[item.texture ?? '']
    return <mesh geometry={item.geometry} {...(material ? { material } : {})} renderOrder={0} />
  }
  if (item.kind === 'solid') {
    const button = item.role === 'button'
    const clickable = interactive && (item.role === 'contactLinkPick' ? cardFocused : cardFocused && ['contact', 'contactPick'].includes(item.role ?? '') ? false : button ? item.available !== false : ['contact', 'contactPick', 'observerPick', 'project', 'directory', 'exhibit', 'exhibitPick'].includes(item.role ?? ''))
    const opacity = item.opacity ?? 1
    const material = ['contactPick', 'contactLinkPick', 'observerPick', 'exhibitPick'].includes(item.role ?? '') ? materials.pick : button && item.available === false ? materials.disabledButton : button && item.level === selectedLevel ? materials.selectedButton : item.role === 'categoryCurtain' && opacity < 1 ? materialFromRegistry(materials.portalVeils, `${item.id}:${item.opacity}`) : opacity < 1 ? materialFromRegistry(materials.translucent, opacity) : materials.solid
    return <mesh {...(item.role === 'observerPick' ? { name: 'about-observer-profile-pick' } : item.role === 'contactPick' ? { name: 'about-contact-card-pick' } : item.role === 'officeDoor' ? { name: 'about-office-entry-panels' } : {})} geometry={item.geometry} material={material} renderOrder={opacity < 1 ? 2 : 0}
      {...(clickable ? {
        onClick: (event: ThreeEvent<MouseEvent>) => { event.stopPropagation();if (event.delta > 5) return;if (button && item.level && onSelect) { playClick();onSelect(item.level) } else if (item.id) onInteract?.(item.id) },
        onPointerOver: (event: ThreeEvent<PointerEvent>) => { event.stopPropagation();document.body.style.cursor = 'pointer';onHover?.(item.id ?? null) },
        onPointerOut: () => { document.body.style.cursor = '';onHover?.(null) },
      } : {})}
    />
  }
  return <mesh geometry={item.geometry} material={materials.mask} renderOrder={-1} />
}

function JourneyCamera({ city, lobby, elevator, elevatorState, roomAssets, roomAlignment, journey, progress, reducedMotion, frameRef, elevatorFrameRef, onFrame, onElevatorFrame, onArrival, onCancel }: JourneyCameraProps) {
  const { camera, size, invalidate } = useThree()
  const current = useRef(progress * (journey.frameEnd - 1) + 1)
  const entrySpring = useRef({ value: progress * (journey.frameEnd - 1) + 1, velocity: 0 })
  const scratch = useMemo(() => ({ ...createPoseScratch(), walkStart: new Vector3(), walkRotation: new Quaternion() }), [])
  const offset = useMemo(() => new Vector3().fromArray(journey.lobbyOffset), [journey])
  const cabinOffset = useMemo(() => new Vector3().fromArray(journey.elevatorOffset || [0, 0, 0]), [journey])
  const panelAim = useMemo(() => ({ target: new Vector3(1.253, 1.42, 1.91).add(cabinOffset), matrix: new Matrix4(), quaternion: new Quaternion(), up: new Vector3(0, 0, 1) }), [cabinOffset])
  const departure = useRef(181)
  const departureTarget = useRef(181)
  const departureSpring = useRef({ value: 181, velocity: 0 })
  const arrivalSent = useRef(false)
  const cancelSent = useRef(false)
  const lastReported = useRef(0)
  useEffect(() => {
    departure.current = 181;arrivalSent.current = false;cancelSent.current = false;lastReported.current = 0;invalidate()
    departureTarget.current = 181;departureSpring.current.value = 181;departureSpring.current.velocity = 0
  }, [elevatorState.run, invalidate])
  useEffect(() => { invalidate() }, [progress, lobby, elevator, roomAssets, elevatorState.status, size.width, size.height, invalidate])
  useFrame((_, delta) => {
    if (!(camera instanceof PerspectiveCamera)) return
    const requested = progress * (journey.frameEnd - 1) + 1
    const holdFrame = journey.lobbyHoldFrame ?? journey.bookmarks.doors
    // Never render an open portal before its interior is available, including
    // a direct jump while the Canvas is still mounting/loading.
    if (!lobby) current.current = Math.min(current.current, holdFrame)
    let target = lobby ? requested : Math.min(requested, holdFrame)
    if (lobby && !elevator && journey.elevatorHoldFrame) {
      current.current = Math.min(current.current, journey.elevatorHoldFrame)
      target = Math.min(target, journey.elevatorHoldFrame)
    }
    const dt = Math.min(delta, .1)
    let next
    if (reducedMotion) { next = target;entrySpring.current.value = target;entrySpring.current.velocity = 0 }
    else if (current.current > journey.lobbyGlobalEnd) {
      next = MathUtils.clamp(advanceCameraSpring(entrySpring.current, target, delta, 28), 1, journey.frameEnd)
      if (next !== entrySpring.current.value) { entrySpring.current.value = next;entrySpring.current.velocity = 0 }
    } else {
      next = MathUtils.damp(current.current, target, 18, dt)
      entrySpring.current.value = next;entrySpring.current.velocity = dt > 0 ? (next - current.current) / dt : 0
    }
    current.current = Math.abs(next - target) < .02 ? target : next
    if (current.current === target) { entrySpring.current.value = target;entrySpring.current.velocity = 0 }
    if (current.current !== target) invalidate()
    const frame = current.current
    frameRef.current = frame
    if (elevatorState.status === 'returning') { onFrame(frame);return }
    let fov
    let cabinFrame = Math.max(journey.elevatorEntryStart || 1, (journey.elevatorEntryStart || 1) + frame - (journey.lobbyGlobalEnd || journey.frameEnd))
    const departing = elevator && ['departing', 'arrived'].includes(elevatorState.status)
    if (departing && requested < journey.frameEnd - 3 && !cancelSent.current) { cancelSent.current = true;onCancel() }
    if (departing && !cancelSent.current) {
      if (elevatorState.status === 'departing') {
        const limit = elevatorState.level && journey.rooms[elevatorState.level] && !roomAssets ? 296 : 510
        departureTarget.current = reducedMotion ? limit : Math.min(limit, departureTarget.current + Math.min(delta, .1) * 30 * ELEVATOR_PLAYBACK_RATE)
        if (reducedMotion) { departureSpring.current.value = limit;departureSpring.current.velocity = 0 }
        departure.current = reducedMotion ? limit : MathUtils.clamp(advanceCameraSpring(departureSpring.current, departureTarget.current, delta, 32), 181, limit)
        if (departure.current < limit) invalidate()
        else if (limit === 510 && !arrivalSent.current) { arrivalSent.current = true;onArrival() }
      }
      cabinFrame = elevatorState.status === 'arrived' ? 510 : departure.current
      if (Math.floor(cabinFrame) - lastReported.current >= 3 || [296, 510].includes(cabinFrame) && cabinFrame !== lastReported.current) { lastReported.current = Math.floor(cabinFrame);onElevatorFrame(cabinFrame) }
    }
    elevatorFrameRef.current = cabinFrame
    if (elevator && (frame > journey.lobbyGlobalEnd || departing)) {
      fov = readCameraPose(elevator, cabinFrame, scratch.position, scratch.quaternion).fov
      scratch.position.add(cabinOffset)
      // The portrait view needs to face the operating panel directly. Ease the
      // extra aim in at selection and out during the authored departure turn.
      const portrait = MathUtils.smoothstep(size.height / Math.max(1, size.width), 1.05, 1.65)
      const panelBlend = portrait * MathUtils.smoothstep(cabinFrame, 156, 180) * (1 - MathUtils.smoothstep(cabinFrame, 221, 268))
      if (panelBlend > 0) {
        panelAim.matrix.lookAt(scratch.position, panelAim.target, panelAim.up)
        scratch.quaternion.slerp(panelAim.quaternion.setFromRotationMatrix(panelAim.matrix), panelBlend)
      }
      if (departing && roomAlignment && cabinFrame >= 360) {
        const startFov = readCameraPose(elevator, 414, scratch.bridgePosition, scratch.bridgeQuaternion).fov
        scratch.bridgePosition.add(cabinOffset)
        readCameraPose(elevator, 360, scratch.walkStart, scratch.walkRotation)
        scratch.walkStart.add(cabinOffset)
        const destination = roomAlignment.poses.main
        scratch.position.set(
          interpolateCameraBridge(scratch.walkStart.x, scratch.bridgePosition.x, destination.position.x, cabinFrame - 360),
          interpolateCameraBridge(scratch.walkStart.y, scratch.bridgePosition.y, destination.position.y, cabinFrame - 360),
          interpolateCameraBridge(scratch.walkStart.z, scratch.bridgePosition.z, destination.position.z, cabinFrame - 360),
        )
        if (cabinFrame >= 414) {
          const t = MathUtils.smootherstep((cabinFrame - 414) / 96, 0, 1)
          scratch.quaternion.copy(scratch.bridgeQuaternion).slerp(destination.quaternion, t)
          fov = MathUtils.lerp(startFov, destination.fov, t)
        }
      }
      if (!departing && lobby && frame - journey.lobbyGlobalEnd <= journey.elevatorTransitionFrames) {
        const lobbyFov = readPose(lobby, lobby.manifest.frameEnd, 0, scratch.bridgePosition, scratch.bridgeQuaternion).fov
        scratch.bridgePosition.add(offset)
        scratch.position.y = Math.max(scratch.position.y, scratch.bridgePosition.y)
        const t = MathUtils.smoothstep((frame - journey.lobbyGlobalEnd) / journey.elevatorTransitionFrames, 0, 1)
        scratch.position.lerpVectors(scratch.bridgePosition, scratch.position, t);scratch.quaternion.copy(scratch.bridgeQuaternion.slerp(scratch.quaternion, t));fov = MathUtils.lerp(lobbyFov, fov, t)
      }
    } else if (frame <= journey.cityEnd || !lobby) {
      fov = readPose(city, Math.min(frame, journey.cityEnd), 0, scratch.position, scratch.quaternion).fov
    } else {
      const local = frame - journey.cityEnd
      fov = readPose(lobby, local, 0, scratch.position, scratch.quaternion).fov
      scratch.position.add(offset)
      if (local <= journey.transitionFrames) {
        const cityFov = readPose(city, journey.cityEnd, 0, scratch.bridgePosition, scratch.bridgeQuaternion).fov
        const t = MathUtils.smoothstep(local / journey.transitionFrames, 0, 1)
        scratch.position.lerpVectors(scratch.bridgePosition, scratch.position, t)
        scratch.quaternion.copy(scratch.bridgeQuaternion.slerp(scratch.quaternion, t))
        fov = MathUtils.lerp(cityFov, fov, t)
      }
    }
    if (roomAssets && elevatorState.status === 'arrived' && !cancelSent.current) { onFrame(frame);return }
    camera.position.copy(scratch.position).applyQuaternion(BASIS)
    camera.quaternion.copy(BASIS).multiply(scratch.quaternion)
    const aspect = size.width / Math.max(1, size.height)
    const adjusted = Math.min(85, MathUtils.radToDeg(2 * Math.atan(Math.tan(MathUtils.degToRad(fov) / 2) * Math.max(1, 1.6 / aspect))))
    const near = roomAlignment && departing ? .01 : .05
    if (Math.abs(camera.fov - adjusted) > .001 || camera.near !== near) { camera.fov = adjusted; camera.near = near; camera.updateProjectionMatrix() }
    camera.updateMatrixWorld()
    onFrame(frame)
  }, -1)
  return null
}

function ZoneGeometry({ assets, frameRef, elevatorFrameRef, roomFrameRef, destinationActive, connectedRoom, reducedMotion, journey, zone, offset = [0, 0, 0], rotation = [0, 0, 0], selectedLevel, focusedLevel, pressedLevel, interactive, showTargets, cardFocused, entryClosed, onSelect, onInteract, onView, navigationRef, projectFocused, roomState, roomArrived }: ZoneGeometryProps) {
  const { gl, size, viewport, invalidate } = useThree()
  const root = useRef<Group>(null)
  const [hovered, setHovered] = useState<string | null>(null)
  const actors = useRef(new Map<number, Group>())
  const variants = useRef(new Map<number, Group>())
  const scratch = useMemo(() => ({ ...createPoseScratch(), turn: new Quaternion(), up: new Vector3(0, 0, 1), motion: { frame: 0, turn: 0, progress: 0, travel: 0, visible: false } satisfies CityActorMotion }), [])
  const cityClock = useCityActorClock({ enabled: zone === 'city', frameRef, journey, fps: assets.manifest.fps, reducedMotion })
  const lobbyLoopFrames = isLobbyManifest(assets.manifest) ? assets.manifest.autonomousLoopFrames ?? assets.manifest.npcLoopFrames : undefined
  const lobbyClock = useCityActorClock({ enabled: zone === 'lobby' && Boolean(lobbyLoopFrames), frameRef, journey, fps: assets.manifest.fps, reducedMotion, zone: 'lobby' })
  const groups = useMemo(() => createCityGeometries(assets), [assets])
  const printerItems = useMemo(() => groups.filter(item => item.role === 'printer'), [groups])
  const lobbyClip = useMemo(() => zone === 'lobby' && journey.lobbyPortal ? createLobbyPortalClip(journey.lobbyPortal, BASIS) : null, [zone, journey])
  const floors = useMemo<ReflectiveFloorProps[]>(() => {
    if (zone === 'city' && assets.manifest.level === undefined && assets.manifest.channelStride === 10 && assets.manifest.streetPlaza) return [
      { name: 'city-reflective-plaza', ...assets.manifest.streetPlaza.reflection },
    ]
    if (zone === 'lobby') return [
      { name: 'lobby-reflective-ground', width: 20, depth: 36.5, position: [0, 6.25, .003] },
      { name: 'lobby-reflective-upper-deck', width: 20, depth: 5.5, position: [0, 21.75, 6.123] },
    ]
    if (zone === 'room-skills') return [{ name: 'skills-reflective-ground', width: 12, depth: 16, position: [0, 1, .003] }]
    if (zone === 'room-projects' && assets.manifest.level === 'projects') {
      const length = assets.manifest.navigation.maxY + 3
      return [{ name: 'projects-reflective-ground', width: (journey.rooms.projects.width || 10.2) + .2, depth: length + 12, position: [0, length / 2 - 6, -.007], strength: .15 }]
    }
    if (zone === 'room-experience') return [{ name: 'experience-reflective-ground', radius: 12.5, position: [0, 0, .003], strength: .12 }]
    return []
  }, [zone, assets, journey])
  const switches = useMemo(() => (isElevatorManifest(assets.manifest) ? assets.manifest.levels : []).map(level => ({ level, items: groups.filter(item => item.level === level.id && ['button', 'buttonDetail'].includes(item.role ?? '')) })), [assets, groups])
  const materials = useMemo<ZoneMaterials>(() => {
    const points = createSceneShaderMaterial({ vertexShader: pointVertex, fragmentShader: pointFragment, transparent: true, depthWrite: false, toneMapped: false }, { viewportHeight: { value: 800 }, walkBlend: { value: 0 }, walkPhase: { value: 0 }, shapeWeights: { value: new Vector4() }, sky: { value: 0 }, shine: { value: 0 }, twinkleTime: { value: 0 }, twinkleEnabled: { value: 0 } })
    Object.assign(points.defaultAttributeValues, { shape0: [0, 0, 0], shape1: [0, 0, 0], shape2: [0, 0, 0], shape3: [0, 0, 0] })
    const sky = points.clone()
    sky.uniforms.sky.value = 1
    const starShine = points.clone()
    starShine.fragmentShader = starShineFragment
    starShine.uniforms.shine.value = 1
    return {
    points,
    sky,
    starShine,
    walkers: Object.fromEntries(assets.manifest.actors.filter((actor) => actor.walk || actor.morphCount).map((actor) => [actor.index, points.clone()])),
    lines: new ShaderMaterial({ vertexShader: lineVertex, fragmentShader: lineFragment, depthWrite: false, toneMapped: false }),
    outline: new LineMaterial({ color: 0xffffff, vertexColors: true, linewidth: 2, depthWrite: false, toneMapped: false }),
    glowWide: new LineMaterial({ color: 0xffffff, vertexColors: true, linewidth: 9, transparent: true, opacity: 0.075, depthWrite: false, toneMapped: false }),
    glowNear: new LineMaterial({ color: 0xffffff, vertexColors: true, linewidth: 4.5, transparent: true, opacity: 0.16, depthWrite: false, toneMapped: false }),
    glowCore: new LineMaterial({ color: 0xffffff, vertexColors: true, linewidth: 1.5, depthWrite: false, toneMapped: false }),
    screens: Object.fromEntries(Object.entries(assets.textures || {}).map(([file, texture]) => {
      const logo = groups.some(group => group.role === 'milestoneLogo' && group.texture === file)
      return [file, new MeshBasicMaterial({ map: texture, color: logo ? 0xffffff : 0xf4f4f4, side: DoubleSide, toneMapped: false, transparent: logo, alphaTest: logo ? .03 : 0, polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1 })]
    })),
    solid: new ShaderMaterial({ vertexShader: lineVertex, fragmentShader: lineFragment, side: DoubleSide, depthWrite: true, polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1, toneMapped: false }),
    selectedButton: new MeshBasicMaterial({ color: 0x777777, side: DoubleSide, toneMapped: false, polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -1 }),
    disabledButton: new MeshBasicMaterial({ color: 0x080808, side: DoubleSide, toneMapped: false }),
    pick: new MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false, side: DoubleSide }),
    translucent: Object.fromEntries(groups.filter((item) => (item.opacity ?? 1) < 1).map((item) => [item.opacity ?? 1, createSceneShaderMaterial({ vertexShader: lineVertex, fragmentShader: transparentFragment, transparent: true, depthWrite: false, side: DoubleSide, toneMapped: false }, { opacity: { value: item.opacity ?? 1 } })])),
    portalVeils: Object.fromEntries(groups.filter(item => item.role === 'categoryCurtain' && item.kind === 'solid' && (item.opacity ?? 1) < 1).map(item => [`${item.id}:${item.opacity}`, createSceneShaderMaterial({ vertexShader: lineVertex, fragmentShader: transparentFragment, transparent: true, depthWrite: false, side: DoubleSide, toneMapped: false }, { opacity: { value: item.opacity ?? 1 } })])),
    mask: new MeshBasicMaterial({ color: 0x000000, side: DoubleSide, toneMapped: false }),
    }
  }, [assets, groups])
  // Resolve static veil resources once. Frames reuse these references rather
  // than asserting a dynamic registry lookup during the camera update.
  const renderGroups = useMemo(() => groups.map(item => ({ item,
    veil: item.role === 'categoryCurtain' && item.kind === 'solid' && (item.opacity ?? 1) < 1
      ? materialFromRegistry(materials.portalVeils, `${item.id}:${item.opacity}`) : null,
  })), [groups, materials])
  useLayoutEffect(() => {
    if (!lobbyClip) return
    for (const value of Object.values(materials)) {
      for (const material of value instanceof Material ? [value] : Object.values(value)) {
        if (!(material instanceof Material)) continue
        if (material instanceof ShaderMaterial) material.clipping = true
        material.clippingPlanes = lobbyClip.planes
        material.needsUpdate = true
      }
    }
  }, [materials, lobbyClip])
  useLayoutEffect(() => {
    materials.points.uniforms.viewportHeight.value = size.height * gl.getPixelRatio()
    materials.sky.uniforms.viewportHeight.value = size.height * gl.getPixelRatio()
    materials.starShine.uniforms.viewportHeight.value = size.height * gl.getPixelRatio()
    for (const material of Object.values(materials.walkers)) material.uniforms.viewportHeight.value = size.height * gl.getPixelRatio()
    invalidate()
  }, [materials, gl, size.height, viewport.dpr, invalidate])
  useEffect(() => () => {
    for (const item of groups) item.geometry.dispose()
  }, [groups])
  useEffect(() => () => {
    for (const material of Object.values(materials)) {
      if (!(material instanceof Material)) for (const resource of Object.values(material)) { if (resource instanceof Material) resource.dispose() }
      else material.dispose()
    }
  }, [materials])
  useEffect(() => () => {
    for (const texture of Object.values(assets.textures || {})) texture.dispose()
  }, [assets])
  useEffect(() => () => { document.body.style.cursor = '' }, [])

  useFrame(({ camera }) => {
    const globalFrame = frameRef.current
    const active = zone.startsWith('room-') ? destinationActive : zone === 'city' ? globalFrame < (journey.cityHideFrame ?? journey.cityEnd) : zone === 'lobby' ? globalFrame >= journey.lobbyRevealFrame && globalFrame < (journey.lobbyHideFrame || Infinity) : globalFrame >= journey.elevatorRevealFrame
    if (root.current) root.current.visible = Boolean(active)
    if (!active) return
    if (lobbyClip) updateLobbyPortalClip(lobbyClip, camera.position, camera.near)
    if (zone === 'city') {
      materials.sky.uniforms.twinkleTime.value = cityClock.current / assets.manifest.fps
      materials.sky.uniforms.twinkleEnabled.value = reducedMotion ? 0 : 1
    }
    const frame = zone.startsWith('room-') ? roomFrameRef?.current ?? 1 : zone === 'city' ? globalFrame : zone === 'elevator' ? elevatorFrameRef?.current ?? 62 : Math.max(1, globalFrame - journey.cityEnd)
    for (const { item, veil } of renderGroups) {
      const object = variants.current.get(item.byteOffset)
      if (object) object.visible = (item.role !== 'officeDoor' || Boolean(entryClosed)) && (item.stage !== 'exit' || frame >= 181 && !connectedRoom) && (!connectedRoom || item.role !== 'destination') && (item.role === 'displayDefault' ? !selectedLevel : !item.level || item.role === 'button' || item.level === selectedLevel)
      if (object && zone==='room-skills' && projectFocused && item.id==='atat') object.visible=false
      if (object && item.role?.startsWith('category') && assets.manifest.level === 'projects' && navigationRef) {
        const category = assets.manifest.navigation.categories.find(category => category.id === item.id)
        if (!category?.door) continue
         // Show the portal from room entry, then clear its light field and
         // lettering around the camera so the passage remains unobstructed.
         const y = navigationRef.current.cameraPosition?.[1] ?? navigationRef.current.position?.[1] ?? navigationRef.current.y
         object.visible = true
         if (item.role === 'categoryCurtain' || item.role === 'categoryDoorLabel') object.visible = Math.abs(y-category.door.y) > 1.15
         if (veil) {
           object.visible = true
           veil.uniforms.opacity.value = (item.opacity ?? 1) * MathUtils.smoothstep(Math.abs(y-category.door.y), .30, 3)
        }
      }
    }
    for (const actor of assets.manifest.actors) {
      const object = actors.current.get(actor.index)
      if (!object) continue
      if (projectFocused) { object.visible=false;continue }
      const autonomous = zone === 'city' && isAutonomousCityActor(actor)
      const motion = autonomous ? sampleCityActorMotion(actor, cityClock.current, assets.manifest, scratch.motion) : null
      const loopFrames = actor.loopFrames ?? lobbyLoopFrames
      const actorFrame = zone === 'lobby' && actor.autonomous && loopFrames !== undefined ? 1 + lobbyClock.current % loopFrames : motion?.frame ?? frame
      const sampled = readPose(assets, actorFrame, actor.index, scratch.position, scratch.quaternion, scratch.scale)
      if (motion) scratch.quaternion.multiply(scratch.turn.setFromAxisAngle(scratch.up, motion.turn))
      object.position.copy(scratch.position);object.quaternion.copy(scratch.quaternion);object.scale.copy(scratch.scale);object.visible = sampled.visible && motion?.visible !== false
      const material = materials.walkers[actor.index]
      if (material && actor.morphCount) {
        sampleMorphWeights(assets, actorFrame, actor.index, material.uniforms.shapeWeights.value)
      }
      if (material && actor.walk) {
        const t = motion?.progress ?? MathUtils.clamp((frame - actor.walk.startFrame) / (actor.walk.endFrame - actor.walk.startFrame), 0, 1)
        material.uniforms.walkPhase.value = actor.walk.phase + (motion?.travel ?? t) * actor.walk.distance * Math.PI * 2 / actor.walk.stride
        material.uniforms.walkBlend.value = reducedMotion ? 0 : Math.min(1, t * 8, (1 - t) * 8)
      }
    }
  })

  return (
      <group ref={root} name={`${zone}-geometry`} position={offset} rotation={rotation}>
        {zone === 'city' && <CityShootingStars clock={cityClock} fps={assets.manifest.fps} frameRef={frameRef} journey={journey} reducedMotion={reducedMotion} />}
        {floors.map(floor => <ReflectiveFloor key={floor.name} {...floor} {...(lobbyClip ? { clippingPlanes: lobbyClip.planes } : {})} />)}
        {switches.length > 0 && <><ambientLight intensity={.24} /><pointLight position={[.65, 1.05, 2.55]} intensity={12} distance={3.8} decay={2} /></>}
        {onSelect && switches.map(({ level, items }) => <ElevatorButton key={level.id} level={level} items={items} selected={level.id === selectedLevel} focused={level.id === focusedLevel} keyboardPressed={level.id === pressedLevel} interactive={Boolean(interactive)} reducedMotion={reducedMotion} onSelect={onSelect} />)}
        {zone === 'room-about' && onInteract && printerItems.length > 0 && <OfficePrinter items={printerItems} enabled={Boolean(interactive && showTargets)} reducedMotion={reducedMotion} onInteract={onInteract} onHover={setHovered} />}
        {groups.filter((item) => item.actor === 0 && !['button', 'buttonDetail', 'printer'].includes(item.role ?? '')).map((item) => <group key={`${item.actor}-${item.kind}-${item.byteOffset}`} ref={(object) => { if (object) variants.current.set(item.byteOffset, object);else variants.current.delete(item.byteOffset) }}>
          <DrawGroup item={item} materials={materials} selectedLevel={selectedLevel} interactive={interactive} cardFocused={cardFocused} onSelect={onSelect} onInteract={onInteract} onHover={zone === 'room-about' || zone === 'room-skills' ? setHovered : undefined} />
        </group>)}
        {zone === 'room-about' && onInteract && <AboutOfficeTargets groups={groups} enabled={Boolean(interactive && showTargets)} hovered={hovered} onInteract={onInteract} />}
        {zone === 'room-about' && onView && <ContactCardDismiss groups={groups} enabled={Boolean(interactive && cardFocused)} onView={onView} />}
        {zone === 'room-skills' && assets.manifest.level === 'skills' && onInteract && <SkillsGalleryTargets groups={groups} exhibits={assets.manifest.exhibits} enabled={Boolean(interactive && showTargets)} hovered={hovered} onInteract={onInteract} />}
        {zone === 'room-projects' && assets.manifest.level === 'projects' && roomState && onInteract && <ProjectVideoBoards projects={assets.manifest.projects} groups={groups} roomState={roomState} roomArrived={Boolean(roomArrived)} reducedMotion={reducedMotion} onInteract={onInteract}/>}
        {assets.manifest.actors.map((actor) => (
          <group key={actor.index} name={actor.name} ref={(object) => { if (object) actors.current.set(actor.index, object); else actors.current.delete(actor.index) }}>
            {groups.filter((item) => item.actor === actor.index).map((item) => <DrawGroup key={`${item.actor}-${item.kind}-${item.byteOffset}`} item={item} materials={materials} />)}
          </group>
        ))}
      </group>
  )
}

export default function CityScene({ assets, lobbyAssets, elevatorAssets, elevatorState, focusedLevel, pressedLevel, roomAssets, roomState, navigationRef, journey, progress, reducedMotion, onFrame, onSelectLevel, onElevatorFrame, onRoomFrame, onRoomInteract, onArrival, onCancel, onRoomView, onToggleWalk, onSeekTour, onStation, onTourEnd, onRequestReturn, onEnterElevator, onReturnProgress, onReturnComplete }: CitySceneProps) {
  const frameRef = useRef(1)
  const elevatorFrameRef = useRef(62)
  const roomFrameRef = useRef(1)
  const roomAlignment = useMemo(() => createRoomAlignment(roomAssets, journey), [roomAssets, journey])
  const returning = elevatorState.status === 'returning'
  const destinationActive = Boolean(roomAssets) && ['departing', 'arrived', 'returning'].includes(elevatorState.status)
  const connectedRoom = Boolean(elevatorState.level && journey.rooms[elevatorState.level])
  return <>
    <color attach="background" args={['#000000']} />
    <JourneyCamera city={assets} lobby={lobbyAssets} elevator={elevatorAssets} elevatorState={elevatorState} roomAssets={roomAssets} roomAlignment={roomAlignment} journey={journey} progress={progress} reducedMotion={reducedMotion} frameRef={frameRef} elevatorFrameRef={elevatorFrameRef} onFrame={onFrame} onElevatorFrame={onElevatorFrame} onArrival={onArrival} onCancel={onCancel} />
    {roomAssets && roomAlignment && <RoomNavigator assets={roomAssets} alignment={roomAlignment} active={destinationActive && !returning} arrived={elevatorState.status === 'arrived'} roomState={roomState} navigationRef={navigationRef} reducedMotion={reducedMotion} roomFrameRef={roomFrameRef} onFrame={onRoomFrame} onRequestReturn={onRequestReturn} onView={onRoomView} onToggleWalk={onToggleWalk} onSeekTour={onSeekTour} onStation={onStation} onTourEnd={onTourEnd} />}
    {elevatorAssets && <RoomReturnJourney assets={elevatorAssets} journey={journey} active={returning} reducedMotion={reducedMotion} elevatorFrameRef={elevatorFrameRef} onProgress={onReturnProgress} onComplete={onReturnComplete} />}
    <group rotation={[-Math.PI / 2, 0, 0]}>
      <ZoneGeometry assets={assets} frameRef={frameRef} reducedMotion={reducedMotion} journey={journey} zone="city" />
      {lobbyAssets && <ZoneGeometry assets={lobbyAssets} frameRef={frameRef} reducedMotion={reducedMotion} journey={journey} zone="lobby" offset={journey.lobbyOffset} />}
      {elevatorAssets && <ZoneGeometry assets={elevatorAssets} frameRef={frameRef} elevatorFrameRef={elevatorFrameRef} connectedRoom={connectedRoom} reducedMotion={reducedMotion} journey={journey} zone="elevator" offset={journey.elevatorOffset} selectedLevel={elevatorState.level} focusedLevel={focusedLevel} pressedLevel={pressedLevel} interactive={progress >= .999 && elevatorState.status === 'idle'} onSelect={onSelectLevel} />}
       {roomAssets && roomAlignment && elevatorState.level && <>
         <ZoneGeometry assets={roomAssets} frameRef={frameRef} roomFrameRef={roomFrameRef} destinationActive={destinationActive} reducedMotion={reducedMotion} journey={journey} zone={`room-${elevatorState.level}`} offset={roomAlignment.position.toArray()} rotation={[0, 0, Math.PI]} interactive={elevatorState.status === 'arrived' && !roomState.profileOpen && !roomState.returnPrompt && (!['projects','experience','skills'].includes(elevatorState.level)||roomState.view==='main')} showTargets={roomState.view === 'main'} cardFocused={roomState.view === 'card'} projectFocused={elevatorState.level==='projects'&&['project','directory'].includes(roomState.view)||elevatorState.level==='skills'&&roomState.view==='skill'} entryClosed={false} onInteract={onRoomInteract} onView={onRoomView} navigationRef={navigationRef} roomState={roomState} roomArrived={elevatorState.status==='arrived'} />
        <group position={roomAlignment.position.toArray()} rotation={[0, 0, Math.PI]}>
          <RoomElevatorEntrance entrance={roomAssets.manifest.entranceAnchor} active={elevatorState.status === 'arrived'} interactive={elevatorState.status === 'arrived' && !roomState.profileOpen && !roomState.returnPrompt && roomState.view === 'main'} navigationRef={navigationRef} onReturn={onEnterElevator} />
        </group>
      </>}
    </group>
  </>
}
