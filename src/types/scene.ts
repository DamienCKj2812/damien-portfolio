import type { BufferGeometry, Texture } from 'three'
import type { LineSegmentsGeometry } from 'three/addons/lines/LineSegmentsGeometry.js'
import type { LevelId } from './navigation'
export type { LevelId } from './navigation'

// All authored coordinates remain Blender Z-up; quaternions use XYZW order.
export type Vec3 = [number, number, number]
export type Quat4 = [number, number, number, number]
export interface Bounds3 { min: Vec3; max: Vec3 }
export interface MorphDescriptor { byteOffset: number; floatCount: number }
export type GeometryKind = 'points' | 'lines' | 'outline' | 'glow' | 'solid' | 'screen' | 'mask'
export interface GeometryDescriptor {
  actor: number
  kind: GeometryKind
  byteOffset: number
  floatCount: number
  vertexCount: number
  stride: number
  role?: string | null
  id?: string | null
  opacity?: number
  texture?: string
  level?: LevelId | null
  available?: boolean
  stage?: 'all' | 'exit'
  morphs?: MorphDescriptor[]
}
export type SceneGeometry = GeometryDescriptor & { geometry: BufferGeometry | LineSegmentsGeometry }
export interface ActorWalk {
  startFrame: number; endFrame: number; distance: number; stride: number; phase: number
}
export interface ActorMotionDescriptor {
  startFrame?: number
  endFrame?: number
  mode?: 'one-way' | 'shuttle'
  passFrames?: number
  resetFrames?: number
  turnFrames?: number
  phase?: number
}
export interface ActorDescriptor {
  index: number
  name: string
  style: string
  autonomous?: boolean
  walk?: ActorWalk
  motion?: ActorMotionDescriptor
  visibilityOffset?: number
  morphCount?: number
  activity?: string
  motionType?: string
  part?: string
  loopFrames?: number
}
export interface CameraDescriptor {
  verticalFov: number; sourceAspect: number; near: number; far: number; fovOffset?: number
}
export interface AuthoredCameraPose { position: Vec3; quaternion: Quat4; fov: number }
export interface CardMetadata {
  center: Vec3; normal: Vec3; right?: Vec3; width: number; height: number; frontDepth?: number
}
export interface CardTarget { position: Vec3; card?: CardMetadata }
export interface CatalogueSection { heading: string; markdown: string }
export interface RepositoryLink { id: string; title: string; url: string }
export interface SiteLink { url: string; label: string }
export interface VideoMetadata {
  preview: string; full: string; poster: string; width: number; height: number
  previewFallback?: string; fullFallback?: string
}
export interface ProjectMetadata extends CardTarget {
  id: string; title: string; summary: string; section: string; category: string
  catalogueNumber: number; catalogueTitle: string; overview: string
  catalogueSections: CatalogueSection[]
  tags: string[]; repositories: RepositoryLink[]; url: string | null
  facing: string; frame: number
  featured?: boolean
  video?: VideoMetadata
  liveUrl?: string; liveLabel?: string; liveStatus?: string; liveNote?: string
  repositoryLinksRestricted?: boolean
}
export interface ExhibitMetadata extends CardTarget {
  id: string; title: string; start: number; end: number; hint: string
  kind?: 'skill'
  number?: number
  catalogueNumber?: number
  summary?: string
  section?: string
  category?: string
  catalogueSections?: CatalogueSection[]
  items?: string[]
  displayItems?: string[]
  profileOnly?: string[]
  evidenceProjectIds?: string[]
  focus?: string
  contentStatus?: string
  repositories?: RepositoryLink[]
  siteLinks?: SiteLink[]
  url?: string | null
  caption?: string
  cardTitle?: string
  cardHeading?: string
  cardSpecialism?: string
  categoryLabel?: string
  icon?: string
  logo?: { id: string; texture: string; source: string }
  metadata?: [string, string][]
}
export interface DirectoryMetadata extends CardTarget {
  id: string; title: string; category: string; card: CardMetadata
  zoomOnly: boolean; projectorPosition: string
}
export interface HallwayCategory {
  id: string; title: string; number: number; startY: number; displayStartY: number; endY: number
  projectIds: string[]
  door?: { y: number; revealY: number; automatic: boolean; previousCategory: string }
}
export interface RouteDescriptor { file: string; frameStart: number; frameEnd: number; stride: 3; loop: boolean }
interface NavigationBase {
  eyeHeight: number
  initialYaw?: number
  initialPitch?: number
  animationBounds?: Bounds3
  animationFollowsWalk?: boolean
  categories?: HallwayCategory[]
}
export interface LookNavigation extends NavigationBase {
  type: 'look'; initialYaw: number; initialPitch: number; lookTarget: Vec3
}
export interface AxisNavigation extends NavigationBase {
  type: 'axis'; minY: number; maxY: number; speed: number; fastSpeed: number; categories: HallwayCategory[]
}
export interface GuidedNavigation extends NavigationBase {
  type: 'guided'; initialYaw: number; initialPitch: number; animationFollowsWalk: boolean
  route: RouteDescriptor; stations: ExhibitMetadata[]; pacing?: 'linear-distance'; travelDistance?: number
}
export type RoomNavigation = LookNavigation | AxisNavigation | GuidedNavigation
export interface SceneManifestBase {
  version: 1 | 2 | 3
  geometry: string; animation: string; assetHash?: string; preview?: string; coordinateSystem?: string
  frameStart: number; frameEnd: number; fps: number; channelCount: number; channelStride: 10 | 12 | 16
  channels: string[]; actors: ActorDescriptor[]; camera: CameraDescriptor; groups: GeometryDescriptor[]
  textures?: string[]; loop?: boolean; statistics?: Record<string, number>
  bookmarks?: Record<string, number>
}
// City, lobby and cabin JSON have no synthetic `level`. Legacy lobbies share
// stride 12 with cabins; only cabins own levels/flow/interactions metadata.
// Room manifests discriminate on their authored `level`.
export interface CityManifest extends SceneManifestBase {
  level?: never; channelStride: 10
  streetPlaza?: { line_segments: number; fixtures: number; labels: number; reflection: {
    width: number; depth: number; position: Vec3; strength: number; paving: boolean
  } }
}
export interface LobbyManifest extends SceneManifestBase {
  level?: never; channelStride: 12 | 16
  levels?: never; flow?: never; interactions?: never
  npcLoopFrames?: number; autonomousLoopFrames?: number; fishLoopFrames?: number
}
export interface ElevatorLevel {
  id: LevelId; number: number; title: string; description: string; button: string
  dialog_collection: string; available: boolean; room: RoomDestination
}
export interface ElevatorManifest extends SceneManifestBase {
  level?: never; channelStride: 12; levels: ElevatorLevel[]
  interactions: { id: LevelId; button: string; position: Vec3; dimensions: Vec3 }[]
  flow: { entryStart: number; selectionFrame: number; departureStart: number; arrivalFrame: number
    doorsClose: [number, number]; doorsOpen: [number, number]; walkout: [number, number] }
}
interface RoomManifestBase extends SceneManifestBase {
  level: LevelId; label: string; entranceAnchor: Vec3
  cameras: Record<string, AuthoredCameraPose> & { main: AuthoredCameraPose }
  projects: ProjectMetadata[]; exhibits: ExhibitMetadata[]; navigation: RoomNavigation; npcCount: number; loop: boolean
}
export interface AboutManifest extends RoomManifestBase { level: 'about'; channelStride: 16; navigation: LookNavigation }
export interface SkillsManifest extends RoomManifestBase { level: 'skills'; channelStride: 12; navigation: GuidedNavigation }
export interface ProjectsManifest extends RoomManifestBase {
  level: 'projects'; channelStride: 16; navigation: AxisNavigation; directory: DirectoryMetadata
}
export interface ExperienceManifest extends RoomManifestBase { level: 'experience'; channelStride: 16; navigation: GuidedNavigation }
export type GuidedRoomManifest = SkillsManifest | ExperienceManifest
export type RoomManifest = AboutManifest | SkillsManifest | ProjectsManifest | ExperienceManifest
export type SceneManifest = CityManifest | LobbyManifest | ElevatorManifest | RoomManifest
export interface LoadedSceneAssets<M extends SceneManifest = SceneManifest> {
  manifest: M
  geometryBuffer: ArrayBuffer
  animation: Float32Array
  route: Float32Array | null
  textures: Record<string, Texture>
}
export type LoadedRoomAssets = LoadedSceneAssets<RoomManifest>
export type LoadedGuidedRoomAssets = LoadedSceneAssets<GuidedRoomManifest> & { route: Float32Array }
export interface PortalMetadata { center: Vec3; width: number; height: number }
export interface RoomDestination {
  label: string; source: string; assetBase: string; entranceAnchor: Vec3; mainCamera: string
  width: number; height: number; entryCamera?: string; focusCamera?: string
  detailCameras?: Record<string, string>; animationFrames?: number; guidedFrames?: number; guidedLoop?: boolean
}
export interface JourneyConfig {
  version: 1; cityEnd: number; cityHideFrame: number; transitionFrames: number; lobbyEnd: number
  frameEnd: number; fps: number; lobbyOffset: Vec3; lobbyRevealFrame: number; lobbyHoldFrame: number; preloadFrame: number
  bookmarks: Record<'start' | 'lookDown' | 'doors' | 'train' | 'entrance' | 'lobby' | 'reception' | 'escalator' | 'landing' | 'elevator' | 'elevatorOpen' | 'cabin', number>
  portal: PortalMetadata; lobbyPortal: PortalMetadata; lobbyAssetBase: string; lobbyGlobalEnd: number; elevatorOffset: Vec3
  elevatorEntryStart: number; elevatorSelectionFrame: number; elevatorTransitionFrames: number; elevatorRevealFrame: number
  elevatorHoldFrame: number; elevatorPreloadFrame: number; lobbyHideFrame: number; rooms: Record<LevelId, RoomDestination>
}
