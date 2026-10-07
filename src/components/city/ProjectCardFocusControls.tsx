import { Fragment, useEffect, useMemo, useRef } from 'react'
import { ProjectCatalogueContent } from './ProjectCatalogueDetails'
import useSoundEffects from '../../audio/useSoundEffects'
import { portfolio } from '../../data/portfolio'
import { isPublicLink, publicCaseSections } from '../../data/publicLinks'
import type { ProjectMetadata, ExhibitMetadata } from '../../types/scene'
import type { CaseSection } from '../../types/portfolio'

export interface ProjectCardFocusBaseProps {
  projectCount: number
  selectedSection: string
  onSection: (heading: string) => void
  onBack: () => void
}

export type ProjectFocusEntry = ProjectMetadata & { year?: string | number }

export type ProjectCardFocusControlsProps = ProjectCardFocusBaseProps & (
  | { variant?: 'project'; project: ProjectFocusEntry }
  | { variant: 'skill'; project: ExhibitMetadata }
  | { variant: 'timeline'; project: ExhibitMetadata }
)

interface FocusCategory { number: string; title: string; type: string }

const TITLES: Record<string, string> = { Overview:'Summary', 'Problem and purpose':'Problem & purpose', 'My role and contribution':'Your role', 'Key features':'Key features', 'Architecture and workflow':'Architecture & workflow', 'Technologies and technical decisions':'Technology & decisions', 'Technical challenges and solutions':'Challenges & solutions', 'Results and evidence':'Results & evidence', 'Lessons and next steps':'Lessons & next steps', 'Links and source references':'Links' }
const CATEGORIES: Record<string, FocusCategory> & { personal: FocusCategory } = { client:{number:'01',title:'Client · real world',type:'Client / real world'}, academic:{number:'02',title:'Academic assignment',type:'Academic assignment'}, personal:{number:'03',title:'Personal project',type:'Personal project'} }
Object.assign(TITLES,{'Core toolkit':'Core toolkit','Applied in projects':'Project evidence','Engineering workflow':'Workflow','Technical decisions':'Decisions & trade-offs','Collaboration and delivery':'Collaboration','Learning and scope':'Learning & scope','Links and sources':'Sources & links'})

function contributionLabel(sections: readonly CaseSection[]) {
  const role=sections.find(section=>section.heading==='My role and contribution')?.markdown || ''
  if (/confirmed: sole developer/i.test(role)) return 'Sole developer'
  if (/confirmed: CMS\/backend/i.test(role)) return 'CMS/backend · deployment'
  if (/confirmed: full-stack development/i.test(role)) return 'Full-stack · server'
  if (/confirmed: Damien contributed the GCS/i.test(role)) return 'Ground Control Station'
  if (/personal portfolio project/i.test(role)) return 'Personal portfolio'
  if (/personal project/i.test(role)) return 'Personal project'
  return 'Scope to confirm'
}

