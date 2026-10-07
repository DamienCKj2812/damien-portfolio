// Cross-clock regression checks against the generated browser packages.
import assert from 'node:assert/strict'
import fs from 'node:fs'
import { Quaternion, Vector3, Vector4 } from 'three'
import { readPose } from '../../src/components/city/journeyTimeline.ts'
import { sampleMorphWeights } from '../../src/components/city/roomJourney.ts'
import { sceneFile } from '../../scripts/node_json.mts'
import type { ActorDescriptor, SceneManifest } from '../../src/types/scene.ts'

function load<M extends SceneManifest>(base: string, manifest: M) {
  const buffer = fs.readFileSync(new URL(`${base}/animation.bin`, import.meta.url))
  assert.equal(buffer.byteLength, (manifest.frameEnd - manifest.frameStart + 1) * manifest.channelCount * manifest.channelStride * 4)
  return { manifest, animation: new Float32Array(buffer.buffer, buffer.byteOffset, buffer.byteLength / 4) }
}
const lobby = load('../../public/models/lobby', sceneFile(new URL('../../public/models/lobby/scene.json', import.meta.url), 'lobby'))
assert.equal(lobby.manifest.npcLoopFrames, 1019)
assert.equal(lobby.manifest.autonomousLoopFrames, 1019)
assert.equal(lobby.manifest.frameEnd, 1020)
// caa19ef already exports 17 people with four native morphs (the escalator
// rider was removed), plus npc_owner accessories and six visible fish parts.
// autonomous is a clock policy, not a population count; see npc_motion.py,
// fish_motion.py and export_browser_lobby.py in the authored lobby pipeline.
const npcs = lobby.manifest.actors.filter(actor => (actor.morphCount ?? 0) > 0)
const fish = lobby.manifest.actors.filter(actor => actor.motionType === 'holographicFish')
const accessories = lobby.manifest.actors.filter(actor => actor.autonomous && !actor.morphCount && actor.motionType !== 'holographicFish')
const autonomous = lobby.manifest.actors.filter(actor => actor.autonomous)
assert.equal(npcs.length, 17)
assert.equal(accessories.length, 14, 'Owned accessories and their feature edges must retain their motion channels')
assert.deepEqual(fish.map(actor => actor.part).sort(), ['body', 'dorsal', 'lower tail', 'lower ventral', 'near pectoral', 'upper tail'])
assert.equal(autonomous.length, npcs.length + accessories.length + fish.length)
assert.ok(!lobby.manifest.channels.includes('Lobby • Escalator / riding upstairs'))
assert.equal(lobby.manifest.channelStride, 16)
const p = new Vector3(), q = new Quaternion(), weights = new Vector4()

