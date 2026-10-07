import { useEffect, useRef } from 'react'
import type { CSSProperties } from 'react'
import { createPortal } from 'react-dom'

export interface AudioConsentDialogProps {
  onEnable(): void
  onMute(): void
  onDismiss?: (() => void) | undefined
}

type ConsentBarStyle = CSSProperties & { '--bar-rest': number }

export default function AudioConsentDialog({ onEnable, onMute, onDismiss }: AudioConsentDialogProps) {
  const dialogRef = useRef<HTMLDialogElement | null>(null)
  const enableRef = useRef<HTMLButtonElement | null>(null)
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
    aria-labelledby="audio-consent-title" aria-describedby="audio-consent-description" data-interaction-sound="off"
    onCancel={event => { event.preventDefault();(onDismiss || onMute)() }}
    onWheel={event => event.stopPropagation()} onTouchMove={event => event.stopPropagation()}
    onKeyDown={event => {
      event.stopPropagation()
      if (!event.isTrusted || event.repeat || event.altKey || event.ctrlKey || event.metaKey) return
      if (event.key.toLowerCase() === 'm') { event.preventDefault();onMute();return }
      if (event.key === 'Enter' && !(event.target instanceof Element && event.target.closest('button'))) { event.preventDefault();onEnable();return }
      if (event.key !== 'Tab') return
      const buttons = [...event.currentTarget.querySelectorAll('button')]
      if (event.shiftKey && document.activeElement === buttons[0]) { event.preventDefault();buttons.at(-1)?.focus() }
      else if (!event.shiftKey && document.activeElement === buttons.at(-1)) { event.preventDefault();buttons[0]?.focus() }
    }}>
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
    </div>
  </dialog>, document.body)
}
