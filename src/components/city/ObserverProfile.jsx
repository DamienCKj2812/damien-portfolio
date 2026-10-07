import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { portfolio } from '../../data/portfolio.js'
import { useReducedMotion } from './useScrollTimeline.js'
import './observerProfile.css'
import PixelPortrait from './PixelPortrait.jsx'
import useSoundEffects from '../../audio/useSoundEffects.js'

function GlitchText({ children, delay = 0 }) {
  return <span className="observer-glitch-text" style={{ '--observer-text-delay': `${delay}ms` }}>
    <span className="observer-glitch-base">{children}</span>
    <span className="observer-glitch-fragment observer-glitch-fragment-top" data-text={children} aria-hidden="true" />
    <span className="observer-glitch-fragment observer-glitch-fragment-bottom" data-text={children} aria-hidden="true" />
    <span className="observer-glitch-text-mask" aria-hidden="true" />
  </span>
}

function RecordSection({ title, items }) {
  return <section className="observer-record-section" aria-label={title}>
    <div className="observer-record-heading"><h3><GlitchText delay={220}>{title}</GlitchText></h3><span><GlitchText delay={250}>{String(items.length).padStart(2, '0')}</GlitchText></span></div>
    {items.length ? items.map((item, index) => <article className="observer-record-row" data-undated={!item.period} key={item.id}>
      {item.period && <p className="observer-period"><GlitchText delay={310 + index * 40}>{item.period}</GlitchText></p>}
      <div><h4><GlitchText delay={330 + index * 40}>{item.organization}</GlitchText></h4><p><GlitchText delay={370 + index * 40}>{item.title}</GlitchText></p>
        {item.category.includes('SAMPLE') && <span className="observer-sample">Sample entry</span>}
        {item.description && <p className="observer-record-description">{item.description}</p>}
        {item.highlights?.length > 0 && <ul className="observer-record-highlights">{item.highlights.map(highlight=><li key={highlight}>{highlight}</li>)}</ul>}
      </div>
    </article>) : <p className="observer-empty-record">Details to be added.</p>}
  </section>
}

