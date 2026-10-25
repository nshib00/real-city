import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useGameStore } from '../game/state/useGameStore'
import { useAuthStore } from '../features/auth/useAuthStore'
import { playRealtimeAudio } from './realtimeAudio'

const { combatSound } = vi.hoisted(() => ({ combatSound: vi.fn() }))
vi.mock('./voiceManager', () => ({ playCombatSound: combatSound }))
vi.mock('../features/world/combatAudio', () => ({ playCombatEvent: vi.fn() }))

function forestEvent(id: string, x: number, playerId = 'other') {
  return {
    type: 'world.tile.changed' as const, event_id: id, seq: 1,
    sent_at: '2026-10-24T00:00:00Z', payload_version: 1, player_id: playerId,
    payload: { reason: 'forest_cut' as const, tile: {
      x, y: 0, chunk_x: 0, chunk_y: 0, terrain: 'forest' as const,
      elevation: 0, safe_zone: false, forest_density: 2,
    } },
  }
}

describe('WS аудиомост', () => {
  beforeEach(() => {
    combatSound.mockClear()
    useAuthStore.setState({ player: { id: 'self' } as ReturnType<typeof useAuthStore.getState>['player'] })
    useGameStore.setState({ viewport: { center: { x: 0, y: 0 }, radius: 1 }, camera: { x: 0, y: 0, zoom: 1 } })
  })

  it('plays one nearby foreign forest cut and ignores replay, owner and distant events', () => {
    const event = forestEvent('audio-forest-near-1', 1)
    playRealtimeAudio(event)
    playRealtimeAudio(event)
    expect(combatSound).toHaveBeenCalledTimes(1)
    expect(combatSound).toHaveBeenCalledWith('world.forest.cut', expect.any(Number), 'audio-forest-near-1:forest', expect.any(Number))
    playRealtimeAudio(forestEvent('audio-forest-own-1', 1, 'self'))
    playRealtimeAudio(forestEvent('audio-forest-far-1', 80))
    expect(combatSound).toHaveBeenCalledTimes(1)
  })

  it('ignores older tile payloads without a reason', () => {
    playRealtimeAudio({ ...forestEvent('audio-forest-legacy-1', 1), payload: {
      tile: forestEvent('audio-forest-legacy-tile', 1).payload.tile,
    } })
    expect(combatSound).not.toHaveBeenCalled()
  })

  it('plays impact for a confirmed hit without a previous building snapshot', () => {
    useGameStore.setState({ buildings: [] })
    playRealtimeAudio({ type: 'world.building.updated', event_id: 'audio-first-hit-1', seq: 1,
      sent_at: '2026-10-25T00:00:00Z', payload_version: 1,
      payload: { reason: 'monster_attack', damage: 18, building: {
        id: 'b1', owner_id: 'other', type: 'dugout', name: 'Землянка', level: 1,
        state: 'damaged', health: 82, tile_x: 1, tile_y: 0, started_at: '2026-10-25T00:00:00Z', completes_at: null,
      } },
    })
    expect(combatSound).toHaveBeenCalledWith('combat.impact.stone', expect.any(Number), 'audio-first-hit-1:building-impact', expect.any(Number))
  })

  it('plays impact for a destroyed ruin without a previous snapshot', () => {
    useGameStore.setState({ buildings: [] })
    playRealtimeAudio({ type: 'world.building.removed', event_id: 'audio-ruin-hit-1', seq: 1,
      sent_at: '2026-10-25T00:00:00Z', payload_version: 1,
      payload: { building_id: 'ruin-1', reason: 'monster_attack', damage: 10, tile_x: 1, tile_y: 0, building_type: 'ruins_archive' },
    })
    expect(combatSound).toHaveBeenCalledWith('combat.impact.stone', expect.any(Number), 'audio-ruin-hit-1:building-impact', expect.any(Number))
  })

  it('plays building damage across the wrapped map edge', () => {
    useGameStore.setState({ buildings: [], viewport: { center: { x: 0, y: 0 }, radius: 1 } })
    playRealtimeAudio({ type: 'world.building.removed', event_id: 'audio-edge-hit-1', seq: 1,
      sent_at: '2026-10-25T00:00:00Z', payload_version: 1,
      payload: { building_id: 'edge-ruin', reason: 'monster_attack', damage: 10,
        tile_x: 159, tile_y: 0, building_type: 'ruins_archive' },
    })
    expect(combatSound).toHaveBeenCalledWith('combat.impact.stone', expect.any(Number), 'audio-edge-hit-1:building-impact', expect.any(Number))
  })
})
