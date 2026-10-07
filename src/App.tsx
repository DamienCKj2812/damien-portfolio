import { lazy, Suspense } from 'react'
import { portfolio } from './data/portfolio'
import BackgroundMusic from './components/BackgroundMusic'
import SoundEffectsProvider from './audio/SoundEffectsProvider'

const CityWalkthrough = lazy(() => import('./components/CityWalkthrough'))

export default function App() {
  return (
    <SoundEffectsProvider><main id="home" className="experience">
      <Suspense fallback={<div className="city-shell"><p className="city-loading-shell" role="status">Loading the interactive city…</p></div>}>
        <CityWalkthrough title={portfolio.siteTitle} />
      </Suspense>
      <BackgroundMusic track={portfolio.music} />
    </main></SoundEffectsProvider>
  )
}
