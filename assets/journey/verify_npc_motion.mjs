// Cross-clock regression checks against the generated browser packages.
import assert from 'node:assert/strict'
import fs from 'node:fs'
import { Quaternion, Vector3, Vector4 } from 'three'
import { readPose } from '../../src/components/city/journeyTimeline.js'
import { sampleMorphWeights } from '../../src/components/city/roomJourney.js'

function load(base) {
  const manifest = JSON.parse(fs.readFileSync(new URL(`${base}/scene.json`, import.meta.url)))
  const buffer = fs.readFileSync(new URL(`${base}/animation.bin`, import.meta.url))
  assert.equal(buffer.byteLength, manifest.frameEnd * manifest.channelCount * manifest.channelStride * 4)
  return { manifest, animation: new Float32Array(buffer.buffer, buffer.byteOffset, buffer.byteLength / 4) }
}
const lobby = load('../../public/models/lobby')
const npcs = lobby.manifest.actors.filter(actor => actor.autonomous)
assert.equal(npcs.length, 18)
assert.equal(lobby.manifest.channelStride, 16)
const p = new Vector3(), q = new Quaternion(), weights = new Vector4()
let walkers = 0
for (const actor of npcs) {
  const group = lobby.manifest.groups.find(group => group.actor === actor.index && group.kind === 'points')
  assert.equal(group.morphs.length, actor.morphCount)
  assert.equal(actor.morphCount, 3)
  readPose(lobby, 1, actor.index, p, q)
  const start = p.clone(), rotation = q.clone()
  readPose(lobby, lobby.manifest.npcLoopFrames + 1, actor.index, p, q)
  assert.ok(p.distanceTo(start) < 1e-5 && q.angleTo(rotation) < 1e-5, 'NPC loop must close')
  readPose(lobby, 400, actor.index, p, q)
  if (p.distanceTo(start) > 1) walkers++
  sampleMorphWeights(lobby, 150, actor.index, weights)
  assert.ok(weights.toArray().every(Number.isFinite))
  assert.ok(weights.z > .01, 'Activity gestures must animate at a stationary camera frame')
}
assert.equal(walkers, 4)
assert.ok(lobby.manifest.actors.some(actor => !actor.autonomous && /R1/.test(actor.name)), 'R1 must remain on the journey clock')
const skills = load('../../public/models/rooms/skills')
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
console.log('PASS autonomous NPC packages: 18 lobby activities, four lobby routes, native morphs, separate door clock, looping Skills visitors and non-looping player route')
