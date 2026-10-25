import { describe, expect, it, vi } from 'vitest'

const { play } = vi.hoisted(() => ({ play: vi.fn(() => true) }))
vi.mock('./AudioManager', () => ({ audioManager: { play } }))

import { playCombatSound } from './voiceManager'

describe('дедупликация звуков событий', () => {
  it('не воспроизводит повтор того же event_id после reconnect', () => {
    expect(playCombatSound('combat.weapon.cannon', 0.8, 'shot-replay-1')).toBe(true)
    expect(playCombatSound('combat.weapon.cannon', 0.8, 'shot-replay-1')).toBe(false)
    expect(play).toHaveBeenCalledTimes(1)
  })
})
