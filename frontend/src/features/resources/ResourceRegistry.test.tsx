import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { beforeEach, describe, expect, it } from 'vitest'

import { useGameStore } from '../../game/state/useGameStore'
import { ResourceRegistry } from './ResourceRegistry'

describe('ResourceRegistry', () => {
  beforeEach(() => {
    useGameStore.setState({
      buildings: [],
      uiPreferences: { mapPowerSave: false, compactPanels: false, resourceRegistryOpen: true, alliancePanelOpen: false, buildMenuOpen: false, isChatCollapsed: false, areNotificationsCollapsed: false },
    })
  })

  it('renders current inventory values and updates when inventory changes', async () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    queryClient.setQueryData(['economy', 'inventory'], inventoryPayload(1500, 20, 2500))

    render(
      <QueryClientProvider client={queryClient}>
        <ResourceRegistry />
      </QueryClientProvider>,
    )

    expect(screen.getByText('1500/2500')).toBeTruthy()
    expect(screen.getByText('20')).toBeTruthy()

    act(() => {
      queryClient.setQueryData(['economy', 'inventory'], inventoryPayload(1800, 21, 3000))
    })

    await waitFor(() => expect(screen.getByText('1800/3000')).toBeTruthy())
    expect(screen.getByText('21')).toBeTruthy()
  })

  it('shows elderwood heart from live inventory in rare resources', () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    queryClient.setQueryData(['economy', 'inventory'], {
      inventory: {
        player_id: 'test-player',
        items: [{ resource: 'elderwood-heart', amount: 1 }],
        coin_capacity: 2000,
        updated_at: '2026-08-27T00:00:00.000Z',
      },
    })

    render(
      <QueryClientProvider client={queryClient}>
        <ResourceRegistry />
      </QueryClientProvider>,
    )

    fireEvent.click(screen.getByText('Редкие'))

    const row = screen.getByText('Сердцевина древня').closest('.resource-registry-row')
    expect(row).toBeTruthy()
    expect(row?.textContent).toContain('1')
  })

  it('keeps zero resources visible in the full registry', () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    queryClient.setQueryData(['economy', 'inventory'], inventoryPayload(1500, 20, 2500))

    render(
      <QueryClientProvider client={queryClient}>
        <ResourceRegistry />
      </QueryClientProvider>,
    )

    fireEvent.click(screen.getByText('Сырье'))

    const row = screen.getByText('Древесина').closest('.resource-registry-row')
    expect(row).toBeTruthy()
    expect(row?.textContent).toContain('0')
  })

  it('lists every weapon in its own category before it is crafted', () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    queryClient.setQueryData(['economy', 'inventory'], inventoryPayload(1500, 20, 2500))
    render(<QueryClientProvider client={queryClient}><ResourceRegistry /></QueryClientProvider>)
    fireEvent.click(screen.getByText('Оружие и бомбы'))
    expect(screen.getByText('Метательные клинки')).toBeTruthy()
    expect(screen.getByText('Резонансный заряд')).toBeTruthy()
  })

  it('shows fiber claimed from a resource guardian', () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    queryClient.setQueryData(['economy', 'inventory'], {
      inventory: {
        player_id: 'test-player',
        items: [{ resource: 'fiber', amount: 4 }],
        coin_capacity: 2000,
        updated_at: '2026-10-16T00:00:00Z',
      },
    })

    render(<QueryClientProvider client={queryClient}><ResourceRegistry /></QueryClientProvider>)
    fireEvent.click(screen.getByText('Сырье'))

    expect(screen.getByText('Волокно').closest('.resource-registry-row')?.textContent).toContain('4')
  })
})

function inventoryPayload(coins: number, population: number, coinCapacity: number) {
  return {
    inventory: {
      player_id: 'test-player',
      items: [
        { resource: 'coins', amount: coins },
        { resource: 'population', amount: population },
      ],
      coin_capacity: coinCapacity,
      updated_at: '2026-08-27T00:00:00.000Z',
    },
  }
}
