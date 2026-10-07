import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import type { CSSProperties } from 'react'
import useSoundEffects from '../../audio/useSoundEffects'
import './guideOverlay.css'

const STEPS = [
  { key: 'scroll', title: 'SCROLL TO MOVE', subtitle: 'SCROLL DOWN TO GO FORWARD · SCROLL UP TO GO BACK',
    detail: 'Follow the city and atrium route, then choose a floor in the elevator. On touch screens, swipe to move.' },
  { key: 'rotate', title: 'DRAG TO LOOK', subtitle: 'IN ROOMS · HOLD THE LEFT BUTTON TO TURN',
    detail: 'Drag to look around the rooms. On touch screens, drag sideways to turn; use the room controls to walk or reset your view.' },
  { key: 'click', title: 'CLICK TO INSPECT', subtitle: 'HIGHLIGHTED OBJECTS ARE INTERACTIVE · CLICK TO OPEN',
    detail: 'Select floor buttons, people, cards and exhibits to explore. You can also use the on-screen controls and keyboard.' },
] as const
const STEP_SECONDS = 4.2

export interface GuideOverlayProps {
  reducedMotion: boolean
  onClose: () => void
}

type DialStyle = CSSProperties & { '--angle': string }

export default function GuideOverlay({ reducedMotion, onClose }: GuideOverlayProps) {
  const { click: playClick } = useSoundEffects()
  const dialogRef = useRef<HTMLDialogElement>(null)
  const nextRef = useRef<HTMLButtonElement>(null)
  const [step, setStep] = useState(0)
  const [elapsed, setElapsed] = useState(0)
  const current = STEPS[step] ?? STEPS[0]
  const go = (index: number) => { setStep(index);setElapsed(0) }
  const next = () => { if (step < STEPS.length - 1) go(step + 1);else onClose() }

  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return
    const previousFocus = document.activeElement
    dialog.showModal()
    nextRef.current?.focus({ preventScroll: true })
    return () => {
      if (dialog.open) dialog.close()
      if (previousFocus instanceof HTMLElement && previousFocus.isConnected) previousFocus.focus({ preventScroll: true })
    }
  }, [])

  useEffect(() => {
    if (reducedMotion) return
    let frame = 0, previous: number | null = null, seconds = 0, lastPaint = 0
    const tick = (now: number) => {
      if (document.hidden) { previous = null;return }
      if (previous != null) seconds += (now - previous) / 1000
      previous = now
      if (seconds >= STEP_SECONDS) {
        if (step < STEPS.length - 1) { setStep(step + 1);setElapsed(0);return }
        seconds %= STEP_SECONDS
      }
      if (now - lastPaint >= 1000 / 30) { setElapsed(seconds);lastPaint = now }
      frame = requestAnimationFrame(tick)
    }
    const visibility = () => {
      cancelAnimationFrame(frame);previous = null
      if (!document.hidden) frame = requestAnimationFrame(tick)
    }
    frame = requestAnimationFrame(tick)
    document.addEventListener('visibilitychange', visibility)
    return () => { cancelAnimationFrame(frame);document.removeEventListener('visibilitychange', visibility) }
  }, [step, reducedMotion])

  const rotating = current.key === 'rotate', inspecting = current.key === 'click'
  const cycle = (elapsed % 1.8) / 1.8
  const hit = inspecting && cycle > .45
  const pulse = hit ? (cycle - .45) / .55 : 0
  const distanceCycle = (elapsed % 4) / 2
  const forward = distanceCycle < 1
  const distance = forward ? distanceCycle : 2 - distanceCycle
  const yaw = Math.sin(elapsed * 1.6)
  const dot = rotating ? 180 + yaw * 55 : inspecting ? 45 : 30 + distance * 120
  const readout = rotating ? `${yaw >= 0 ? '+' : '−'}${String(Math.round(Math.abs(yaw) * 55)).padStart(3, '0')}°`
    : inspecting ? hit ? 'OPEN' : 'IN RANGE' : `${forward ? '▼' : '▲'} ${(distance * 4.8).toFixed(1).padStart(4, '0')} M`
  const mouseX = rotating ? yaw * 14 : inspecting ? Math.min(cycle / .45, 1) * 10 : 0
  const mouseY = inspecting ? -Math.min(cycle / .45, 1) * 10 : 0
  const wheelY = rotating || inspecting ? 7 : forward ? 6 + (elapsed * 2.2 % 1) * 7 : 13 - (elapsed * 2.2 % 1) * 7
  const orbitStyle: DialStyle = { '--angle': `${dot}deg` }

  return createPortal(<dialog ref={dialogRef} className="portfolio-guide" id="portfolio-guide" aria-modal="true"
    aria-labelledby="portfolio-guide-title" aria-describedby="portfolio-guide-detail" data-step={current.key}
    onCancel={event => { event.preventDefault();playClick();onClose() }}
    onWheel={event => event.stopPropagation()} onTouchMove={event => event.stopPropagation()}
    onKeyDown={event => {
      event.stopPropagation()
      if (event.altKey || event.ctrlKey || event.metaKey) return
      if (event.key === 'ArrowRight') { event.preventDefault();if (!event.repeat) { playClick();next() } }
      else if (event.key === 'ArrowLeft') { event.preventDefault();if (!event.repeat && step > 0) { playClick();go(step - 1) } }
      else if (event.key === 'Enter' && !(event.target instanceof Element && event.target.closest('button'))) {
        event.preventDefault();if (!event.repeat) { playClick();next() }
      }
    }}>
    <div className="guide-orientation"><span>ORIENTATION</span><span>{String(step + 1).padStart(2, '0')} / 03</span></div>
    <div className="guide-content">
      <div className="guide-instrument" aria-hidden="true">
        <div className="guide-dial">
          {Array.from({ length: 72 }, (_, index) => {
            const angle = index * 5
            const delta = Math.abs((angle - dot + 540) % 360 - 180)
            const style: DialStyle = { '--angle': `${angle}deg`, height: index % 9 === 0 ? 10 : 5, opacity: .14 + .8 * Math.max(0, 1 - delta / 40) }
            return <span key={index} className="guide-tick" style={style} />
          })}
          <span className="guide-orbit-dot" style={orbitStyle} />
          <span className="guide-click-pulse" style={{ width: 70 + pulse * 150, height: 70 + pulse * 150, opacity: hit ? 1 - pulse : 0 }} />
          <div className="guide-mouse" style={{ transform: `translate(${mouseX}px, ${mouseY}px)` }}>
            <span className="guide-mouse-left" style={{ opacity: rotating ? .55 + .35 * Math.sin(elapsed * 6) : hit && pulse < .25 ? .95 : 0 }} />
            <span className="guide-mouse-divider" /><span className="guide-mouse-bottom" />
            <span className="guide-mouse-wheel" style={{ top: wheelY, opacity: rotating || inspecting ? .35 : 1 }} />
          </div>
          {['up', 'down'].map(direction => <div key={direction} className={`guide-chevrons guide-chevrons-${direction}`} style={{ opacity: !rotating && !inspecting && (direction === 'down') === forward ? 1 : 0 }}>
            {[0, 1, 2].map(index => <span key={index} style={{ opacity: .15 + .85 * Math.max(0, Math.sin(elapsed * 4 - index * .9)) }} />)}
          </div>)}
        </div>
        <div className="guide-readout"><span>{rotating ? 'YAW' : inspecting ? 'TARGET' : forward ? 'FORWARD' : 'BACK'}</span><strong>{readout}</strong></div>
      </div>
      <div className="guide-copy">
        <h2 id="portfolio-guide-title" aria-live="polite">{current.title}</h2>
        <p className="guide-subtitle">{current.subtitle}</p>
        <p id="portfolio-guide-detail">{current.detail}</p>
      </div>
      <nav className="guide-segments" aria-label="Guide steps">
        {STEPS.map((item, index) => <button key={item.key} type="button" aria-label={`Step ${index + 1}: ${item.title.toLowerCase()}`}
          aria-current={index === step ? 'step' : undefined} onClick={() => go(index)}>
          <span><i style={{ width: `${index < step ? 100 : index > step ? 0 : reducedMotion ? 100 : Math.min(100, elapsed / STEP_SECONDS * 100)}%` }} /></span>
        </button>)}
      </nav>
    </div>
    <footer className="guide-actions">
      <button type="button" onClick={onClose}><kbd>ESC</kbd> SKIP</button>
      <button ref={nextRef} type="button" onClick={next}>{step < STEPS.length - 1 ? 'NEXT' : 'ENTER'} <kbd>↵</kbd></button>
    </footer>
  </dialog>, document.body)
}
