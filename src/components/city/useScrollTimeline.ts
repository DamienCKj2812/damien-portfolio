import { useCallback, useEffect, useState } from 'react'
import type { RefObject } from 'react'
import { ELEVATOR_PLAYBACK_RATE } from './elevatorTiming'
import { TOUCH_SCROLL_MULTIPLIER } from './navigationInput'

export function useReducedMotion() {
  const [reduced, setReduced] = useState(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches)
  useEffect(() => {
    const query = window.matchMedia('(prefers-reduced-motion: reduce)')
    const update = () => setReduced(query.matches)
    query.addEventListener('change', update)
    return () => query.removeEventListener('change', update)
  }, [])
  return reduced
}

// Scroll gestures drive the scene, not the document's scroll position.
export function useScrollTimeline(sectionRef: RefObject<HTMLElement | null>, enabled = true, elevatorEntryProgress = 1) {
  const [progress, setProgress] = useState(0)
  const seek = useCallback((next: number) => setProgress(Math.min(1, Math.max(0, next))), [])
  useEffect(() => {
    const element = sectionRef.current
    if (!element || !enabled) return
    const interactive = (target: EventTarget | null) => target instanceof Element && target.closest('button, a, input, select, textarea, [contenteditable="true"], .room-interface, .elevator-interface, .observer-profile')
    const travel = () => Math.max(9600, window.innerHeight * 18) - window.innerHeight
    // Map the cabin segment into half the gesture distance, in both directions.
    // Crossing its boundary in one gesture must keep the preceding journey's pace.
    const toGestureProgress = (value: number) => value <= elevatorEntryProgress ? value : elevatorEntryProgress + (value - elevatorEntryProgress) / ELEVATOR_PLAYBACK_RATE
    const fromGestureProgress = (value: number) => value <= elevatorEntryProgress ? value : elevatorEntryProgress + (value - elevatorEntryProgress) * ELEVATOR_PLAYBACK_RATE
    const advance = (pixels: number) => setProgress(current => Math.min(1, Math.max(0, fromGestureProgress(toGestureProgress(current) + pixels / travel()))))
    const wheel = (event: WheelEvent) => {
      if (interactive(event.target) || event.ctrlKey || event.metaKey) return
      event.preventDefault()
      const unit = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? window.innerHeight : 1
      advance(event.deltaY * unit)
    }
    let touchY: number | null = null
    const touchstart = (event: TouchEvent) => {
      const firstTouch = event.touches[0]
      touchY = !interactive(event.target) && event.touches.length === 1 && firstTouch ? firstTouch.clientY : null
    }
    const touchmove = (event: TouchEvent) => {
      if (touchY === null || event.touches.length !== 1) return
      const firstTouch = event.touches[0]
      if (!firstTouch) return
      event.preventDefault()
      const next = firstTouch.clientY
      advance((touchY - next) * TOUCH_SCROLL_MULTIPLIER)
      touchY = next
    }
    const touchend = () => { touchY = null }
    const keydown = (event: KeyboardEvent) => {
      if (interactive(event.target) || event.altKey || event.ctrlKey || event.metaKey) return
      const gestures: Record<string, number> = { ArrowDown: 160, ArrowRight: 160, ArrowUp: -160, ArrowLeft: -160,
        PageDown: window.innerHeight, PageUp: -window.innerHeight, ' ': window.innerHeight * (event.shiftKey ? -1 : 1) }
      const pixels = gestures[event.key]
      if (pixels !== undefined) { event.preventDefault();advance(pixels) }
      else if (event.key === 'Home' || event.key === 'End') { event.preventDefault();seek(event.key === 'Home' ? 0 : 1) }
    }
    element.addEventListener('wheel', wheel, { passive: false })
    element.addEventListener('touchstart', touchstart, { passive: true })
    element.addEventListener('touchmove', touchmove, { passive: false })
    element.addEventListener('touchend', touchend)
    element.addEventListener('touchcancel', touchend)
    window.addEventListener('keydown', keydown)
    return () => {
      element.removeEventListener('wheel', wheel)
      element.removeEventListener('touchstart', touchstart)
      element.removeEventListener('touchmove', touchmove)
      element.removeEventListener('touchend', touchend)
      element.removeEventListener('touchcancel', touchend)
      window.removeEventListener('keydown', keydown)
    }
  }, [sectionRef, enabled, seek, elevatorEntryProgress])
  return { progress, seek }
}
