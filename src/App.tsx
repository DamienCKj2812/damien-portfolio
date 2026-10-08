import { Component, lazy, Suspense, useCallback, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { portfolio } from './data/portfolio'
import BackgroundMusic from './components/BackgroundMusic'
import SoundEffectsProvider from './audio/SoundEffectsProvider'
import LoadingScreen from './components/LoadingScreen'
import { initialStartupState, startupReady } from './components/startupLoading'
import type { ReportStartup } from './components/startupLoading'
import EntryChoice from './components/EntryChoice'
import { initialMode, rememberedMode, saveMode } from './data/portfolioMode'
import type { PortfolioMode } from './data/portfolioMode'

const CityWalkthrough = lazy(() => import('./components/CityWalkthrough'))
const Portfolio2D = lazy(() => import('./components/Portfolio2D'))

class StartupBoundary extends Component<{children: ReactNode; onError: (message: string) => void}, {failed: boolean}> {
  state = {failed:false}
  static getDerivedStateFromError() { return {failed:true} }
  componentDidCatch(error: Error) { this.props.onError(error.message) }
  render() { return this.state.failed?null:this.props.children }
}

export default function App() {
  const [mode, setMode] = useState(initialMode)
  useEffect(() => {
    const restore = () => setMode(initialMode())
    window.addEventListener('popstate', restore)
    return () => window.removeEventListener('popstate', restore)
  }, [])
  const choose = (next: PortfolioMode, remember = rememberedMode() !== null) => {
    if (next !== 'entry') saveMode(next, remember)
    const url = new URL(window.location.href)
    url.searchParams.set('mode', next); url.hash = ''
    window.history.pushState(null, '', url)
    setMode(next)
  }
  if (mode === 'entry') return <EntryChoice onChoose={choose}/>
  if (mode === '2d') return <FlatBoundary onBack={() => choose('entry')}><Suspense fallback={<div className="flat-mode mode-loading" role="status">Opening the portfolio…</div>}><Portfolio2D onEnter3D={() => choose('3d')} onEntry={() => choose('entry')}/></Suspense></FlatBoundary>
  return <Portfolio3D onEnter2D={() => choose('2d')} onEntry={() => choose('entry')}/>
}

class FlatBoundary extends Component<{ children: ReactNode; onBack: () => void }, { failed: boolean }> {
  state = { failed: false }
  static getDerivedStateFromError() { return { failed: true } }
  render() {
    return this.state.failed ? <div className="flat-mode mode-loading" role="alert"><p>The portfolio could not load.</p><button className="flat-action" onClick={() => window.location.reload()}>Retry</button><button className="flat-action" onClick={this.props.onBack}>Choose experience</button></div> : this.props.children
  }
}

function Portfolio3D({ onEnter2D, onEntry }: { onEnter2D: () => void; onEntry: () => void }) {
  const [startup, setStartup] = useState(initialStartupState)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)
  const ready = !error && startupReady(startup)
  const report = useCallback<ReportStartup>((stage,status)=>setStartup(current=>current[stage]===status?current:{...current,[stage]:status}),[])
  const reportError = useCallback((message: string)=>setError(message),[])
  const reportEffects = useCallback((available: boolean)=>report('effects',available?'ready':'unavailable'),[report])
  const reportMusic = useCallback((available: boolean)=>report('music',available?'ready':'unavailable'),[report])
  const retry = () => {
    if(startup.runtime!=='ready') {window.location.reload();return}
    setError('')
    setStartup(current=>({...initialStartupState(),music:current.music,effects:current.effects}))
    setAttempt(value=>value+1)
  }
  return (
    <SoundEffectsProvider onPrepared={reportEffects} startupReady={ready}><main id="home" className="experience" data-startup-ready={ready}>
      <div className="portfolio-scene" inert={!ready}>
        <StartupBoundary key={attempt} onError={reportError}><Suspense fallback={null}>
          <CityWalkthrough startupReady={ready} onStartup={report} onStartupError={reportError} onEnter2D={onEnter2D}/>
        </Suspense></StartupBoundary>
      </div>
      {!ready && <LoadingScreen state={startup} error={error} onRetry={retry}/>}
      {!ready && <button className="startup-mode-back" onClick={onEntry}>← Choose experience</button>}
      <BackgroundMusic track={portfolio.music} startupReady={ready} onPrepared={reportMusic}/>
    </main></SoundEffectsProvider>
  )
}
