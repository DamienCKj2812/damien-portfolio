import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { createInteractionAudio } from './interactionAudio.js'
import { mediaUrls } from '../assets/media.js'
import { SoundEffectsContext } from './useSoundEffects.js'

const STORAGE_KEY = 'damien-portfolio:sound-effects'
const CONSENT_KEY = 'damien-portfolio:audio-consent'
const FIXED_VOLUME = .45
const TARGETS = 'button, a[href], summary, select, input[type="range"], input[type="checkbox"], input[type="radio"], [role="button"], [data-interaction-sound="on"]'

function readSettings() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY))
    return { enabled: saved?.enabled !== false, volume: FIXED_VOLUME }
  } catch { return { enabled: true, volume: FIXED_VOLUME } }
}

function readConsent() {
  try {
    const saved = localStorage.getItem(CONSENT_KEY)
    return saved === 'enabled' || saved === 'muted' ? saved : null
  } catch { return null }
}

function soundTarget(target) {
  const element = target instanceof Element ? target.closest(TARGETS) : null
  if (!element || element.matches(':disabled') || element.closest('[inert], [hidden], [aria-disabled="true"], [data-interaction-sound="off"]')) return null
  return element
}

export default function SoundEffectsProvider({ children }) {
  const [settings, setSettings] = useState(readSettings)
  const [consent, setConsent] = useState(readConsent)
  const [preferencesOpen, setPreferencesOpen] = useState(false)
  const openPreferences = useCallback(() => { if (consent !== null) setPreferencesOpen(true) }, [consent])
  const closePreferences = useCallback(() => setPreferencesOpen(false), [])
  const [error, setError] = useState(false)
  const engine = useRef(null)
  const activated = useRef(false)
  const click = useCallback(() => { if (activated.current) engine.current?.click() }, [])
  const environmentClick = useCallback(() => { if (activated.current) engine.current?.environmentClick() }, [])
  const portalCrossing = useCallback(id => { if (activated.current) engine.current?.portalCrossing(id) }, [])
  const doorSound = useCallback((id, delay) => { if (activated.current) engine.current?.doorSound(id, delay) }, [])
  const cancelDoorSounds = useCallback(() => engine.current?.cancelDoorSounds(), [])
  const chooseSound = useCallback(enabled => {
    // This is called directly by the startup dialog's real click/keypress so
    // Web Audio is created/resumed inside the browser's activation window.
    activated.current = true
    engine.current?.setEnabled(enabled)
    if (enabled) void engine.current?.unlock()
    else engine.current?.suspend()
    setError(false)
    const next = { ...settings, enabled }
    const choice = enabled ? 'enabled' : 'muted'
    setSettings(next)
    setConsent(choice)
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
      localStorage.setItem(CONSENT_KEY, choice)
    } catch { /* The current visit still works without persistent storage. */ }
  }, [settings])
  const toggle = useCallback(event => {
    if (consent === null || event && !event.isTrusted) return
    activated.current = true
    const enabled = !settings.enabled
    engine.current?.setEnabled(enabled)
    // Delegation is silent while muted, so enabling supplies its own system click.
    if (enabled) engine.current?.click()
    setError(false);setSettings(current => ({ ...current, enabled }))
  }, [settings.enabled, consent])

  useEffect(() => {
    const audio = createInteractionAudio({ urls: { system: mediaUrls.systemClick, environment: mediaUrls.environmentClick, portal: mediaUrls.portal, door: mediaUrls.door }, onError: () => setError(true) })
    engine.current = audio
    audio.setEnabled(false)
    const gesture = event => {
      if (!event.isTrusted) return
      if (event.type === 'keydown' && (event.ctrlKey || event.metaKey || event.altKey)) return
      if (navigator.userActivation && !navigator.userActivation.isActive) return
      activated.current = true
      void audio.unlock()
    }
    const activate = event => {
      if (!event.isTrusted) return
      const target = soundTarget(event.target)
      if (!target) return
      activated.current = true
      if (target.closest('[data-sound-effect="environment"]')) audio.environmentClick()
      else audio.click()
    }
    const visibility = () => { if (document.hidden) audio.suspend() }
    document.addEventListener('pointerdown', gesture, true)
    document.addEventListener('keydown', gesture, true)
    document.addEventListener('click', activate, true)
    document.addEventListener('visibilitychange', visibility)
    return () => {
      document.removeEventListener('pointerdown', gesture, true)
      document.removeEventListener('keydown', gesture, true)
      document.removeEventListener('click', activate, true)
      document.removeEventListener('visibilitychange', visibility)
      audio.dispose();engine.current = null
    }
  }, [])
  useEffect(() => {
    engine.current?.setEnabled(consent !== null && settings.enabled);engine.current?.setVolume(settings.volume)
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(settings)) }
    catch { /* Effects remain usable when storage is unavailable. */ }
  }, [settings, consent])
  const value = useMemo(() => ({ ...settings, enabled: consent !== null && settings.enabled, consent, chooseSound, preferencesOpen, openPreferences, closePreferences, click, environmentClick, portalCrossing, doorSound, cancelDoorSounds, toggle, error }), [settings, consent, chooseSound, preferencesOpen, openPreferences, closePreferences, click, environmentClick, portalCrossing, doorSound, cancelDoorSounds, toggle, error])
  return <SoundEffectsContext.Provider value={value}>{children}</SoundEffectsContext.Provider>
}
