import { audioManager } from './AudioManager'
import type { SoundId } from './soundEvents'

const seenEvents = new Map<string, number>()

export function playCombatSound(id: SoundId, gain = 1, eventId?: string, pan = 0): boolean {
  if (gain <= 0) return false
  const now = performance.now()
  if (eventId) {
    if (seenEvents.has(eventId)) return false
    seenEvents.set(eventId, now)
    if (seenEvents.size > 500) for (const [key, at] of seenEvents) if (now - at > 60_000) seenEvents.delete(key)
  }
  return audioManager.play(id, { gain, pan })
}
