// Verify the Projects package independently of other elevator destinations.
import assert from 'node:assert/strict'
import { createHash } from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { Quaternion, Vector3, Vector4 } from 'three'
import { createRoomAlignment, sampleMorphWeights } from '../../src/components/city/roomJourney.ts'
import { readPose } from '../../src/components/city/journeyTimeline.ts'
import { hallwayLayoutFile, journeyFile, sceneFile } from '../../scripts/node_json.mts'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..')
const base = path.join(root, 'public/models/rooms/projects')
const manifest = sceneFile(path.join(base, 'scene.json'), 'projects')
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
let minRibX = Infinity, maxRibX = -Infinity
const layout = hallwayLayoutFile(path.join(root, 'assets/project-hallway/hallway-layout.json'))
assert.equal(layout.ceiling.ribCount, 41)
assert.equal(layout.ceiling.curvedLightRails, 5)
assert.equal(layout.ceiling.perimeterLightRails, 2)
// The spacious-layout refresh stretches the existing roof, not its topology.
// caa19ef's native validation and ceiling-browser-verification.json retain 41
// six-sided ribs, 424596 triangle vertices and 5 * 287 + 2 light segments.
// Match validate_project_hallway.py's width-relative envelope; 4.85 m alone
// was the old 10.2 m-wide hallway assumption, already stale before migration.
const widthRatio = layout.widthMeters / 10.2
const roofStart = -10, tolerance = 1e-4, roofSamples = 287
const verticesPerRib = roofSamples * 6 * 2 * 3 + 2 * 4 * 3
const ribGroups = manifest.groups.filter(group => group.role === 'ceilingRib')
const lightGroups = manifest.groups.filter(group => group.role === 'ceilingLight')
assert.equal(ribGroups.length, 1)
assert.equal(lightGroups.length, 1)
for (const [group, kind, id] of [[ribGroups[0], 'solid', 'wave-ribs'], [lightGroups[0], 'glow', 'ceiling-lights']] as const) {
  assert.equal(group.actor, 0, `${id}: ceiling must remain static`)
  assert.equal(group.kind, kind, `${id}: native render role changed`)
  assert.equal(group.id, id)
  assert.equal(group.stride, 4)
  assert.equal(group.floatCount, group.vertexCount * group.stride)
  assert.ok(!group.morphs?.length, `${id}: ceiling must not acquire visitor morphs`)
}
assert.equal(ribGroups[0].vertexCount, layout.ceiling.ribCount * verticesPerRib, 'Missing or changed authored rib topology')
assert.equal(lightGroups[0].vertexCount, 2 * (layout.ceiling.curvedLightRails * roofSamples + layout.ceiling.perimeterLightRails))
for (const group of manifest.groups) {
  assert.ok(group.byteOffset + group.floatCount * 4 <= geometry.length)
  for (const morph of group.morphs || []) assert.ok(morph.byteOffset + morph.floatCount * 4 <= geometry.length)
  if (group.actor !== 0) continue
  const start = group.byteOffset / 4
  if (group.kind === 'points') {
    for (let i = start; i < start + group.floatCount; i += 5) {
      if (floats[i + 2] > 5.9 && Math.abs(floats[i]) < 3.8 * widthRatio) interiorCeilingDots++
    }
  } else if (group.role === 'ceilingRib' && group.kind === 'solid') {
    for (let i = start; i < start + group.floatCount; i += 4) {
      const [x, y, z, luminance] = floats.subarray(i, i + 4)
      assert.ok(Math.abs(x) < 4.85 * widthRatio && z > 5.87 && z < 6.19
        && y >= roofStart - .0425 - tolerance && y <= layout.lengthMeters + .0425 + tolerance,
      'Wave ribs leave the authored ceiling envelope')
      assert.ok(luminance >= 0 && luminance < .04, 'Rib surfaces must remain dark')
      ribVertices++
      if (y < -2) entryRibVertices++
      minRibZ = Math.min(minRibZ, z);maxRibZ = Math.max(maxRibZ, z)
      minRibY = Math.min(minRibY, y);maxRibY = Math.max(maxRibY, y)
      minRibX = Math.min(minRibX, x);maxRibX = Math.max(maxRibX, x)
    }
  } else if (group.role === 'ceilingLight' && group.kind === 'glow') {
    for (let i = start; i < start + group.floatCount; i += 8) {
      lightSegments++
      for (const endpoint of [i, i + 4]) {
        assert.ok(Math.abs(floats[endpoint]) <= 4.85 * widthRatio
          && floats[endpoint + 1] >= roofStart - tolerance && floats[endpoint + 1] <= layout.lengthMeters + tolerance
          && floats[endpoint + 2] >= 5.878 - tolerance && floats[endpoint + 2] < 6.02, 'Light rail leaves its authored envelope/clearance')
        assert.ok(floats[endpoint + 3] > 1, 'Integrated light rails must remain luminous')
      }
      if (Math.abs(floats[i] - floats[i + 4]) > .001) curvedSegments++
    }
  }
}
assert.equal(interiorCeilingDots, 0, 'Old dotted ceiling remains in browser export')
// Exported ribs are concatenated complete meshes, each with side triangles and
// two end caps. Check all 41, so one long rib cannot stand in for a missing roof.
const ribCenters = new Set<string>()
for (let rib = 0; rib < layout.ceiling.ribCount; rib++) {
  const start = ribGroups[0].byteOffset / 4 + rib * verticesPerRib * 4
  let minY = Infinity, maxY = -Infinity, minZ = Infinity, maxZ = -Infinity
  for (let i = start; i < start + verticesPerRib * 4; i += 4) {
    minY = Math.min(minY, floats[i + 1]);maxY = Math.max(maxY, floats[i + 1])
    minZ = Math.min(minZ, floats[i + 2]);maxZ = Math.max(maxZ, floats[i + 2])
  }
  assert.ok(minY <= roofStart + tolerance && maxY >= layout.lengthMeters - tolerance, `Rib ${rib}: incomplete entrance/hallway coverage`)
  assert.ok(maxZ - minZ > .25, `Rib ${rib}: missing sculpted depth`)
  ribCenters.add(floats[start].toFixed(4))
}
assert.equal(ribCenters.size, layout.ceiling.ribCount, 'Repeated rib meshes cannot substitute for the 41 distinct louvers')
assert.ok(minRibX < -4.72 * widthRatio && maxRibX > 4.72 * widthRatio, 'Ribs no longer cover the spacious hallway width')
// Recover the seven native polylines from adjacent segment endpoints. Curved
// rails have 287 segments each; perimeter rails span the roof in one segment.
const lightStart = lightGroups[0].byteOffset / 4
const lightEnd = lightStart + lightGroups[0].floatCount
let curvedRails = 0, perimeterRails = 0
for (let start = lightStart; start < lightEnd;) {
  let end = start + 8
  while (end < lightEnd && [0, 1, 2].every(axis => Math.abs(floats[end - 4 + axis] - floats[end + axis]) < tolerance)) end += 8
  const segments = (end - start) / 8
  assert.ok(Math.abs(floats[start + 1] - roofStart) < tolerance && Math.abs(floats[end - 3] - layout.lengthMeters) < tolerance, 'Light rail must cover the complete roof')
  if (segments === 1) {
    perimeterRails++
    assert.ok(Math.abs(Math.abs(floats[start]) - 4.84 * widthRatio) < tolerance
      && Math.abs(floats[start] - floats[start + 4]) < tolerance
      && Math.abs(floats[start + 2] - 5.996) < tolerance
      && Math.abs(floats[start + 6] - 5.996) < tolerance, 'Perimeter rail must remain at the authored edge and height')
  } else {
    curvedRails++
    assert.equal(segments, roofSamples, 'Curved integrated strip topology changed')
  }
  start = end
}
assert.equal(curvedRails, layout.ceiling.curvedLightRails)
assert.equal(perimeterRails, layout.ceiling.perimeterLightRails)
assert.ok(ribVertices > 100000 && entryRibVertices > 1000, 'Flowing rib ceiling must cover the hallway and entrance')
assert.ok(minRibY <= -10 && maxRibY >= layout.lengthMeters - .01)
assert.ok(maxRibZ - minRibZ > .25, 'Ribs must have real sculpted depth')
assert.ok(lightSegments > 1000 && curvedSegments > 1000, 'Curved integrated light strips missing')
const room = { manifest, animation: new Float32Array(animation.buffer, animation.byteOffset, animation.length / 4) }
const journey = journeyFile(path.join(root, 'public/models/journey.json'))
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
  ribWidthRange: [minRibX, maxRibX], ribHeightRange: [minRibZ, maxRibZ], lightSegments, curvedSegments,
  verifiedRibs: ribCenters.size, verifiedCurvedRails: curvedRails, verifiedPerimeterRails: perimeterRails,
  doorwayAligned: true, verifiedNpcLoops: manifest.actors.length,
  checkedExistingMotion: Boolean(process.argv[2]), validation: 'passed' }
// Keep verification read-only unless an explicit evidence destination is given.
if (process.env.CEILING_VERIFICATION_REPORT) fs.writeFileSync(process.env.CEILING_VERIFICATION_REPORT, JSON.stringify(report, null, 2) + '\n')
console.log(JSON.stringify(report, null, 2))
