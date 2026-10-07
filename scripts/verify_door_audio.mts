import assert from 'node:assert/strict'
import fs from 'node:fs'
import { journeyFile } from './node_json.mts'
import { createHash } from 'node:crypto'
import { createDoorSoundTiming, RETURN_DOOR_SOUND_DELAY_MS } from '../src/components/city/doorSoundTiming.ts'
import { createInteractionAudio } from '../src/audio/interactionAudio.ts'
import type { InteractionAudioContext, InteractionAudioGain } from '../src/types/audio.ts'

const config = journeyFile(new URL('../public/models/journey.json', import.meta.url))
const timing = createDoorSoundTiming()
assert.deepEqual(timing.journey(config.lobbyHoldFrame, config), [], 'Interior load hold is silent')
assert.equal(timing.journey(config.lobbyHoldFrame + 1, config)[0].id, 'main-gate-open')
assert.deepEqual(timing.journey(280, config), [], 'Open gate does not repeat')
timing.journey(200, config)
assert.equal(timing.journey(260, config)[0].id, 'main-gate-open', 'Reverse then reopen re-arms the gate')
assert.deepEqual(timing.journey(config.elevatorRevealFrame, config), [])
assert.equal(timing.journey(config.elevatorRevealFrame + 1, config)[0].id, 'lobby-elevator-open')
assert.deepEqual(timing.journey(config.frameEnd, config), [])
assert.deepEqual(timing.departure(296), [], 'Room load hold cannot open/sound the doors')
assert.equal(timing.departure(300)[0].id, 'elevator-open')
assert.deepEqual(timing.departure(350), [])
timing.resetDeparture();assert.equal(timing.departure(510)[0].id, 'elevator-open', 'Reduced motion still signals a selected opening')
timing.resetReturn();assert.deepEqual(timing.returning(360, false), [])
assert.deepEqual(timing.returning(350, false), [{ id: 'elevator-return-close', delay: RETURN_DOOR_SOUND_DELAY_MS }])
assert.deepEqual(timing.returning(300, false), []);assert.deepEqual(timing.completeReturn(), [])
timing.resetReturn();assert.deepEqual(timing.returning(180, true), [])
assert.equal(timing.completeReturn()[0].delay, 250, 'Instant reduced-motion return defers its closing cue')

const original = fs.readFileSync(new URL('../assets/media/audio/effects/sci-fi-door.mp3', import.meta.url))
const deployed = fs.readFileSync(new URL('../public/media/audio/effects/sci-fi-door.mp3', import.meta.url))
assert.equal(createHash('sha256').update(original).digest('hex'), createHash('sha256').update(deployed).digest('hex'))
let time = 0, hidden = false, started = 0, stopped = 0, created = 0, decoded = 0, nextTimer = 0
const timers = new Map<number, { callback: () => void; delay: number }>()
const tick = () => new Promise(resolve => setImmediate(resolve))
const context: InteractionAudioContext<object, object, InteractionAudioGain<object>> & { state: string } = {
  state: 'suspended', destination: {}, async resume() { this.state = 'running' }, async suspend() { this.state = 'suspended' }, async close() { this.state = 'closed' },
  async decodeAudioData() { decoded++;return {} },
  createBufferSource() { return { connect() {}, disconnect() {}, start() { started++ }, stop() { stopped++ } } },
  createGain() { return { gain: { value: 0 }, connect() {}, disconnect() {} } },
}
const engine = createInteractionAudio({ urls: { door: '/door.mp3' }, now: () => time, isHidden: () => hidden,
  createContext: () => { created++;return context }, fetchAudio: async () => ({ ok: true, arrayBuffer: async () => new ArrayBuffer(4) }),
  setTimer: (callback, delay) => { const id = ++nextTimer;timers.set(id, { callback, delay });return id }, clearTimer: id => timers.delete(id),
})
const fire = async () => { for (const [id, entry] of [...timers]) { timers.delete(id);time += entry.delay;entry.callback() } await tick() }
engine.doorSound('open');assert.equal(created, 0)
await engine.unlock();engine.doorSound('open');await tick();assert.equal(started, 1)
engine.doorSound('open');await tick();assert.equal(started, 1)
engine.doorSound('close', 250);assert.equal(started, 1);assert.equal(timers.size, 1)
await fire();assert.equal(started, 2);assert.equal(decoded, 1)
engine.doorSound('close', 250);engine.cancelDoorSounds();assert.equal(timers.size, 0)
engine.doorSound('open');engine.cancelDoorSounds();await tick();assert.equal(started, 2, 'Cancel aborts an async queued opening')
engine.doorSound('close', 250);engine.setEnabled(false);assert.equal(timers.size, 0);await fire();assert.equal(started, 2)
engine.setEnabled(true);engine.doorSound('close', 250);hidden = true;engine.suspend();assert.equal(timers.size, 0)
hidden = false;engine.doorSound('open');await tick();assert.equal(started, 2, 'Render-driven audio cannot resume a suspended context')
await engine.unlock();engine.doorSound('close', 250);engine.dispose();assert.equal(timers.size, 0);assert.equal(context.state, 'closed');assert(stopped >= 2)
console.log('PASS door audio: main gate/lobby/cabin opening thresholds, delayed normal/instant return closing, one-shot/reverse handling, mute/cancel/hidden/disposal and exact asset copy')
