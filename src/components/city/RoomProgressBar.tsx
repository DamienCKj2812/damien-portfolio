import { useLayoutEffect } from 'react'
import type { CSSProperties, RefObject } from 'react'
import type { LoadedRoomAssets } from '../../types/scene'
import type { NavigationState } from '../../types/navigation'
import { getRoomProgress, updateRoomProgress } from './roomProgress'

export interface RoomProgressBarProps {
  assets: Pick<LoadedRoomAssets, 'manifest'>
  navigationRef: RefObject<NavigationState>
  inputRef: RefObject<HTMLInputElement | null>
  onSeek: (value: number) => void
}

type ProgressStyle = CSSProperties & { '--timeline-progress': string }
const progressStyle: ProgressStyle = { '--timeline-progress': '0%' }

export default function RoomProgressBar({ assets, navigationRef, inputRef, onSeek }: RoomProgressBarProps) {
  const { manifest } = assets
  const progress = getRoomProgress(manifest.navigation, 0, undefined)
  useLayoutEffect(() => {
    const nav = navigationRef.current
    updateRoomProgress(inputRef.current, getRoomProgress(manifest.navigation, nav.position?.[1] ?? nav.y, nav.walkFrame), manifest.label)
  }, [manifest, navigationRef, inputRef])
  if (!progress) return null
  return <div className="city-controls room-progress-controls" aria-label={`${manifest.label} walkthrough controls`}>
    <label className="sr-only" htmlFor="room-progress">{manifest.label} walkthrough progress. Use arrow keys to move along the route.</label>
    <div className="city-timeline">
      <input ref={inputRef} id="room-progress" type="range" min={progress.min} max={progress.max}
        step={manifest.navigation.type === 'guided' ? 1 : .01} defaultValue={progress.min}
        style={progressStyle} onChange={event => onSeek(Number(event.target.value))} />
    </div>
  </div>
}
