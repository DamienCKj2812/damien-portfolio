import { useEffect, useId, useRef, useState } from 'react'

const WIDTH = 640
const HEIGHT = 800
const CELL = 10
const RADIUS = 42
const TRAIL_MS = 700

export default function PixelPortrait({ src, originalSrc, alt, reducedMotion, active }) {
  const rootRef = useRef(null)
  const trailRef = useRef(null)
  const maskId = `portrait-${useId().replace(/:/g, '')}`
  const [focused, setFocused] = useState(false)
  const [trailVisible, setTrailVisible] = useState(false)

  useEffect(() => {
    if (!active || !originalSrc) return
    const root = rootRef.current
    const trail = trailRef.current
    const cells = new Map()
    let head = new Set()
    let previous = null
    let frame = 0
    const preference = window.matchMedia('(hover: hover) and (pointer: fine)')
    const clear = () => {
      cancelAnimationFrame(frame)
      frame = 0
      cells.clear()
      head.clear()
      previous = null
      trail.replaceChildren()
      setTrailVisible(false)
    }
    const reset = () => { clear();setFocused(false) }
    const paint = now => {
      frame = 0
      let fading = false
      for (const [key, cell] of cells) {
        const opacity = head.has(key) ? 1 : reducedMotion ? 0 : Math.max(0, 1 - (now - cell.time) / TRAIL_MS)
        if (opacity === 0) {
          cell.node.remove()
          cells.delete(key)
        } else {
          cell.node.setAttribute('opacity', String(opacity))
          if (!head.has(key)) fading = true
        }
      }
      if (fading) frame = requestAnimationFrame(paint)
      if (cells.size === 0) setTrailVisible(false)
    }
    const stamp = (x, y, now, keys) => {
      for (let row = Math.max(0, Math.floor((y - RADIUS) / CELL)); row < Math.min(HEIGHT / CELL, Math.ceil((y + RADIUS) / CELL)); row++) {
        for (let col = Math.max(0, Math.floor((x - RADIUS) / CELL)); col < Math.min(WIDTH / CELL, Math.ceil((x + RADIUS) / CELL)); col++) {
          if (Math.hypot((col + .5) * CELL - x, (row + .5) * CELL - y) > RADIUS) continue
          const key = `${col}:${row}`
          keys.add(key)
          let cell = cells.get(key)
          if (!cell) {
            const node = document.createElementNS('http://www.w3.org/2000/svg', 'rect')
            node.setAttribute('x', String(col * CELL))
            node.setAttribute('y', String(row * CELL))
            node.setAttribute('width', String(CELL))
            node.setAttribute('height', String(CELL))
            node.setAttribute('fill', 'white')
            trail.append(node)
            cell = { node, time: now }
            cells.set(key, cell)
          }
          cell.time = now
        }
      }
    }
    const reveal = event => {
      if (document.hidden || event.pointerType !== 'mouse' || !preference.matches) return
      setFocused(false)
      setTrailVisible(true)
      const bounds = root.getBoundingClientRect()
      const x = (event.clientX - bounds.left) / bounds.width * WIDTH
      const y = (event.clientY - bounds.top) / bounds.height * HEIGHT
      const now = performance.now()
      // Fill between pointer samples so quick movements leave a continuous pixel trail.
      if (previous && !reducedMotion) {
        const steps = Math.ceil(Math.hypot(x - previous.x, y - previous.y) / (CELL / 2))
        for (let step = 1; step < steps; step++) stamp(previous.x + (x - previous.x) * step / steps, previous.y + (y - previous.y) * step / steps, now, new Set())
      }
      head = new Set()
      stamp(x, y, now, head)
      previous = { x, y }
      cancelAnimationFrame(frame)
      paint(now)
    }
    const leave = () => {
      previous = null
      if (reducedMotion) { clear();return }
      const now = performance.now()
      // The held brush has not been aging while hovered. Release it at exit,
      // then keep painting outside the image until every remaining cell fades.
      for (const key of head) {
        const cell = cells.get(key)
        if (cell) cell.time = now
      }
      head.clear()
      cancelAnimationFrame(frame)
      paint(now)
    }
    const observer = new IntersectionObserver(([entry]) => { if (!entry.isIntersecting) reset() }, { threshold: .08 })
    observer.observe(root)
    const visibility = () => { if (document.hidden) reset() }
    root.addEventListener('pointerenter', reveal)
    root.addEventListener('pointermove', reveal)
    root.addEventListener('pointerleave', leave)
    root.addEventListener('pointercancel', clear)
    document.addEventListener('visibilitychange', visibility)
    window.addEventListener('blur', reset)
    preference.addEventListener('change', reset)
    return () => {
      clear()
      root.removeEventListener('pointerenter', reveal)
      root.removeEventListener('pointermove', reveal)
      root.removeEventListener('pointerleave', leave)
      root.removeEventListener('pointercancel', clear)
      observer.disconnect()
      document.removeEventListener('visibilitychange', visibility)
      window.removeEventListener('blur', reset)
      preference.removeEventListener('change', reset)
    }
  }, [active, originalSrc, reducedMotion])

  return <div ref={rootRef} className="observer-portrait-images" data-portrait-hover={active}
    data-reduced-motion={reducedMotion}
    role="img" aria-label={`${alt}${originalSrc ? '. Move your cursor to reveal color in a pixelated trail, or focus to reveal the original photograph.' : ''}`}
    tabIndex={active && originalSrc ? 0 : undefined}
    onFocus={event => setFocused(event.currentTarget.matches(':focus-visible'))} onBlur={() => setFocused(false)}>
    <img className="observer-portrait-image" src={src} alt="" draggable="false" />
    {originalSrc && <svg className="observer-portrait-original" viewBox={`0 0 ${WIDTH} ${HEIGHT}`} aria-hidden="true" style={{ visibility: active && (focused || trailVisible) ? 'visible' : 'hidden' }}>
      <defs><mask id={maskId} maskUnits="userSpaceOnUse" x="0" y="0" width={WIDTH} height={HEIGHT} style={{ maskType: 'luminance' }}>
        <rect width={WIDTH} height={HEIGHT} fill="white" opacity={active && focused ? 1 : 0} />
        <g ref={trailRef} />
      </mask></defs>
      <image href={originalSrc} width={WIDTH} height={HEIGHT} mask={`url(#${maskId})`} />
    </svg>}
  </div>
}
