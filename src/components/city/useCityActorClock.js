/* eslint react-hooks/immutability: "off" -- The independent city clock is a demand-rendered mutable animation resource. */
import { useEffect, useRef } from 'react'
import { useFrame, useThree } from '@react-three/fiber'

export default function useCityActorClock({ enabled, frameRef, journey, fps, reducedMotion, zone = 'city' }) {
  const frames = useRef(0)
  const lastTick = useRef(0)
  const visible = useRef(true)
  const wasLive = useRef(false)
  const { gl, invalidate } = useThree()
  useEffect(() => {
    if (!enabled) return
    lastTick.current = performance.now()
    const resume = () => { lastTick.current = performance.now();wasLive.current = false;if (!document.hidden) invalidate() }
    const observer = new IntersectionObserver(([entry]) => {
      visible.current = entry.isIntersecting;lastTick.current = performance.now();wasLive.current = false
      if (entry.isIntersecting) invalidate()
    })
    observer.observe(gl.domElement)
    document.addEventListener('visibilitychange', resume)
    invalidate()
    return () => { observer.disconnect();document.removeEventListener('visibilitychange', resume) }
  }, [enabled, reducedMotion, gl, invalidate])
  useFrame(() => {
    if (!enabled) return
    const now = performance.now()
    const elapsed = Math.max(0, now - lastTick.current) / 1000
    lastTick.current = now
    const active = zone === 'lobby'
      ? frameRef.current >= journey.lobbyRevealFrame && frameRef.current < (journey.lobbyHideFrame || Infinity)
      : frameRef.current < (journey.cityHideFrame ?? journey.cityEnd)
    if (!active || reducedMotion || document.hidden || !visible.current) { wasLive.current = false;return }
    if (wasLive.current) frames.current += elapsed * fps
    wasLive.current = true
    invalidate()
  }, -.25)
  return frames
}
