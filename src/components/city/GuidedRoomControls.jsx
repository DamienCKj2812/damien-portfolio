import RoomSidebar, { RoomAction, RoomIndex, RoomMoreControls } from './RoomSidebar.jsx'
import { portfolio } from '../../data/portfolio.js'

const viewNames = { atat: 'AT-AT close-up', globe: 'Globe detail', oculus: 'Roof window', window: 'Observation window' }

export default function GuidedRoomControls({ assets, state, reducedMotion, onView, onLook, onPause, onToggleWalk, onSeekTour, onStation, onExhibit, onLookAt, onResetLook }) {
  const { manifest } = assets
  const skills = manifest.level === 'skills'
  const tourAction = state.walkPaused ? 'Start / resume tour' : skills ? 'Pause tour' : 'Pause walking'
  return <RoomSidebar number={skills ? '02' : '04'} chapter={skills ? 'Skills' : 'Experience & education'} title={manifest.label}
    description={skills ? `${portfolio.skills.description} Click a skill card to inspect its toolkit and project evidence.` : 'Scroll to walk continuously through the timeline. Drag to look around or select a node to inspect it.'}
    status={<>
      <div className="room-status-row">
        <button type="button" className="room-tour-toggle" data-paused={state.walkPaused} aria-label={tourAction} aria-pressed={!state.walkPaused} onClick={onToggleWalk} disabled={reducedMotion}>
          <span className="room-status-dot" aria-hidden="true"/><span>{reducedMotion ? 'Reduced motion' : state.walkPaused ? 'Tour paused' : 'Tour running'}</span>
        </button>
        <span aria-hidden="true">·</span><output id="room-tour-status" className="room-tour-status" aria-live="off">Entrance</output>
        <kbd aria-hidden="true">Space</kbd>
      </div>
    </>} controls={<>
      <div className="room-motion-controls">
        <RoomAction shortcut="←" aria-label="Previous exhibit" onClick={() => onStation(-1)}>Prev</RoomAction>
        <RoomAction shortcut="→" aria-label="Next exhibit" onClick={() => onStation(1)}>Next</RoomAction>
        <RoomAction shortcut="R" onClick={onResetLook}>Reset look</RoomAction>
      </div>
      <p className="room-key-hint"><kbd>Drag</kbd> Look</p>
      <RoomMoreControls>
        <div className="room-motion-controls">
          <RoomAction shortcut="Home" onClick={() => onSeekTour(1)}>Restart route</RoomAction>
          <RoomAction onClick={() => onLook(-Math.PI / 4)}>Look left</RoomAction><RoomAction onClick={() => onLook(Math.PI / 4)}>Look right</RoomAction>
        </div>
        <label className="room-project-label" htmlFor="room-view">View</label>
        <select id="room-view" value={state.view} onChange={(event) => onView(event.target.value)}>
          <option value="main">Guided view / free-look</option>
          {Object.keys(manifest.cameras).filter(key => key !== 'main').map(key => <option key={key} value={key}>{viewNames[key] || key}</option>)}
        </select>
        <RoomAction onClick={onPause} disabled={reducedMotion}>{reducedMotion ? 'Reduced motion' : state.paused ? 'Resume animation' : 'Pause animation'}</RoomAction>
        <p className="room-key-hint">Guided route · {Math.round(manifest.navigation.route.frameEnd / manifest.fps)} seconds{reducedMotion ? ' · Choose an exhibit to navigate' : ''}</p>
      </RoomMoreControls>
    </>}>
    <RoomIndex label={skills ? 'Exhibits' : 'Timeline'} items={manifest.exhibits} selected={state.exhibit} onSelect={id => onExhibit(id, true)} renderDetail={item => <>
      <p>{item.items?.length ? item.items.join(' · ') : item.caption}</p>
      <button type="button" className="room-detail-action" onClick={onLookAt}>Look at selected exhibit <span aria-hidden="true">↗</span></button>
    </>} />
  </RoomSidebar>
}
