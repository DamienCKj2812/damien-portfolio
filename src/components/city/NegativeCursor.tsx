import { useCallback, useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'

const FOLLOW_TIME_MS = 80
const SETTLE_DISTANCE = .1

export default function NegativeCursor() {
  const [host, setHost] = useState<Element>(() => document.body)
  const hostRef = useRef(host)
  const cursorRef = useRef<HTMLDivElement>(null)
  const pointer = useRef({ x: -300, y: -300, active: false, interactive: false, portrait: false })
  const position = useRef({ x: -300, y: -300 })
  const sync = useCallback((node: HTMLDivElement | null) => {
    if (!node) return
    node.style.setProperty('--cursor-x', `${position.current.x}px`)
    node.style.setProperty('--cursor-y', `${position.current.y}px`)
    node.dataset.active = String(pointer.current.active)
    node.dataset.interactive = String(pointer.current.interactive)
    node.dataset.portrait = String(pointer.current.portrait)
  }, [])
  const setCursor = useCallback((node: HTMLDivElement | null) => { cursorRef.current = node;sync(node) }, [sync])

  useEffect(() => {
    const hover = window.matchMedia('(hover: hover) and (pointer: fine)')
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)')
    let hit: Element | null = null
    let followFrame: number | null = null
    let lastTick: number | null = null
    const stopFollowing = () => {
      if (followFrame !== null) cancelAnimationFrame(followFrame)
      followFrame = null
      lastTick = null
    }
    const snapToPointer = () => {
      position.current.x = pointer.current.x
      position.current.y = pointer.current.y
      sync(cursorRef.current)
    }
    const follow = (now: number) => {
      followFrame = null
      if (!pointer.current.active) { stopFollowing();return }
      if (reducedMotion.matches) { stopFollowing();snapToPointer();return }
      const elapsed = Math.min(64, Math.max(0, now - (lastTick ?? now)))
      lastTick = now
      const blend = 1 - Math.exp(-elapsed / FOLLOW_TIME_MS)
      position.current.x += (pointer.current.x - position.current.x) * blend
      position.current.y += (pointer.current.y - position.current.y) * blend
      if (Math.hypot(pointer.current.x - position.current.x, pointer.current.y - position.current.y) <= SETTLE_DISTANCE) {
        stopFollowing()
        snapToPointer()
      } else {
        sync(cursorRef.current)
        followFrame = requestAnimationFrame(follow)
      }
    }
    const startFollowing = () => {
      if (followFrame !== null) return
      lastTick = performance.now()
      followFrame = requestAnimationFrame(follow)
    }
    const updateInteractive = () => {
      if (!pointer.current.active) return
      const control = hit?.closest('button, a[href], summary, input, select, textarea, [role="button"], [data-cursor-interactive="true"]')
      const uiInteractive = Boolean(control && !control.matches(':disabled, [aria-disabled="true"]') && !control.closest('[inert], [aria-disabled="true"]'))
      const sceneInteractive = Boolean(hit?.closest('canvas') && document.body.style.cursor === 'pointer')
      pointer.current.interactive = uiInteractive || sceneInteractive
      pointer.current.portrait = Boolean(hit?.closest('[data-portrait-hover="true"]'))
      if (cursorRef.current) cursorRef.current.dataset.interactive = String(pointer.current.interactive)
      if (cursorRef.current) cursorRef.current.dataset.portrait = String(pointer.current.portrait)
    }
    const hide = () => {
      stopFollowing()
      pointer.current.active = false
      pointer.current.interactive = false
      pointer.current.portrait = false
      hit = null
      document.documentElement.classList.remove('has-negative-cursor')
      sync(cursorRef.current)
    }
    const moveHost = (nextHost: Element) => {
      if (nextHost === hostRef.current) return
      hostRef.current = nextHost
      setHost(nextHost)
    }
    const move = (event: PointerEvent) => {
      if (!hover.matches || event.pointerType !== 'mouse') { hide();return }
      const wasActive = pointer.current.active
      pointer.current = { x: event.clientX, y: event.clientY, active: true, interactive: false, portrait: false }
      hit = event.target instanceof Element ? event.target : null
      updateInteractive()
      const nextHost = hit?.closest('dialog[open]') || document.body
      moveHost(nextHost)
      document.documentElement.classList.add('has-negative-cursor')
      if (!wasActive || reducedMotion.matches) {
        stopFollowing()
        snapToPointer()
      } else {
        sync(cursorRef.current)
        startFollowing()
      }
    }
    const focus = (event: FocusEvent) => {
      if (!pointer.current.active) return
      const focused = event.target instanceof Element ? event.target : null
      moveHost(focused?.closest('dialog[open]') || document.querySelector('dialog[open]') || document.body)
      hit = document.elementFromPoint(pointer.current.x, pointer.current.y)
      updateInteractive()
    }
    const over = (event: PointerEvent) => {
      if (event.pointerType !== 'mouse') return
      hit = event.target instanceof Element ? event.target : null
      updateInteractive()
    }
    // Three's existing raycast handlers advertise clickable objects through
    // body.style.cursor, even though the native cursor is visually hidden.
    const sceneHover = new MutationObserver(updateInteractive)
    sceneHover.observe(document.body, { attributes: true, attributeFilter: ['style'] })
    const visibility = () => { if (document.hidden) hide() }
    const motionPreference = () => { stopFollowing();snapToPointer() }
    document.addEventListener('pointermove', move, { passive: true })
    document.addEventListener('pointerover', over, { passive: true })
    document.addEventListener('pointerleave', hide)
    document.addEventListener('focusin', focus)
    document.addEventListener('visibilitychange', visibility)
    window.addEventListener('blur', hide)
    hover.addEventListener('change', hide)
    reducedMotion.addEventListener('change', motionPreference)
    return () => {
      hide()
      sceneHover.disconnect()
      document.removeEventListener('pointermove', move)
      document.removeEventListener('pointerover', over)
      document.removeEventListener('pointerleave', hide)
      document.removeEventListener('focusin', focus)
      document.removeEventListener('visibilitychange', visibility)
      window.removeEventListener('blur', hide)
      hover.removeEventListener('change', hide)
      reducedMotion.removeEventListener('change', motionPreference)
    }
  }, [sync])

  return createPortal(<div ref={setCursor} className="city-negative-cursor" data-active="false" data-interactive="false" data-portrait="false" aria-hidden="true" />, host)
}