function sample(frame: number, actor: ActorDescriptor, offset: number) {
  return lobby.animation[((frame - 1) * lobby.manifest.channelCount + actor.index) * lobby.manifest.channelStride + offset]
}
for (const actor of autonomous) {
  assert.equal(lobby.manifest.channels[actor.index], actor.name)
  assert.ok(lobby.manifest.groups.some(group => group.actor === actor.index && group.vertexCount > 0), `${actor.name}: missing animated geometry`)
  // Check every baked component, including scale, visibility and morphs;
  // accessories/fish must loop too, rather than being ignored by an NPC filter.
  for (let offset = 0; offset < 16; offset++) {
    assert.ok(Math.abs(sample(1, actor, offset) - sample(1020, actor, offset)) < 1e-5, `${actor.name}: loop seam`)
  }
}
let walkers = 0
for (const actor of npcs) {
  assert.equal(actor.autonomous, true)
  assert.ok(actor.activity, `${actor.name}: missing authored activity`)
  const group = lobby.manifest.groups.find(group => group.actor === actor.index && group.kind === 'points')
  assert.ok(group?.morphs)
  assert.equal(group.morphs.length, actor.morphCount)
  assert.equal(actor.morphCount, 4)
  for (const morph of group.morphs) assert.equal(morph.floatCount, group.vertexCount * 3)
  readPose(lobby, 1, actor.index, p, q)
  const start = p.clone(), rotation = q.clone()
  readPose(lobby, lobby.manifest.npcLoopFrames + 1, actor.index, p, q)
  assert.ok(p.distanceTo(start) < 1e-5 && q.angleTo(rotation) < 1e-5, 'NPC loop must close')
  readPose(lobby, 400, actor.index, p, q)
  if (p.distanceTo(start) > 1) walkers++
  const minimum = [Infinity, Infinity], maximum = [-Infinity, -Infinity]
  const firstWeights = new Vector4(), lastWeights = new Vector4()
  sampleMorphWeights(lobby, 1, actor.index, firstWeights)
  sampleMorphWeights(lobby, 1020, actor.index, lastWeights)
  assert.ok(firstWeights.clone().sub(lastWeights).length() < 1e-5, `${actor.name}: morph loop seam`)
  for (let frame = 1; frame <= 1020; frame++) {
    sampleMorphWeights(lobby, frame, actor.index, weights)
    assert.ok(weights.toArray().every(value => Number.isFinite(value) && value >= 0 && value <= 1))
    for (const [channel, value] of [weights.z, weights.w].entries()) {
      minimum[channel] = Math.min(minimum[channel], value)
      maximum[channel] = Math.max(maximum[channel], value)
    }
  }
  // Role gestures are staggered and include pauses, so frame 150 need not be
  // active. Both Activity gesture and Attention and response must actually vary.
  assert.ok(maximum.every((value, channel) => value - minimum[channel] > .05), `${actor.name}: frozen role gesture/attention`)
  assert.equal(p.distanceTo(start) > 1, actor.activity === 'walk, pause, look, return', `${actor.name}: route/activity mismatch`)
}
assert.equal(walkers, 4)
let heldAccessories = 0, movingAccessories = 0
for (const actor of accessories) {
  assert.ok(npcs.some(owner => actor.name.startsWith(`${owner.name} / `)), `${actor.name}: accessory has no exported NPC owner`)
  assert.equal(actor.morphCount, 0)
  assert.ok(lobby.manifest.groups.filter(group => group.actor === actor.index).every(group => !group.morphs?.length))
  readPose(lobby, 1, actor.index, p, q)
  const start = p.clone(), rotation = q.clone()
  const moves = [75, 150, 225, 400, 600, 900].some(frame => {
    readPose(lobby, frame, actor.index, p, q)
    return p.distanceTo(start) > .001 || q.angleTo(rotation) > .001
  })
  // npc_motion.py keeps the phone-holding left hand planted (pitch = 0),
  // while the right hand taps. Those phones/edges have authored channels but
  // intentionally constant transforms; books, cup and routed briefcase move.
  const heldPhone = / \/ phone(?: \/ feature edges)?$/.test(actor.name)
  assert.equal(moves, !heldPhone, `${actor.name}: accessory no longer follows its authored held/moving role`)
  if (heldPhone) heldAccessories++
  else movingAccessories++
}
assert.equal(heldAccessories, 6)
assert.equal(movingAccessories, 8)
assert.equal(lobby.manifest.fishLoopFrames, 1019)
for (const actor of fish) {
  assert.equal(actor.autonomous, true)
  assert.equal(actor.morphCount, 0)
  assert.equal(actor.loopFrames, 1019)
}
const doors = lobby.manifest.actors.filter(actor => actor.name.startsWith('Lobby • Elevator R1 /'))
assert.equal(doors.length, 3, 'R1 seam and both leaves must remain exported')
assert.ok(doors.every(actor => !actor.autonomous && !actor.morphCount), 'All R1 parts must remain on the journey clock')
const skills = load('../../public/models/rooms/skills', sceneFile(new URL('../../public/models/rooms/skills/scene.json', import.meta.url), 'skills'))
assert.equal(skills.manifest.navigation.animationFollowsWalk, false)
assert.equal(skills.manifest.navigation.route.loop, false)
assert.equal(skills.manifest.loop, true)
assert.equal(skills.manifest.frameEnd, 959)
for (const actor of skills.manifest.actors) {
  readPose(skills, 1, actor.index, p, q)
  const start = p.clone(), rotation = q.clone()
  readPose(skills, 960, actor.index, p, q)
  assert.ok(p.distanceTo(start) < 1e-5 && q.angleTo(rotation) < 1e-5)
}
console.log('PASS autonomous NPC packages: 17 lobby people, four routes, four native morphs, 14 owned accessory channels, six fish parts, three journey-clock R1 parts, looping Skills visitors and non-looping player route')
