import { portfolio } from '../../data/portfolio.js'
import GuidedRoomControls from './GuidedRoomControls.jsx'
import RoomSidebar, { RoomAction, RoomIndex, RoomMoreControls } from './RoomSidebar.jsx'
import ProjectRepositoryLinks from './ProjectRepositoryLinks.jsx'
import ProjectCatalogueDetails from './ProjectCatalogueDetails.jsx'
import ProjectCardFocusControls from './ProjectCardFocusControls.jsx'

export default function RoomControls({ assets, state, reducedMotion, onView, onObserver, onProject, onProjectSection, onCloseProject, onMove, onLook, onPause, onToggleWalk, onSeekTour, onStation, onExhibit, onLookAt, onResetLook }) {
  if (assets.manifest.level==='projects'&&state.view==='directory') return <button type="button" className="project-focus-back" onClick={()=>onView('main')}>← Back to hallway <kbd>Esc</kbd></button>
  if (assets.manifest.level==='skills' && state.view==='skill') {
    const entry=assets.manifest.exhibits.find(item=>item.id===state.exhibit)
    if (entry) return <ProjectCardFocusControls variant="skill" project={entry} projectCount={assets.manifest.exhibits.filter(item=>item.kind==='skill').length} selectedSection={state.projectSection} onSection={onProjectSection} onBack={()=>onView('main')}/>
  }
  if (assets.manifest.level==='experience' && state.view==='timeline') {
    const entry=assets.manifest.exhibits.find(item=>item.id===state.exhibit)
    if (entry) return <ProjectCardFocusControls variant="timeline" project={entry} projectCount={assets.manifest.exhibits.length} selectedSection={state.projectSection} onSection={onProjectSection} onBack={()=>onView('main')}/>
  }
  if (assets.manifest.navigation?.type === 'guided') return <GuidedRoomControls assets={assets} state={state} reducedMotion={reducedMotion} onView={onView} onLook={onLook} onPause={onPause} onToggleWalk={onToggleWalk} onSeekTour={onSeekTour} onStation={onStation} onExhibit={onExhibit} onLookAt={onLookAt} onResetLook={onResetLook} />
  const hallway = assets.manifest.level === 'projects'
  const project = assets.manifest.projects.find(project=>project.id===state.project)
  if (hallway && state.view==='project' && project) return <ProjectCardFocusControls project={project} projectCount={assets.manifest.projects.length} selectedSection={state.projectSection} onSection={onProjectSection} onBack={onCloseProject}/>
  const card = state.view === 'card'
  return <RoomSidebar number={hallway ? '03' : '01'} chapter={hallway ? 'Projects' : 'About me'} title={hallway ? 'The project hallway' : card ? 'Let’s connect' : 'About office'}
    description={hallway ? 'Walk through the displays. Drag to look around or scroll over the scene to move.' : card ? portfolio.contact.description : portfolio.about.description}
    status={hallway && <><p id="hallway-category-status">Client / real world project</p><div className="room-status-row"><button type="button" className="room-tour-toggle" data-paused={state.paused} aria-pressed={!state.paused} onClick={onPause} disabled={reducedMotion}><span className="room-status-dot" aria-hidden="true"/>{reducedMotion ? 'Reduced motion' : state.paused ? 'Resume visitors' : 'Pause visitors'}</button></div></>} controls={hallway ? <>
      <div className="room-motion-controls">
        {[['Back', -1, '↓'], ['Forward', 1, '↑']].map(([label, direction, shortcut]) => <RoomAction key={label} shortcut={shortcut} onPointerDown={(event) => { event.currentTarget.setPointerCapture(event.pointerId);onMove(direction) }} onPointerUp={() => onMove(0)} onPointerCancel={() => onMove(0)} onKeyDown={(event) => { if (['Enter', ' '].includes(event.key)) { event.preventDefault();onMove(direction) } }} onKeyUp={() => onMove(0)} onBlur={() => onMove(0)}>{label}</RoomAction>)}
      </div>
      <p className="room-key-hint"><kbd>W / S</kbd> Walk <span>·</span> <kbd>Drag</kbd> Look</p>
      <RoomMoreControls>
        <div className="room-motion-controls"><RoomAction onClick={() => onLook(-Math.PI / 4)}>Look left</RoomAction><RoomAction onClick={() => onLook(Math.PI / 4)}>Look right</RoomAction></div>
        <p className="room-key-hint">Hold Shift to walk faster.</p>
      </RoomMoreControls>
    </> : <>
      {card && <RoomAction shortcut="←" onClick={() => onView('main')}>Back to office</RoomAction>}
      {!card && <div className="room-motion-controls"><RoomAction shortcut="←" onClick={() => onLook(-Math.PI / 4)}>Look left</RoomAction><RoomAction shortcut="→" onClick={() => onLook(Math.PI / 4)}>Look right</RoomAction><RoomAction shortcut="R" onClick={onResetLook}>Reset look</RoomAction></div>}
      <p className="room-key-hint">{card ? 'Click outside the card or use Back to return to your office view.' : 'Drag to turn around · Arrow keys to look'}</p>
    </>}>
    {hallway ? <>
      {assets.manifest.navigation.categories.map(category => <section className="room-category-group" key={category.id} aria-label={category.title}>
      {category.door && !state.openedCategories.includes(category.id) && <p className="room-category-locked">Walk through the luminous portal to continue into this category.</p>}
      <RoomIndex label={`${category.number} / ${category.title}`} items={assets.manifest.projects.filter(project => project.section === category.id).map(project => ({ ...project, locked: !state.openedCategories.includes(category.id) }))} selected={state.project} onSelect={id => onProject(id, true)} renderDetail={project => <>
        {project.catalogueTitle && <h4 className="project-catalogue-title">{project.catalogueTitle}</h4>}
        <p>{project.overview || project.summary.replaceAll('\n', ' ')}</p>
        <ProjectRepositoryLinks project={project} />
        {project.id === state.project && <ProjectCatalogueDetails project={project} />}
      </>} />
      </section>)}
    </> : <>
      <RoomIndex label="Explore" items={[{ id: 'observer', buttonId: 'observer-profile-trigger', dialog: true, title: `Meet ${portfolio.name}` }, { id: 'card', title: 'View business card' }]} selected={card ? 'card' : state.profileOpen ? 'observer' : null} onSelect={id => id === 'observer' ? onObserver() : onView('card')} />
      {card && <div className="room-contact-links"><h3>Contact</h3>{portfolio.contact.links.map(link => <a key={link.id} className="room-detail-action" href={link.href} target="_blank" rel="noreferrer">{link.label} <span aria-hidden="true">↗</span></a>)}</div>}
    </>}
  </RoomSidebar>
}
