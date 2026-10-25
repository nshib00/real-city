import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, render, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { ReactElement } from 'react'

import { useGameStore } from '../../game/state/useGameStore'
import { useAuthStore } from '../auth/useAuthStore'
import type { Player } from '../auth/types'
import { BuildingSync } from './BuildingSync'

const foreignBuilding = {
  id: 'foreign-dugout', owner_id: 'p2', type: 'dugout', name: 'Землянка', level: 1,
  state: 'active', health: 100, tile_x: 43, tile_y: 77,
  started_at: '2026-08-25T00:00:00Z', completes_at: null,
}

vi.mock('../../shared/api/buildings', async () => {
  const actual = await vi.importActual<typeof import('../../shared/api/buildings')>('../../shared/api/buildings')
  return {
    ...actual,
    listBuildings: vi.fn(async () => ({
      buildings: [
        {
          id: 'foreign-town-hall',
          owner_id: 'p2',
          type: 'town_hall',
          name: 'Ратуша',
          level: 1,
          state: 'active',
          health: 100,
          tile_x: 3,
          tile_y: 4,
          started_at: '2026-08-25T00:00:00Z',
          completes_at: null,
        },
        {
          id: 'own-town-hall',
          owner_id: 'p1',
          type: 'town_hall',
          name: 'Ратуша',
          level: 1,
          state: 'active',
          health: 100,
          tile_x: 42,
          tile_y: 77,
          started_at: '2026-08-25T00:00:00Z',
          completes_at: null,
        },
      ],
    })),
    listVisibleBuildings: vi.fn(async () => ({ buildings: [foreignBuilding, { ...foreignBuilding, id: 'border-dugout', tile_x: 31 }] })),
  }
})

describe('BuildingSync', () => {
  beforeEach(() => {
    useGameStore.setState({
      buildings: [],
      selectedTile: null,
      selectedBuildingId: null,
      camera: { x: 0, y: 0, zoom: 1 },
      viewport: { center: { x: 0, y: 0 }, radius: 1 },
    })
    useAuthStore.setState({ player: testPlayer('p1'), isAuthenticated: true })
  })

  it('focuses the map on the current player town hall after loading buildings', async () => {
    renderWithClient(<BuildingSync />)

    await waitFor(() => expect(useGameStore.getState().viewport.center).toEqual({ x: 42, y: 77 }))
  })

  it('loads nearby buildings belonging to other players', async () => {
    renderWithClient(<BuildingSync />)

    await waitFor(() => expect(useGameStore.getState().buildings.find((building) => building.id === 'foreign-dugout')).toMatchObject({ owner: 'p2', tile: { x: 43, y: 77 } }))
  })

  it('keeps buildings from both districts when the center crosses their border', async () => {
    renderWithClient(<BuildingSync />)
    await waitFor(() => expect(useGameStore.getState().buildings.some((building) => building.id === 'border-dugout')).toBe(true))

    act(() => useGameStore.getState().setViewportCenter({ x: 31, y: 77 }))
    act(() => useGameStore.getState().setViewportCenter({ x: 32, y: 77 }))

    await waitFor(() => expect(useGameStore.getState().buildings.map((building) => building.id)).toEqual(expect.arrayContaining(['border-dugout', 'foreign-dugout'])))
  })
})

function renderWithClient(ui: ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>)
}

function testPlayer(id: string): Player {
  return {
    id,
    email: `${id}@test.local`,
    name: id,
    status: 'active',
    role: 'user',
    profile: {
      display_name: id,
      city_name: 'Тестовый двор',
      avatar_url: '',
      level: 1,
      xp: 0,
      level_start_xp: 0,
      next_level_xp: 100,
      settings: {
        notifications: { raid_alerts: true, production_ready: true, market_updates: true },
        render_quality: 'medium',
      },
      updated_at: '2026-09-20T00:00:00Z',
    },
    created_at: '2026-09-20T00:00:00Z',
    updated_at: '2026-09-20T00:00:00Z',
  }
}
