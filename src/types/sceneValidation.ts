import type { CityManifest, ElevatorManifest, JourneyConfig, LobbyManifest, SceneManifest } from './scene'

// Run these at fetch/JSON boundaries, once per package, never in render loops.
type Check = (value: unknown) => boolean
type Fields = Record<string, Check>
const number: Check = value => typeof value === 'number' && Number.isFinite(value)
const natural: Check = value => typeof value === 'number' && Number.isSafeInteger(value) && value >= 0
const positiveInteger: Check = value => natural(value) && value !== 0
const positive: Check = value => typeof value === 'number' && Number.isFinite(value) && value > 0
const string: Check = value => typeof value === 'string'
const boolean: Check = value => typeof value === 'boolean'
const record = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null && !Array.isArray(value)
const array = (check: Check): Check => value => {
  if (!Array.isArray(value)) return false
  // Iteration checks holes as undefined, unlike Array.every on sparse inputs.
  for (const item of value) if (!check(item)) return false
  return true
}
const tuple = (size: number, check: Check): Check => value => Array.isArray(value) && value.length === size && array(check)(value)
const vec3 = tuple(3, number)
const quat4 = tuple(4, number)
const nullable = (check: Check): Check => value => value === null || check(value)
const dictionary = (check: Check): Check => value => record(value) && Object.values(value).every(check)
const oneOf = (...values: (string | number)[]): Check => value => values.some(item => item === value)
const fields = (required: Fields, extra: Fields = {}): Check => value => record(value) &&
  Object.entries(required).every(([key, check]) => check(value[key])) &&
  Object.entries(extra).every(([key, check]) => !(key in value) || check(value[key]))
const level = oneOf('about', 'skills', 'projects', 'experience')
const bounds = fields({ min: vec3, max: vec3 })
const camera = fields({ verticalFov: positive, sourceAspect: positive, near: positive, far: positive }, { fovOffset: natural })
const cameraPose = fields({ position: vec3, quaternion: quat4, fov: number })
const card = fields({ center: vec3, normal: vec3, width: number, height: number }, { right: vec3, frontDepth: number })
const catalogueSections = array(fields({ heading: string, markdown: string }))
const repositories = array(fields({ id: string, title: string, url: string }))
const video = fields({ preview: string, full: string, poster: string, width: number, height: number }, {
  previewFallback: string, fullFallback: string,
})
const project = fields({
  id: string, title: string, summary: string, section: string, category: string,
  catalogueNumber: number, catalogueTitle: string, overview: string, catalogueSections,
  tags: array(string), repositories, url: nullable(string), position: vec3, facing: string, frame: number,
}, {
  card, featured: boolean, video, liveUrl: string, liveLabel: string, liveStatus: string, liveNote: string,
  repositoryLinksRestricted: boolean,
})
const exhibit = fields({ id: string, title: string, start: number, end: number, hint: string, position: vec3 }, {
  card, kind: oneOf('skill'), number, catalogueNumber: number, summary: string, section: string, category: string,
  catalogueSections, items: array(string), displayItems: array(string), profileOnly: array(string), evidenceProjectIds: array(string),
  focus: string, contentStatus: string, repositories, siteLinks: array(fields({ url: string, label: string })),
  url: nullable(string), caption: string, cardTitle: string, cardHeading: string, cardSpecialism: string,
  categoryLabel: string, icon: string, logo: fields({ id: string, texture: string, source: string }),
  metadata: array(tuple(2, string)),
})
const category = fields({
  id: string, title: string, number, startY: number, displayStartY: number, endY: number, projectIds: array(string),
}, { door: fields({ y: number, revealY: number, automatic: boolean, previousCategory: string }) })
const route = fields({ file: string, frameStart: positiveInteger, frameEnd: positiveInteger, stride: oneOf(3), loop: boolean })
const navigationBase = fields({ eyeHeight: number }, {
  initialYaw: number, initialPitch: number, animationBounds: bounds, animationFollowsWalk: boolean, categories: array(category),
})
const lookNavigation: Check = value => navigationBase(value) && fields({
  type: oneOf('look'), initialYaw: number, initialPitch: number, lookTarget: vec3,
})(value)
const axisNavigation: Check = value => navigationBase(value) && fields({
  type: oneOf('axis'), minY: number, maxY: number, speed: number, fastSpeed: number, categories: array(category),
})(value)
const guidedNavigation: Check = value => navigationBase(value) && fields({
  type: oneOf('guided'), initialYaw: number, initialPitch: number, animationFollowsWalk: boolean, route, stations: array(exhibit),
}, { pacing: oneOf('linear-distance'), travelDistance: number })(value)
const actor = fields({ index: natural, name: string, style: string }, {
  autonomous: boolean, visibilityOffset: natural, morphCount: natural, activity: string, motionType: string, part: string, loopFrames: positiveInteger,
  walk: fields({ startFrame: positiveInteger, endFrame: positiveInteger, distance: number, stride: positive, phase: number }),
  motion: fields({}, { startFrame: number, endFrame: number, mode: oneOf('one-way', 'shuttle'), passFrames: number,
    resetFrames: number, turnFrames: number, phase: number }),
})
const geometry = fields({
  actor: natural, kind: oneOf('points', 'lines', 'outline', 'glow', 'solid', 'screen', 'mask'),
  byteOffset: natural, floatCount: natural, vertexCount: natural, stride: positiveInteger,
}, {
  role: nullable(string), id: nullable(string), opacity: number, texture: string, level: nullable(level), available: boolean,
  stage: oneOf('all', 'exit'),
  morphs: array(fields({ byteOffset: natural, floatCount: natural })),
})
const destination = fields({
  label: string, source: string, assetBase: string, entranceAnchor: vec3, mainCamera: string, width: number, height: number,
}, {
  entryCamera: string, focusCamera: string, detailCameras: dictionary(string), animationFrames: number,
  guidedFrames: number, guidedLoop: boolean,
})
const elevatorLevel = fields({
  id: level, number, title: string, description: string, button: string, dialog_collection: string, available: boolean, room: destination,
})
const sceneBase = fields({
  version: oneOf(1, 2, 3), geometry: string, animation: string, frameStart: positiveInteger, frameEnd: positiveInteger, fps: positive,
  channelCount: positiveInteger, channelStride: oneOf(10, 12, 16), channels: array(string), actors: array(actor), camera, groups: array(geometry),
}, {
  assetHash: string, preview: string, coordinateSystem: string, textures: array(string), loop: boolean,
  statistics: dictionary(number), bookmarks: dictionary(number),
})
const roomBase = fields({
  level, label: string, entranceAnchor: vec3, cameras: value => dictionary(cameraPose)(value) && record(value) && cameraPose(value.main),
  projects: array(project), exhibits: array(exhibit), npcCount: number, loop: boolean,
})
const streetPlaza = fields({ line_segments: number, fixtures: number, labels: number, reflection: fields({
  width: number, depth: number, position: vec3, strength: number, paving: boolean,
}) })
const elevatorFlow = fields({
  entryStart: number, selectionFrame: number, departureStart: number, arrivalFrame: number,
  doorsClose: tuple(2, number), doorsOpen: tuple(2, number), walkout: tuple(2, number),
})

