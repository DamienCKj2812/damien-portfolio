export const STARTUP_STAGES = [
  { id: 'runtime', label: 'Interactive renderer', weight: 5 },
  { id: 'cityManifest', label: 'City scene manifest', weight: 5 },
  { id: 'geometry', label: 'City tower · streets · point geometry', weight: 19 },
  { id: 'animation', label: 'Crowd · vehicles · animation channels', weight: 8 },
  { id: 'textures', label: 'City billboards · decoded textures', weight: 7 },
  { id: 'journey', label: 'Journey routes · floor destinations', weight: 5 },
  { id: 'lobby', label: 'KAJU atrium · NPCs · holographic fish', weight: 10 },
  { id: 'elevator', label: 'Elevator cabin · floor controls', weight: 7 },
  { id: 'about', label: '01 About · skyline office', weight: 6 },
  { id: 'skills', label: '02 Skills · gallery · guided route', weight: 6 },
  { id: 'projects', label: '03 Projects · hallway · catalogue', weight: 7 },
  { id: 'experience', label: '04 Experience · observatory · logos', weight: 6 },
  { id: 'portraits', label: 'Profile · pixel portrait · original color', weight: 3 },
  { id: 'posters', label: 'Project walkthrough · poster images', weight: 3 },
  { id: 'renderer', label: 'First city frame · GPU upload', weight: 3 },
  { id: 'effects', label: 'Click · environment · door audio', weight: 0 },
  { id: 'music', label: 'Audio · Cyberpunk Suspense', weight: 0 },
] as const

export type StartupStage = typeof STARTUP_STAGES[number]['id']
export type StartupStatus = 'waiting' | 'loading' | 'ready' | 'unavailable'
export type StartupState = Record<StartupStage, StartupStatus>
export type ReportStartup = (stage: StartupStage, status: StartupStatus) => void
export const initialStartupState = (): StartupState => Object.fromEntries(STARTUP_STAGES.map(stage=>[stage.id,['runtime','music','effects'].includes(stage.id)?'loading':'waiting'])) as StartupState
export const startupReady = (state: StartupState) => STARTUP_STAGES.every(stage=>stage.weight===0 || state[stage.id]==='ready' || state[stage.id]==='unavailable')
export const startupProgress = (state: StartupState) => STARTUP_STAGES.reduce((sum,stage)=>sum+(state[stage.id]==='ready'||state[stage.id]==='unavailable'?stage.weight:0),0)
