export type VideoAudioFocusOwner = object
export type VideoAudioFocusListener = (active: boolean) => void

const owners = new Set<VideoAudioFocusOwner>()
const listeners = new Set<VideoAudioFocusListener>()

export const hasVideoAudioFocus = () => owners.size > 0

export function setVideoAudioFocus(owner: VideoAudioFocusOwner, active: boolean) {
  const before = owners.size > 0
  if (active) owners.add(owner)
  else owners.delete(owner)
  if (before !== (owners.size > 0)) for (const listener of listeners) listener(owners.size > 0)
}

export function subscribeVideoAudioFocus(listener: VideoAudioFocusListener): () => void {
  listeners.add(listener)
  return () => { listeners.delete(listener) }
}
