// Detection does not request permission. Unknown browsers use play()'s promise
// as the definitive result, and a blocked attempt falls back to a real gesture.
export function musicAutoplayPolicy(audio, browser = navigator) {
  if (typeof browser.getAutoplayPolicy !== 'function') return 'unknown'
  try {
    const policy = browser.getAutoplayPolicy(audio)
    return ['allowed', 'allowed-muted', 'disallowed'].includes(policy) ? policy : 'unknown'
  } catch { return 'unknown' }
}