export default function ObserverProfile({ onClose }) {
  const { click: playClick } = useSoundEffects()
  const dialogRef = useRef(null)
  const closeRef = useRef(null)
  const reducedMotion = useReducedMotion()
  const [closing, setClosing] = useState(false)
  const requestClose = () => {
    if (closing) return
    if (reducedMotion) onClose()
    else setClosing(true)
  }
  const profile = portfolio.about.profile
  const education = portfolio.journey.items.filter((item) => /education/i.test(item.category))
  const experience = portfolio.journey.items.filter((item) => !/education/i.test(item.category))
  const stack = (profile.stack || [...new Set(portfolio.skills.groups.flatMap((group) => group.items))]).join(', ')
  const portrait = profile.portrait
  const portraitSrc = portrait?.src ? /^https?:\/\//.test(portrait.src) ? portrait.src : `${import.meta.env.BASE_URL}${portrait.src.replace(/^\/+/, '')}` : null
  const originalPortraitSrc = portrait?.originalSrc ? /^https?:\/\//.test(portrait.originalSrc) ? portrait.originalSrc : `${import.meta.env.BASE_URL}${portrait.originalSrc.replace(/^\/+/, '')}` : null

  useEffect(() => {
    const dialog = dialogRef.current
    const previousFocus = document.activeElement
    const body = document.body
    const previousOverflow = body.style.overflow
    const previousPadding = body.style.paddingRight
    const scrollbar = window.innerWidth - document.documentElement.clientWidth
    if (scrollbar > 0) body.style.paddingRight = `${parseFloat(getComputedStyle(body).paddingRight) + scrollbar}px`
    body.style.overflow = 'hidden'
    dialog.showModal()
    closeRef.current.focus({ preventScroll: true })
    return () => {
      if (dialog.open) dialog.close()
      body.style.overflow = previousOverflow
      body.style.paddingRight = previousPadding
      const fallback = document.getElementById('observer-profile-trigger')
      const target = previousFocus instanceof HTMLElement && previousFocus.isConnected && previousFocus.matches('button, a, input, select, textarea, [tabindex]') ? previousFocus : fallback
      target?.focus({ preventScroll: true })
    }
  }, [])

  useEffect(() => {
    if (!closing) return
    const timer = window.setTimeout(onClose, reducedMotion ? 0 : 960)
    return () => window.clearTimeout(timer)
  }, [closing, reducedMotion, onClose])

  return createPortal(<dialog
    ref={dialogRef}
    id="observer-profile-dialog"
    className="observer-profile"
    data-closing={closing}
    aria-labelledby="observer-profile-title"
    onKeyDown={(event) => {
      if (event.key !== 'Tab') return
      const items = [...dialogRef.current.querySelectorAll('button, a[href], input, select, textarea, [tabindex="0"]')].filter((item) => !item.disabled)
      const first = items[0], last = items.at(-1)
      if (event.shiftKey && document.activeElement === first) { event.preventDefault();last.focus() }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault();first.focus() }
    }}
    onCancel={(event) => { event.preventDefault();playClick();requestClose() }}
  >
    <div className="observer-sheet">
      <header className="observer-sheet-header">
        <span>ROOM 01 / ABOUT</span>
        <span className="observer-header-center">{portfolio.name.toUpperCase()} / PERSONAL PORTFOLIO</span>
        <div className="observer-header-actions"><span>REV. {profile.revision}</span><button ref={closeRef} type="button" onClick={requestClose} aria-label="Close about profile">CLOSE <span aria-hidden="true">×</span></button></div>
      </header>

      <div className="observer-columns">
        <div className="observer-signal-blocks" aria-hidden="true">
          {Array.from({ length: 18 }, (_, index) => <span key={index} style={{ '--signal-index': index, '--signal-origin': index % 3 === 0 ? 'top' : 'bottom', '--signal-delay': `${(index * 37) % 190}ms` }} />)}
        </div>
        <section className="observer-column observer-identity" aria-label="Identity" tabIndex={0}>
          <p className="observer-section-index"><GlitchText delay={80}>01 — IDENTITY</GlitchText></p>
          <h2 id="observer-profile-title">{(portfolio.fullName || portfolio.name).split(/\s+/).map((part, index) => <GlitchText key={`${part}-${index}`} delay={130 + index * 70}>{part.toUpperCase()}</GlitchText>)}</h2>
          {portfolio.fullName && <p className="observer-role"><GlitchText delay={190}>{`English name · ${portfolio.name}`}</GlitchText></p>}
          <p className="observer-role"><GlitchText delay={210}>{profile.role}</GlitchText></p>
          <p className="observer-status"><span className="observer-status-dot" aria-hidden="true" /><GlitchText delay={250}>{profile.status}</GlitchText></p>
          <p className="observer-bio"><GlitchText delay={290}>{portfolio.about.description}</GlitchText></p>
          {profile.approach && <p className="observer-bio"><GlitchText delay={310}>{profile.approach}</GlitchText></p>}
          <dl className="observer-identity-facts">
            <div><dt><GlitchText delay={330}>BASED</GlitchText></dt><dd><GlitchText delay={350}>{profile.location || '—'}</GlitchText></dd></div>
            <div><dt><GlitchText delay={370}>STACK</GlitchText></dt><dd><GlitchText delay={390}>{stack}</GlitchText></dd></div>
            <div><dt><GlitchText delay={410}>FOCUS</GlitchText></dt><dd><GlitchText delay={430}>{profile.focus}</GlitchText></dd></div>
            {portfolio.skills.learning?.length > 0 && <div><dt><GlitchText delay={450}>LEARNING</GlitchText></dt><dd><GlitchText delay={470}>{portfolio.skills.learning.join(', ')}</GlitchText></dd></div>}
            {profile.strengths?.length > 0 && <div><dt><GlitchText delay={490}>STRENGTHS</GlitchText></dt><dd><GlitchText delay={510}>{profile.strengths.join(', ')}</GlitchText></dd></div>}
          </dl>
          <section className="observer-record-section" aria-label="Contact"><div className="observer-record-heading"><h3>Contact</h3></div><ul className="observer-profile-links">{portfolio.contact.links.map(link=><li key={link.id}><a href={link.href} target={/^https?:/.test(link.href)?'_blank':undefined} rel={/^https?:/.test(link.href)?'noreferrer':undefined}>{link.label}</a></li>)}</ul></section>
          {profile.interests?.length > 0 && <section className="observer-record-section" aria-label="Interests"><div className="observer-record-heading"><h3>Interests</h3></div><ul className="observer-record-highlights">{profile.interests.map(interest=><li key={interest}>{interest}</li>)}</ul></section>}
        </section>

        <section className="observer-column observer-portrait-column" aria-label="Portrait" tabIndex={0}>
          <p className="observer-section-index"><GlitchText delay={140}>02 — PORTRAIT</GlitchText></p>
          <figure className="observer-portrait">
            <div className="observer-portrait-frame">
              {[0, 1, 2, 3].map((corner) => <span key={corner} className={`observer-corner observer-corner-${corner}`} aria-hidden="true" />)}
              <div className="observer-portrait-window">
                {portraitSrc ? <PixelPortrait src={portraitSrc} originalSrc={originalPortraitSrc} alt={portrait.alt || `Portrait of ${portfolio.name}`} reducedMotion={reducedMotion} active={!closing} /> : <span className="observer-portrait-placeholder">[ PORTRAIT ]</span>}
              </div>
            </div>
            <figcaption><span>FIG. 01</span><span>{portrait?.caption || '4 : 5'}</span></figcaption>
          </figure>
        </section>

        <section className="observer-column observer-record" aria-label="Experience and education" tabIndex={0}>
          <p className="observer-section-index"><GlitchText delay={180}>03 — RECORD</GlitchText></p>
          <RecordSection title="Experience" items={experience} />
          <RecordSection title="Education" items={education} />
        </section>
      </div>
      <footer className="observer-sheet-footer"><span>IDENTITY / PORTRAIT / RECORD</span><button type="button" onClick={requestClose}>RETURN TO OFFICE <span aria-hidden="true">↗</span></button><span>ESC TO CLOSE</span></footer>
    </div>
  </dialog>, document.body)
}
