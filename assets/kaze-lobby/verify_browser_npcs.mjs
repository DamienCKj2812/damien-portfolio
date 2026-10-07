import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const base = new URL('../../public/models/lobby/', import.meta.url)
const manifest = JSON.parse(readFileSync(new URL('scene.json', base), 'utf8'))
const animation = readFileSync(new URL(manifest.animation, base))
const geometry = readFileSync(new URL(manifest.geometry, base))
const people = manifest.actors.filter(actor => actor.morphCount > 0)
const accessories = manifest.actors.filter(actor => actor.autonomous && !actor.morphCount && actor.motionType !== 'holographicFish')
assert.equal(people.length, 17)
assert.ok(!manifest.channels.includes('Lobby • Escalator / riding upstairs'))
assert.equal(manifest.channelStride, 16)
assert.equal(manifest.npcLoopFrames, 1019)
assert.equal(animation.length, manifest.frameEnd * manifest.channelCount * 16 * 4)
assert.ok(accessories.length > 0)
assert.ok(people.every(actor => actor.autonomous && actor.morphCount === 4 && actor.activity))

const sample = (frame, actor, offset) => animation.readFloatLE(((frame - 1) * manifest.channelCount * 16 + actor.index * 16 + offset) * 4)
for (const actor of [...people, ...accessories]) {
  for (let offset = 0; offset < 16; offset++) {
    assert.ok(Math.abs(sample(1, actor, offset) - sample(1020, actor, offset)) < 1e-5, `${actor.name}: loop seam`)
  }
  if (actor.morphCount) {
    const group = manifest.groups.find(group => group.actor === actor.index && group.kind === 'points')
    assert.equal(group.morphs.length, 4)
    for (const morph of group.morphs) {
      assert.equal(morph.floatCount, group.vertexCount * 3)
      assert.ok(morph.byteOffset + morph.floatCount * 4 <= geometry.length)
    }
    for (const offset of [14, 15]) {
      const values = Array.from({ length: manifest.frameEnd }, (_, i) => sample(i + 1, actor, offset))
      assert.ok(values.every(value => Number.isFinite(value) && value >= 0 && value <= 1))
      assert.ok(Math.max(...values) - Math.min(...values) > .05, `${actor.name}: frozen activity`)
    }
  }
}
assert.ok(manifest.actors.filter(actor => !actor.autonomous).every(actor => !actor.morphCount), 'Doors must remain journey-driven')
console.log(`PASS lobby: ${people.length} autonomous NPCs, ${accessories.length} accessory channels, role gestures, morph buffers and loop seams`)