// Any cabin marker commits the package to the complete cabin contract. A
// partial or malformed cabin must never fall back to the legacy lobby shape.
function hasCabinMarkers(value: object): boolean {
  return 'levels' in value || 'flow' in value || 'interactions' in value
}

// These guards classify already-validated scene manifests; they do not decode
// unknown JSON. Lobby and elevator strides overlap in native legacy packages.
export function isCityManifest(manifest: SceneManifest): manifest is CityManifest {
  return manifest.level === undefined && manifest.channelStride === 10
}
export function isLobbyManifest(manifest: SceneManifest): manifest is LobbyManifest {
  return manifest.level === undefined && (manifest.channelStride === 12 || manifest.channelStride === 16) && !hasCabinMarkers(manifest)
}
export function isElevatorManifest(manifest: SceneManifest): manifest is ElevatorManifest {
  return manifest.level === undefined && manifest.channelStride === 12 &&
    'levels' in manifest && 'flow' in manifest && 'interactions' in manifest
}

function hasSceneStructure(value: unknown): value is SceneManifest {
  if (!record(value) || !sceneBase(value)) return false
  switch (value.level) {
    case 'about': return roomBase(value) && value.channelStride === 16 && lookNavigation(value.navigation)
    case 'skills': return roomBase(value) && value.channelStride === 12 && guidedNavigation(value.navigation)
    case 'projects': return roomBase(value) && value.channelStride === 16 && axisNavigation(value.navigation) && fields({
      directory: fields({ id: string, title: string, category: string, position: vec3, card, zoomOnly: boolean, projectorPosition: string }),
    })(value)
    case 'experience': return roomBase(value) && value.channelStride === 16 && guidedNavigation(value.navigation)
    case undefined:
      if ('level' in value) return false
      if (hasCabinMarkers(value)) return value.channelStride === 12 && fields({ levels: array(elevatorLevel), flow: elevatorFlow,
        interactions: array(fields({ id: level, button: string, position: vec3, dimensions: vec3 })),
      })(value)
      if (value.channelStride === 10) return fields({}, { streetPlaza })(value)
      return (value.channelStride === 12 || value.channelStride === 16) && fields({}, {
        npcLoopFrames: positiveInteger, autonomousLoopFrames: positiveInteger, fishLoopFrames: positiveInteger,
      })(value)
    default: return false
  }
}

