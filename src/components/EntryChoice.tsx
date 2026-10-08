import { useEffect, useState } from 'react'
import { portfolio } from '../data/portfolio'
import { rememberedMode } from '../data/portfolioMode'
import { cvDownload } from '../data/cv'
import './portfolioFlat.css'

export function Starfield() {
  return <div className="flat-sky" aria-hidden="true">
    {Array.from({ length: 60 }, (_, i) => {
      const random = (n: number) => { const v = Math.sin(i * 12.9898 + n * 78.233) * 43758.5453; return v - Math.floor(v) }
      return <span key={i} style={{ left: `${random(1) * 100}%`, top: `${random(2) * 70}%`, width: random(3) > .9 ? 2.5 : 1.5, height: random(3) > .9 ? 2.5 : 1.5, opacity: .15 + random(4) * .5 }} />
    })}
    <div className="flat-orbit"/><div className="flat-moon"/>
  </div>
}

export default function EntryChoice({ onChoose }: { onChoose: (mode: '2d' | '3d', remember: boolean) => void }) {
  const [remember, setRemember] = useState(() => rememberedMode() !== null)
  const [lowPower, setLowPower] = useState(false)
  useEffect(() => {
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)')
    const small = window.matchMedia('(pointer: coarse) and (max-width: 699px)')
    const update = () => setLowPower(reduce.matches || small.matches)
    update()
    reduce.addEventListener('change', update); small.addEventListener('change', update)
    return () => { reduce.removeEventListener('change', update); small.removeEventListener('change', update) }
  }, [])
  return <div className="entry-mode flat-mode">
    <Starfield/>
    <header className="entry-brand flat-mono"><span className="flat-diamond"/>{portfolio.siteTitle}</header>
    <main className="entry-main">
      <div className="entry-intro"><h1>How would you like to explore?</h1><p>Same projects, experience and contact details in both. You can switch at any time.</p></div>
      <div className="entry-options">
        {(['3d', '2d'] as const).map(mode => {
          const is3d = mode === '3d', primary = lowPower ? !is3d : is3d
          return <a key={mode} href={`${import.meta.env.BASE_URL}?mode=${mode}`} className={`entry-option${primary ? ' entry-primary' : ''}`} onClick={event => {
            if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return
            event.preventDefault(); onChoose(mode, remember)
          }}>
            <div className="entry-option-top"><span className="entry-code flat-mono">
              <svg width="44" height="44" viewBox="0 0 44 44" fill="none" stroke="currentColor" strokeWidth="1.2" aria-hidden="true">{is3d ? <><path d="M22 4 38 13 38 31 22 40 6 31 6 13Z"/><path d="M6 13 22 22 38 13M22 22V40"/><path d="M22 4V22" strokeDasharray="2 3" opacity=".5"/></> : <><rect x="7" y="7" width="30" height="30"/><path d="M7 17H37M17 17V37"/></>}</svg>{is3d ? '3D' : '2D'}</span>
              <span className="flat-badge">{is3d ? lowPower ? 'Heavier on this device' : 'Immersive' : lowPower ? 'Recommended' : 'Fastest'}</span></div>
            <div><h2>{is3d ? 'Explore the Atrium' : 'Read the portfolio'}</h2><p>{is3d ? 'An interactive 3D world you explore to find my work.' : 'A simple page with all my info in one scroll.'}</p></div>
            <dl><div><dt>Best for</dt><dd>{is3d ? 'A memorable, hands-on look' : 'Recruiters and quick reviews'}</dd></div><div><dt>Best in</dt><dd>{is3d ? 'Desktop or a recent phone, with optional sound' : 'Any device, any connection'}</dd></div></dl>
            <span className={`flat-action${primary ? ' flat-action-primary' : ''}`}>{is3d ? 'Enter 3D' : 'Open 2D'}<span aria-hidden="true">→</span></span>
          </a>
        })}
      </div>
      <label className="entry-remember"><input type="checkbox" checked={remember} onChange={event => setRemember(event.target.checked)}/>Remember my choice on this device</label>
      <a className="entry-cv flat-mono" href={cvDownload.primary.href} download={cvDownload.primary.file}>Download CV ({cvDownload.primary.format}) <span aria-hidden="true">↓</span></a>
    </main>
  </div>
}
