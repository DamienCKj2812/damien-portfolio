import assert from 'node:assert/strict'
import fs from 'node:fs'
import { sceneFile } from './node_json.mts'
import { createHash } from 'node:crypto'
import { createHallwayPortalAudio } from '../src/components/city/hallwayPortalAudio.ts'
import { createInteractionAudio } from '../src/audio/interactionAudio.ts'
import type { InteractionAudioContext, InteractionAudioGain } from '../src/types/audio.ts'

const manifest = sceneFile(new URL('../public/models/rooms/projects/scene.json', import.meta.url), 'projects')
const [academic, personal] = manifest.navigation.categories.filter(category => category.door)
assert.ok(academic.door && personal.door)
const tracker = createHallwayPortalAudio(manifest.navigation)
const a = academic.door.y, p = personal.door.y
assert.deepEqual(tracker.update(a - 1), [])
for (const y of [a - .05, a + .05, a - .1, a + .1]) assert.deepEqual(tracker.update(y), [], 'Threshold jitter stays silent')
assert.deepEqual(tracker.update(a + .5).map(event => [event.id, event.direction]), [[academic.id, 'enter']])
assert.deepEqual(tracker.update(a + .6), [], 'Standing beyond the door cannot repeat')
assert.deepEqual(tracker.update(a - .5).map(event => [event.id, event.direction]), [[academic.id, 'exit']])
assert.deepEqual(tracker.update(p + 1).map(event => [event.id, event.direction]), [[academic.id, 'enter'], [personal.id, 'enter']])
assert.deepEqual(tracker.update(a - 1).map(event => [event.id, event.direction]), [[personal.id, 'exit'], [academic.id, 'exit']])
assert.deepEqual(tracker.update(p + 1, false), [], 'Detail/modal/seek movement rebaselines silently')
assert.deepEqual(tracker.update(p + 2), [])
tracker.reset()
assert.deepEqual(tracker.update(a + 1), [], 'Arrival/remount must not play a portal sound')

const original = fs.readFileSync(new URL('../assets/media/audio/effects/light-saber.mp3', import.meta.url))
const packaged = fs.readFileSync(new URL('../public/media/audio/effects/light-saber.mp3', import.meta.url))
assert.equal(createHash('sha256').update(packaged).digest('hex'), createHash('sha256').update(original).digest('hex'))
let time = 0, hidden = false, created = 0, started = 0, stopped = 0, decodes = 0
const tick = () => new Promise(resolve => setImmediate(resolve))
const context: InteractionAudioContext<object, object, InteractionAudioGain<object>> & { state: string } = {
  state: 'suspended', destination: {},
  async resume() { this.state = 'running' }, async suspend() { this.state = 'suspended' }, async close() { this.state = 'closed' },
  async decodeAudioData() { decodes++;return {} },
  createBufferSource() { return { connect() {}, disconnect() {}, start() { started++ }, stop() { stopped++ } } },
  createGain() { return { gain: { value: 0 }, connect() {}, disconnect() {} } },
}
const engine = createInteractionAudio({ urls: { system: '/system.mp3', environment: '/environment.mp3', portal: '/light-saber.mp3' },
  now: () => time, isHidden: () => hidden, createContext: () => { created++;return context },
  fetchAudio: async () => ({ ok: true, arrayBuffer: async () => new ArrayBuffer(4) }),
})
engine.preload();engine.portalCrossing(academic.id);await tick()
assert.equal(created, 0, 'Frame-based crossings must not create audio before a trusted unlock')
await engine.unlock()
engine.portalCrossing(academic.id);await tick();assert.equal(started, 1)
engine.portalCrossing(academic.id);await tick();assert.equal(started, 1, 'Duplicate portal activation is limited')
engine.portalCrossing(personal.id);await tick();assert.equal(started, 2, 'Distinct doors may sound in the same movement update')
time += 200;engine.portalCrossing(academic.id);await tick();assert.equal(started, 3, 'Reverse passage can reuse the sound')
assert.equal(decodes, 1, 'The lightsaber buffer is decoded once')
engine.setEnabled(false);time += 200;engine.portalCrossing(personal.id);await tick();assert.equal(started, 3)
engine.setEnabled(true);engine.setVolume(0);time += 200;engine.portalCrossing(personal.id);await tick();assert.equal(started, 3)
engine.setVolume(.45);hidden = true;engine.suspend();time += 200;engine.portalCrossing(personal.id);await tick();assert.equal(started, 3)
hidden = false;time += 200;engine.portalCrossing(personal.id);await tick();assert.equal(started, 3, 'Suspended frame effects cannot resume themselves')
await engine.unlock();time += 200;engine.portalCrossing(personal.id);engine.setEnabled(false);await tick();assert.equal(started, 3, 'Mute cancels a queued crossing')
engine.dispose();assert.equal(context.state, 'closed');assert(stopped >= 3)
console.log('PASS category portal audio: enter/exit order, jitter suppression, silent arrival/seek/modal, exact asset copy, mute/zero volume, gesture-only context, buffer reuse and cleanup')
