import { useCallback, useEffect, useRef } from 'react'
import { useThree } from '@react-three/fiber'
import { attachContactCardDismissal } from './contactCardDismissal'
import useSoundEffects from '../../audio/useSoundEffects'
import type { Group } from 'three'
import type { SceneGeometry } from '../../types/scene'
import type { RoomView } from '../../types/navigation'

export interface ContactCardDismissProps { groups: SceneGeometry[]; enabled: boolean; onView: (view: RoomView) => void }

export default function ContactCardDismiss({ groups, enabled, onView }: ContactCardDismissProps) {
  const root = useRef<Group>(null)
  const { camera, gl } = useThree()
  const { click } = useSoundEffects()
  const geometry = groups.find(item => item.role === 'contact' && item.id === 'card')?.geometry
  const dismiss = useCallback(() => { click();onView('main') }, [click, onView])
  useEffect(() => {
    if (!enabled || !geometry || !root.current) return
    return attachContactCardDismissal({ canvas: gl.domElement, camera, root: root.current, geometry, onDismiss: dismiss })
  }, [enabled, geometry, gl, camera, dismiss])
  return <group ref={root} name="contact-card-outside-click" />
}
