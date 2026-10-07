// One decoded buffer per effect, short-lived voices, and no animation/timer loop.
export function createInteractionAudio({ urls, createContext = () => new (window.AudioContext || window.webkitAudioContext)(), fetchAudio = fetch, now = () => performance.now(), isHidden = () => document.hidden, onError = () => {}, setTimer = setTimeout, clearTimer = clearTimeout }) {
  const abort = new AbortController()
  const files = new Map(), buffers = new Map(), voices = new Set()
  const portalTimes = new Map()
  const doorTimes = new Map(), doorTimers = new Map()
  let doorGeneration = 0
  let lastClick = -Infinity
  let context, enabled = true, volume = .45, disposed = false, generation = 0

  function load(kind) {
    if (!files.has(kind)) {
      const pending = fetchAudio(urls[kind], { signal: abort.signal }).then(response => {
        if (!response.ok) throw new Error(`Could not load ${kind} sound`)
        return response.arrayBuffer()
      }).catch(error => {
        files.delete(kind)
        if (!disposed && error.name !== 'AbortError') onError()
        return null
      })
      files.set(kind, pending)
    }
    return files.get(kind)
  }
  function preload() { if (!disposed) for (const kind of Object.keys(urls)) void load(kind) }
  function stop(voice) {
    voices.delete(voice)
    voice.source.onended = null
    try { voice.source.stop() } catch { /* A completed source is already stopped. */ }
    voice.source.disconnect();voice.gain.disconnect()
  }
  function cancelDoorSounds() {
    doorGeneration++
    for (const timer of doorTimers.values()) clearTimer(timer)
    doorTimers.clear()
    doorTimes.clear()
    for (const voice of [...voices]) if (voice.kind === 'door') stop(voice)
  }
  function stopAll() { generation++;cancelDoorSounds();for (const voice of [...voices]) stop(voice) }
  async function unlock() {
    if (disposed || !enabled || isHidden()) return false
    try {
      context ||= createContext()
      // resume() must be requested directly from a pointer/keyboard gesture.
      const resume = context.state === 'running' ? Promise.resolve() : context.resume()
      await resume
      return !disposed && context.state === 'running'
    } catch { return false }
  }
  async function decode(kind) {
    if (!buffers.has(kind)) {
      const pending = load(kind).then(data => data && context.decodeAudioData(data.slice(0))).catch(() => {
        buffers.delete(kind)
        if (!disposed) onError()
        return null
      })
      buffers.set(kind, pending)
      // Failed downloads can be retried when effects are re-enabled.
      void pending.then(buffer => { if (!buffer) buffers.delete(kind) })
    }
    return buffers.get(kind)
  }
  async function play(kind, portalId = 'portal') {
    if (disposed || !enabled || !volume || isHidden() || !urls[kind]) return
    // Crossing comes from a render frame, not a fresh gesture. Never construct
    // or resume Web Audio here; normal page gestures have already unlocked it.
    if (['portal', 'door'].includes(kind) && context?.state !== 'running') return
    const requested = now(), token = generation, doorToken = doorGeneration
    if (kind === 'portal' || kind === 'door') {
      const times = kind === 'portal' ? portalTimes : doorTimes
      if (requested - (times.get(portalId) ?? -Infinity) < 50) return
      times.set(portalId, requested)
    } else {
      if (requested - lastClick < 50) return
      lastClick = requested
    }
    if (!await unlock()) return
    const buffer = await decode(kind)
    if (!buffer || disposed || token !== generation || kind === 'door' && doorToken !== doorGeneration || !enabled || isHidden() || now() - requested > 350 || context.state !== 'running') return
    // Clicks can overlap up to four; hover and focus never request playback.
    while (voices.size >= 4) stop(voices.values().next().value)
    const source = context.createBufferSource(), gain = context.createGain()
    const voice = { source, gain, kind }
    source.buffer = buffer;gain.gain.value = volume * (kind === 'environment' ? .45 : .7)
    source.connect(gain);gain.connect(context.destination)
    source.onended = () => { voices.delete(voice);source.disconnect();gain.disconnect() }
    voices.add(voice)
    source.start()
  }
  function doorSound(id, delay = 0) {
    if (disposed || !enabled || !volume || isHidden() || context?.state !== 'running' || !urls.door || doorTimers.has(id)) return
    if (!delay) { void play('door', id);return }
    const token = generation, doorToken = doorGeneration
    doorTimers.set(id, setTimer(() => {
      doorTimers.delete(id)
      if (!disposed && token === generation && doorToken === doorGeneration) void play('door', id)
    }, delay))
  }
  return {
    preload, unlock,
    click: () => { void play('system') },
    environmentClick: () => { void play('environment') },
    portalCrossing: id => { void play('portal', id) },
    doorSound, cancelDoorSounds,
    setEnabled(value) { enabled = value;if (!value) stopAll();else preload() },
    setVolume(value) {
      volume = Math.max(0, Math.min(1, value))
      if (!volume) stopAll()
      for (const voice of voices) voice.gain.gain.value = volume * (voice.kind === 'environment' ? .45 : .7)
    },
    suspend() { stopAll();if (context?.state === 'running') void context.suspend().catch(() => {}) },
    dispose() {
      disposed = true;stopAll();abort.abort();files.clear();buffers.clear();portalTimes.clear();doorTimes.clear()
      if (context && context.state !== 'closed') void context.close().catch(() => {})
    },
  }
}
