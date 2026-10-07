import { MathUtils } from 'three'

export function isAutonomousCityActor(actor) {
  return Boolean(actor.autonomous || actor.walk || actor.style === 'outlined_vehicle' && !/maglev train/i.test(actor.name))
}

// Cars/walkers shuttle with eased turns. One-way trains reset only while hidden
// at authored offscreen endpoints; the foreground train remains scroll-driven.
export function sampleCityActorMotion(actor, elapsedFrames, manifest, result = {}) {
  const start = actor.motion?.startFrame ?? actor.walk?.startFrame ?? manifest.frameStart
  const end = actor.motion?.endFrame ?? actor.walk?.endFrame ?? manifest.frameEnd
  const duration = Math.max(1, end - start)
  result.visible = true
  if (actor.motion?.mode === 'one-way') {
    const passFrames = Math.max(1, actor.motion.passFrames ?? duration)
    const resetFrames = Math.max(1, actor.motion.resetFrames ?? 60)
    const phase = MathUtils.euclideanModulo(elapsedFrames + (actor.motion.phase ?? 0), passFrames + resetFrames)
    const progress = Math.min(1, phase / passFrames)
    result.frame = start + progress * duration
    result.turn = 0
    result.progress = progress
    result.travel = progress
    result.visible = phase < passFrames
    return result
  }
  const turnFrames = actor.motion?.turnFrames ?? (actor.walk ? 24 : 30)
  const cycle = 2 * (duration + turnFrames)
  const offset = actor.motion?.phase ?? (actor.walk ? actor.walk.startFrame : actor.index * 17)
  const phase = MathUtils.euclideanModulo(elapsedFrames + offset, cycle)
  let progress, heading, travel
  if (phase < duration) {
    progress = MathUtils.smoothstep(phase / duration, 0, 1)
    heading = 0;travel = progress
  } else if (phase < duration + turnFrames) {
    progress = 1
    heading = Math.PI * MathUtils.smootherstep((phase - duration) / turnFrames, 0, 1)
    travel = 1
  } else if (phase < 2 * duration + turnFrames) {
    const back = MathUtils.smoothstep((phase - duration - turnFrames) / duration, 0, 1)
    progress = 1 - back
    heading = Math.PI;travel = 1 + back
  } else {
    progress = 0
    heading = Math.PI + Math.PI * MathUtils.smootherstep((phase - 2 * duration - turnFrames) / turnFrames, 0, 1)
    travel = 2
  }
  result.frame = start + progress * duration
  result.turn = heading
  result.progress = progress
  result.travel = travel
  return result
}