export default function ProjectCardFocusControls(props: ProjectCardFocusControlsProps) {
  const { project, projectCount, selectedSection, onSection, onBack, variant = 'project' } = props
  const { click } = useSoundEffects()
  const description = useRef<HTMLDivElement>(null)
  const chapterSheet = useRef<HTMLDialogElement>(null)
  const wheel = useRef({ delta: 0, lastEvent: 0, changedAt: -Infinity })
  const sections = useMemo(()=>publicCaseSections(project,project.catalogueSections || [{heading:'Overview',markdown:('overview' in project && project.overview) || (project.summary ?? '').replaceAll('\n',' ')}]),[project])
  const index = Math.max(0,sections.findIndex(section=>section.heading===selectedSection))
  const section = sections[index]
  const timeline=variant==='timeline'
  const skill=variant==='skill'
  const category=props.variant==='skill'?{number:'02',title:'Applied skills',type:'Skill area'}:props.variant==='timeline'?{number:'04',title:'Experience & education',type:props.project.categoryLabel ?? ''}:CATEGORIES[props.project.section ?? ''] || CATEGORIES.personal
  const metadata: [string, string][] = props.variant==='skill'?[['Type',category.type],['Focus',props.project.focus ?? '']]:props.variant==='timeline'?props.project.metadata ?? []:[['Type',category.type],['Role',contributionLabel(sections)]]
  if (props.variant !== 'skill' && props.variant !== 'timeline' && props.project.liveStatus) metadata.push(['Access',props.project.liveStatus==='private'?'Private · Tailscale':props.project.liveStatus==='unreleased'?'Unreleased preview':'Public website'])
  const prev=index>0?sections[index-1]:null,next=index<sections.length-1?sections[index+1]:null
  useEffect(() => { if (description.current) description.current.scrollTop=0 }, [selectedSection,project.id])
  useEffect(() => {
    const onWheel = (event: WheelEvent) => {
      if (event.defaultPrevented || event.ctrlKey || event.metaKey || Math.abs(event.deltaX)>Math.abs(event.deltaY) || !event.deltaY) return
      if (document.querySelector('dialog[open], [role="dialog"][aria-modal="true"]')) return
      if (event.target instanceof Element && event.target.closest('input,textarea,select,[contenteditable="true"],.project-video-controls')) return
      const reading = description.current
      if (reading && event.target instanceof Node && reading.contains(event.target)) {
        const canScroll = event.deltaY>0 ? reading.scrollTop+reading.clientHeight<reading.scrollHeight-1 : reading.scrollTop>1
        if (canScroll) {
          wheel.current.delta=0
          wheel.current.lastEvent=performance.now()
          return
        }
      }
      event.preventDefault()
      event.stopPropagation()
      const now=performance.now(), gesture=wheel.current
      if (now-gesture.lastEvent>180) gesture.delta=0
      gesture.lastEvent=now
      if (now-gesture.changedAt<400) return
      const unit=event.deltaMode===1?16:event.deltaMode===2?window.innerHeight:1
      const delta=event.deltaY*unit
      if (Math.sign(delta)!==Math.sign(gesture.delta)) gesture.delta=0
      gesture.delta+=delta
      if (Math.abs(gesture.delta)<60) return
      const nextIndex=Math.max(0,Math.min(sections.length-1,index+(gesture.delta>0?1:-1)))
      gesture.delta=0
      gesture.changedAt=now
      const nextSection = sections[nextIndex]
      if (nextIndex!==index && nextSection) onSection(nextSection.heading)
    }
    window.addEventListener('wheel',onWheel,{passive:false,capture:true})
    return () => window.removeEventListener('wheel',onWheel,{capture:true})
  }, [index,sections,onSection])
  useEffect(() => {
    const keydown = (event: KeyboardEvent) => {
      if (!['ArrowUp','ArrowDown'].includes(event.key) || event.repeat || event.defaultPrevented || event.ctrlKey || event.metaKey || event.altKey) return
      if (event.target instanceof Element && event.target.closest('input,textarea,select,[contenteditable="true"],dialog,[role="dialog"]')) return
      event.preventDefault()
      const nextIndex=Math.max(0,Math.min(sections.length-1,index+(event.key==='ArrowDown'?1:-1)))
      const nextSection = sections[nextIndex]
      if (nextIndex===index || !nextSection) return
      click();onSection(nextSection.heading)
      document.getElementById(`project-case-section-${nextIndex}`)?.focus({preventScroll:true})
    }
    window.addEventListener('keydown',keydown)
    return () => window.removeEventListener('keydown',keydown)
  }, [index,sections,onSection,click])
  if (!section) return null
  const liveUrl = 'liveUrl' in project ? project.liveUrl : undefined
  const liveLabel = 'liveLabel' in project ? project.liveLabel : undefined
  return <>
    <>
      <header className="project-mobile-header">
        <button type="button" aria-label={skill?'Back to gallery':timeline?'Back to observatory':'Back to hallway'} onClick={onBack}>←</button>
        <div><span>{skill?'Skills / Skill guide':timeline?'Journey / Journey record':'Projects / Case file'}</span><strong>{String(project.catalogueNumber || 1).padStart(2,'0')} {project.title.replaceAll('\n',' ')}</strong></div>
        <nav aria-label="Chapter progress">{sections.map((item,i)=><button key={item.heading} type="button" aria-label={`Chapter ${i+1}: ${TITLES[item.heading] || item.heading}`} aria-current={i===index?'step':undefined} data-complete={i<=index} onClick={()=>onSection(item.heading)}><span/></button>)}</nav>
      </header>
      <nav className="project-mobile-dock" aria-label={skill?'Skill chapters':timeline?'Timeline chapters':'Project chapters'}>
        <button type="button" aria-label="Previous chapter" disabled={!prev} onClick={()=>{if(prev) onSection(prev.heading)}}>←</button>
        <button type="button" aria-haspopup="dialog" onClick={()=>chapterSheet.current?.showModal()}><span>{String(index+1).padStart(2,'0')}/{String(sections.length).padStart(2,'0')}</span><strong>{TITLES[section.heading] || section.heading}</strong><span>▴</span></button>
        <button type="button" aria-label="Next chapter" disabled={!next} onClick={()=>{if(next) onSection(next.heading)}}>→</button>
      </nav>
      <dialog ref={chapterSheet} className="project-mobile-sheet" aria-labelledby="project-mobile-chapters-title" onKeyDown={event=>event.stopPropagation()} onClick={event=>{if(event.target===event.currentTarget) chapterSheet.current?.close()}}>
        <header><h2 id="project-mobile-chapters-title">Chapters</h2><button type="button" aria-label="Close chapters" onClick={()=>chapterSheet.current?.close()}>×</button></header>
        <ol>{sections.map((item,i)=><li key={item.heading}><button type="button" aria-current={i===index?'step':undefined} onClick={()=>{onSection(item.heading);chapterSheet.current?.close()}}><span>{String(i+1).padStart(2,'0')}</span><strong>{TITLES[item.heading] || item.heading}</strong><span>{i===index?'●':''}</span></button></li>)}</ol>
      </dialog>
    </>
    <button type="button" className="project-focus-back" data-exploring="true" onClick={onBack}>← {skill?'Back to gallery':timeline?'Back to observatory':'Back to hallway'} <kbd>Esc</kbd></button>
      <div className="project-case-sidefade project-case-sidefade-left" aria-hidden="true"/>
      <div className="project-case-sidefade project-case-sidefade-right" aria-hidden="true"/>
      <div className="project-case-context" aria-label={skill?'Skill context':timeline?'Timeline context':'Project context'}><span>{portfolio.siteTitle}</span><span aria-hidden="true">/</span><span>{skill?'Skills':timeline?'Journey':'Projects'}</span><span aria-hidden="true">/</span><span>{category.number} {category.title}</span></div>
      <aside className="project-case-description" data-mobile-project="true" aria-label={skill?'Skill description':timeline?'Timeline entry description':'Project description'}>
        <header>
          <div className="project-case-eyebrow"><span>{skill?'Skill':timeline?'Entry':'Project'} {String(project.catalogueNumber||1).padStart(2,'0')} / {projectCount}</span>{props.variant==='timeline'?<span>{props.project.categoryLabel}</span>:'year' in project && project.year && <span>{project.year}</span>}</div>
          <h2>{project.title.replaceAll('\n',' ')}</h2>
          <p className="project-case-intro">{(project.summary ?? '').replaceAll('\n',' ')}</p>
        </header>
        <dl className="project-case-meta">{metadata.map(([label,value])=><Fragment key={label}><dt>{label}</dt><dd>{value}</dd></Fragment>)}</dl>
        <section aria-live="polite">
          <div className="project-mobile-chapter-count">Chapter {String(index+1).padStart(2,'0')} / {String(sections.length).padStart(2,'0')}</div>
          <h3><span className="project-case-section-number">{String(index+1).padStart(2,'0')} / </span>{TITLES[section.heading] || section.heading}</h3>
          <div className="project-case-scroll" ref={description}><ProjectCatalogueContent section={section} numberedRows/>
            <button type="button" className="project-mobile-next" onClick={()=>onSection((next || sections[0] || section).heading)}><span><small>{next?`Next · ${String(index+2).padStart(2,'0')}`:'Back to start'}</small><strong>{TITLES[(next || sections[0] || section).heading] || (next || sections[0] || section).heading}</strong></span><span>→</span></button>
          </div>
          <div className="project-case-pagination">
            <button type="button" disabled={!prev} onClick={()=>{ if (prev) onSection(prev.heading) }} aria-label={`Previous ${skill?'skill':'project'} section`}>← {prev?(TITLES[prev.heading]||prev.heading):'Start'}</button>
            <button type="button" disabled={!next} onClick={()=>{ if (next) onSection(next.heading) }} aria-label={`Next ${skill?'skill':'project'} section`}>{next?(TITLES[next.heading]||next.heading):'End'} →</button>
          </div>
        </section>
      </aside>
      <nav className="project-case-navigation" aria-label={skill?'Skill case-file sections':timeline?'Timeline entry sections':'Project case-file sections'}>
        <div className="project-case-nav-heading"><span>{skill?'Skill guide':timeline?'Journey record':'Case file'}</span><span>{String(index+1).padStart(2,'0')} / {String(sections.length).padStart(2,'0')}</span></div>
        <div className="project-case-index">
        <div className="project-case-progress" aria-hidden="true"><span style={{height:`${(index+1)/sections.length*100}%`}}/></div>
        <ol>{sections.map((item,i)=><li key={item.heading} data-active={i===index} data-complete={i<index}>
          <button type="button" id={`project-case-section-${i}`} aria-current={i===index?'step':undefined} onClick={()=>onSection(item.heading)}>
            <span>{String(i+1).padStart(2,'0')}</span>{TITLES[item.heading] || item.heading}
          </button>
        </li>)}</ol>
        </div>
        <label className="project-case-mobile-select">{skill?'Skill guide':timeline?'Journey record':'Case file'}
          <select aria-label={skill?'Skill case-file section':timeline?'Timeline entry section':'Project case-file section'} value={section.heading} onChange={event=>onSection(event.target.value)}>{sections.map((item,i)=><option key={item.heading} value={item.heading}>{String(i+1).padStart(2,'0')} / {TITLES[item.heading] || item.heading}</option>)}</select>
        </label>
        <footer>{isPublicLink(project.url) && <a href={project.url ?? undefined} target="_blank" rel="noreferrer">{skill?'Project evidence':'Repository'} ↗</a>}{isPublicLink(liveUrl)&&<a href={liveUrl} target="_blank" rel="noreferrer">{liveLabel || 'Website'} ↗</a>}</footer>
      </nav>
      <div className="project-case-shortcuts"><span><kbd>Scroll / ↑ ↓</kbd> Section</span><span><kbd>Esc</kbd> Back</span></div>
  </>
}
