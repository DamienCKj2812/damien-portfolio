import type { MouseEvent as ReactMouseEvent } from 'react'

export type AudioConsent = 'enabled' | 'muted' | null

export interface AudioSettings {
  enabled: boolean
  volume: number
}

export interface BackgroundMusicTrack {
  src: string
  volume: number
  source: string
  title: string
  artist: string
}

export interface SoundEffectsValue extends AudioSettings {
  consent: AudioConsent
  chooseSound(enabled: boolean): void
  preferencesOpen: boolean
  openPreferences(): void
  closePreferences(): void
  click(): void
  environmentClick(): void
  portalCrossing(id: string): void
  doorSound(id: string, delay?: number): void
  cancelDoorSounds(): void
  toggle(event?: MouseEvent | ReactMouseEvent<HTMLButtonElement>): void
  error: boolean
}

export type EffectKind = 'system' | 'environment' | 'portal' | 'door'
export type EffectUrls = Partial<Record<EffectKind, string | undefined>>

// Only the operations used by the engine are required. Buffer, destination,
// gain and timer identities are inferred from the injected environment, so
// test doubles do not need to implement browser AudioContext/AudioNode APIs.
export interface InteractionAudioGain<Destination> {
  gain: { value: number }
  connect(destination: Destination): unknown
  disconnect(): void
}

export interface InteractionAudioSource<Buffer, Gain> {
  buffer?: Buffer | null
  onended?: ((event: Event) => void) | null
  connect(gain: Gain): unknown
  disconnect(): void
  start(): void
  stop(): void
}

export interface InteractionAudioContext<Buffer, Destination, Gain extends InteractionAudioGain<Destination>> {
  readonly state: string
  readonly destination: Destination
  resume(): Promise<void>
  suspend(): Promise<void>
  close(): Promise<void>
  decodeAudioData(data: ArrayBuffer): Promise<Buffer>
  // Infer the gain identity from createGain(), rather than widening it from
  // native AudioNode.connect() overloads on the source.
  createBufferSource(): InteractionAudioSource<Buffer, NoInfer<Gain>>
  createGain(): Gain
}

export interface InteractionAudioOptions {
  urls: EffectUrls
  fetchAudio?: (url: string, options: { signal: AbortSignal }) => Promise<{
    ok: boolean
    arrayBuffer(): Promise<ArrayBuffer>
  }>
  now?: () => number
  isHidden?: () => boolean
  onError?: () => void
}

export type InteractionAudioTimers<Timer = ReturnType<typeof setTimeout>> = {
  setTimer: (callback: () => void, delay: number) => Timer
  clearTimer: (timer: Timer) => unknown
} | {
  setTimer?: undefined
  clearTimer?: undefined
}

export type InteractionAudioEnvironment<Buffer = AudioBuffer, Destination = AudioNode, Gain extends InteractionAudioGain<Destination> = InteractionAudioGain<Destination>, Timer = ReturnType<typeof setTimeout>> = InteractionAudioOptions & InteractionAudioTimers<Timer> & (
  { createContext: () => InteractionAudioContext<Buffer, Destination, Gain> } | { createContext?: undefined }
)

export interface InteractionAudioEngine {
  preload(): void
  unlock(): Promise<boolean>
  click(): void
  environmentClick(): void
  portalCrossing(id?: string): void
  doorSound(id: string, delay?: number): void
  cancelDoorSounds(): void
  setEnabled(enabled: boolean): void
  setVolume(volume: number): void
  suspend(): void
  dispose(): void
}

export interface DoorSoundEvent {
  id: 'main-gate-open' | 'lobby-elevator-open' | 'elevator-open' | 'elevator-return-close'
  delay: number
}

export interface DoorSoundJourneyConfig {
  lobbyHoldFrame?: number
  bookmarks: { doors: number }
  elevatorRevealFrame?: number
  cityEnd: number
  lobbyGlobalEnd: number
}

export interface PortalAudioNavigation {
  categories?: readonly { id: string; door?: { y: number } | null }[]
}

export interface PortalCrossing {
  id: string
  y: number
  direction: 'enter' | 'exit'
}
