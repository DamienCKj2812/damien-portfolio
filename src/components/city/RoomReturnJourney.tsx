/* eslint react-hooks/immutability: "off" -- The finite return journey owns mutable Three.js camera resources. */
import { useEffect, useLayoutEffect, useMemo, useRef } from 'react'
import { useFrame, useThree } from '@react-three/fiber'
import { MathUtils, Matrix4, PerspectiveCamera, Quaternion, Vector3 } from 'three'
import { createPoseScratch, readCameraPose } from './journeyTimeline'
import { advanceCameraSpring } from './cameraMotion'
import { ELEVATOR_PLAYBACK_RATE } from './elevatorTiming'
import type { RefObject } from 'react'
import type { ElevatorManifest, JourneyConfig, LoadedSceneAssets } from '../../types/scene'

export type ReturnJourneyPhase = 'turning' | 'walking' | 'entering' | 'panel'
export interface RoomReturnJourneyProps {
  assets: LoadedSceneAssets<ElevatorManifest>; journey: JourneyConfig; active: boolean; reducedMotion: boolean
  elevatorFrameRef: RefObject<number>; onProgress: (frame: number, phase: ReturnJourneyPhase) => void; onComplete: () => void
}

const BASIS = new Quaternion().setFromAxisAngle(new Vector3(1, 0, 0), -Math.PI / 2)
const INVERSE_BASIS = BASIS.clone().invert()
const REVERSE_FACING = new Quaternion().setFromAxisAngle(new Vector3(0, 0, 1), Math.PI)

export default function RoomReturnJourney({ assets, journey, active, reducedMotion, elevatorFrameRef, onProgress, onComplete }: RoomReturnJourneyProps) {
  const { camera, gl, size, invalidate } = useThree()
  const elapsed = useRef(0)
  const finished = useRef(false)
  const playback = useRef({ value: 414, velocity: 0 })
  const visible = useRef(true)
  const pose = useMemo(() => ({ ...createPoseScratch(), start: new Vector3(), startRotation: new Quaternion(), turnRotation: new Quaternion(), cabinFacing: new Quaternion(), panelRotation: new Quaternion(), panelTarget: new Vector3(), matrix: new Matrix4(), up: new Vector3(0, 0, 1), target: new Vector3(), offset: new Vector3().fromArray(journey.elevatorOffset), startFov: 50, walkDuration: 1 }), [journey])
  useLayoutEffect(() => {
    if (!active || !(camera instanceof PerspectiveCamera)) return
    elapsed.current = 0;finished.current = false
    playback.current.value = 414;playback.current.velocity = 0
    pose.start.copy(camera.position).applyQuaternion(INVERSE_BASIS)
    pose.startRotation.copy(INVERSE_BASIS).multiply(camera.quaternion)
    pose.startFov = camera.fov
    readCameraPose(assets, 414, pose.bridgePosition, pose.bridgeQuaternion)
    pose.bridgePosition.add(pose.offset)
    pose.cabinFacing.copy(REVERSE_FACING).multiply(pose.bridgeQuaternion)
    pose.target.copy(pose.bridgePosition);pose.target.z = pose.start.z
    if (pose.start.distanceTo(pose.target) < .001) pose.turnRotation.copy(pose.cabinFacing)
    else pose.turnRotation.setFromRotationMatrix(pose.matrix.lookAt(pose.start, pose.target, pose.up))
    // Quintic easing has a higher peak speed; allow a little more walk time so
    // its gentler acceleration does not introduce larger per-render steps.
    pose.walkDuration = MathUtils.clamp(pose.start.distanceTo(pose.bridgePosition) / 1.3 * 1.25, .95, 3.25)
    invalidate()
  }, [active, assets, camera, pose, invalidate])
  useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => { if (!entry) return;visible.current = entry.isIntersecting;if (entry.isIntersecting && active) invalidate() })
    observer.observe(gl.domElement)
    const resume = () => { if (!document.hidden && active) invalidate() }
    document.addEventListener('visibilitychange', resume)
    return () => { observer.disconnect();document.removeEventListener('visibilitychange', resume) }
  }, [active, gl, invalidate])
  useEffect(() => { if (active) invalidate() }, [active, reducedMotion, size.width, size.height, invalidate])
  useFrame((_, delta) => {
    if (!active || !(camera instanceof PerspectiveCamera) || finished.current || document.hidden || !visible.current) return
    elapsed.current += Math.min(delta, .1) * ELEVATOR_PLAYBACK_RATE
    const turnEnd = 1.2, walkEnd = turnEnd + pose.walkDuration
    const time = reducedMotion ? walkEnd + (414 - 180) / 45 : elapsed.current
    const targetFrame = Math.max(180, 414 - (time - walkEnd) * 45)
    const frame = reducedMotion ? 180 : time < walkEnd ? 510 : MathUtils.clamp(advanceCameraSpring(playback.current, targetFrame, delta, 32), 180, 414)
    elevatorFrameRef.current = frame
    let phase: ReturnJourneyPhase, fov: number
    const adjustedFov = (value: number) => Math.min(85, MathUtils.radToDeg(2 * Math.atan(Math.tan(MathUtils.degToRad(value) / 2) * Math.max(1, 1.6 / (size.width / Math.max(1, size.height))))))
    if (time < turnEnd) {
      phase = 'turning'
      pose.position.copy(pose.start)
      pose.quaternion.copy(pose.startRotation).slerp(pose.turnRotation, MathUtils.smootherstep(time / turnEnd, 0, 1))
      fov = pose.startFov
    } else if (time < walkEnd) {
      phase = 'walking'
      const blend = MathUtils.smootherstep((time - turnEnd) / pose.walkDuration, 0, 1)
      pose.position.lerpVectors(pose.start, pose.bridgePosition, blend)
      pose.quaternion.copy(pose.turnRotation).slerp(pose.cabinFacing, blend)
      fov = MathUtils.lerp(pose.startFov, adjustedFov(readCameraPose(assets, 414, pose.target, pose.bridgeQuaternion).fov), blend)
    } else {
      fov = adjustedFov(readCameraPose(assets, frame, pose.position, pose.quaternion).fov)
      pose.position.add(pose.offset)
      phase = frame > 360 ? 'entering' : 'panel'
      if (frame >= 360) pose.quaternion.copy(pose.cabinFacing)
      else {
        // Walk into the cabin, then turn directly to its selection view. Keep
        // looking at the buttons while the door animation finishes behind us.
        readCameraPose(assets, 180, pose.target, pose.panelRotation)
        const portrait = MathUtils.smoothstep(size.height / Math.max(1, size.width), 1.05, 1.65)
        if (portrait > 0) {
          pose.target.add(pose.offset)
          pose.panelTarget.set(1.253, 1.42, 1.91).add(pose.offset)
          pose.panelRotation.slerp(pose.bridgeQuaternion.setFromRotationMatrix(pose.matrix.lookAt(pose.target, pose.panelTarget, pose.up)), portrait)
        }
        pose.quaternion.copy(pose.cabinFacing).slerp(pose.panelRotation, MathUtils.smootherstep((360 - frame) / 84, 0, 1))
      }
    }
    camera.position.copy(pose.position).applyQuaternion(BASIS)
    camera.quaternion.copy(BASIS).multiply(pose.quaternion)
    if (Math.abs(camera.fov - fov) > .001 || camera.near !== .01) { camera.fov = fov;camera.near = .01;camera.updateProjectionMatrix() }
    camera.updateMatrixWorld()
    onProgress(frame, phase)
    if (frame <= 180) { finished.current = true;onComplete() }
    else invalidate()
  }, -.75)
  return null
}
