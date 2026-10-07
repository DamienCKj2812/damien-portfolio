// Verify the Projects package independently of other elevator destinations.
import assert from 'node:assert/strict'
import { createHash } from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { Quaternion, Vector3, Vector4 } from 'three'
import { createRoomAlignment, sampleMorphWeights } from '../../src/components/city/roomJourney.js'
import { readPose } from '../../src/components/city/journeyTimeline.js'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..')
const base = path.join(root, 'public/models/rooms/projects')
const manifest = JSON.parse(fs.readFileSync(path.join(base, 'scene.json'), 'utf8'))
const geometry = fs.readFileSync(path.join(base, manifest.geometry))
const animation = fs.readFileSync(path.join(base, manifest.animation))
const floats = new Float32Array(geometry.buffer, geometry.byteOffset, geometry.length / 4)
const animationHash = createHash('sha256').update(animation).digest('hex')
const assetHash = createHash('sha256').update(geometry).update(animation).digest('hex').slice(0, 12)
assert.equal(manifest.assetHash, assetHash, 'Manifest and buffers must be regenerated together')
assert.equal(manifest.projects.length, 16)
assert.equal(manifest.actors.length, 15)
assert.equal(manifest.channelStride, 16)
assert.equal(animation.length, 1200 * manifest.channelCount * 16 * 4)
if (process.argv[2]) assert.equal(animationHash, process.argv[2], 'Ceiling edit changed existing room motion')
assert.ok(floats.every(Number.isFinite))
let interiorCeilingDots = 0, ribVertices = 0, entryRibVertices = 0, lightSegments = 0, curvedSegments = 0
let minRibZ = Infinity, maxRibZ = -Infinity, minRibY = Infinity, maxRibY = -Infinity
const layout = JSON.parse(fs.readFileSync(path.join(root, 'assets/project-hallway/hallway-layout.json'), 'utf8'))
assert.equal(layout.ceiling.ribCount, 41)
assert.equal(layout.ceiling.curvedLightRails, 5)
assert.equal(layout.ceiling.perimeterLightRails, 2)
for (const group of manifest.groups) {
  assert.ok(group.byteOffset + group.floatCount * 4 <= geometry.length)
  for (const morph of group.morphs || []) assert.ok(morph.byteOffset + morph.floatCount * 4 <= geometry.length)
  if (group.actor !== 0) continue
  const start = group.byteOffset / 4
  if (group.kind === 'points') {
    for (let i = start; i < start + group.floatCount; i += 5) {
      if (floats[i + 2] > 5.9 && Math.abs(floats[i]) < 3.8) interiorCeilingDots++
    }
  } else if (group.role === 'ceilingRib' && group.kind === 'solid') {
    for (let i = start; i < start + group.floatCount; i += 4) {
      const [x, y, z, luminance] = floats.subarray(i, i + 4)
      assert.ok(Math.abs(x) < 4.85 && z > 5.87 && z < 6.19, 'Wave ribs leave the authored ceiling envelope')
      assert.ok(luminance >= 0 && luminance < .04, 'Rib surfaces must remain dark')
      ribVertices++
      if (y < -2) entryRibVertices++
      minRibZ = Math.min(minRibZ, z);maxRibZ = Math.max(maxRibZ, z)
      minRibY = Math.min(minRibY, y);maxRibY = Math.max(maxRibY, y)
    }
  } else if (group.role === 'ceilingLight' && group.kind === 'glow') {
    for (let i = start; i < start + group.floatCount; i += 8) {
      lightSegments++
      assert.ok(floats[i + 2] > 5.86 && floats[i + 2] < 6.02)
      if (Math.abs(floats[i] - floats[i + 4]) > .001) curvedSegments++
    }
  }
}
assert.equal(interiorCeilingDots, 0, 'Old dotted ceiling remains in browser export')
assert.ok(ribVertices > 100000 && entryRibVertices > 1000, 'Flowing rib ceiling must cover the hallway and entrance')
assert.ok(minRibY <= -10 && maxRibY >= layout.lengthMeters - .01)
assert.ok(maxRibZ - minRibZ > .25, 'Ribs must have real sculpted depth')
assert.ok(lightSegments > 1000 && curvedSegments > 1000, 'Curved integrated light strips missing')
const room = { manifest, animation: new Float32Array(animation.buffer, animation.byteOffset, animation.length / 4) }
const journey = JSON.parse(fs.readFileSync(path.join(root, 'public/models/journey.json'), 'utf8'))
const alignment = createRoomAlignment(room, journey)
const entrance = new Vector3().fromArray(manifest.entranceAnchor).applyQuaternion(alignment.rotation).add(alignment.position)
assert.ok(entrance.distanceTo(new Vector3().fromArray(journey.elevatorOffset)) < .00001, 'Hallway no longer meets cabin threshold')
assert.ok(new Vector3(0, 1, 0).applyQuaternion(alignment.rotation).y < -.999)
const p = new Vector3(), q = new Quaternion(), a = new Vector4(), b = new Vector4()
for (const actor of manifest.actors) {
  sampleMorphWeights(room, 1, actor.index, a)
  sampleMorphWeights(room, 1201, actor.index, b)
  assert.ok(a.clone().sub(b).length() < 1e-6, 'NPC morph loop no longer wraps')
  readPose(room, 1, actor.index, p, q)
  const start = p.clone(), rotation = q.clone().normalize()
  readPose(room, 1201, actor.index, p, q)
  assert.ok(start.distanceTo(p) < 1e-6 && rotation.angleTo(q.normalize()) < 1e-6)
  sampleMorphWeights(room, 46, actor.index, b)
  assert.ok(a.clone().sub(b).length() > .001, `Missing visitor motion: ${actor.name}`)
}
const report = { assetHash, animationHash, geometryBytes: geometry.length, animationBytes: animation.length,
  flowingRibs: layout.ceiling.ribCount, curvedLightRails: layout.ceiling.curvedLightRails,
  perimeterLightRails: layout.ceiling.perimeterLightRails, interiorCeilingDots, ribVertices, entryRibVertices,
  ribHeightRange: [minRibZ, maxRibZ], lightSegments, curvedSegments, doorwayAligned: true, verifiedNpcLoops: manifest.actors.length,
  checkedExistingMotion: Boolean(process.argv[2]), validation: 'passed' }
fs.writeFileSync(path.join(root, 'assets/project-hallway/ceiling-browser-verification.json'), JSON.stringify(report, null, 2) + '\n')
console.log(JSON.stringify(report, null, 2))
