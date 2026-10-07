import assert from 'node:assert/strict'
import fs from 'node:fs'
import { journeyFile, sceneFile } from './node_json.mts'
import { Quaternion, Vector3 } from 'three'
import { createLobbyPortalClip, updateLobbyPortalClip } from '../src/components/city/lobbyPortal.ts'

const journey = journeyFile(new URL('../public/models/journey.json', import.meta.url))
const city = sceneFile(new URL('../public/models/city/scene.json', import.meta.url), 'city')
const bytes = fs.readFileSync(new URL('../public/models/city/animation.bin', import.meta.url))
const motion = new Float32Array(bytes.buffer, bytes.byteOffset, bytes.byteLength / 4)
const basis = new Quaternion().setFromAxisAngle(new Vector3(1, 0, 0), -Math.PI / 2)
const clip = createLobbyPortalClip(journey.lobbyPortal, basis)
const originalPlanes = clip.planes
let outsideFrames = 0
for (let frame = journey.lobbyRevealFrame; frame < journey.cityHideFrame; frame++) {
  const index = (frame - 1) * city.channelCount * city.channelStride
  const eye = new Vector3().fromArray(motion, index).applyQuaternion(basis)
  if (!updateLobbyPortalClip(clip, eye)) continue
  outsideFrames++
  assert(clip.planes.every(plane => plane.distanceToPoint(clip.center) >= -1e-5))
  assert(clip.corners.every(corner => clip.planes.every(plane => plane.distanceToPoint(corner) >= -1e-5)))
  for (const sign of [-1, 1]) {
    const outside = new Vector3(...journey.lobbyPortal.center)
    outside.x += sign * journey.lobbyPortal.width * .75
    outside.applyQuaternion(basis)
    assert(clip.planes.some(plane => plane.distanceToPoint(outside) < -.01), 'Lobby must not cover scenery outside the doorway')
  }
}
assert(outsideFrames > 100)
const entered = clip.center.clone().addScaledVector(clip.forward, .2)
assert.equal(updateLobbyPortalClip(clip, entered), false)
assert(clip.planes.every(plane => plane.distanceToPoint(entered) > 0))
assert.equal(updateLobbyPortalClip(clip, clip.center.clone().addScaledVector(clip.forward, -10)), true)
assert.equal(clip.planes, originalPlanes, 'Reversing must reuse the same four planes')
assert.equal(clip.planes.length, 4)
console.log(`PASS lobby aperture: ${outsideFrames} authored approach frames preserve exterior, entering clears clipping, reverse reuses planes`)
