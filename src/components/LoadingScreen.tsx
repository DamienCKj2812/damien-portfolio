import type { CSSProperties } from 'react'
import { portfolio } from '../data/portfolio'
import { STARTUP_STAGES, startupProgress } from './startupLoading'
import type { StartupState } from './startupLoading'
import './loadingScreen.css'

const BUILDINGS = [
  [1,9,36],[8,7,56],[16,10,44],[25,6,70],[32,9,50],
  [58,7,62],[66,10,40],[75,6,76],[82,9,48],[90,9,32],
] as const
const STARS = Array.from({length:48},(_,i)=>({left:`${(i*37.13+11)%100}%`,top:`${(i*19.71+7)%48}%`,opacity:.2+(i%5)*.12}))

export default function LoadingScreen({ state, error, onRetry }: { state: StartupState; error: string; onRetry: () => void }) {
  const progress = startupProgress(state)
  const active = STARTUP_STAGES.find(stage=>stage.weight>0 && state[stage.id]==='loading')
  const done = STARTUP_STAGES.filter(stage=>stage.weight>0 && ['ready','unavailable'].includes(state[stage.id])).length
  const total = STARTUP_STAGES.filter(stage=>stage.weight>0).length
  return <section className="startup-loader" aria-label="Preparing portfolio" data-progress={progress} data-error={Boolean(error)} style={{'--startup-progress':`${progress}%`} as CSSProperties}>
    <div className="startup-grid" aria-hidden="true"/>
    <div className="startup-stars" aria-hidden="true">{STARS.map((star,i)=><span key={i} style={star}/>)}</div>
    <div className="startup-moon" aria-hidden="true"/>
    {[0,1,2,3].map(corner=><span key={corner} className={`startup-corner startup-corner-${corner}`} aria-hidden="true"/>)}
    <header><span><strong>{portfolio.siteTitle}</strong> / KAJU Atrium</span><span>{error?'Connection interrupted':`Stage ${Math.min(done+1,total)} / ${total}`}</span></header>
    <div className="startup-body">
      <div className="startup-skyline" aria-hidden="true">
        {BUILDINGS.map(([left,width,height],i)=><div key={i} className="startup-building" data-antenna={i%3===1} style={{left:`${left}%`,width:`${width}%`,height:`${height}%`,opacity:progress>=i*8?1:.25}}/>)}
        <div className="startup-tower"><span className="startup-tower-fill"/><span className="startup-scan"/></div>
        <span className="startup-crown"/><span className="startup-spire"/><span className="startup-beacon"/>
        <div className="startup-hologram">KAJU<span><i/></span></div>
        <span className="startup-horizon"/>
      </div>
      <div className="startup-summary">
        <div className="startup-percentage" aria-hidden="true">{String(progress).padStart(2,'0')}<span>%</span></div>
        <div className="sr-only" role="progressbar" aria-label="Portfolio preparation" aria-valuemin={0} aria-valuemax={100} aria-valuenow={progress}/>
        <p role={error?'alert':'status'}>{error || active?.label || 'Preparing the next chapter'}</p>
        {error && <button type="button" onClick={onRetry}>Retry loading ↻</button>}
      </div>
      <ol className="startup-log" aria-label="Preloaded portfolio assets" tabIndex={0}>{STARTUP_STAGES.map(stage=><li key={stage.id} data-stage={stage.id} data-state={state[stage.id]}><span>{stage.id==='music'?`Audio · ${portfolio.music.title}`:stage.label}</span><span>{({waiting:'—',loading:'Loading',ready:'OK',unavailable:'Unavailable'})[state[stage.id]]}</span></li>)}</ol>
    </div>
  </section>
}
