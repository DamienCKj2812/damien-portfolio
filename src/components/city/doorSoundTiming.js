export const RETURN_DOOR_SOUND_DELAY_MS = 250

// Threshold events follow rendered journey frames, so asset loading holds and
// paused/offscreen playback cannot sound a door that has not started moving.
export function createDoorSoundTiming() {
  let journeyFrame = 1, departurePlayed = false, returnPlayed = false
  return {
    journey(frame, config) {
      const events = []
      const gate = config.lobbyHoldFrame ?? config.bookmarks.doors
      const lobby = config.elevatorRevealFrame
      if (journeyFrame <= gate && frame > gate && frame <= config.cityEnd) events.push({ id: 'main-gate-open', delay: 0 })
      if (lobby && journeyFrame <= lobby && frame > lobby && frame <= config.lobbyGlobalEnd) events.push({ id: 'lobby-elevator-open', delay: 0 })
      journeyFrame = frame
      return events
    },
    resetDeparture() { departurePlayed = false },
    departure(frame, opening = 300) {
      if (departurePlayed || frame < opening) return []
      departurePlayed = true
      return [{ id: 'elevator-open', delay: 0 }]
    },
    resetReturn() { returnPlayed = false },
    returning(frame, reducedMotion, closingStart = 350) {
      if (returnPlayed || reducedMotion || frame > closingStart) return []
      returnPlayed = true
      return [{ id: 'elevator-return-close', delay: RETURN_DOOR_SOUND_DELAY_MS }]
    },
    completeReturn() {
      if (returnPlayed) return []
      returnPlayed = true
      return [{ id: 'elevator-return-close', delay: RETURN_DOOR_SOUND_DELAY_MS }]
    },
  }
}
