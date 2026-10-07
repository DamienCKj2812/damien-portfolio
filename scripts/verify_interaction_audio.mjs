// Lifecycle/race regression checks without requiring an audio device or browser.
import assert from 'node:assert/strict'
import { createInteractionAudio } from '../src/audio/interactionAudio.js'

const tick = () => new Promise(resolve => setImmediate(resolve))
let time = 0, hidden = false, fetches = 0, starts = 0, stops = 0, decodes = 0, contextCount = 0
const contexts = []
const played = []
function createContext() {
  contextCount++
  const context = {
    state: 'suspended', destination: {},
    async resume() { this.state = 'running' },
    async suspend() { this.state = 'suspended' },
    async close() { this.state = 'closed' },
    async decodeAudioData(data) { decodes++;return { kind: new Uint8Array(data)[0] } },
    createBufferSource() { return { connect() {}, disconnect() {}, start() { starts++;played.push(this.buffer.kind) }, stop() { stops++ } } },
    createGain() { return { gain: { value: 0 }, connect() {}, disconnect() {} } },
  }
  contexts.push(context)
  return context
}
const audio = createInteractionAudio({ urls: { system: '/system.mp3', environment: '/environment.mp3' }, createContext,
  now: () => time, isHidden: () => hidden,
  fetchAudio: async url => { fetches++;return { ok: true, arrayBuffer: async () => new Uint8Array([url.includes('environment') ? 1 : 2]).buffer } },
})
audio.preload();await tick()
assert.equal(fetches, 2)
assert.equal(audio.hover, undefined, 'Hover playback must not be exposed')
assert.equal(contextCount, 0, 'Preloading must not create/unlock audio before a user gesture')
audio.click();await tick()
assert.equal(starts, 1, 'The first activation must unlock and play')
audio.click();await tick()
assert.equal(starts, 1, 'Duplicate activation must be suppressed')
time += 200;audio.environmentClick();await tick()
assert.equal(starts, 2)
time += 200;audio.environmentClick();await tick()
assert.equal(starts, 3)
assert.deepEqual(played, [2, 1, 1], 'System and environment clicks must use distinct decoded buffers')
assert.equal(fetches, 2);assert.equal(decodes, 2, 'Decoded sounds must be reused')
audio.setEnabled(false)
time += 200;audio.click();audio.environmentClick();await tick()
assert.equal(starts, 3, 'Mute must suppress all playback')
audio.setEnabled(true);audio.setVolume(0)
time += 200;audio.click();await tick();assert.equal(starts, 3)
audio.setVolume(.5)
time += 200;audio.click();audio.setEnabled(false);await tick()
assert.equal(starts, 3, 'A queued click must be cancelled if muted during decoding/resume')
audio.setEnabled(true);hidden = true;audio.suspend()
time += 200;audio.click();await tick()
assert.equal(starts, 3);assert.equal(contexts[0].state, 'suspended')
hidden = false
for (let i = 0; i < 6; i++) { time += 200;audio.click();await tick() }
assert.equal(starts, 9);assert.ok(stops >= 5, 'The voice count must be bounded')
audio.dispose();time += 200;audio.click();audio.environmentClick();await tick()
assert.equal(starts, 9);assert.equal(contexts[0].state, 'closed')
console.log('PASS click-only audio: distinct system/environment buffers, gesture unlock, buffer reuse, click limiting, mute/zero volume, queued-play cancellation, hidden-page suspension, bounded voices and disposal')
