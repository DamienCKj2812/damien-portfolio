const owners = new Set()
const listeners = new Set()

export const hasVideoAudioFocus = () => owners.size > 0

export function setVideoAudioFocus(owner, active) {
  const before = owners.size > 0
  if (active) owners.add(owner)
  else owners.delete(owner)
  if (before !== (owners.size > 0)) for (const listener of listeners) listener(owners.size > 0)
}

export function subscribeVideoAudioFocus(listener) {
  listeners.add(listener)
  return () => listeners.delete(listener)
}
