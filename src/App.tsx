import { Component, lazy, Suspense, useCallback, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { portfolio } from './data/portfolio'
import BackgroundMusic from './components/BackgroundMusic'
import SoundEffectsProvider from './audio/SoundEffectsProvider'
import LoadingScreen from './components/LoadingScreen'
import { initialStartupState, startupReady } from './components/startupLoading'
import type { ReportStartup } from './components/startupLoading'

const CityWalkthrough = lazy(() => import('./components/CityWalkthrough'))

class StartupBoundary extends Component<{children: ReactNode; onError: (message: string) => void}, {failed: boolean}> {
  state = {failed:false}
  static getDerivedStateFromError() { return {failed:true} }
  componentDidCatch(error: Error) { this.props.onError(error.message) }
  render() { return this.state.failed?null:this.props.children }
}

export default function App() {
  const [startup, setStartup] = useState(initialStartupState)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)
  const [journeyReady, setJourneyReady] = useState(false)
  const prepared = !error && startupReady(startup)
  const ready = prepared && journeyReady
  useEffect(()=>{
    if(!prepared) return
    const timer=window.setTimeout(()=>setJourneyReady(true),1000)
    return ()=>window.clearTimeout(timer)
  },[prepared,attempt])
  const report = useCallback<ReportStartup>((stage,status)=>setStartup(current=>current[stage]===status?current:{...current,[stage]:status}),[])
  const reportError = useCallback((message: string)=>{setJourneyReady(false);setError(message)},[])
  const reportEffects = useCallback((available: boolean)=>report('effects',available?'ready':'unavailable'),[report])
  const reportMusic = useCallback((available: boolean)=>report('music',available?'ready':'unavailable'),[report])
  const retry = () => {
    if(startup.runtime!=='ready') {window.location.reload();return}
    setError('')
    setJourneyReady(false)
    setStartup(current=>({...initialStartupState(),music:current.music,effects:current.effects}))
    setAttempt(value=>value+1)
  }
  return (
    <SoundEffectsProvider onPrepared={reportEffects} startupReady={ready}><main id="home" className="experience" data-startup-ready={ready}>
      <div className="portfolio-scene" inert={!ready}>
        <StartupBoundary key={attempt} onError={reportError}><Suspense fallback={null}>
          <CityWalkthrough startupReady={ready} onStartup={report} onStartupError={reportError}/>
        </Suspense></StartupBoundary>
      </div>
      {!ready && <LoadingScreen state={startup} error={error} starting={prepared} onRetry={retry}/>}
      <BackgroundMusic track={portfolio.music} startupReady={ready} onPrepared={reportMusic}/>
    </main></SoundEffectsProvider>
  )
}
