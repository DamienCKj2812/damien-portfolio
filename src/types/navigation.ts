import type { Quaternion, Vector3 } from 'three'
import type { Vec3 } from './scene'

export type LevelId = 'about' | 'skills' | 'projects' | 'experience'
export type RoomView = 'main' | 'entry' | 'card' | 'atat' | 'globe' | 'oculus' | 'window' | 'project' | 'directory' | 'timeline' | 'skill'
export type ElevatorStatus = 'idle' | 'departing' | 'arrived' | 'returning'
export interface ElevatorState { level: LevelId | null; status: ElevatorStatus; frame: number; run: number }
export interface RoomState {
  view: RoomView
  project: string | null
  projectExploring: boolean
  projectSection: string
  projectFocusReady: boolean
  exhibit: string | null
  paused: boolean
  walkPaused: boolean
  profileOpen: boolean
  returnPrompt: boolean
  openedCategories: string[]
}

export interface CameraSpring { value: number; velocity: number }
// These fields are installed by RoomNavigator when a room becomes active.
export interface NavigationState {
  y: number
  yaw: number
  pitch: number
  forward: number
  fast: boolean
  dragDistance: number
  invalidate: (() => void) | null
  walkFrame?: number
  walkTarget?: number
  walkManual?: boolean
  walkSpring?: CameraSpring
  finished?: boolean
  position?: Vec3
  cameraPosition?: Vec3
  projectCardFramed?: boolean
  projectFocusSettled?: boolean
  returnRequested?: boolean
  returnCooldown?: number
  portalAudioSeeking?: boolean
}
export interface ActiveNavigationState extends NavigationState {
  walkFrame: number
  walkTarget: number
  walkManual: boolean
  walkSpring: CameraSpring
  finished: boolean
  position: Vec3
  cameraPosition: Vec3
  returnRequested: boolean
  returnCooldown: number
  portalAudioSeeking: boolean
}

export interface CameraPose { position: Vector3; quaternion: Quaternion; fov: number }
export interface RoomAlignment {
  position: Vector3
  rotation: Quaternion
  poses: Record<string, CameraPose> & { main: CameraPose }
}
export interface PoseScratch {
  position: Vector3
  quaternion: Quaternion
  scale: Vector3
  bridgePosition: Vector3
  bridgeQuaternion: Quaternion
}
export interface CameraFocusState {
  position: Vector3 | null
  quaternion: Quaternion | null
  fov: number | null
}
export interface FocusRect { left: number; right: number; top: number; bottom: number }
export interface ProjectCardFocus extends CameraPose {
  displayFov: number
  rect: FocusRect
  corners: Vector3[]
  offsetX: number
  offsetY: number
}
export interface RoomProgress { min: number; max: number; value: number; percent: number }
export interface CityActorMotion { frame: number; turn: number; progress: number; travel: number; visible: boolean }
export interface ShootingStarSample { active: boolean; progress: number; opacity: number }
