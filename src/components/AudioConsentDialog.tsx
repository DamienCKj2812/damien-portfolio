import { useEffect, useRef, useState } from 'react'
import type { CSSProperties, MouseEvent } from 'react'
import { createPortal } from 'react-dom'
import type { BackgroundMusicTrack } from '../types/audio'

export interface AudioConsentDialogProps {
  onEnable(): void
  onMute(): void
  onDismiss?: (() => void) | undefined
  preferences?: {
    musicEnabled: boolean; effectsEnabled: boolean; track: BackgroundMusicTrack
    onToggleMusic: (event: MouseEvent<HTMLButtonElement>) => void
    onToggleEffects: () => void
  }
}

type ConsentBarStyle = CSSProperties & { '--bar-rest': number }

export default function AudioConsentDialog({ onEnable, onMute, onDismiss, preferences }: AudioConsentDialogProps) {
  const dialogRef = useRef<HTMLDialogElement | null>(null)
  const enableRef = useRef<HTMLButtonElement | null>(null)
  const [narrow, setNarrow] = useState(() => window.matchMedia('(max-width: 600px)').matches)
  const mobilePreferences = narrow && Boolean(onDismiss && preferences)
  useEffect(() => {
    const query = window.matchMedia('(max-width: 600px)')
    const update = () => setNarrow(query.matches)
    query.addEventListener('change', update)
    return () => query.removeEventListener('change', update)
  }, [])
  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return
    const previousFocus = document.activeElement
    dialog.showModal()
    enableRef.current?.focus({ preventScroll: true })
    return () => {
      if (dialog.open) dialog.close()
      if (previousFocus instanceof HTMLElement && previousFocus.isConnected) previousFocus.focus({ preventScroll: true })
    }
  }, [])
  return createPortal(<dialog ref={dialogRef} id="audio-consent-dialog" className="audio-consent" aria-modal="true"
    aria-labelledby={mobilePreferences ? 'audio-settings-title' : 'audio-consent-title'} aria-describedby={mobilePreferences ? undefined : 'audio-consent-description'} data-interaction-sound={mobilePreferences ? undefined : 'off'}
    data-mobile-preferences={mobilePreferences} data-background-music
    onClick={event => { if (mobilePreferences && event.target === event.currentTarget) onDismiss?.() }}
    onCancel={event => { event.preventDefault();(onDismiss || onMute)() }}
    onWheel={event => event.stopPropagation()} onTouchMove={event => event.stopPropagation()}
    onKeyDown={event => {
      event.stopPropagation()
      if (!event.isTrusted || event.repeat || event.altKey || event.ctrlKey || event.metaKey) return
      if (mobilePreferences && event.key !== 'Tab') return
      if (!mobilePreferences && event.key.toLowerCase() === 'm') { event.preventDefault();onMute();return }
      if (!mobilePreferences && event.key === 'Enter' && !(event.target instanceof Element && event.target.closest('button'))) { event.preventDefault();onEnable();return }
      if (event.key !== 'Tab') return
      const buttons = [...event.currentTarget.querySelectorAll<HTMLElement>('button, a[href]')]
      if (event.shiftKey && document.activeElement === buttons[0]) { event.preventDefault();buttons.at(-1)?.focus() }
      else if (!event.shiftKey && document.activeElement === buttons.at(-1)) { event.preventDefault();buttons[0]?.focus() }
    }}>
    {mobilePreferences && preferences ? <div className="audio-settings-sheet">
      <div className="audio-settings-head"><h2 id="audio-settings-title">Settings</h2><button ref={enableRef} type="button" aria-label="Close sound preferences" onClick={onDismiss}>×</button></div>
      <button type="button" className="audio-settings-row" aria-label="Toggle background music" aria-pressed={preferences.musicEnabled} onClick={preferences.onToggleMusic}>
        <span>MUSIC</span><span className="audio-settings-segments" aria-hidden="true"><span data-on={preferences.musicEnabled}>ON</span><span data-on={!preferences.musicEnabled}>OFF</span></span>
      </button>
      <button type="button" className="audio-settings-row" aria-label="Toggle interaction sound effects" aria-pressed={preferences.effectsEnabled} onClick={preferences.onToggleEffects}>
        <span>SFX</span><span className="audio-settings-segments" aria-hidden="true"><span data-on={preferences.effectsEnabled}>ON</span><span data-on={!preferences.effectsEnabled}>OFF</span></span>
      </button>
      <a className="audio-settings-credit" href={preferences.track.source} target="_blank" rel="noopener noreferrer"
        aria-label={`Music credit: ${preferences.track.title} by ${preferences.track.artist}, via Pixabay`}><span>♪ {preferences.track.title} — {preferences.track.artist}</span><span aria-hidden="true">↗</span></a>
    </div> : <>
    <div className="audio-consent-scene" aria-hidden="true"><img src={`${import.meta.env.BASE_URL}models/city/preview.png`} alt="" /></div>
    <div className="audio-consent-content">
      <div className="audio-consent-bars" aria-hidden="true">
        {[.625, 1, .625, .25, .65].map((height, index) => {
          const style: ConsentBarStyle = { '--bar-rest': height, animationDelay: `${index * -.32}s` }
          return <span key={index} style={style} />
        })}
      </div>
      <h2 id="audio-consent-title">Enter with sound?</h2>
      <p id="audio-consent-description" className="sr-only">Enable background music and subtle interaction sounds, or continue muted. Your choice is remembered. Press Enter for sound or M to mute. {onDismiss ? 'Escape closes without changing your choice.' : 'Escape also continues muted.'}</p>
      <div className="audio-consent-actions">
        <button ref={enableRef} type="button" aria-label="Enable sound" onClick={event => { if (event.isTrusted) onEnable() }}>YES <kbd aria-hidden="true">↵</kbd></button>
        <button type="button" aria-label="Continue muted" onClick={onMute}>MUTED <span className="audio-consent-emoticon" aria-hidden="true">(╥﹏╥)</span><kbd aria-hidden="true">M</kbd></button>
      </div>
    </div></>}
  </dialog>, document.body)
}
