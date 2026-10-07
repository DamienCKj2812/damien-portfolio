import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import type { JourneyRecord } from '../../types/portfolio'
import { portfolio } from '../../data/portfolio'
import { useReducedMotion } from './useScrollTimeline'
import PixelPortrait from './PixelPortrait'
import useSoundEffects from '../../audio/useSoundEffects'
import './observerProfile.css'

export interface ObserverProfileProps { onClose: () => void }

function recordHighlights(lines: readonly string[]) {
  const cards: { title: string; description: string; result?: string }[] = []
  for (const line of lines) {
    const match = /^([^:]{1,80}): (.+)$/.exec(line)
    const title = match?.[1] || ''
    const description = match?.[2] || line
    const previous = cards.at(-1)
    const resultName = title.endsWith(' achievement') ? title.replace(/ achievement$/, '') : null
    if (resultName && previous?.title.startsWith(resultName)) previous.result = description
    else cards.push({ title, description })
  }
  return cards
}

function RecordEntry({ item, narrow, initiallyOpen }: { item: JourneyRecord; narrow: boolean; initiallyOpen: boolean }) {
  const [expanded, setExpanded] = useState(initiallyOpen)
  const highlights = 'highlights' in item ? item.highlights : []
  const cards = recordHighlights(highlights)
  const showDetails = !narrow || expanded
  return <article className="observer-record-row">
    <div className="observer-record-title">
      {item.period && <p className="observer-period">{item.period === 'Ongoing' && <span className="observer-status-dot" aria-hidden="true"/>}{item.period}</p>}
      <h4>{item.organization}</h4>
      <p className="observer-record-role">{item.title}</p>
      {item.category.includes('SAMPLE') && <span className="observer-sample">Sample entry</span>}
    </div>
    {item.description && <p className="observer-record-description">{item.description}</p>}
    {highlights.length > 0 && <>
      <ul id={`observer-highlights-${item.id}`} className="observer-record-highlights" hidden={!showDetails}>{cards.map(card=><li key={card.description}>{card.title && <strong>{card.title}</strong>}<p>{card.description}</p>{card.result && <div className="observer-highlight-result"><span>Result</span><p>{card.result}</p></div>}</li>)}</ul>
      {narrow && <button type="button" className="observer-details-toggle" aria-expanded={expanded} aria-controls={`observer-highlights-${item.id}`} onClick={()=>setExpanded(value=>!value)}>{expanded?'Hide details −':`Show ${cards.length} highlights +`}</button>}
    </>}
  </article>
}

function RecordSection({ title, items, narrow }: { title: string; items: readonly JourneyRecord[]; narrow: boolean }) {
  return <section className="observer-record-section" aria-label={title}>
    <div className="observer-record-heading"><h3>{title}</h3><span>{String(items.length).padStart(2,'0')}</span></div>
    {items.length ? items.map((item,index)=><RecordEntry key={item.id} item={item} narrow={narrow} initiallyOpen={index===0}/>) : <p className="observer-empty-record">Details to be added.</p>}
  </section>
}

const PANEL_LABELS = ['Identity','Portrait','Record'] as const

