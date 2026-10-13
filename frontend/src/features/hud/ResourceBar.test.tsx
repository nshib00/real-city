import { fireEvent, render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { beforeEach, describe, expect, it } from 'vitest'

import { resourceCatalog } from '../../../../shared/catalog/resources'
import type { BuildingKind, PlacedBuilding } from '../../game/state/useGameStore'
import { useGameStore } from '../../game/state/useGameStore'
import { ResourceBar } from './ResourceBar'

describe('ResourceBar', () => {
  beforeEach(() => {
    useGameStore.setState({
      buildings: [],
      uiPreferences: { compactPanels: false, resourceRegistryOpen: false, alliancePanelOpen: false, buildMenuOpen: false, isChatCollapsed: false, areNotificationsCollapsed: false },
      realtimeStatus: 'connected',
    })
  })

  it('renders pinned economy counters and toggles related panels', () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={queryClient}>
        <ResourceBar />
      </QueryClientProvider>,
    )

    expect(screen.getByLabelText('Жители: 0')).toBeTruthy()
    expect(screen.getByLabelText('Монеты: 50/2000')).toBeTruthy()
    expect(screen.getByLabelText('Постройки: 0/8')).toBeTruthy()
    expect(screen.getByLabelText('Эолийские кристаллы: 0')).toBeTruthy()
    expect(screen.queryByLabelText('Древесина: 0')).toBeNull()
    expect(screen.queryByLabelText('Нефть: 0')).toBeNull()
    expect(screen.queryByLabelText('Бензин: 0')).toBeNull()
    expect(screen.getByLabelText('Ресурсы').querySelector('.resource-chip')?.getAttribute('aria-label')).toBe('Постройки: 0/8')
    expect(screen.getByLabelText('Монеты: 50/2000').querySelector('img')?.getAttribute('src')).toContain('/assets/resources/icons/coins.png')

    fireEvent.click(screen.getByLabelText('Реестр ресурсов'))
    expect(useGameStore.getState().uiPreferences.resourceRegistryOpen).toBe(true)

    fireEvent.click(screen.getByLabelText('Союз'))
    expect(useGameStore.getState().uiPreferences.alliancePanelOpen).toBe(true)
  })

  it('shows only non-zero regular resources in catalog display order', () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    queryClient.setQueryData(['economy', 'inventory'], {
      inventory: {
        player_id: 'test',
        items: [
          { resource: 'wood', amount: 0 },
          { resource: 'stone', amount: 5 },
          { resource: 'clay', amount: 3 },
          { resource: 'windleaf', amount: 1 },
          { resource: 'brick', amount: 7 },
          { resource: 'fuel', amount: 2 },
        ],
        coin_capacity: 2000,
        updated_at: '2026-10-10T00:00:00Z',
      },
    })

    render(
      <QueryClientProvider client={queryClient}>
        <ResourceBar />
      </QueryClientProvider>,
    )

    expect(screen.queryByLabelText('Древесина: 0')).toBeNull()
    expect(resourceChipLabels()).toEqual([
      'Постройки: 0/8',
      'Жители: 0',
      'Монеты: 50/2000',
      'Эолийские кристаллы: 0',
      'Глина: 3',
      'Камень: 5',
      'Ветролист: 1',
      'Кирпич: 7',
      'Бензин: 2',
    ])
  })

  it('keeps display order on regular resources only', () => {
    const pinnedIds = new Set(['coins', 'population', 'aeolian-crystal'])
    const regularResources = resourceCatalog.filter((resource) => !pinnedIds.has(resource.id))

    expect(resourceCatalog.filter((resource) => pinnedIds.has(resource.id)).every((resource) => resource.displayOrder === undefined)).toBe(true)
    expect(regularResources.every((resource) => typeof resource.displayOrder === 'number' && Number.isInteger(resource.displayOrder) && resource.displayOrder >= 0)).toBe(true)
    const displayOrders = regularResources.map((resource) => resource.displayOrder ?? -1)
    expect(new Set(displayOrders).size).toBe(displayOrders.length)
  })

  it('renders live population and building limits from buildings', () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    queryClient.setQueryData(['economy', 'inventory'], {
      inventory: {
        player_id: 'test',
        items: [{ resource: 'population', amount: 0 }],
        coin_capacity: 2000,
        updated_at: '2026-10-10T00:00:00Z',
      },
    })
    useGameStore.setState({
      buildings: [
        activeBuilding('town_hall', 2),
        activeBuilding('dugout', 3),
        activeBuilding('wood_house', 2),
        activeBuilding('road', 1),
        activeBuilding('wooden_wall', 1),
        { ...activeBuilding('market', 1), state: 'ruined' },
      ],
    })

    render(
      <QueryClientProvider client={queryClient}>
        <ResourceBar />
      </QueryClientProvider>,
    )

    expect(screen.getByLabelText('Жители: 3/16')).toBeTruthy()
    expect(screen.getByLabelText('Постройки: 3/11')).toBeTruthy()
  })
})

function resourceChipLabels() {
  return Array.from(screen.getByLabelText('Ресурсы').querySelectorAll('.resource-chip'))
    .map((chip) => chip.getAttribute('aria-label'))
    .filter((label): label is string => Boolean(label))
}

function activeBuilding(kind: BuildingKind, level: number): PlacedBuilding {
  return {
    id: `${kind}-${level}`,
    kind,
    name: kind,
    level,
    tile: { x: level, y: level },
    status: 'active' as const,
    health: 100,
    owner: 'test',
    startedAt: 0,
    completesAt: null,
  }
}
