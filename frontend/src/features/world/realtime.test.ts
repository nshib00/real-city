import { QueryClient } from '@tanstack/react-query'
import { beforeEach, describe, expect, it } from 'vitest'

import { useGameStore } from '../../game/state/useGameStore'
import { applyRealtimeEvent } from './realtime'

describe('world realtime reducer', () => {
  beforeEach(() => {
    useGameStore.setState({
      buildings: [],
      resourceNodes: [],
      worldTiles: [{ x: 1, y: 1, chunk_x: 0, chunk_y: 0, terrain: 'forest', elevation: 0, safe_zone: false, forest_density: 3 }],
    })
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
      },
    )

    expect(useGameStore.getState().worldTiles[0].terrain).toBe('grass')
    expect(useGameStore.getState().buildings[0]).toMatchObject({ id: 'b1', level: 2, status: 'construction' })
  })
})
