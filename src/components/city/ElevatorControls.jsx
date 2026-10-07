export default function ElevatorControls({ levels, state, onSelect, onReplay, onEnterRoom, onFocusLevel, onPressLevel }) {
  const selected = levels.find((level) => level.id === state.level)
  if (state.status === 'departing') return <div className="elevator-trip-status">
    <p role="status">LEVEL {String(selected?.number || 1).padStart(2, '0')} · {state.frame < 221 ? 'Closing doors…' : state.frame < 300 ? 'Turning toward the exit…' : state.frame < 370 ? 'Opening your destination…' : 'Entering your room…'}</p>
    <button type="button" onClick={onReplay}>Cancel / return to selection</button>
  </div>
  if (state.status === 'arrived') return <div className="elevator-interface" role="dialog" aria-labelledby="elevator-arrival-title">
    <p className="elevator-eyebrow">ARRIVED / LEVEL {String(selected?.number || 1).padStart(2, '0')}</p>
    <h2 id="elevator-arrival-title">{selected?.title}</h2>
    <p>{selected?.description}</p>
    <div className="elevator-actions">
      <button type="button" onClick={() => onEnterRoom(selected?.id)}>Enter this room ↗</button>
      <button type="button" onClick={onReplay}>Choose another level</button>
    </div>
  </div>
  return <div className="sr-only" role="region" aria-label="Elevator floor selection">
    <p>Choose a floor. Keyboard focus lights the corresponding modeled button; Enter or Space selects it.</p>
    <div>
      {[...levels].sort((a, b) => b.number - a.number).map((level) => <button key={level.id} type="button" data-sound-effect="environment" disabled={!level.available} onFocus={() => onFocusLevel(level.id)} onBlur={() => { onFocusLevel(null);onPressLevel(null) }} onKeyDown={(event) => { if (['Enter', ' '].includes(event.key)) onPressLevel(level.id) }} onKeyUp={() => onPressLevel(null)} onClick={() => onSelect(level.id)} aria-label={`Select level ${level.number}: ${level.title}${level.available ? '' : ' (Coming soon)'}`}>
        <span>{String(level.number).padStart(2, '0')}</span><span>{level.title}{!level.available && <small>Coming soon</small>}</span><span aria-hidden="true">↗</span>
      </button>)}
    </div>
  </div>
}
