import { createContext, useContext } from 'react'
import type { SoundEffectsValue } from '../types/audio'

export const SoundEffectsContext = createContext<SoundEffectsValue>({ click: () => {}, environmentClick: () => {}, portalCrossing: () => {}, doorSound: () => {}, cancelDoorSounds: () => {}, enabled: false, volume: .45, consent: null, chooseSound: () => {}, preferencesOpen: false, openPreferences: () => {}, closePreferences: () => {}, toggle: () => {}, error: false })

export default function useSoundEffects() {
  return useContext(SoundEffectsContext)
}
