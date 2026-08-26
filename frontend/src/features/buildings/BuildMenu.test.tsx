import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { ReactElement } from 'react'

import { useGameStore } from '../../game/state/useGameStore'
import { BuildMenu } from './BuildMenu'

vi.mock('../../shared/api/buildings', async () => {
  const actual = await vi.importActual<typeof import('../../shared/api/buildings')>('../../shared/api/buildings')
  return {
    ...actual,
    placeBuilding: vi.fn(async ({ type, tile_x, tile_y }: { type: string; tile_x: number; tile_y: number }) => ({
      building: {
        id: `${type}-test`,
        owner_id: 'p1',
        type,
        name: type === 'town_hall' ? 'Ратуша' : 'Землянка',
        level: 1,
        state: type === 'town_hall' ? 'active' : 'building',
        health: 100,
        tile_x,
        tile_y,
        started_at: '2026-08-25T00:00:00Z',
        completes_at: type === 'town_hall' ? null : '2026-08-25T00:01:00Z',
      },
    })),
  }
})

describe('BuildMenu', () => {
  beforeEach(() => {
    useGameStore.setState({
      selectedTile: { x: 0, y: 0 },
      selectedBuildingId: null,
      buildings: [],
      uiPreferences: { compactPanels: false, resourceRegistryOpen: false, alliancePanelOpen: false, buildMenuOpen: true },
    })
  })

  it('allows one free town hall before other buildings', async () => {
    renderWithClient(<BuildMenu />)

    expect(screen.getByLabelText('Построить Землянка').hasAttribute('disabled')).toBe(true)
    fireEvent.click(screen.getByLabelText('Построить Ратуша'))

    await waitFor(() => expect(useGameStore.getState().buildings).toHaveLength(1))
    expect(useGameStore.getState().buildings[0].kind).toBe('town_hall')
  })

  it('places first-level buildings after town hall exists', async () => {
    useGameStore.setState({
      selectedTile: { x: 4, y: 1 },
      buildings: [
        {
          id: 'town-hall-test',
          kind: 'town_hall',
          name: 'Ратуша',
          level: 1,
          tile: { x: 0, y: 0 },
          status: 'active',
          health: 100,
          owner: 'Северный двор',
          startedAt: 1000,
          completesAt: null,
        },
      ],
    })
    renderWithClient(<BuildMenu />)

    fireEvent.click(screen.getByLabelText('Построить Землянка'))

    await waitFor(() =>
      expect(useGameStore.getState().buildings.some((building) => building.kind === 'dugout' && building.level === 1 && building.status === 'construction')).toBe(true),
    )
  })
})

function renderWithClient(ui: ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>)
}