// Structural checks establish the shapes above; these load-only numeric checks
// establish the packedNumber range proofs used by animation/route readers. The
// loader separately checks actual buffer byte lengths before returning assets.
function hasPackedRanges(manifest: SceneManifest): boolean {
  const frameCount = manifest.frameEnd - manifest.frameStart + 1
  if (frameCount < 1 || !Number.isSafeInteger(frameCount * manifest.channelCount * manifest.channelStride * 4)) return false
  if (manifest.channels.length !== manifest.channelCount) return false
  if (manifest.camera.fovOffset !== undefined && manifest.camera.fovOffset >= manifest.channelStride) return false
  if (manifest.camera.verticalFov >= 180 || manifest.camera.far <= manifest.camera.near) return false
  for (const actor of manifest.actors) {
    if (actor.index >= manifest.channelCount) return false
    if (actor.visibilityOffset !== undefined && actor.visibilityOffset >= manifest.channelStride) return false
    if (actor.morphCount !== undefined && actor.morphCount > 4) return false
    if (actor.morphCount && (manifest.channelStride !== 16 || manifest.frameStart !== 1)) return false
    if (actor.walk && (actor.walk.startFrame > actor.walk.endFrame || actor.walk.startFrame < manifest.frameStart || actor.walk.endFrame > manifest.frameEnd)) return false
  }
  for (const group of manifest.groups) {
    const minimumStride = group.kind === 'points' || group.kind === 'screen' ? 5 : group.kind === 'mask' ? 3 : 4
    if (group.actor >= manifest.channelCount || group.stride < minimumStride) return false
    if (group.byteOffset % 4 || group.floatCount !== group.vertexCount * group.stride) return false
    if (!Number.isSafeInteger(group.byteOffset + group.floatCount * 4)) return false
    if (group.morphs && (manifest.channelStride !== 16 || group.morphs.length > 4)) return false
    for (const morph of group.morphs || []) {
      if (morph.byteOffset % 4 || morph.floatCount !== group.vertexCount * 3) return false
      if (!Number.isSafeInteger(morph.byteOffset + morph.floatCount * 4)) return false
    }
  }
  if (manifest.level === undefined) return true
  const navigation = manifest.navigation
  if (navigation.type !== 'guided') return navigation.type !== 'axis' || navigation.maxY > navigation.minY
  const descriptor = navigation.route, count = descriptor.frameEnd - descriptor.frameStart + 1
  if (count < 2 || !Number.isSafeInteger(count * descriptor.stride * 4)) return false
  // Linear-distance remapping indexes the distance array with native starts,
  // so these must be integers, not fractional inspection coordinates. Once
  // remapped in memory their fractional start/end values are not parsed again.
  for (const item of [...manifest.exhibits, ...navigation.stations]) {
    if (!Number.isSafeInteger(item.start) || !Number.isSafeInteger(item.end)) return false
    if (item.start < descriptor.frameStart || item.end > descriptor.frameEnd || item.end < item.start) return false
  }
  return true
}

export function isSceneManifest(value: unknown): value is SceneManifest {
  return hasSceneStructure(value) && hasPackedRanges(value)
}

export function parseSceneManifest(value: unknown): SceneManifest {
  if (!isSceneManifest(value)) throw new Error('Invalid scene manifest.')
  return value
}

const portal = fields({ center: vec3, width: number, height: number })
const journey = fields({
  version: oneOf(1), cityEnd: number, cityHideFrame: number, transitionFrames: number, lobbyEnd: number,
  frameEnd: number, fps: number, lobbyOffset: vec3, lobbyRevealFrame: number, lobbyHoldFrame: number, preloadFrame: number,
  bookmarks: fields({ start: number, lookDown: number, doors: number, train: number, entrance: number, lobby: number,
    reception: number, escalator: number, landing: number, elevator: number, elevatorOpen: number, cabin: number }),
  portal, lobbyPortal: portal, lobbyAssetBase: string, lobbyGlobalEnd: number, elevatorOffset: vec3,
  elevatorEntryStart: number, elevatorSelectionFrame: number, elevatorTransitionFrames: number, elevatorRevealFrame: number,
  elevatorHoldFrame: number, elevatorPreloadFrame: number, lobbyHideFrame: number,
  rooms: fields({ about: destination, skills: destination, projects: destination, experience: destination }),
})
export function isJourneyConfig(value: unknown): value is JourneyConfig { return journey(value) }
export function parseJourneyConfig(value: unknown): JourneyConfig {
  if (!isJourneyConfig(value)) throw new Error('Invalid journey configuration.')
  return value
}
