import { MathUtils, Quaternion, Vector3 } from 'three'
import { interpolateCameraSample } from './cameraMotion.js'

const destinationQuaternion = new Quaternion()

export function readPose(assets, frame, channel, position, quaternion, scale) {
  const { manifest, animation } = assets
  const frameCount = manifest.frameEnd - manifest.frameStart + 1
  const relative = manifest.loop ? MathUtils.euclideanModulo(frame - manifest.frameStart, frameCount) : MathUtils.clamp(frame - manifest.frameStart, 0, frameCount - 1)
  const first = Math.floor(relative)
  const second = manifest.loop ? (first + 1) % frameCount : Math.min(first + 1, frameCount - 1)
  const blend = relative - first
  const stride = manifest.channelStride
  const a = (first * manifest.channelCount + channel) * stride
  const b = (second * manifest.channelCount + channel) * stride
  position.set(
    MathUtils.lerp(animation[a], animation[b], blend),
    MathUtils.lerp(animation[a + 1], animation[b + 1], blend),
    MathUtils.lerp(animation[a + 2], animation[b + 2], blend),
  )
  quaternion.fromArray(animation, a + 3).normalize().slerp(destinationQuaternion.fromArray(animation, b + 3).normalize(), blend)
  if (scale) scale.set(MathUtils.lerp(animation[a + 7], animation[b + 7], blend), MathUtils.lerp(animation[a + 8], animation[b + 8], blend), MathUtils.lerp(animation[a + 9], animation[b + 9], blend))
  const fovOffset = manifest.camera.fovOffset
  const fov = fovOffset == null ? manifest.camera.verticalFov : MathUtils.lerp(animation[a + fovOffset], animation[b + fovOffset], blend)
  return { fov, visible: stride < 12 || animation[a + 11] > 0.5 }
}

export function createPoseScratch() {
  return { position: new Vector3(), quaternion: new Quaternion(), scale: new Vector3(), bridgePosition: new Vector3(), bridgeQuaternion: new Quaternion() }
}

export function readCameraPose(assets, frame, position, quaternion) {
  const result = readPose(assets, frame, 0, position, quaternion)
  const { manifest, animation } = assets
  const count = manifest.frameEnd - manifest.frameStart + 1
  const relative = manifest.loop ? MathUtils.euclideanModulo(frame - manifest.frameStart, count) : MathUtils.clamp(frame - manifest.frameStart, 0, count - 1)
  const first = Math.floor(relative), blend = relative - first
  const index = frameIndex => (manifest.loop ? MathUtils.euclideanModulo(frameIndex, count) : MathUtils.clamp(frameIndex, 0, count - 1)) * manifest.channelCount * manifest.channelStride
  const a = index(first - 1), b = index(first), c = index(first + 1), d = index(first + 2)
  const sample = offset => interpolateCameraSample(animation[a + offset], animation[b + offset], animation[c + offset], animation[d + offset], blend)
  position.set(sample(0), sample(1), sample(2))
  // Adjacent quaternions must share a hemisphere before cubic interpolation.
  const sign = offset => animation[offset + 3] * animation[b + 3] + animation[offset + 4] * animation[b + 4] + animation[offset + 5] * animation[b + 5] + animation[offset + 6] * animation[b + 6] < 0 ? -1 : 1
  const signA = sign(a), signC = sign(c), signD = sign(d)
  const rotation = axis => interpolateCameraSample(animation[a + 3 + axis] * signA, animation[b + 3 + axis], animation[c + 3 + axis] * signC, animation[d + 3 + axis] * signD, blend)
  quaternion.set(rotation(0), rotation(1), rotation(2), rotation(3)).normalize()
  if (manifest.camera.fovOffset != null) result.fov = sample(manifest.camera.fovOffset)
  return result
}
