import { MathUtils, Quaternion, Vector3 } from 'three'
import { interpolateCameraSample } from './cameraMotion.js'

export function createRoomAlignment(assets, journey) {
  if (!assets) return null
  const rotation = new Quaternion().setFromAxisAngle(new Vector3(0, 0, 1), Math.PI)
  const position = new Vector3().fromArray(journey.elevatorOffset).sub(new Vector3().fromArray(assets.manifest.entranceAnchor).applyQuaternion(rotation))
  const poses = Object.fromEntries(Object.entries(assets.manifest.cameras).map(([key, pose]) => [key, {
    position: new Vector3().fromArray(pose.position).applyQuaternion(rotation).add(position),
    quaternion: rotation.clone().multiply(new Quaternion().fromArray(pose.quaternion).normalize()),
    fov: pose.fov,
  }]))
  return { position, rotation, poses }
}

export function sampleMorphWeights(assets, frame, channel, target) {
  const { manifest, animation } = assets
  const relative = manifest.loop ? MathUtils.euclideanModulo(frame - 1, manifest.frameEnd) : MathUtils.clamp(frame - 1, 0, manifest.frameEnd - 1)
  const first = Math.floor(relative)
  const second = manifest.loop ? (first + 1) % manifest.frameEnd : Math.min(first + 1, manifest.frameEnd - 1)
  const blend = relative - first
  const a = (first * manifest.channelCount + channel) * manifest.channelStride + 12
  const b = (second * manifest.channelCount + channel) * manifest.channelStride + 12
  target.set(MathUtils.lerp(animation[a], animation[b], blend), MathUtils.lerp(animation[a+1], animation[b+1], blend), MathUtils.lerp(animation[a+2], animation[b+2], blend), MathUtils.lerp(animation[a+3], animation[b+3], blend))
}

export function readRoomRoute(assets, frame, position) {
  const descriptor = assets.manifest.navigation.route
  const count = descriptor.frameEnd - descriptor.frameStart + 1
  const relative = descriptor.loop ? MathUtils.euclideanModulo(frame - descriptor.frameStart, count) : MathUtils.clamp(frame - descriptor.frameStart, 0, count - 1)
  const first = Math.floor(relative)
  const index = frameIndex => (descriptor.loop ? MathUtils.euclideanModulo(frameIndex, count) : MathUtils.clamp(frameIndex, 0, count - 1)) * descriptor.stride
  const blend = relative - first, a = index(first - 1), b = index(first), c = index(first + 1), d = index(first + 2)
  const sample = axis => interpolateCameraSample(assets.route[a + axis], assets.route[b + axis], assets.route[c + axis], assets.route[d + axis], blend)
  position.set(sample(0), sample(1), sample(2))
  return position
}

export function isRoomAtEntrance(assets, navigation, view = 'main') {
  if (view !== 'main') return false
  const limits = assets.manifest.navigation
  if (limits?.type === 'guided') return navigation.walkFrame <= limits.route.frameStart + .01
  if (limits?.type === 'axis') return navigation.y <= limits.minY + .01
  return true
}
