// Run with `node --import tsx assets/journey/verify_rooms.mts` after exporting the destinations.
import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { Quaternion, Vector3, Vector4 } from 'three'
import { createRoomAlignment, readRoomRoute, sampleMorphWeights } from '../../src/components/city/roomJourney.ts'
import { readPose } from '../../src/components/city/journeyTimeline.ts'
import { journeyFile, jsonFile, sceneFile } from '../../scripts/node_json.mts'
import { isCityManifest, isElevatorManifest, isLobbyManifest, isSceneManifest, parseSceneManifest } from '../../src/types/sceneValidation.ts'
import type { GeometryDescriptor } from '../../src/types/scene.ts'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..')
function assets(base: string) {
  const manifest = parseSceneManifest(jsonFile(path.join(root, base, 'scene.json')))
  const buffer = fs.readFileSync(path.join(root, base, manifest.animation))
  const geometry = fs.readFileSync(path.join(root, base, manifest.geometry))
  const animation = new Float32Array(buffer.buffer, buffer.byteOffset, buffer.length / 4)
  assert.equal(buffer.length, (manifest.frameEnd - manifest.frameStart + 1) * manifest.channelCount * manifest.channelStride * 4)
  for (const group of manifest.groups) {
    assert.ok(group.byteOffset + group.floatCount * 4 <= geometry.length)
    for (const morph of group.morphs || []) { assert.equal(morph.floatCount, group.vertexCount * 3);assert.ok(morph.byteOffset + morph.floatCount * 4 <= geometry.length) }
  }
  assert.ok(animation.every(Number.isFinite))
  let route = null
  if (manifest.level && manifest.navigation.type === 'guided') {
    const descriptor = manifest.navigation.route, data = fs.readFileSync(path.join(root, base, descriptor.file))
    assert.equal(data.length, (descriptor.frameEnd-descriptor.frameStart+1)*descriptor.stride*4)
    route = new Float32Array(data.buffer, data.byteOffset, data.length/4)
    assert.ok(route.every(Number.isFinite))
  }
  return { manifest, animation, route }
}
const journey = journeyFile(path.join(root, 'public/models/journey.json'))
const city = sceneFile(path.join(root, 'public/models/city/scene.json'), 'city')
const lobby = sceneFile(path.join(root, 'public/models/lobby/scene.json'), 'lobby')
assert.ok(isCityManifest(city))
assert.ok(isLobbyManifest(lobby) && !isElevatorManifest(lobby))
const elevator = assets('public/models/elevator')
assert.ok(isElevatorManifest(elevator.manifest) && !isLobbyManifest(elevator.manifest))

// These fixtures change JSON metadata only, never the exported packed buffers.
const legacyLobby = structuredClone(lobby)
legacyLobby.channelStride = 12
for (const actor of legacyLobby.actors) delete actor.morphCount
for (const group of legacyLobby.groups) delete group.morphs
for (const version of [1, 2, 3] as const) {
  const manifest = parseSceneManifest({ ...legacyLobby, version })
  assert.ok(isLobbyManifest(manifest), `Native version ${version} stride-12 lobby must remain supported`)
  assert.ok(!isElevatorManifest(manifest) && !isCityManifest(manifest), 'Legacy lobby must not be classified as a cabin or city')
}
for (const fixture of [lobby, legacyLobby]) {
  for (const period of ['npcLoopFrames', 'autonomousLoopFrames', 'fishLoopFrames'] as const) {
    for (const value of [0, -1, 1.5, NaN, Infinity, -Infinity]) {
      const invalid = { ...fixture, [period]: value }
      assert.ok(!isSceneManifest(invalid), `${period}=${value} must not reach pose/morph sampling`)
      assert.throws(() => parseSceneManifest(invalid), /Invalid scene manifest/)
    }
    assert.ok(isLobbyManifest(parseSceneManifest({ ...fixture, [period]: 1 })), `${period}=1 is a valid loop`)
  }
}
const cabinMarkers = Object.entries({ levels: elevator.manifest.levels, flow: elevator.manifest.flow, interactions: elevator.manifest.interactions })
for (const fixture of [lobby, legacyLobby]) {
  // Every non-empty proper subset must reject instead of becoming a lobby.
  for (let mask = 1; mask < 7; mask++) {
    const markers = Object.fromEntries(cabinMarkers.filter((_, index) => mask & (1 << index)))
    assert.ok(!isSceneManifest({ ...fixture, ...markers }), 'Partial cabin metadata must never fall back to a lobby')
  }
  for (const [key] of cabinMarkers) {
    assert.ok(!isSceneManifest({ ...fixture, [key]: undefined }), 'Even an undefined cabin marker must prevent lobby fallback')
    assert.ok(!isSceneManifest({ ...fixture, ...Object.fromEntries(cabinMarkers), [key]: null }), 'Malformed complete cabin metadata must reject')
  }
}
console.log('PASS scene contracts: legacy stride-12 lobbies v1–3, exclusive lobby/cabin guards, positive integer loop periods and partial/malformed cabin rejection')

