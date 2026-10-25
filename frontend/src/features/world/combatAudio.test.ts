import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useGameStore } from '../../game/state/useGameStore'
import { useAuthStore } from '../auth/useAuthStore'
import { monsterActionSound, playCombatEvent } from './combatAudio'
import { playCombatSound } from '../../audio/voiceManager'

vi.mock('../../audio/voiceManager', () => ({ playCombatSound: vi.fn() }))

const envelope = (type: 'monster.moved' | 'monster.damaged' | 'monster.attacked' | 'cannon.shot', payload: unknown, playerId?: string) => ({
  type, event_id: `${type}-1`, seq: 1, sent_at: '2026-10-24T10:00:00Z', payload_version: 1, payload, player_id: playerId,
})

describe('combat event sounds', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useAuthStore.setState({ player: { id: 'self' } as ReturnType<typeof useAuthStore.getState>['player'] })
    useGameStore.setState({ monsters: [], buildings: [], viewport: { center: { x: 0, y: 0 }, radius: 1 } as ReturnType<typeof useGameStore.getState>['viewport'] })
  })

  it('selects a distinct timbre for each monster type', () => {
    expect(monsterActionSound('resource_guardian', 'death')).toBe('combat.monster.resource_guardian.death')
    expect(monsterActionSound('unknown', 'death')).toBe('combat.monster.death')
  })

  it('sounds aggro only on a known transition and does not sound distant movement', () => {
    const monster = { id: 'm1', type: 'forest_stalker' as const, state: 'aggro' as const, tile_x: 2, tile_y: 2, health: 100, damage: 10 }
    playCombatEvent(envelope('monster.moved', { monster }))
    expect(playCombatSound).not.toHaveBeenCalled()
    useGameStore.setState({ monsters: [{ id: 'm1', type: 'forest_stalker', state: 'wandering', tile: { x: 2, y: 2 }, targetId: '', targetType: '', health: 100, maxHealth: 100, damage: 10, aggroRadius: 3, updatedAt: 0 }] })
    playCombatEvent(envelope('monster.moved', { monster }))
    expect(playCombatSound).toHaveBeenCalledWith('combat.monster.forest_stalker.aggro', expect.any(Number), 'monster.moved-1:aggro', expect.any(Number))
    vi.clearAllMocks()
    playCombatEvent(envelope('monster.moved', { monster: { ...monster, tile_x: 80, tile_y: 0 } }))
    expect(playCombatSound).not.toHaveBeenCalled()
  })

  it('suppresses the WS echo of the local manual hit while retaining a remote hit', () => {
    const payload = { monster: { id: 'm1', type: 'spore_beast', state: 'aggro', tile_x: 2, tile_y: 2, health: 50, damage: 10 } }
    playCombatEvent(envelope('monster.damaged', payload, 'self'))
    expect(playCombatSound).not.toHaveBeenCalled()
    playCombatEvent(envelope('monster.damaged', payload, 'other'))
    expect(playCombatSound).toHaveBeenCalledWith('combat.monster.spore_beast.hit', expect.any(Number), 'monster.damaged-1:hit', expect.any(Number))
  })

  it('uses the confirmed weapon type and shot coordinate', () => {
    playCombatEvent(envelope('cannon.shot', { building_id: 'b1', building_type: 'defense_storm_coil', monster_id: 'm1', damage: 20, ammo: '', tile_x: 1, tile_y: 1 }))
    expect(playCombatSound).toHaveBeenCalledWith('combat.weapon.storm_coil', expect.any(Number), 'cannon.shot-1:shot', expect.any(Number))
  })

  it('plays cannon fire on the confirmed shot event', () => {
    playCombatEvent(envelope('cannon.shot', { building_id: 'b1', building_type: 'defense_cannon', monster_id: 'm1', damage: 55, ammo: 'stone', tile_x: 1, tile_y: 1 }))
    expect(playCombatSound).toHaveBeenCalledWith('combat.weapon.cannon', expect.any(Number), 'cannon.shot-1:shot', expect.any(Number))
  })

  it("plays a nearby player's confirmed attack", () => {
    playCombatEvent(envelope('monster.damaged', { source: 'player', damage: 28, monster: {
      id: 'm1', type: 'roaming_melee', state: 'aggro', tile_x: 1, tile_y: 1, health: 50,
    } }, 'other'))
    expect(playCombatSound).toHaveBeenCalledWith('combat.player.attack', expect.any(Number), 'monster.damaged-1:player-attack', expect.any(Number))
  })
})
