// Detection does not request permission. Unknown browsers use play()'s promise
// as the definitive result, and a blocked attempt falls back to a real gesture.
export type MusicAutoplayPolicy = 'allowed' | 'allowed-muted' | 'disallowed' | 'unknown'
export interface AutoplayPolicyBrowser<Media = HTMLMediaElement> {
  getAutoplayPolicy?: (audio: Media) => string
}

export function musicAutoplayPolicy(audio: HTMLMediaElement): MusicAutoplayPolicy
export function musicAutoplayPolicy<Media>(audio: Media, browser: AutoplayPolicyBrowser<Media>): MusicAutoplayPolicy
export function musicAutoplayPolicy<Media>(audio: Media, browser?: AutoplayPolicyBrowser<Media>): MusicAutoplayPolicy {
  if (!browser) {
    if (!(audio instanceof HTMLMediaElement)) return 'unknown'
    return musicAutoplayPolicy(audio, navigator)
  }
  if (typeof browser.getAutoplayPolicy !== 'function') return 'unknown'
  try {
    const policy = browser.getAutoplayPolicy(audio)
    return policy === 'allowed' || policy === 'allowed-muted' || policy === 'disallowed' ? policy : 'unknown'
  } catch { return 'unknown' }
}
