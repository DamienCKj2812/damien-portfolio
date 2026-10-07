import { useId, useState } from 'react'

export default function ToplineControl({ label, tooltip, className, children, onClick, ...props }) {
  const id = `topline-tooltip-${useId().replace(/:/g, '')}`
  const [hovered, setHovered] = useState(false)
  const [focused, setFocused] = useState(false)
  const [dismissed, setDismissed] = useState(false)
  const visible = (hovered || focused) && !dismissed
  return <span className="topline-control" onPointerEnter={event => { if (event.pointerType !== 'touch') { setHovered(true);setDismissed(false) } }}
    onPointerLeave={() => setHovered(false)} onFocus={() => { setFocused(true);setDismissed(false) }} onBlur={() => setFocused(false)}
    onKeyDown={event => { if (event.key === 'Escape' && visible) { event.preventDefault();event.stopPropagation();setDismissed(true) } }}>
    <button type="button" className={className} aria-label={label} aria-describedby={id}
      onClick={event => { setDismissed(true);onClick(event) }} {...props}>{children}</button>
    <span id={id} className="topline-tooltip" role="tooltip" hidden={!visible}>{tooltip}</span>
  </span>
}
