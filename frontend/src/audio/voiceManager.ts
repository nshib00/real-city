import { audioManager } from './AudioManager'
import type { SoundId } from './soundEvents'
import { AudioEventWindow } from './eventWindow'

const seenEvents = new AudioEventWindow(500, 60_000)

export function playCombatSound(id: SoundId, gain = 1, eventId?: string, pan = 0): boolean {
  if (gain <= 0) return false
  if (eventId && !seenEvents.accept(eventId)) return false
  return audioManager.play(id, { gain, pan })
}
