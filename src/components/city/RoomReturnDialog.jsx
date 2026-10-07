import { useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import useSoundEffects from '../../audio/useSoundEffects.js'

export default function RoomReturnDialog({ label, onConfirm, onCancel }) {
  const { click: playClick } = useSoundEffects()
  const dialogRef = useRef(null)
  const cancelRef = useRef(null)
  useEffect(() => {
    const dialog = dialogRef.current
    const previousFocus = document.activeElement
    dialog.showModal()
    cancelRef.current.focus({ preventScroll: true })
    return () => {
      if (dialog.open) dialog.close()
      if (previousFocus instanceof HTMLElement && previousFocus.isConnected) previousFocus.focus({ preventScroll: true })
    }
  }, [])
  return createPortal(<dialog ref={dialogRef} className="room-return-dialog" role="dialog" aria-modal="true" aria-labelledby="room-return-title" aria-describedby="room-return-description"
    onCancel={event => { event.preventDefault();playClick();onCancel() }}
    onKeyDown={event => {
      if (event.key !== 'Tab') return
      const buttons = [...dialogRef.current.querySelectorAll('button')]
      if (event.shiftKey && document.activeElement === buttons[0]) { event.preventDefault();buttons.at(-1).focus() }
      else if (!event.shiftKey && document.activeElement === buttons.at(-1)) { event.preventDefault();buttons[0].focus() }
    }}>
    <p className="room-dialog-eyebrow">{label} / Entrance</p>
    <h2 id="room-return-title">Return to elevator?</h2>
    <p id="room-return-description">Walk back into the cabin and choose another floor?</p>
    <div className="room-dialog-actions">
      <button ref={cancelRef} type="button" onClick={onCancel}>Stay in room</button>
      <button type="button" onClick={onConfirm}>Yes, return to elevator</button>
    </div>
  </dialog>, document.body)
}