export default function ObserverProfile({ onClose }: ObserverProfileProps) {
  const { click: playClick } = useSoundEffects()
  const dialogRef = useRef<HTMLDialogElement>(null)
  const closeRef = useRef<HTMLButtonElement>(null)
  const mainRef = useRef<HTMLDivElement>(null)
  const panels = useRef<(HTMLElement | null)[]>([])
  const copyTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const copyRequest = useRef({ value: 0 })
  const reducedMotion = useReducedMotion()
  const [narrow, setNarrow] = useState(()=>window.matchMedia('(max-width: 899px)').matches)
  const [activePanel, setActivePanel] = useState(0)
  const [copied, setCopied] = useState<string | null>(null)
  const [copyMessage, setCopyMessage] = useState('')
  const profile = portfolio.about.profile
  const education = portfolio.journey.items.filter(item=>/education/i.test(item.category))
  const experience = portfolio.journey.items.filter(item=>!/education/i.test(item.category))
  const stack = profile.stack || [...new Set(portfolio.skills.groups.flatMap(group=>group.items))]
  const portrait = profile.portrait
  const assetUrl = (src?: string | null) => src ? /^https?:\/\//.test(src) ? src : `${import.meta.env.BASE_URL}${src.replace(/^\/+/, '')}` : null
  const portraitSrc = assetUrl(portrait?.src)
  const originalPortraitSrc = assetUrl(portrait?.originalSrc)

  useEffect(()=>{
    const query = window.matchMedia('(max-width: 899px)')
    const update = () => setNarrow(query.matches)
    query.addEventListener('change',update)
    return ()=>query.removeEventListener('change',update)
  },[])

  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return
    const previousFocus = document.activeElement
    const request = copyRequest.current
    const body = document.body
    const previousOverflow = body.style.overflow
    const previousPadding = body.style.paddingRight
    const scrollbar = window.innerWidth - document.documentElement.clientWidth
    if (scrollbar > 0) body.style.paddingRight = `${parseFloat(getComputedStyle(body).paddingRight) + scrollbar}px`
    body.style.overflow = 'hidden'
    dialog.showModal()
    closeRef.current?.focus({ preventScroll: true })
    return () => {
      if (dialog.open) dialog.close()
      body.style.overflow = previousOverflow
      body.style.paddingRight = previousPadding
      request.value++
      if (copyTimer.current) clearTimeout(copyTimer.current)
      const fallback = document.getElementById('observer-profile-trigger')
      const target = previousFocus instanceof HTMLElement && previousFocus.isConnected && previousFocus.matches('button, a, input, select, textarea, [tabindex]') ? previousFocus : fallback
      target?.focus({ preventScroll: true })
    }
  }, [])

  const copyContact = async (id: string, text: string) => {
    const request = ++copyRequest.current.value
    if (copyTimer.current) clearTimeout(copyTimer.current)
    try {
      await navigator.clipboard.writeText(text)
      if (request !== copyRequest.current.value) return
      setCopied(id)
      setCopyMessage(`${id === 'email'?'Email address':'Phone number'} copied.`)
      copyTimer.current = setTimeout(()=>{setCopied(null);setCopyMessage('')},1500)
    } catch {
      if (request !== copyRequest.current.value) return
      setCopied(null)
      setCopyMessage('Could not copy. Please select the contact text to copy it.')
    }
  }

  const selectPanel = (index: number) => {
    const panel = panels.current[index]
    if (!panel || !mainRef.current) return
    mainRef.current.scrollTo({top:panel.offsetTop,behavior:reducedMotion?'instant':'smooth'})
    panel.focus({preventScroll:true})
    setActivePanel(index)
  }
  const updateActivePanel = () => {
    const main = mainRef.current
    if (!narrow || !main) return
    let index = 0
    panels.current.forEach((panel,i)=>{if(panel && panel.offsetTop <= main.scrollTop+120) index=i})
    setActivePanel(index)
  }

  return createPortal(<dialog ref={dialogRef} id="observer-profile-dialog" className="observer-profile" aria-labelledby="observer-profile-title"
    onKeyDown={event=>{
      if(event.key!=='Tab') return
      const items = [...event.currentTarget.querySelectorAll<HTMLElement>('button, a[href], input, select, textarea, [tabindex="0"]')].filter(item=>!item.matches(':disabled') && item.getClientRects().length>0)
      const first=items[0],last=items.at(-1)
      if(event.shiftKey && document.activeElement===first) {event.preventDefault();last?.focus()}
      else if(!event.shiftKey && document.activeElement===last) {event.preventDefault();first?.focus()}
    }} onCancel={event=>{event.preventDefault();playClick();onClose()}}>
    <div className="observer-sheet">
      <header className="observer-sheet-header">
        <span>Room 01 / About</span>
        <span className="observer-header-center">{portfolio.name} / Personal portfolio</span>
        <div className="observer-header-actions"><span>Rev. {profile.revision}</span><button ref={closeRef} type="button" onClick={onClose} aria-label="Close about profile">Close <span aria-hidden="true">×</span></button></div>
      </header>
      <nav className="observer-mobile-nav" aria-label="Profile sections">{PANEL_LABELS.map((label,index)=><button type="button" key={label} aria-current={index===activePanel?'location':undefined} onClick={()=>selectPanel(index)}>{label}</button>)}</nav>
      <div className="observer-columns" ref={mainRef} onScroll={updateActivePanel}>
        <section ref={node=>{panels.current[0]=node}} className="observer-column observer-identity" aria-label="Identity" tabIndex={0}>
          <p className="observer-section-index">01 — Identity</p>
          <div className="observer-identity-heading">
            <h2 id="observer-profile-title">{(portfolio.fullName || portfolio.name).split(/\s+/).map((part,index)=><span key={`${part}-${index}`}>{part}</span>)}</h2>
            <div className="observer-roles">{portfolio.fullName && <p className="observer-role">English name · {portfolio.name}</p>}<p className="observer-role">{profile.role}</p></div>
            <p className="observer-status"><span className="observer-status-dot" aria-hidden="true"/>{profile.status}</p>
          </div>
          <div className="observer-bios"><p className="observer-bio">{portfolio.about.description}</p>{profile.approach && <p className="observer-bio">{profile.approach}</p>}</div>
          <dl className="observer-identity-facts">
            <div><dt>Based</dt><dd>{profile.location || '—'}</dd></div>
            <div><dt>Focus</dt><dd>{profile.focus}</dd></div>
            {portfolio.skills.learning.length>0 && <div><dt>Learning</dt><dd>{portfolio.skills.learning.join(', ')}</dd></div>}
            {profile.strengths?.length>0 && <div><dt>Strengths</dt><dd>{profile.strengths.join(', ')}</dd></div>}
            <div><dt>Stack</dt><dd className="observer-stack">{stack.map(tag=><span key={tag}>{tag}</span>)}</dd></div>
          </dl>
          <section className="observer-contacts" aria-label="Contact"><h3>Contact</h3>
            {portfolio.contact.links.filter(link=>link.id==='email'||link.id==='phone').map(link=><div className="observer-contact" key={link.id}><a href={link.href}><span>{link.id}</span><strong>{link.label}</strong></a><button type="button" aria-label={`Copy ${link.id}`} onClick={()=>{void copyContact(link.id,link.label)}}>{copied===link.id?'Copied':'Copy'}</button></div>)}
            <ul className="observer-profile-links">{portfolio.contact.links.filter(link=>link.id!=='email'&&link.id!=='phone').map(link=><li key={link.id}><a href={link.href} target="_blank" rel="noopener noreferrer">{link.label} ↗</a></li>)}</ul>
            <p className="observer-copy-status" role="status">{copyMessage}</p>
          </section>
          {profile.interests?.length>0 && <section className="observer-interests" aria-label="Interests"><h3>Interests</h3><ul>{profile.interests.map(interest=><li key={interest}>{interest}</li>)}</ul></section>}
        </section>
        <section ref={node=>{panels.current[1]=node}} className="observer-column observer-portrait-column" aria-label="Portrait" tabIndex={0}>
          <p className="observer-section-index">02 — Portrait</p>
          <figure className="observer-portrait"><div className="observer-portrait-frame">
            {[0,1,2,3].map(corner=><span key={corner} className={`observer-corner observer-corner-${corner}`} aria-hidden="true"/>)}
            <div className="observer-portrait-window">{portraitSrc?<PixelPortrait src={portraitSrc} originalSrc={originalPortraitSrc} alt={portrait?.alt || `Portrait of ${portfolio.name}`} reducedMotion={reducedMotion} active/>:<span className="observer-portrait-placeholder">[ Portrait ]</span>}</div>
          </div><figcaption><span>Fig. 01</span><span>{portrait?.caption || 'Pixel portrait'}</span></figcaption></figure>
          <p className="observer-portrait-hint">Move your cursor across the portrait to reveal its original colors. Keyboard focus reveals the full photograph.</p>
        </section>
        <section ref={node=>{panels.current[2]=node}} className="observer-column observer-record" aria-label="Experience and education" tabIndex={0}>
          <p className="observer-section-index">03 — Record</p>
          <RecordSection title="Experience" items={experience} narrow={narrow}/>
          <RecordSection title="Education" items={education} narrow={narrow}/>
        </section>
      </div>
      <footer className="observer-sheet-footer"><span>Identity / Portrait / Record</span><button type="button" onClick={onClose}>Return to office <span aria-hidden="true">↗</span></button><span>Esc to close</span></footer>
    </div>
  </dialog>,document.body)
}
