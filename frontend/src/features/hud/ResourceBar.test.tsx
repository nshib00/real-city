import { fireEvent, render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { beforeEach, describe, expect, it } from 'vitest'

import type { BuildingKind, PlacedBuilding } from '../../game/state/useGameStore'
import { useGameStore } from '../../game/state/useGameStore'
import { ResourceBar } from './ResourceBar'

describe('ResourceBar', () => {
  beforeEach(() => {
    useGameStore.setState({
      buildings: [],
      uiPreferences: { compactPanels: false, resourceRegistryOpen: false, alliancePanelOpen: false, buildMenuOpen: false },
      realtimeStatus: 'connected',
    })
  })

  it('renders expanded economy resources and toggles related panels', () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={queryClient}>
        <ResourceBar />
      </QueryClientProvider>,
    )

    expect(screen.getByLabelText('Жители: 18/24')).toBeTruthy()
    expect(screen.getByLabelText('Монеты: 1240/2000')).toBeTruthy()
    expect(screen.getByLabelText('Постройки: 0/8')).toBeTruthy()
    expect(screen.getByLabelText('Эолийские кристаллы: 18')).toBeTruthy()
    expect(screen.getByLabelText('Нефть: 36')).toBeTruthy()
    expect(screen.getByLabelText('Бензин: 12')).toBeTruthy()

    fireEvent.click(screen.getByLabelText('Реестр ресурсов'))
    expect(useGameStore.getState().uiPreferences.resourceRegistryOpen).toBe(true)

    fireEvent.click(screen.getByLabelText('Союз'))
    expect(useGameStore.getState().uiPreferences.alliancePanelOpen).toBe(true)
  })

  it('renders live population and building limits from buildings', () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    useGameStore.setState({
      buildings: [
        activeBuilding('town_hall', 2),
        activeBuilding('dugout', 3),
        activeBuilding('wood_house', 2),
        activeBuilding('road', 1),
        { ...activeBuilding('villa', 1), status: 'construction' },
      ],
    })

    render(
      <QueryClientProvider client={queryClient}>
        <ResourceBar />
      </QueryClientProvider>,
    )

    expect(screen.getByLabelText('Жители: 18/13')).toBeTruthy()
    expect(screen.getByLabelText('Постройки: 4/13')).toBeTruthy()
  })
})

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
