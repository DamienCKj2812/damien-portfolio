import { useEffect, useRef } from 'react'
import { useFrame, useThree } from '@react-three/fiber'

// R3F subscribers run before its draw. Report on the following browser frame,
// only after the renderer has actually submitted scene geometry to the GPU.
export default function StartupFrameReady({ onReady }: { onReady: () => void }) {
  const { gl, invalidate } = useThree()
  const pending = useRef(0)
  const complete = useRef(false)
  useEffect(()=>()=>{cancelAnimationFrame(pending.current);pending.current=0;complete.current=false},[])
  useFrame(()=>{
    if(complete.current || pending.current) return
    pending.current = requestAnimationFrame(()=>{
      pending.current=0
      if(gl.info.render.calls>0 && !gl.getContext().isContextLost()) {complete.current=true;onReady()}
      else invalidate()
    })
  })
  return null
}
