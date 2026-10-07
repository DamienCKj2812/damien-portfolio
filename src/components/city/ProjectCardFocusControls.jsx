import { Fragment, useEffect, useMemo, useRef } from 'react'
import { ProjectCatalogueContent } from './ProjectCatalogueDetails.jsx'
import useSoundEffects from '../../audio/useSoundEffects.js'
import { portfolio } from '../../data/portfolio.js'
import { isPublicLink, publicCaseSections } from '../../data/publicLinks.js'

const TITLES = { Overview:'Summary', 'Problem and purpose':'Problem & purpose', 'My role and contribution':'Your role', 'Key features':'Key features', 'Architecture and workflow':'Architecture & workflow', 'Technologies and technical decisions':'Technology & decisions', 'Technical challenges and solutions':'Challenges & solutions', 'Results and evidence':'Results & evidence', 'Lessons and next steps':'Lessons & next steps', 'Links and source references':'Links' }
const CATEGORIES = { client:{number:'01',title:'Client · real world',type:'Client / real world'}, academic:{number:'02',title:'Academic assignment',type:'Academic assignment'}, personal:{number:'03',title:'Personal project',type:'Personal project'} }
Object.assign(TITLES,{'Core toolkit':'Core toolkit','Applied in projects':'Project evidence','Engineering workflow':'Workflow','Technical decisions':'Decisions & trade-offs','Collaboration and delivery':'Collaboration','Learning and scope':'Learning & scope','Links and sources':'Sources & links'})

function contributionLabel(sections) {
  const role=sections.find(section=>section.heading==='My role and contribution')?.markdown || ''
  if (/confirmed: sole developer/i.test(role)) return 'Sole developer'
  if (/confirmed: CMS\/backend/i.test(role)) return 'CMS/backend · deployment'
  if (/confirmed: full-stack development/i.test(role)) return 'Full-stack · server'
  if (/confirmed: Damien contributed the GCS/i.test(role)) return 'Ground Control Station'
  if (/personal portfolio project/i.test(role)) return 'Personal portfolio'
  if (/personal project/i.test(role)) return 'Personal project'
  return 'Scope to confirm'
}

