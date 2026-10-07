import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { Matrix4, Quaternion, Vector3 } from 'three'
import { readPose } from '../../src/components/city/journeyTimeline.ts'
import { sceneFile } from '../../scripts/node_json.mts'

const base = new URL('../../public/models/lobby/', import.meta.url)
const manifest = sceneFile(new URL('scene.json', base), 'lobby')
const binary = await readFile(new URL(manifest.animation, base))
const geometry = await readFile(new URL(manifest.geometry, base))
const animation = new Float32Array(binary.buffer, binary.byteOffset, binary.byteLength / 4)
const assets = { manifest, animation }
assert.equal(binary.byteLength, (manifest.frameEnd - manifest.frameStart + 1) * manifest.channelCount * manifest.channelStride * 4)
assert.equal(manifest.fishLoopFrames, 1019)
assert.equal(manifest.autonomousLoopFrames, 1019)
const fish = manifest.actors.filter(actor => actor.motionType === 'holographicFish')
assert.equal(fish.length, 6, 'Nested fins must retain their own animated channels.')
assert.deepEqual(fish.map(actor => actor.part).sort(), ['body', 'dorsal', 'lower tail', 'lower ventral', 'near pectoral', 'upper tail'])

function pose(frame: number, channel: number) {
  const position = new Vector3(), quaternion = new Quaternion(), scale = new Vector3()
  readPose(assets, frame, channel, position, quaternion, scale)
  return { position, quaternion, scale, matrix: new Matrix4().compose(position, quaternion, scale) }
}

for (const actor of fish) {
  assert.equal(actor.autonomous, true)
  assert.equal(actor.loopFrames, 1019)
  const groups = manifest.groups.filter(group => group.actor === actor.index)
  assert(groups.some(group => group.kind === 'points'))
  assert(groups.some(group => group.kind === 'glow'), `${actor.part}: moving outlines are missing.`)
  for (const group of groups) assert(group.byteOffset + group.floatCount * 4 <= geometry.byteLength)
  const first = pose(1, actor.index), last = pose(1020, actor.index)
  assert(first.position.distanceTo(last.position) < 1e-5)
  assert(first.quaternion.angleTo(last.quaternion) < 1e-5)
  assert(Array.from({ length: 42 }, (_, index) => pose(1 + index * 4, actor.index)).some(sample => first.quaternion.angleTo(sample.quaternion) > .04))
}

// Hold the journey/camera at the exhibit approach while sampling the fish's
// independent clock. Actual package data must keep the camera still and move
// the tail, including its inherited body/tail-joint transformations.
const heldJourneyFrame = 420
const camera = pose(heldJourneyFrame, 0)
const lowerTail = fish.find(actor => actor.part === 'lower tail')
assert.ok(lowerTail?.loopFrames)
const points = manifest.groups.find(group => group.actor === lowerTail.index && group.kind === 'points')
assert.ok(points)
const data = new Float32Array(geometry.buffer, geometry.byteOffset + points.byteOffset, points.floatCount)
const tip = new Vector3(data[0], data[1], data[2])
for (let offset = 0; offset < data.length; offset += points.stride) {
  if (data[offset] < tip.x) tip.set(data[offset], data[offset + 1], data[offset + 2])
}
const positions = []
for (let clockFrame = 0; clockFrame < 170; clockFrame += 4) {
  const fixedCamera = pose(heldJourneyFrame, 0)
  assert(fixedCamera.position.distanceTo(camera.position) < 1e-8)
  assert(fixedCamera.quaternion.angleTo(camera.quaternion) < 1e-7)
  positions.push(tip.clone().applyMatrix4(pose(1 + clockFrame % lowerTail.loopFrames, lowerTail.index).matrix))
}
assert(Math.max(...positions.map(point => point.y)) - Math.min(...positions.map(point => point.y)) > .8)
assert(!manifest.actors.filter(actor => /door leaf|center door seam/.test(actor.name)).some(actor => actor.autonomous))
console.log('PASS holographic fish: nested animated parts, moving point/outline groups, seamless loop, fixed camera with independently swishing tail.')
