import { useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import useSoundEffects from '../../audio/useSoundEffects'

export interface RoomReturnDialogProps {
  label: string
  onConfirm: () => void
  onCancel: () => void
}

export default function RoomReturnDialog({ label, onConfirm, onCancel }: RoomReturnDialogProps) {
  const { click: playClick } = useSoundEffects()
  const dialogRef = useRef<HTMLDialogElement>(null)
  const cancelRef = useRef<HTMLButtonElement>(null)
  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return
    const previousFocus = document.activeElement
    dialog.showModal()
    cancelRef.current?.focus({ preventScroll: true })
    return () => {
      if (dialog.open) dialog.close()
      if (previousFocus instanceof HTMLElement && previousFocus.isConnected) previousFocus.focus({ preventScroll: true })
    }
  }, [])
  return createPortal(<dialog ref={dialogRef} className="room-return-dialog" role="dialog" aria-modal="true" aria-labelledby="room-return-title" aria-describedby="room-return-description"
    onCancel={event => { event.preventDefault();playClick();onCancel() }}
    onKeyDown={event => {
      if (event.key !== 'Tab') return
      const buttons = [...event.currentTarget.querySelectorAll('button')]
      if (event.shiftKey && document.activeElement === buttons[0]) { event.preventDefault();buttons.at(-1)?.focus() }
      else if (!event.shiftKey && document.activeElement === buttons.at(-1)) { event.preventDefault();buttons[0]?.focus() }
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