export default function ProjectCardFocusControls({ project, projectCount, selectedSection, onSection, onBack, variant = 'project' }) {
  const { click } = useSoundEffects()
  const description = useRef(null)
  const wheel = useRef({ delta: 0, lastEvent: 0, changedAt: -Infinity })
  const sections = useMemo(()=>publicCaseSections(project,project.catalogueSections || [{heading:'Overview',markdown:project.overview || project.summary.replaceAll('\n',' ')}]),[project])
  const index = Math.max(0,sections.findIndex(section=>section.heading===selectedSection))
  const section = sections[index]
  const timeline=variant==='timeline'
  const skill=variant==='skill'
  const category=skill?{number:'02',title:'Applied skills',type:'Skill area'}:timeline?{number:'04',title:'Experience & education',type:project.categoryLabel}:CATEGORIES[project.section] || CATEGORIES.personal
  const metadata=skill?[['Type',category.type],['Focus',project.focus]]:timeline?project.metadata:[['Type',category.type],['Role',contributionLabel(sections)],...(project.liveStatus?[['Access',project.liveStatus==='private'?'Private · Tailscale':project.liveStatus==='unreleased'?'Unreleased preview':'Public website']]:[])]
  const prev=index>0?sections[index-1]:null,next=index<sections.length-1?sections[index+1]:null
  useEffect(() => { if (description.current) description.current.scrollTop=0 }, [selectedSection,project.id])
  useEffect(() => {
    const onWheel = event => {
      if (event.defaultPrevented || event.ctrlKey || event.metaKey || Math.abs(event.deltaX)>Math.abs(event.deltaY) || !event.deltaY) return
      if (document.querySelector('dialog[open], [role="dialog"][aria-modal="true"]')) return
      if (event.target instanceof Element && event.target.closest('input,textarea,select,[contenteditable="true"],.project-video-controls')) return
      const reading = description.current
      if (reading?.contains(event.target)) {
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
      if (nextIndex!==index) onSection(sections[nextIndex].heading)
    }
    window.addEventListener('wheel',onWheel,{passive:false,capture:true})
    return () => window.removeEventListener('wheel',onWheel,{capture:true})
  }, [index,sections,onSection])
  useEffect(() => {
    const keydown = event => {
      if (!['ArrowUp','ArrowDown'].includes(event.key) || event.repeat || event.defaultPrevented || event.ctrlKey || event.metaKey || event.altKey) return
      if (event.target instanceof Element && event.target.closest('input,textarea,select,[contenteditable="true"],dialog,[role="dialog"]')) return
      event.preventDefault()
      const nextIndex=Math.max(0,Math.min(sections.length-1,index+(event.key==='ArrowDown'?1:-1)))
      if (nextIndex===index) return
      click();onSection(sections[nextIndex].heading)
      document.getElementById(`project-case-section-${nextIndex}`)?.focus({preventScroll:true})
    }
    window.addEventListener('keydown',keydown)
    return () => window.removeEventListener('keydown',keydown)
  }, [index,sections,onSection,click])
  return <>
    <button type="button" className="project-focus-back" data-exploring="true" onClick={onBack}>← {skill?'Back to gallery':timeline?'Back to observatory':'Back to hallway'} <kbd>Esc</kbd></button>
      <div className="project-case-sidefade project-case-sidefade-left" aria-hidden="true"/>
      <div className="project-case-sidefade project-case-sidefade-right" aria-hidden="true"/>
      <div className="project-case-context" aria-label={skill?'Skill context':timeline?'Timeline context':'Project context'}><span>{portfolio.siteTitle}</span><span aria-hidden="true">/</span><span>{skill?'Skills':timeline?'Journey':'Projects'}</span><span aria-hidden="true">/</span><span>{category.number} {category.title}</span></div>
      <aside className="project-case-description" aria-label={skill?'Skill description':timeline?'Timeline entry description':'Project description'}>
        <header>
          <div className="project-case-eyebrow"><span>{skill?'Skill':timeline?'Entry':'Project'} {String(project.catalogueNumber||1).padStart(2,'0')} / {projectCount}</span>{timeline?<span>{project.categoryLabel}</span>:project.year&&<span>{project.year}</span>}</div>
          <h2>{project.title.replaceAll('\n',' ')}</h2>
          <p className="project-case-intro">{project.summary.replaceAll('\n',' ')}</p>
        </header>
        <dl className="project-case-meta">{metadata.map(([label,value])=><Fragment key={label}><dt>{label}</dt><dd>{value}</dd></Fragment>)}</dl>
        <section aria-live="polite">
          <h3>{String(index+1).padStart(2,'0')} / {TITLES[section.heading] || section.heading}</h3>
          <div className="project-case-scroll" ref={description}><ProjectCatalogueContent section={section} numberedRows/></div>
          <div className="project-case-pagination">
            <button type="button" disabled={!prev} onClick={()=>onSection(prev.heading)} aria-label={`Previous ${skill?'skill':'project'} section`}>← {prev?(TITLES[prev.heading]||prev.heading):'Start'}</button>
            <button type="button" disabled={!next} onClick={()=>onSection(next.heading)} aria-label={`Next ${skill?'skill':'project'} section`}>{next?(TITLES[next.heading]||next.heading):'End'} →</button>
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
        <footer>{isPublicLink(project.url) && <a href={project.url} target="_blank" rel="noreferrer">{skill?'Project evidence':'Repository'} ↗</a>}{isPublicLink(project.liveUrl)&&<a href={project.liveUrl} target="_blank" rel="noreferrer">{project.liveLabel || 'Website'} ↗</a>}</footer>
      </nav>
      <div className="project-case-shortcuts"><span><kbd>Scroll / ↑ ↓</kbd> Section</span><span><kbd>Esc</kbd> Back</span></div>
  </>
}
