import { useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { portfolio } from '../data/portfolio'
import projects from '../data/projects2d.generated.json'
import { isPublicLink } from '../data/publicLinks'
import PixelPortrait from './city/PixelPortrait'
import { ProjectCatalogueContent } from './city/ProjectCatalogueDetails'
import { Starfield } from './EntryChoice'

const floors = [['about', 'About'], ['work', 'Work'], ['skills', 'Skills'], ['journey', 'Journey'], ['contact', 'Contact']] as const
const categories: Record<string, string> = { all: 'All', client: 'Client', academic: 'Academic', personal: 'Personal' }

function Tags({ items }: { items: string[] }) {
  return <div className="flat-tags">{items.map(item => <span key={item}>{item}</span>)}</div>
}

function Heading({ code, label, title, children }: { code: string; label: string; title: string; children?: ReactNode }) {
  return <><div className="flat-section-label"><span>{code}</span><i aria-hidden="true"/>{label}</div><div className="flat-section-heading"><h2>{title}</h2>{children}</div></>
}

export default function Portfolio2D({ onEnter3D, onEntry }: { onEnter3D: () => void; onEntry: () => void }) {
  const profile = portfolio.about.profile
  const root = useRef<HTMLDivElement>(null)
  const dialog = useRef<HTMLDialogElement>(null)
  const title = useRef<HTMLHeadingElement>(null)
  const [active, setActive] = useState(0)
  const [filter, setFilter] = useState('all')
  const [reducedMotion, setReducedMotion] = useState(false)
  const [copyStatus, setCopyStatus] = useState<{ id: string; text: string } | null>(null)
  const copyTimer = useRef(0)
  const copyRequest = useRef(0)

  useEffect(() => {
    const requests = copyRequest
    const container = root.current
    if (!container) return
    const media = window.matchMedia('(prefers-reduced-motion: reduce)')
    const updateMotion = () => setReducedMotion(media.matches)
    updateMotion(); media.addEventListener('change', updateMotion)
    const updateSection = () => {
      const top = container.getBoundingClientRect().top + container.clientHeight * .4
      let current = 0
      floors.forEach(([id], index) => { if ((document.getElementById(id)?.getBoundingClientRect().top ?? Infinity) < top) current = index })
      setActive(previous => previous === current ? previous : current)
    }
    container.addEventListener('scroll', updateSection, { passive: true })
    window.addEventListener('resize', updateSection)
    title.current?.focus({ preventScroll: true })
    updateSection()
    return () => {
      container.removeEventListener('scroll', updateSection)
      window.removeEventListener('resize', updateSection)
      media.removeEventListener('change', updateMotion)
      window.clearTimeout(copyTimer.current); requests.current++
    }
  }, [])

  const go = (id: string) => {
    dialog.current?.close()
    const section = document.getElementById(id)
    section?.scrollIntoView({ behavior: reducedMotion ? 'instant' : 'smooth', block: 'start' })
    section?.focus({ preventScroll: true })
  }
  const copy = async (id: string, text: string) => {
    const request = ++copyRequest.current
    window.clearTimeout(copyTimer.current)
    try {
      if (!navigator.clipboard) throw new Error('Clipboard unavailable')
      await navigator.clipboard.writeText(text)
      if (request !== copyRequest.current) return
      setCopyStatus({ id, text: 'Copied' })
    } catch {
      if (request !== copyRequest.current) return
      setCopyStatus({ id, text: 'Copy unavailable' })
    }
    copyTimer.current = window.setTimeout(() => setCopyStatus(null), 2000)
  }
  const freelance = portfolio.journey.items.find(item => item.id === 'freelance-full-stack')
  const outcome = (id: string) => {
    const prefix = id === 'agent-property' ? 'MyRumawip achievement:' : id === 'Aria' ? 'DWMLight achievement:' : null
    return prefix && freelance?.category === 'EXPERIENCE' ? freelance.highlights.find(text => text.startsWith(prefix))?.slice(prefix.length).trim() : undefined
  }
  const visibleProjects = projects.filter(project => filter === 'all' || project.section === filter)
  const current = floors[active] ?? floors[0]

  return <div className="flat-mode flat-scroll" ref={root} data-portfolio-mode="2d">
    <a className="flat-skip" href="#about" onClick={event => { event.preventDefault(); go('about') }}>Skip to portfolio content</a>
    <header className="flat-header"><div className="flat-header-inner">
      <a className="flat-brand" href="#top" onClick={event => { event.preventDefault(); go('top') }}><span className="flat-diamond"/>DamienCKJ</a>
      <nav className="flat-desktop-nav" aria-label="Portfolio sections">{floors.map(([id, label], index) => <button key={id} aria-current={active === index ? 'location' : undefined} onClick={() => go(id)}><span>F0{index + 1}</span>{label}</button>)}</nav>
      <div className="flat-header-actions"><button className="flat-action" onClick={onEnter3D}>Enter 3D <span aria-hidden="true">↗</span></button></div>
    </div></header>
    <main>
      <section id="top" className="flat-hero" tabIndex={-1}>
        <Starfield/>
        <div className="flat-container flat-hero-inner">
          <div className="flat-status flat-mono"><span/>{profile.status}</div>
          <div><h1 ref={title} tabIndex={-1}>{portfolio.fullName}</h1><div className="flat-role flat-mono">{portfolio.name} · {profile.role}</div></div>
          <p className="flat-hero-intro">{portfolio.hero.headline}</p>
          <div className="flat-hero-actions"><button className="flat-action flat-action-primary" onClick={() => go('work')}>{portfolio.hero.action.label} ↓</button><button className="flat-action" onClick={() => go('contact')}>Contact</button></div>
          <dl className="flat-hero-facts">{[['Focus', profile.focus], ['Based', profile.location], ['Now', profile.status]].map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>
        </div>
      </section>
      <div className="flat-container flat-content">
        <section id="about" className="flat-section flat-about" tabIndex={-1}>
          <div><Heading code="F01" label="About" title={portfolio.about.title}/><div className="flat-about-copy"><p>{portfolio.about.description}</p><p>{profile.approach}</p></div>
            <dl className="flat-about-facts">{[{ label: 'Core stack', items: profile.stack }, { label: 'Strengths', items: profile.strengths }, { label: 'Interests', items: profile.interests }].map(({ label, items }) => <div key={label}><dt>{label}</dt><dd><Tags items={items}/></dd></div>)}</dl>
          </div>
          <figure className="flat-portrait"><div className="flat-portrait-frame"><PixelPortrait src={`${import.meta.env.BASE_URL}${profile.portrait.src}`} originalSrc={profile.portrait.originalSrc ? `${import.meta.env.BASE_URL}${profile.portrait.originalSrc}` : null} alt={profile.portrait.alt} reducedMotion={reducedMotion} active/></div><figcaption><span>{profile.portrait.caption}</span><span>Rev. {profile.revision}</span></figcaption></figure>
        </section>
        <section id="work" className="flat-section" tabIndex={-1}>
          <Heading code="F02" label="Work" title="Selected projects"><div className="flat-filters" role="group" aria-label="Filter projects">{Object.entries(categories).map(([id, label]) => <button key={id} aria-pressed={filter === id} onClick={() => setFilter(id)}>{label}</button>)}</div></Heading>
          <p className="flat-project-count" role="status">{visibleProjects.length} {filter === 'all' ? 'reviewed' : categories[filter]?.toLowerCase()} projects</p>
          <div className="flat-projects">{visibleProjects.map((project, index) => {
            const role = project.sections.find(section => section.heading === 'My role and contribution')
            const result = outcome(project.id)
            return <details className="flat-project" key={project.id} open={index === 0}>
              <summary><span className="flat-project-number">P/{String(projects.findIndex(item => item.id === project.id) + 1).padStart(2, '0')}</span><span className="flat-project-title"><strong>{project.id === 'agent-property' ? 'MyRumawip' : project.title}</strong><span>{project.summary}</span></span><span className="flat-project-kind">{categories[project.section]}</span><span className="flat-project-end">{project.status === 'unreleased' && <span className="flat-badge">Unreleased</span>}<span className="flat-project-sign" aria-hidden="true"/></span></summary>
              <div className="flat-project-detail"><div><ProjectCatalogueContent section={{ heading: 'Overview', markdown: project.overview }}/>{result && <div className="flat-outcome"><span className="flat-mono">Outcome</span><p>{result}</p></div>}</div><div className="flat-project-meta">{role && <div><span className="flat-mono">Role / contribution</span><ProjectCatalogueContent section={role}/></div>}<Tags items={project.tags}/><div className="flat-project-links">{project.links.filter(link => isPublicLink(link.href)).map(link => <a className="flat-action" key={link.href} href={link.href} target="_blank" rel="noopener noreferrer">{link.label} →</a>)}</div></div></div>
              <div className="flat-case-sections">{project.sections.filter(section => !['Overview', 'My role and contribution', 'Links and source references'].includes(section.heading)).map(section => <details key={section.heading}><summary>{section.heading}<span aria-hidden="true">+</span></summary><ProjectCatalogueContent section={section}/></details>)}</div>
            </details>
          })}</div>
        </section>
        <section id="skills" className="flat-section" tabIndex={-1}>
          <Heading code="F03" label="Skills" title={portfolio.skills.title}/><p className="flat-section-description">{portfolio.skills.description}</p>
          <div className="flat-skill-grid">{portfolio.skills.groups.map(group => <div key={group.id}><div className="flat-skill-title flat-mono"><span>{group.title}</span><span>{String(group.items.length).padStart(2, '0')}</span></div><Tags items={group.items}/></div>)}</div>
          <div className="flat-learning"><span className="flat-mono">Currently learning</span><Tags items={portfolio.skills.learning}/></div>
        </section>
        <section id="journey" className="flat-section" tabIndex={-1}>
          <Heading code="F04" label="Experience & education" title={portfolio.journey.title}/>
          <div className="flat-experience">{portfolio.journey.items.filter(item => item.category === 'EXPERIENCE').map(item => <article key={item.id}><div className={`flat-period flat-mono${item.period === 'Ongoing' ? ' flat-period-current' : ''}`}><span/>{item.period}</div><div><h3>{item.title}</h3><p className="flat-organization">{item.organization}</p><p>{item.description}</p>{item.category === 'EXPERIENCE' && <details className="flat-highlights"><summary>Work highlights <span aria-hidden="true">+</span></summary><ul>{item.highlights.map(highlight => <li key={highlight}>{highlight}</li>)}</ul></details>}</div></article>)}</div>
          <p className="flat-mono flat-education-label">Education</p><div className="flat-education">{portfolio.journey.items.filter(item => item.category === 'EDUCATION').map(item => <article key={item.id}><span className="flat-mono">{item.period}</span><div><h3>{item.title}</h3><p className="flat-organization">{item.organization}</p></div><p className="flat-education-result">{item.description}</p></article>)}</div>
        </section>
        <section id="contact" className="flat-section flat-contact" tabIndex={-1}>
          <Heading code="F05" label="Contact" title={portfolio.contact.title}/><p className="flat-section-description">{portfolio.contact.description}</p>
          <div className="flat-contacts">{portfolio.contact.links.map(link => {
            const copyText = link.id === 'email' ? portfolio.contact.email : link.id === 'phone' ? portfolio.contact.phone : null
            return <div key={link.id}><a href={link.href} target={/^https:/.test(link.href) ? '_blank' : undefined} rel={/^https:/.test(link.href) ? 'noopener noreferrer' : undefined}><span className="flat-mono">{link.id} ↗</span><span>{link.label}</span></a>{copyText && <button aria-label={`Copy ${link.id}`} onClick={() => { void copy(link.id, copyText) }}>{copyStatus?.id === link.id ? copyStatus.text : 'Copy'}</button>}</div>
          })}</div><span className="flat-copy-feedback" role="status">{copyStatus ? `${copyStatus.id}: ${copyStatus.text}` : ''}</span>
          <button className="flat-action" onClick={onEntry}>Change portfolio experience ↗</button>
          <footer><span>© {new Date().getFullYear()} {portfolio.fullName}</span><span>Off duty: {profile.interests.join(' · ')}</span></footer>
        </section>
      </div>
    </main>
    <div className="flat-mobile-dock"><button className="flat-floor-trigger" onClick={() => dialog.current?.showModal()} aria-haspopup="dialog" aria-controls="flat-floor-dialog"><span className="flat-mono">F0{active + 1}</span><span>{current[1]}</span><span className="flat-floor-pips" aria-hidden="true">{floors.slice().reverse().map(([id], index) => <i key={id} className={floors.length - index - 1 <= active ? 'is-active' : ''}/>)}</span></button><button className="flat-action flat-action-primary" onClick={() => go('contact')}>Contact</button></div>
    <dialog ref={dialog} id="flat-floor-dialog" className="flat-floor-dialog" aria-labelledby="flat-floor-title" onClick={event => { if (event.target === event.currentTarget) dialog.current?.close() }}>
      <div className="flat-floor-sheet"><div className="flat-floor-sheet-title"><h2 id="flat-floor-title" className="flat-mono">Choose a floor</h2><button aria-label="Close floor picker" onClick={() => dialog.current?.close()}>✕</button></div>{floors.map(([id, label], index) => <button key={id} aria-current={active === index ? 'location' : undefined} onClick={() => go(id)}><span>F0{index + 1}</span>{label}<span aria-hidden="true">{active === index ? '●' : ''}</span></button>)}</div>
    </dialog>
  </div>
}
