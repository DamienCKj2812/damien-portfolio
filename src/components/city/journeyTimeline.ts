import { MathUtils, Quaternion, Vector3 } from 'three'
import { interpolateCameraSample } from './cameraMotion'
import type { LoadedSceneAssets, SceneManifestBase } from '../../types/scene'
import type { PoseScratch } from '../../types/navigation'
import { packedNumber } from '../../types/packedNumbers'

export type AnimationAssets = Pick<LoadedSceneAssets, 'animation'> & { manifest: Pick<SceneManifestBase, 'frameStart' | 'frameEnd' | 'loop' | 'channelCount' | 'channelStride' | 'camera'> }

const destinationQuaternion = new Quaternion()

export function readPose(assets: AnimationAssets, frame: number, channel: number, position: Vector3, quaternion: Quaternion, scale?: Vector3) {
  const { manifest, animation } = assets
  const frameCount = manifest.frameEnd - manifest.frameStart + 1
  const relative = manifest.loop ? MathUtils.euclideanModulo(frame - manifest.frameStart, frameCount) : MathUtils.clamp(frame - manifest.frameStart, 0, frameCount - 1)
  const first = Math.floor(relative)
  const second = manifest.loop ? (first + 1) % frameCount : Math.min(first + 1, frameCount - 1)
  const blend = relative - first
  const stride = manifest.channelStride
  const a = (first * manifest.channelCount + channel) * stride
  const b = (second * manifest.channelCount + channel) * stride
  // Loading validates the frame/channel dimensions and buffer length. The
  // clamped/wrapped frame indices and caller's camera/actor channel stay in that
  // range; pose slots 0–9, optional FOV and visibility are within the stride.
  position.set(
    MathUtils.lerp(packedNumber(animation, a), packedNumber(animation, b), blend),
    MathUtils.lerp(packedNumber(animation, a + 1), packedNumber(animation, b + 1), blend),
    MathUtils.lerp(packedNumber(animation, a + 2), packedNumber(animation, b + 2), blend),
  )
  quaternion.fromArray(animation, a + 3).normalize().slerp(destinationQuaternion.fromArray(animation, b + 3).normalize(), blend)
  if (scale) scale.set(MathUtils.lerp(packedNumber(animation, a + 7), packedNumber(animation, b + 7), blend), MathUtils.lerp(packedNumber(animation, a + 8), packedNumber(animation, b + 8), blend), MathUtils.lerp(packedNumber(animation, a + 9), packedNumber(animation, b + 9), blend))
  const fovOffset = manifest.camera.fovOffset
  const fov = fovOffset == null ? manifest.camera.verticalFov : MathUtils.lerp(packedNumber(animation, a + fovOffset), packedNumber(animation, b + fovOffset), blend)
  return { fov, visible: stride < 12 || packedNumber(animation, a + 11) > 0.5 }
}

export function createPoseScratch(): PoseScratch {
  return { position: new Vector3(), quaternion: new Quaternion(), scale: new Vector3(), bridgePosition: new Vector3(), bridgeQuaternion: new Quaternion() }
}

export function readCameraPose(assets: AnimationAssets, frame: number, position: Vector3, quaternion: Quaternion) {
  const result = readPose(assets, frame, 0, position, quaternion)
  const { manifest, animation } = assets
  const count = manifest.frameEnd - manifest.frameStart + 1
  const relative = manifest.loop ? MathUtils.euclideanModulo(frame - manifest.frameStart, count) : MathUtils.clamp(frame - manifest.frameStart, 0, count - 1)
  const first = Math.floor(relative), blend = relative - first
  const index = (frameIndex: number) => (manifest.loop ? MathUtils.euclideanModulo(frameIndex, count) : MathUtils.clamp(frameIndex, 0, count - 1)) * manifest.channelCount * manifest.channelStride
  const a = index(first - 1), b = index(first), c = index(first + 1), d = index(first + 2)
  // index wraps/clamps every neighbouring frame in the validated camera channel
  // (channel 0); sampled XYZ/XYZW/FOV offsets are validated within its stride.
  const sample = (offset: number) => interpolateCameraSample(packedNumber(animation, a + offset), packedNumber(animation, b + offset), packedNumber(animation, c + offset), packedNumber(animation, d + offset), blend)
  position.set(sample(0), sample(1), sample(2))
  // Adjacent quaternions must share a hemisphere before cubic interpolation.
  const sign = (offset: number) => packedNumber(animation, offset + 3) * packedNumber(animation, b + 3) + packedNumber(animation, offset + 4) * packedNumber(animation, b + 4) + packedNumber(animation, offset + 5) * packedNumber(animation, b + 5) + packedNumber(animation, offset + 6) * packedNumber(animation, b + 6) < 0 ? -1 : 1
  const signA = sign(a), signC = sign(c), signD = sign(d)
  const rotation = (axis: number) => interpolateCameraSample(packedNumber(animation, a + 3 + axis) * signA, packedNumber(animation, b + 3 + axis), packedNumber(animation, c + 3 + axis) * signC, packedNumber(animation, d + 3 + axis) * signD, blend)
  quaternion.set(rotation(0), rotation(1), rotation(2), rotation(3)).normalize()
  if (manifest.camera.fovOffset != null) result.fov = sample(manifest.camera.fovOffset)
  return result
}
