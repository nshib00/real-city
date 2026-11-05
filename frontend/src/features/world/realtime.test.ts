import { QueryClient } from '@tanstack/react-query'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useGameStore } from '../../game/state/useGameStore'
import { useAuthStore } from '../auth/useAuthStore'
import { applyRealtimeEvent } from './realtime'
import * as uiAudio from '../../audio/playUiSound'

describe('world realtime reducer', () => {
  beforeEach(() => {
    useGameStore.setState({
      buildings: [],
      resourceNodes: [],
      monsters: [],
      deadMonsterIds: new Set(),
      cannonShots: [],
      monsterDamageEvents: [],
      buildingDamageEvents: [],
      worldTiles: [{ x: 1, y: 1, chunk_x: 0, chunk_y: 0, terrain: 'forest', elevation: 0, safe_zone: false, forest_density: 3 }],
    })
  })

  it('clears cached alliance history after membership changes', () => {
    const state = useGameStore.getState()
    const queryClient = new QueryClient()
    queryClient.setQueryData(['chat', 'alliance', 'player-1'], { messages: [{ id: 'secret' }] })
    applyRealtimeEvent({ type: 'alliance.member.kicked', event_id: 'kick', seq: 1, sent_at: '2026-10-30T00:00:00Z', payload_version: 1, payload: { target_player_id: 'player-1' } }, {
      queryClient, updateWorldTile: state.updateWorldTile, addBuilding: state.addBuilding,
      deleteBuilding: state.deleteBuilding, upsertResourceNode: state.upsertResourceNode, upsertMonster: state.upsertMonster,
    })
    expect(queryClient.getQueryData(['chat', 'alliance', 'player-1'])).toBeUndefined()
    queryClient.clear()
  })

  it('shows a building placed by another player in the visible map state', () => {
    const state = useGameStore.getState()
    const queryClient = new QueryClient()
    const visibleKey = ['buildings', 'visible', 1, 2, 1]
    queryClient.setQueryData(visibleKey, { buildings: [] })
    applyRealtimeEvent({
      type: 'world.building.placed', event_id: 'foreign-build', seq: 1,
      sent_at: '2026-10-25T00:00:00Z', payload_version: 1,
      chunk_id: 'dev-world:1:2', player_id: 'other',
      payload: { building: {
        id: 'foreign-house', owner_id: 'other', type: 'dugout', name: 'Землянка', level: 1,
        state: 'building', health: 100, tile_x: 35, tile_y: 68,
        started_at: '2026-10-25T00:00:00Z', completes_at: '2026-10-25T01:00:00Z',
      } },
    }, {
      queryClient, updateWorldTile: state.updateWorldTile, addBuilding: state.addBuilding,
      deleteBuilding: state.deleteBuilding, upsertResourceNode: state.upsertResourceNode, upsertMonster: state.upsertMonster,
    })
    expect(useGameStore.getState().buildings).toMatchObject([{
      id: 'foreign-house', owner: 'other', tile: { x: 35, y: 68 }, status: 'construction',
    }])
    expect(queryClient.getQueryData<{ buildings: { id: string }[] }>(visibleKey)?.buildings[0].id).toBe('foreign-house')
  })

  it('tracks watchkeeper assignment from normalized and raw building events', () => {
    const state = useGameStore.getState()
    const handlers = {
      queryClient: new QueryClient(), updateWorldTile: state.updateWorldTile, addBuilding: state.addBuilding,
      deleteBuilding: state.deleteBuilding, upsertResourceNode: state.upsertResourceNode, upsertMonster: state.upsertMonster,
    }
    const building = {
      id: 'tower', owner_id: 'owner', type: 'tower', name: 'Сторожевая башня', level: 1,
      state: 'active', health: 100, tile_x: 1, tile_y: 1,
      started_at: '2026-11-05T00:00:00Z', completes_at: null,
    }
    const emit = (payload: unknown, id: string) => applyRealtimeEvent({
      type: 'world.building.updated', event_id: id, seq: 1,
      sent_at: '2026-11-05T00:00:00Z', payload_version: 1, payload: { building: payload },
    }, handlers)
    emit({ ...building, tower_watchkeeper_assigned: true }, 'assigned')
    expect(useGameStore.getState().buildings[0].towerWatchkeeperAssigned).toBe(true)
    emit({ ID: 'tower', OwnerID: 'owner', Type: 'tower', Name: 'Сторожевая башня', Level: 1,
      State: 'active', Health: 100, Tile: { X: 1, Y: 1 }, StartedAt: '2026-11-05T00:00:00Z',
      CompletesAt: null, TowerWatchkeeperAssigned: false }, 'unassigned-raw')
    expect(useGameStore.getState().buildings[0].towerWatchkeeperAssigned).toBe(false)
    emit({ ...building, tower_watchkeeper_assigned: true }, 'assigned-again')
    emit(building, 'legacy-without-field')
    expect(useGameStore.getState().buildings[0].towerWatchkeeperAssigned).toBe(false)
  })

  it('moves nearby player balloons immediately and removes them from old viewports', () => {
    useAuthStore.setState({ player: null })
    const queryClient = new QueryClient()
    const nearKey = ['players', 'nearby', 16, 16, 32]
    const oldKey = ['players', 'nearby', 120, 120, 16]
    const oldPlayer = { player_id: 'other', name: 'Аэрон', level: 4, tile_x: 1, tile_y: 1 }
    queryClient.setQueryData(nearKey, { players: [oldPlayer] })
    queryClient.setQueryData(oldKey, { players: [oldPlayer] })
    const state = useGameStore.getState()
    applyRealtimeEvent({
      type: 'presence.moved', event_id: 'move-1', seq: 1, sent_at: '2026-10-25T00:00:00Z', payload_version: 1,
      payload: { player: { ...oldPlayer, tile_x: 33, tile_y: 2 } },
    }, {
      queryClient, updateWorldTile: state.updateWorldTile, addBuilding: state.addBuilding,
      deleteBuilding: state.deleteBuilding, upsertResourceNode: state.upsertResourceNode, upsertMonster: state.upsertMonster,
    })
    expect(queryClient.getQueryData<{ players: typeof oldPlayer[] }>(nearKey)?.players).toEqual([{ ...oldPlayer, tile_x: 33, tile_y: 2 }])
    expect(queryClient.getQueryData<{ players: typeof oldPlayer[] }>(oldKey)?.players).toEqual([])
  })

  it('applies tile and building events to canonical state', () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const state = useGameStore.getState()

    applyRealtimeEvent(
      {
        type: 'world.tile.changed',
        event_id: 'evt-1',
        seq: 1,
        sent_at: '2026-08-25T00:00:00Z',
        payload_version: 1,
        payload: {
          tile: { x: 1, y: 1, chunk_x: 0, chunk_y: 0, terrain: 'grass', elevation: 0, safe_zone: false, forest_density: 0 },
        },
      },
      {
        queryClient,
        updateWorldTile: state.updateWorldTile,
        addBuilding: state.addBuilding,
        deleteBuilding: state.deleteBuilding,
        upsertResourceNode: state.upsertResourceNode,
        upsertMonster: state.upsertMonster,
      },
    )

    applyRealtimeEvent(
      {
        type: 'world.building.updated',
        event_id: 'evt-2',
        seq: 2,
        sent_at: '2026-08-25T00:00:00Z',
        payload_version: 1,
        payload: {
          building: {
            id: 'b1',
            owner_id: 'p1',
            type: 'dugout',
            name: 'Землянка',
            level: 2,
            state: 'building',
            health: 140,
            tile_x: 1,
            tile_y: 1,
            started_at: '2026-08-25T00:00:00Z',
            completes_at: '2026-08-25T00:01:00Z',
          },
        },
      },
      {
        queryClient,
        updateWorldTile: state.updateWorldTile,
        addBuilding: state.addBuilding,
        deleteBuilding: state.deleteBuilding,
        upsertResourceNode: state.upsertResourceNode,
        upsertMonster: state.upsertMonster,
      },
    )

    expect(useGameStore.getState().worldTiles[0].terrain).toBe('grass')
    expect(useGameStore.getState().buildings[0]).toMatchObject({ id: 'b1', level: 2, status: 'construction' })
  })

  it('keeps cannon stats while applying server shot events', () => {
    const state = useGameStore.getState()
    state.addBuilding({
      id: 'c1', kind: 'defense_cannon', name: 'Пушка', level: 1, status: 'active', state: 'active',
      health: 260, maxHealth: 260, owner: 'p1', tile: { x: 1, y: 2 }, startedAt: 0, completesAt: null,
      cannonRange: 2, cannonDamage: 55, cannonAmmo: 'stone', cannonEnabled: true,
    })
    applyRealtimeEvent({
      type: 'world.building.updated', event_id: 'cannon-shot', seq: 1,
      sent_at: '2026-10-17T12:00:00Z', payload_version: 1,
      payload: { building: {
        ID: 'c1', OwnerID: 'p1', Type: 'defense_cannon', Name: 'Пушка', Level: 1,
        State: 'active', Health: 260, Tile: { X: 1, Y: 2 }, StartedAt: '2026-10-17T11:00:00Z',
        CompletesAt: null, CannonEnabled: true, CannonTargetID: 'm1', CannonNextAttackAt: '2026-10-17T12:00:12Z',
      } },
    }, {
      queryClient: new QueryClient(), updateWorldTile: state.updateWorldTile, addBuilding: state.addBuilding,
      deleteBuilding: state.deleteBuilding, upsertResourceNode: state.upsertResourceNode, upsertMonster: state.upsertMonster,
    })
    expect(useGameStore.getState().buildings[0]).toMatchObject({
      cannonRange: 2, cannonDamage: 55, cannonEnabled: true, cannonTargetId: 'm1',
    })
  })

  it('records each cannon hit and ammunition cost once', () => {
    const state = useGameStore.getState()
    const queryClient = new QueryClient()
    queryClient.setQueryData(['economy', 'inventory'], { inventory: { items: [] } })
    const handlers = {
      queryClient, updateWorldTile: state.updateWorldTile, addBuilding: state.addBuilding,
      deleteBuilding: state.deleteBuilding, upsertResourceNode: state.upsertResourceNode, upsertMonster: state.upsertMonster,
    }
    const event = { type: 'cannon.shot' as const, event_id: 'shot-1', seq: 1,
      sent_at: '2026-10-17T12:00:00Z', payload_version: 1,
      payload: { building_id: 'c1', monster_id: 'm1', damage: 55, damage_type: 'explosive', ammo: 'stone' } }
    applyRealtimeEvent(event, handlers)
    applyRealtimeEvent(event, handlers)
    expect(useGameStore.getState().cannonShots).toEqual([{
      id: 'shot-1', buildingId: 'c1', monsterId: 'm1', damage: 55, ammo: 'stone',
    }])
    applyRealtimeEvent({ ...event, type: 'economy.inventory.changed', payload: {} }, handlers)
    expect(queryClient.getQueryState(['economy', 'inventory'])?.isInvalidated).toBe(true)
  })

  it('records exact damage on a killing hit only once', () => {
    const state = useGameStore.getState()
    const handlers = {
      queryClient: new QueryClient(), updateWorldTile: state.updateWorldTile, addBuilding: state.addBuilding,
      deleteBuilding: state.deleteBuilding, upsertResourceNode: state.upsertResourceNode, upsertMonster: state.upsertMonster,
    }
    const event = { type: 'monster.died' as const, event_id: 'hit-1', seq: 1,
      sent_at: '2026-10-24T12:00:00Z', payload_version: 1,
      payload: { damage: 12, source: 'cannon', monster: {
        id: 'm1', type: 'roaming_melee' as const, state: 'dead' as const,
        tile_x: 4, tile_y: 5, health: 0, damage: 18,
      } },
    }
    applyRealtimeEvent(event, handlers)
    applyRealtimeEvent(event, handlers)
    expect(useGameStore.getState().monsterDamageEvents).toMatchObject([{ id: 'hit-1', tile: { x: 4, y: 5 }, damage: 12 }])
  })

  it('shows only confirmed monster damage to buildings, including a destroyed ruin', () => {
    const state = useGameStore.getState()
    const handlers = {
      queryClient: new QueryClient(), updateWorldTile: state.updateWorldTile, addBuilding: state.addBuilding,
      deleteBuilding: state.deleteBuilding, upsertResourceNode: state.upsertResourceNode, upsertMonster: state.upsertMonster,
    }
    const building = {
      id: 'b1', owner_id: 'p1', type: 'dugout' as const, name: 'Землянка', level: 1,
      state: 'active' as const, health: 100, tile_x: 4, tile_y: 5,
      started_at: '2026-10-25T00:00:00Z', completes_at: null,
    }
    const update = (id: string, health: number, reason?: 'monster_attack' | 'repaired') => applyRealtimeEvent({
      type: 'world.building.updated', event_id: id, seq: 1, sent_at: '2026-10-25T00:00:00Z', payload_version: 1,
      payload: { building: { ...building, health }, reason },
    }, handlers)
    update('initial', 100)
    update('hit-1', 77, 'monster_attack')
    update('hit-1', 77, 'monster_attack')
    update('repair', 90, 'repaired')
    update('other-hit', 75)
    expect(useGameStore.getState().buildingDamageEvents).toMatchObject([
      { id: 'hit-1', buildingId: 'b1', tile: { x: 4, y: 5 }, damage: 23 },
    ])

    applyRealtimeEvent({
      type: 'world.building.removed', event_id: 'fatal-hit', seq: 2,
      sent_at: '2026-10-25T00:00:00Z', payload_version: 1,
      payload: { building_id: 'b1', reason: 'monster_attack' },
    }, handlers)
    expect(useGameStore.getState().buildingDamageEvents).toMatchObject([
      { damage: 23 }, { id: 'fatal-hit', buildingId: 'b1', damage: 75 },
    ])
  })

  it('shows confirmed building damage even before its first snapshot arrives', () => {
    const state = useGameStore.getState()
    const handlers = {
      queryClient: new QueryClient(), updateWorldTile: state.updateWorldTile, addBuilding: state.addBuilding,
      deleteBuilding: state.deleteBuilding, upsertResourceNode: state.upsertResourceNode, upsertMonster: state.upsertMonster,
    }
    applyRealtimeEvent({ type: 'world.building.updated', event_id: 'first-hit', seq: 1,
      sent_at: '2026-10-25T00:00:00Z', payload_version: 1,
      payload: { reason: 'monster_attack', damage: 18, building: {
        id: 'b2', owner_id: 'p1', type: 'dugout', name: 'Землянка', level: 1, state: 'damaged', health: 82,
        tile_x: 4, tile_y: 5, started_at: '2026-10-25T00:00:00Z', completes_at: null,
      } },
    }, handlers)
    applyRealtimeEvent({ type: 'world.building.removed', event_id: 'ruin-hit', seq: 2,
      sent_at: '2026-10-25T00:00:01Z', payload_version: 1,
      payload: { building_id: 'ruin-1', reason: 'monster_attack', damage: 10, tile_x: 7, tile_y: 8, building_type: 'ruins_archive' },
    }, handlers)
    expect(useGameStore.getState().buildingDamageEvents).toMatchObject([
      { id: 'first-hit', buildingId: 'b2', tile: { x: 4, y: 5 }, damage: 18 },
      { id: 'ruin-hit', buildingId: 'ruin-1', tile: { x: 7, y: 8 }, damage: 10 },
    ])
  })

  it('keeps inventory refresh silent without a confirmed reward reason', () => {
    const signal = vi.spyOn(uiAudio, 'playUiSound')
    const state = useGameStore.getState()
    const queryClient = new QueryClient()
    applyRealtimeEvent({ type: 'economy.inventory.changed', event_id: 'inventory-refresh', seq: 1,
      sent_at: '2026-10-17T12:00:00Z', payload_version: 1, payload: {} }, {
      queryClient, updateWorldTile: state.updateWorldTile, addBuilding: state.addBuilding,
      deleteBuilding: state.deleteBuilding, upsertResourceNode: state.upsertResourceNode, upsertMonster: state.upsertMonster,
    })
    expect(signal).not.toHaveBeenCalled()
    signal.mockRestore()
  })

  it('refreshes public monster loot when it drops or is claimed', () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const state = useGameStore.getState()
    queryClient.setQueryData(['monster-loot', 0, 0, 1], { loot: [] })
    const handlers = {
      queryClient,
      updateWorldTile: state.updateWorldTile,
      addBuilding: state.addBuilding,
      deleteBuilding: state.deleteBuilding,
      upsertResourceNode: state.upsertResourceNode,
      upsertMonster: state.upsertMonster,
    }
    for (const type of ['monster.loot.dropped', 'monster.loot.claimed'] as const) {
      applyRealtimeEvent({ type, event_id: type, seq: 1, sent_at: '2026-08-25T00:00:00Z', payload_version: 1, payload: {} }, handlers)
      expect(queryClient.getQueryState(['monster-loot', 0, 0, 1])?.isInvalidated).toBe(true)
    }
  })

  it('does not revive a dead monster from a delayed movement event or cached list', () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const state = useGameStore.getState()
    const handlers = {
      queryClient,
      updateWorldTile: state.updateWorldTile,
      addBuilding: state.addBuilding,
      deleteBuilding: state.deleteBuilding,
      upsertResourceNode: state.upsertResourceNode,
      upsertMonster: state.upsertMonster,
    }
    const monster = {
      id: 'dead-monster', type: 'roaming_melee' as const, state: 'wandering' as const,
      tile_x: 2, tile_y: 3, health: 1, max_health: 180,
      damage: 18, aggro_radius: 5, updated_at: '2026-10-16T00:00:00Z',
    }
    queryClient.setQueryData(['monsters', 0, 0, 1], { monsters: [monster] })
    state.upsertMonster({
      id: monster.id, type: monster.type, state: 'wandering', tile: { x: 2, y: 3 },
      targetId: '', targetType: '', health: 1, maxHealth: 180, damage: 18, aggroRadius: 5, updatedAt: 0,
    })

    applyRealtimeEvent({ type: 'monster.died', event_id: 'died', seq: 2, sent_at: monster.updated_at, payload_version: 1, payload: { monster: { ...monster, state: 'dead', health: 0 } } }, handlers)
    applyRealtimeEvent({ type: 'monster.moved', event_id: 'moved', seq: 1, sent_at: monster.updated_at, payload_version: 1, payload: { monster: { ...monster, tile_x: 3 } } }, handlers)
    state.setMonsters([{ id: monster.id, type: monster.type, state: 'wandering', tile: { x: 3, y: 3 }, targetId: '', targetType: '', health: 1, maxHealth: 180, damage: 18, aggroRadius: 5, updatedAt: 0 }])

    expect(useGameStore.getState().monsters).toEqual([])
    expect(queryClient.getQueryData<{ monsters: { id: string }[] }>(['monsters', 0, 0, 1])?.monsters).toEqual([])
  })
})
