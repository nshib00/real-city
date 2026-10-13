import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { ReactElement } from 'react'

import { useGameStore } from '../../game/state/useGameStore'
import { useAuthStore } from '../auth/useAuthStore'
import type { Player } from '../auth/types'
import { BuildingSync } from './BuildingSync'

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
