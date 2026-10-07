import { MathUtils, Quaternion, Vector3 } from 'three'
import type { Vector4 } from 'three'
import { interpolateCameraSample } from './cameraMotion'
import type { JourneyConfig, LoadedGuidedRoomAssets, LoadedRoomAssets } from '../../types/scene'
import type { ActiveNavigationState, RoomAlignment, RoomView } from '../../types/navigation'
import type { AnimationAssets } from './journeyTimeline'
import { packedNumber } from '../../types/packedNumbers'

export function createRoomAlignment(assets: Pick<LoadedRoomAssets, 'manifest'>, journey: Pick<JourneyConfig, 'elevatorOffset'>): RoomAlignment
export function createRoomAlignment(assets: Pick<LoadedRoomAssets, 'manifest'> | null | undefined, journey: Pick<JourneyConfig, 'elevatorOffset'>): RoomAlignment | null
export function createRoomAlignment(assets: Pick<LoadedRoomAssets, 'manifest'> | null | undefined, journey: Pick<JourneyConfig, 'elevatorOffset'>): RoomAlignment | null {
  if (!assets) return null
  const rotation = new Quaternion().setFromAxisAngle(new Vector3(0, 0, 1), Math.PI)
  const position = new Vector3().fromArray(journey.elevatorOffset).sub(new Vector3().fromArray(assets.manifest.entranceAnchor).applyQuaternion(rotation))
  const poses = Object.fromEntries(Object.entries(assets.manifest.cameras).map(([key, pose]) => [key, {
    position: new Vector3().fromArray(pose.position).applyQuaternion(rotation).add(position),
    quaternion: rotation.clone().multiply(new Quaternion().fromArray(pose.quaternion).normalize()),
    fov: pose.fov,
  }])) as RoomAlignment['poses']
  return { position, rotation, poses }
}

export function sampleMorphWeights(assets: AnimationAssets, frame: number, channel: number, target: Vector4) {
  const { manifest, animation } = assets
  const relative = manifest.loop ? MathUtils.euclideanModulo(frame - 1, manifest.frameEnd) : MathUtils.clamp(frame - 1, 0, manifest.frameEnd - 1)
  const first = Math.floor(relative)
  const second = manifest.loop ? (first + 1) % manifest.frameEnd : Math.min(first + 1, manifest.frameEnd - 1)
  const blend = relative - first
  const a = (first * manifest.channelCount + channel) * manifest.channelStride + 12
  const b = (second * manifest.channelCount + channel) * manifest.channelStride + 12
  // Callers sample only validated morph actors: native frames start at 1,
  // channels are in range, and stride 16 reserves slots 12–15 for weights.
  // Loading checks the full animation length; first/second wrap or clamp.
  target.set(MathUtils.lerp(packedNumber(animation, a), packedNumber(animation, b), blend), MathUtils.lerp(packedNumber(animation, a+1), packedNumber(animation, b+1), blend), MathUtils.lerp(packedNumber(animation, a+2), packedNumber(animation, b+2), blend), MathUtils.lerp(packedNumber(animation, a+3), packedNumber(animation, b+3), blend))
}

export function readRoomRoute(assets: Pick<LoadedGuidedRoomAssets, 'manifest' | 'route'>, frame: number, position: Vector3) {
  const descriptor = assets.manifest.navigation.route
  const count = descriptor.frameEnd - descriptor.frameStart + 1
  const relative = descriptor.loop ? MathUtils.euclideanModulo(frame - descriptor.frameStart, count) : MathUtils.clamp(frame - descriptor.frameStart, 0, count - 1)
  const first = Math.floor(relative)
  const index = (frameIndex: number) => (descriptor.loop ? MathUtils.euclideanModulo(frameIndex, count) : MathUtils.clamp(frameIndex, 0, count - 1)) * descriptor.stride
  const blend = relative - first, a = index(first - 1), b = index(first), c = index(first + 1), d = index(first + 2)
  // The loaded route has count * stride floats, stride is XYZ (3), and index
  // wraps/clamps each neighbouring sample. Callers below use only axes 0–2.
  const sample = (axis: number) => interpolateCameraSample(packedNumber(assets.route, a + axis), packedNumber(assets.route, b + axis), packedNumber(assets.route, c + axis), packedNumber(assets.route, d + axis), blend)
  position.set(sample(0), sample(1), sample(2))
  return position
}

export function isRoomAtEntrance(assets: Pick<LoadedRoomAssets, 'manifest'>, navigation: Pick<ActiveNavigationState, 'walkFrame' | 'y'>, view: RoomView = 'main') {
  if (view !== 'main') return false
  const limits = assets.manifest.navigation
  if (limits?.type === 'guided') return navigation.walkFrame <= limits.route.frameStart + .01
  if (limits?.type === 'axis') return navigation.y <= limits.minY + .01
  return true
}