assert.deepEqual(elevator.manifest.levels.filter(level => level.available).map(level => level.number), [1, 2, 3, 4])
assert.equal(elevator.manifest.levels.length, 4)
assert.equal(elevator.manifest.interactions.length, 4)
assert.ok(!elevator.manifest.groups.some(group => String(group.level) === 'contact'))
for (const level of elevator.manifest.levels) {
  const assembly: GeometryDescriptor[] = elevator.manifest.groups.filter(group => group.level === level.id && ['button', 'buttonDetail'].includes(group.role ?? ''))
  assert.equal(assembly.filter(group => group.role === 'button').length, 1)
  assert.ok(assembly.some(group => group.role === 'buttonDetail' && group.kind === 'solid'), 'Switch lettering must remain in its moving assembly')
  assert.ok(assembly.some(group => group.role === 'buttonDetail' && group.kind === 'lines'), 'Switch border must remain in its moving assembly')
}
const heights = elevator.manifest.levels.map(level => {assert.ok(isElevatorManifest(elevator.manifest));const item=elevator.manifest.interactions.find(item => item.id === level.id);assert.ok(item);return item.position[2]})
assert.ok(heights.every((height, i) => !i || height > heights[i - 1]), 'Floor numbers must ascend bottom-to-top')
const p = new Vector3(), q = new Quaternion(), exit = new Vector3(), exitQ = new Quaternion()
readPose(elevator, 414, 0, exit, exitQ);exit.add(new Vector3().fromArray(journey.elevatorOffset))
for (const level of ['about', 'skills', 'projects', 'experience']) {
  const room = assets(`public/models/rooms/${level}`)
  assert.ok(room.manifest.level)
  const alignment = createRoomAlignment({ manifest: room.manifest }, journey)
  const entrance = new Vector3().fromArray(room.manifest.entranceAnchor).applyQuaternion(alignment.rotation).add(alignment.position)
  assert.ok(entrance.distanceTo(new Vector3().fromArray(journey.elevatorOffset)) < .00001, 'Room entrance must meet the cabin threshold')
  assert.ok(new Vector3(0, 1, 0).applyQuaternion(alignment.rotation).y < -.999, 'Rooms must face the departure direction')
  assert.ok(alignment.poses.main.position.y < exit.y, 'Arrival must continue forward into the room')
  if (room.manifest.level === 'projects') {
    assert.equal(room.manifest.projects.length, 16)
    assert.deepEqual(room.manifest.navigation.categories.map(category => category.id), ['client','academic','personal'])
    assert.equal(room.manifest.navigation.categories.filter(category => category.door).length, 2)
    assert.equal(room.manifest.projects.find(project => project.id === 'fyp')!.repositories.length, 2, 'Only the two verified public FYP repositories may be published')
    assert.equal(room.manifest.actors.length, 15)
    for (const actor of room.manifest.actors) {
      const a = new Vector4(), b = new Vector4()
      sampleMorphWeights(room, 1, actor.index, a);sampleMorphWeights(room, 1201, actor.index, b)
      assert.ok(a.clone().sub(b).length() < 1e-6, 'Native NPC morph loops must wrap exactly')
      readPose(room, 1, actor.index, p, q)
      const start = p.clone(), rotation = q.clone().normalize()
      readPose(room, 1201, actor.index, p, q)
      assert.ok(start.distanceTo(p) < 1e-6 && rotation.angleTo(q.normalize()) < 1e-6)
      sampleMorphWeights(room, 46, actor.index, b)
      assert.ok(a.clone().sub(b).length() > .001, `Missing authored motion: ${actor.name}`)
    }
  } else if (room.manifest.level === 'about') {
    assert.equal(room.manifest.navigation.type, 'look')
    const target = new Vector3().fromArray(room.manifest.navigation.lookTarget)
    const home = room.manifest.cameras.main
    assert.ok(Math.abs(home.position[0] - target.x) < .00001, 'Office camera must be centered horizontally on the computer')
    const direction = new Vector3(0, 0, -1).applyQuaternion(new Quaternion().fromArray(home.quaternion))
    assert.ok(direction.angleTo(target.sub(new Vector3().fromArray(home.position))) < .00001, 'Office camera must look directly at the computer center')
    assert.ok(room.manifest.cameras.card)
    const entryPanels = room.manifest.groups.filter(group => group.role === 'officeDoor')
    assert.equal(entryPanels.length, 1, 'Flush office entry panels must remain independently hideable for elevator transitions')
    assert.equal(entryPanels[0].id, 'office-entry')
    assert.equal(entryPanels[0].kind, 'solid')
    assert.equal(room.manifest.groups.filter(group => group.role === 'contactPick').length, 1)
    const contactLinks = room.manifest.groups.filter(group => group.role === 'contactLinkPick')
    assert.deepEqual(contactLinks.map(group => group.id).sort(), ['contact-github', 'contact-whatsapp'])
    for (const link of contactLinks) {
      assert.equal(link.kind, 'solid')
      assert.equal(link.opacity, 0, 'Contact link targets must stay invisible')
      assert.equal(link.vertexCount, 6, 'Contact links must use precise printed-line faces')
      assert.equal(link.actor, 0)
    }
    const observer = room.manifest.groups.filter(group => group.role === 'observerPick')
    assert.equal(observer.length, 1)
    assert.equal(observer[0].id, 'observer')
    assert.equal(observer[0].opacity, 0)
    assert.equal(observer[0].vertexCount, 36)
    assert.ok(room.manifest.loop && room.manifest.frameEnd > 1, 'Aquarium animation must repeat')
    assert.ok(room.manifest.navigation.animationBounds, 'Aquarium playback must have visibility bounds')
    const fish = room.manifest.actors.filter(actor => actor.name.includes('/ swim route'))
    const bubbles = room.manifest.actors.filter(actor => actor.name.includes('/ rise loop'))
    assert.equal(fish.length, 3);assert.equal(bubbles.length, 16)
    for (const actor of fish) {
      readPose(room, 1, actor.index, p, q)
      const start = p.clone(), rotation = q.clone()
      readPose(room, 91, actor.index, p, q)
      assert.ok(p.distanceTo(start) > .2, 'Fish must follow a moving preset route')
      readPose(room, room.manifest.frameEnd, actor.index, p, q)
      assert.ok(p.distanceTo(start) < .02 && q.angleTo(rotation) < .03, 'Fish must cross the loop seam smoothly')
      readPose(room, room.manifest.frameEnd + 1, actor.index, p, q)
      assert.ok(p.distanceTo(start) < 1e-6 && q.angleTo(rotation) < 1e-6)
    }
    for (const actor of bubbles) {
      const previous = new Vector3(), previousScale = new Vector3(), scale = new Vector3()
      readPose(room, 1, actor.index, previous, q, previousScale)
      const start = previous.clone()
      readPose(room, 121, actor.index, p, q)
      assert.ok(p.distanceTo(start) < 1e-6, 'Bubble rise paths must repeat')
      for (let frame = 2; frame <= room.manifest.frameEnd; frame++) {
        readPose(room, frame, actor.index, p, q, scale)
        assert.ok(p.z >= 1.29 && p.z <= 2.79, 'Bubbles must stay inside the tank')
        if (p.z < previous.z) assert.ok(Math.max(previousScale.x, scale.x) < .11, 'Bubble recycling must happen while faded out')
        previous.copy(p);previousScale.copy(scale)
      }
    }
  } else {
    const guided = room.manifest.navigation
    const endpoint = new Vector3()
    assert.equal(guided.type, 'guided')
    assert.ok(room.route)
    assert.equal(room.manifest.exhibits.length, level === 'skills' ? 10 : 6)
    readRoomRoute({ manifest: room.manifest, route: room.route }, 1, p)
    assert.ok(p.distanceTo(new Vector3().fromArray(room.manifest.cameras.main.position)) < .00001)
    if (level === 'skills') {
      assert.equal(guided.animationFollowsWalk, false, 'Skills NPCs must run independently of walking')
      assert.ok(room.manifest.loop && room.manifest.frameEnd === 959, 'Skills must wrap the native visitor clip')
      assert.equal(room.manifest.npcCount, 6);assert.equal(room.manifest.actors.length, 90)
      const walker = room.manifest.groups.filter(group => group.id === 'atat')
      assert.ok(walker.some(group => group.kind === 'solid'), 'AT-AT must have black armor and a real mesh pick')
      assert.ok(walker.some(group => group.kind === 'lines'), 'AT-AT must retain native white contour curves')
      assert.ok(walker.every(group => group.kind !== 'points'), 'The AT-AT is an outlined mechanical exhibit, not the old dot sculpture')
      assert.ok(!room.manifest.groups.some(group => group.id === 'trex'))
      assert.ok(room.manifest.cameras.atat)
      readRoomRoute({ manifest: room.manifest, route: room.route }, guided.route.frameEnd + 100, p)
      readRoomRoute({ manifest: room.manifest, route: room.route }, guided.route.frameEnd, endpoint)
      assert.ok(p.distanceTo(endpoint) < .00001, 'Gallery tour must stop at its endpoint')
    } else {
      assert.equal(room.manifest.npcCount, 0);assert.equal(room.manifest.actors.length, 6)
      assert.equal(room.manifest.groups.filter(group => group.role === 'exhibitPick').length, 6)
      readRoomRoute({ manifest: room.manifest, route: room.route }, guided.route.frameEnd + 1, p);readRoomRoute({ manifest: room.manifest, route: room.route }, 1, endpoint)
      assert.ok(p.distanceTo(endpoint) < .00001, 'Observatory route must wrap exactly')
    }
    for (const actor of room.manifest.actors) {
      readPose(room, room.manifest.loop ? 1 : room.manifest.frameEnd, actor.index, p, q)
      const first = p.clone(), rotation = q.clone()
      readPose(room, room.manifest.frameEnd+1, actor.index, p, q)
      assert.ok(first.distanceTo(p)<1e-6 && rotation.angleTo(q)<1e-6)
    }
  }
  console.log(`PASS ${level}: package bounds, doorway alignment, arrival direction, authored interactions/motion`)
}
assert.ok(!('project-meeting' in journey.rooms), 'The retired meeting room must not be an elevator floor')
assert.ok(!fs.existsSync(path.join(root, 'public/models/rooms/project-meeting')), 'The retired meeting-room package must not be deployed')
console.log('PASS retired meeting room: no browser package or elevator destination')
console.log('PASS floor panel order and destination availability')
console.log('PASS all seven current scene packages: city, lobby, elevator and four rooms')
