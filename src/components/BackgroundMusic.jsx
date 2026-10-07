import { useCallback, useEffect, useRef, useState } from 'react'
import './backgroundMusic.css'
import useSoundEffects from '../audio/useSoundEffects.js'
import AudioConsentDialog from './AudioConsentDialog.jsx'
import { musicAutoplayPolicy } from '../audio/autoplayPolicy.js'
import { hasVideoAudioFocus, subscribeVideoAudioFocus } from '../audio/videoAudioFocus.js'

const STORAGE_KEY = 'damien-portfolio:background-music'

function readSettings(defaultVolume) {
  try {
    const saved = JSON.parse(window.localStorage.getItem(STORAGE_KEY))
    return { enabled: saved?.enabled !== false, volume: defaultVolume }
  } catch { return { enabled: true, volume: defaultVolume } }
}

export default function BackgroundMusic({ track }) {
  const effects = useSoundEffects()
  const [settings, setSettings] = useState(() => readSettings(track.volume))
  const [playing, setPlaying] = useState(false)
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState('')
  const [automaticPolicy, setAutomaticPolicy] = useState('not-checked')
  const [autoplayBlocked, setAutoplayBlocked] = useState(false)
  const audioRef = useRef(null)
  const wanted = useRef(false)
  const activated = useRef(false)
  const rememberedChoice = useRef(effects.consent !== null)
  const automaticAttempted = useRef(false)
  const pending = useRef(false)
  const version = useRef(0)
  const cancelAttempt = useCallback(() => { version.current++;pending.current = false }, [])

  const tryPlay = useCallback(async (automatic = false) => {
    const audio = audioRef.current
    if (!audio || hasVideoAudioFocus() || (!activated.current && !automatic) || !wanted.current || document.hidden || pending.current || !audio.paused) return
    const attempt = ++version.current
    pending.current = true
    setStarting(true)
    try {
      if (audio.error) audio.load()
      await audio.play()
      if (attempt === version.current && (!wanted.current || document.hidden)) audio.pause()
    } catch (failure) {
      if (automatic && attempt === version.current && failure.name === 'NotAllowedError') setAutoplayBlocked(true)
      if (attempt === version.current && failure.name !== 'NotAllowedError' && failure.name !== 'AbortError') {
        setError('Music could not start. Tap the sound button to retry.')
      }
    } finally {
      if (attempt === version.current) { pending.current = false;setStarting(false) }
    }
  }, [])

  useEffect(() => subscribeVideoAudioFocus(active => {
    if (active) { cancelAttempt();setStarting(false);audioRef.current?.pause() }
    else if (activated.current && wanted.current && !document.hidden) void tryPlay()
  }), [cancelAttempt, tryPlay])

  const tryAutomatic = useCallback(() => {
    const audio = audioRef.current
    if (!audio || !rememberedChoice.current || automaticAttempted.current || !wanted.current || document.hidden) return
    automaticAttempted.current = true
    setAutomaticPolicy(musicAutoplayPolicy(audio))
    // A remembered YES permits one actual playback attempt. Its result is
    // authoritative and lets the browser expose its blocked-autoplay control.
    void tryPlay(true)
  }, [tryPlay])

  useEffect(() => {
    audioRef.current.volume = settings.volume
    try { window.localStorage.setItem(STORAGE_KEY, JSON.stringify(settings)) }
    catch { /* Sound controls still work when storage is unavailable. */ }
  }, [settings])

  useEffect(() => {
    const audio = audioRef.current
    wanted.current = effects.consent !== null && settings.enabled
    if (!wanted.current) { cancelAttempt();setStarting(false);audio.pause();return }
    let cancelled = false
    // Defer only the automatic attempt so StrictMode's effect replay can clean
    // up its first instance without consuming the document's single attempt.
    queueMicrotask(() => { if (!cancelled) tryAutomatic() })
    const resumeOnGesture = event => {
      if (!event.isTrusted) return
      if (event.target instanceof Element && event.target.closest('[data-background-music]')) return
      if (event.type === 'keydown' && (event.ctrlKey || event.metaKey || event.altKey)) return
      if (navigator.userActivation && !navigator.userActivation.isActive) return
      activated.current = true
      void tryPlay()
    }
    const visibility = () => {
      if (document.hidden) {
        cancelAttempt();setStarting(false);audio.pause()
      } else if (activated.current) void tryPlay()
      else tryAutomatic()
    }
    document.addEventListener('pointerdown', resumeOnGesture, true)
    document.addEventListener('keydown', resumeOnGesture, true)
    document.addEventListener('visibilitychange', visibility)
    return () => {
      cancelled = true
      document.removeEventListener('pointerdown', resumeOnGesture, true)
      document.removeEventListener('keydown', resumeOnGesture, true)
      document.removeEventListener('visibilitychange', visibility)
    }
  }, [settings.enabled, effects.consent, tryPlay, tryAutomatic, cancelAttempt])
  useEffect(() => {
    const audio = audioRef.current
    return () => { cancelAttempt();audio.pause() }
  }, [cancelAttempt])

  const chooseSound = enabled => {
    effects.chooseSound(enabled)
    effects.closePreferences()
    activated.current = true
    wanted.current = enabled
    setError('')
    const next = { ...settings, enabled }
    setSettings(next)
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(next)) }
    catch { /* The current visit still works without persistent storage. */ }
    if (enabled) void tryPlay()
    else { cancelAttempt();setStarting(false);setPlaying(false);audioRef.current.pause() }
  }

  const toggle = event => {
    if (effects.consent === null || !event.isTrusted) return
    activated.current = true
    setError('')
    if (playing || starting) {
      wanted.current = false;cancelAttempt();setStarting(false)
      setPlaying(false)
      setSettings(current => ({ ...current, enabled: false }))
      audioRef.current.pause()
    } else {
      wanted.current = true
      setSettings(current => ({ ...current, enabled: true }))
      void tryPlay()
    }
  }

  const musicState = error ? 'error' : playing ? 'playing' : starting ? 'starting' : settings.enabled ? 'ready' : 'off'
  const musicLabel = { error: 'Music unavailable', playing: 'Music on', starting: 'Starting…', ready: 'Music ready', off: 'Music off' }[musicState]
  return <>
    {(effects.consent === null || effects.preferencesOpen) && <AudioConsentDialog onEnable={() => chooseSound(true)} onMute={() => chooseSound(false)} onDismiss={effects.preferencesOpen ? effects.closePreferences : undefined} />}
    <aside className="background-music" data-background-music data-music-enabled={settings.enabled} data-music-state={musicState} data-autoplay-policy={automaticPolicy} data-autoplay-blocked={autoplayBlocked} aria-label="Audio controls">
    <audio id="background-music-audio" ref={audioRef} src={`${import.meta.env.BASE_URL}${track.src}`} preload="none" loop
      onPlaying={() => {
        if (!wanted.current || document.hidden || hasVideoAudioFocus()) { audioRef.current.pause();return }
        activated.current = true;setPlaying(true);setStarting(false);setAutoplayBlocked(false);setError('')
      }} onPause={() => { setPlaying(false);setStarting(false) }}
      onWaiting={() => { setPlaying(false);setStarting(wanted.current && !audioRef.current.paused) }}
      onError={() => { setPlaying(false);setStarting(false);setError('Music could not load. Tap the sound button to retry.') }} />
    <div className="background-music-controls">
      <button type="button" className="background-music-toggle" data-enabled={playing} onClick={toggle} aria-pressed={playing} aria-busy={starting}
        aria-label={playing || starting ? 'Pause background music' : 'Play background music'}
        title={autoplayBlocked ? 'Your browser blocked automatic music. Click to play, or allow autoplay for this site in your browser settings.' : undefined}>
        <svg className="background-music-icon" data-active={playing} width="13" height="14" viewBox="0 0 13 14" fill="currentColor" aria-hidden="true">
          {[5, 9, 13, 7].map((height, index) => <rect key={index} x={index * 3} y={14 - (playing ? height : 3)} width="1.5" height={playing ? height : 3} />)}
        </svg>
        <span>{musicLabel}</span>
      </button>
      <button type="button" className="background-music-toggle sound-effects-toggle" data-enabled={effects.enabled} onClick={effects.toggle} aria-pressed={effects.enabled}
        aria-label={effects.enabled ? 'Mute interaction sound effects' : 'Enable interaction sound effects'}>
        <span>{effects.enabled ? 'SFX on' : 'SFX off'}</span>
      </button>
    </div>
    <a className="background-music-credit" href={track.source} target="_blank" rel="noopener noreferrer"
      aria-label={`Music credit: ${track.title} by ${track.artist}, via Pixabay`}><span className="background-music-note" aria-hidden="true">♪</span>{track.title} – {track.artist}<span className="background-music-credit-arrow" aria-hidden="true">↗</span></a>
    {error && <p className="background-music-error" role="status">{error}</p>}
    {effects.error && <p className="background-music-error" role="status">Sound effects could not load. Switch effects off and on to retry.</p>}
    </aside>
  </>
}
