interface Window {
  webkitAudioContext?: typeof AudioContext
}

interface Navigator {
  getAutoplayPolicy?: (audio: HTMLMediaElement) => string
}
