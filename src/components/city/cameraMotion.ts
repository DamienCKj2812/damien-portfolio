import type { CameraSpring } from '../../types/navigation'

// Critically damped motion preserves velocity when a scroll target changes.
// The closed-form step stays stable across different rendering frame rates.
export function advanceCameraSpring(state: CameraSpring, target: number, delta: number, frequency = 18) {
  const dt = Math.min(Math.max(delta, 0), .1)
  const offset = state.value - target
  const impulse = state.velocity + frequency * offset
  const decay = Math.exp(-frequency * dt)
  state.value = target + (offset + impulse * dt) * decay
  state.velocity = (state.velocity - frequency * impulse * dt) * decay
  if (Math.abs(state.value - target) < .01 && Math.abs(state.velocity) < .1) {
    state.value = target;state.velocity = 0
  }
  return state.value
}

// Shape-preserving cubic interpolation gives continuous velocity between native
// camera samples, retaining every authored sample and avoiding path overshoot.
export function interpolateCameraSample(previous: number, start: number, end: number, next: number, blend: number) {
  const before = start - previous, middle = end - start, after = next - end
  const startSlope = before * middle <= 0 ? 0 : 2 * before * middle / (before + middle)
  const endSlope = middle * after <= 0 ? 0 : 2 * middle * after / (middle + after)
  return interpolateCameraSegment(start, end, startSlope, endSlope, blend)
}

function interpolateCameraSegment(start: number, end: number, startSlope: number, endSlope: number, blend: number) {
  const squared = blend * blend, cubed = squared * blend
  return (2 * cubed - 3 * squared + 1) * start + (cubed - 2 * squared + blend) * startSlope + (-2 * cubed + 3 * squared) * end + (cubed - squared) * endSlope
}

// The threshold is a shared waypoint, not a separate stop: both walk segments
// have the same velocity there and settle gently at the cabin/room endpoints.
export function interpolateCameraBridge(start: number, threshold: number, end: number, frame: number, firstSpan = 54, secondSpan = 96) {
  const before = (threshold - start) / firstSpan, after = (end - threshold) / secondSpan
  const slope = before * after <= 0 ? 0 : 2 * before * after / (before + after)
  if (frame <= firstSpan) return interpolateCameraSegment(start, threshold, 0, slope * firstSpan, Math.max(0, frame / firstSpan))
  return interpolateCameraSegment(threshold, end, slope * secondSpan, 0, Math.min(1, (frame - firstSpan) / secondSpan))
}
