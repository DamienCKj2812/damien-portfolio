import { createContext, useContext } from 'react'

export const SoundEffectsContext = createContext({ click: () => {}, environmentClick: () => {}, portalCrossing: () => {}, doorSound: () => {}, cancelDoorSounds: () => {}, enabled: false, volume: .45, consent: null, chooseSound: () => {}, preferencesOpen: false, openPreferences: () => {}, closePreferences: () => {}, toggle: () => {}, error: false })

export default function useSoundEffects() {
  return useContext(SoundEffectsContext)
}
