import { fireEvent, render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { beforeEach, describe, expect, it } from 'vitest'
import type { ReactElement } from 'react'

import { useGameStore } from '../../game/state/useGameStore'
import { Inspector } from './Inspector'

describe('Inspector', () => {
  beforeEach(() => {
    useGameStore.setState({
      selectedTile: { x: 2, y: 3 },
      selectedBuildingId: null,
      hoveredTile: null,
      buildings: [],
      resourceNodes: [],
      monsters: [],
      worldTiles: [],
      tool: 'select',
    })
  })

  it('shows selected tile details and object/player tabs', () => {
    useGameStore.setState({
      worldTiles: [{ x: 2, y: 3, chunk_x: 0, chunk_y: 0, terrain: 'forest', elevation: 0, safe_zone: false, forest_density: 2 }],
    })
    renderWithClient(<Inspector />)

    expect(screen.getByText('Тайл 2:3')).toBeTruthy()
    expect(screen.getByText('2, 3')).toBeTruthy()
    expect(screen.getByText('2/3')).toBeTruthy()
    expect(screen.queryByLabelText('Срубить лес')).toBeNull()

    fireEvent.click(screen.getByRole('tab', { name: 'Объект' }))
    expect(screen.getByText('Постройка не выбрана')).toBeTruthy()

    fireEvent.click(screen.getByRole('tab', { name: 'Игрок' }))
    expect(screen.getByText('Игрок: Северный двор')).toBeTruthy()
  })

  it('opens selected building actions and deletes it', () => {
    useGameStore.setState({
      buildings: [
        {
          id: 'town-hall-test',
          kind: 'town_hall',
          name: 'Ратуша',
          level: 1,
          tile: { x: 2, y: 3 },
          status: 'active',
          health: 100,
          owner: 'Северный двор',
          startedAt: 1000,
          completesAt: null,
        },
      ],
      selectedBuildingId: 'town-hall-test',
    })

    renderWithClient(<Inspector />)
    expect(screen.getByText('Ратуша, уровень 1')).toBeTruthy()

    fireEvent.click(screen.getByLabelText('Удалить'))
    expect(useGameStore.getState().buildings).toEqual([])
  })

  it('opens upgrade dialog with next level details', () => {
    useGameStore.setState({
      buildings: [
        {
          id: 'dugout-test',
          kind: 'dugout',
          name: 'Землянка',
          level: 1,
          tile: { x: 2, y: 3 },
          status: 'active',
          health: 35,
          owner: 'Северный двор',
          startedAt: 1000,
          completesAt: null,
        },
      ],
      selectedBuildingId: 'dugout-test',
    })

    renderWithClient(<Inspector />)
    fireEvent.click(screen.getByLabelText('Улучшить'))

    expect(screen.getByRole('dialog', { name: 'Улучшение постройки' })).toBeTruthy()
    expect(screen.getByText('Уровень 1 -> 2')).toBeTruthy()
    expect(screen.getByText('45 сек')).toBeTruthy()
    expect(screen.getByText('400')).toBeTruthy()
    expect(screen.getByText('10')).toBeTruthy()
  })

  it('opens build menu from the inspector build action', () => {
    renderWithClient(<Inspector />)

    fireEvent.click(screen.getByLabelText('Построить'))

    expect(useGameStore.getState().tool).toBe('build')
    expect(useGameStore.getState().uiPreferences.buildMenuOpen).toBe(true)
  })

  it('opens town hall upgrade dialog when town hall has next level', () => {
    useGameStore.setState({
      buildings: [
        {
          id: 'town-hall-test',
          kind: 'town_hall',
          name: 'Ратуша',
          level: 1,
          tile: { x: 2, y: 3 },
          status: 'active',
          health: 100,
          owner: 'Северный двор',
          startedAt: 1000,
          completesAt: null,
        },
      ],
      selectedBuildingId: 'town-hall-test',
    })

    renderWithClient(<Inspector />)
    fireEvent.click(screen.getByLabelText('Улучшить'))

    expect(screen.getByRole('dialog', { name: 'Улучшение постройки' })).toBeTruthy()
    expect(screen.getByText('Уровень 1 -> 2')).toBeTruthy()
    expect(screen.getByText('1 мин 30 сек')).toBeTruthy()
    expect(screen.getByText('1500')).toBeTruthy()
  })

  it('shows rush completion crystal cost for construction', () => {
    useGameStore.setState({
      constructionNow: 1000,
      buildings: [
        {
          id: 'dugout-test',
          kind: 'dugout',
          name: 'Землянка',
          level: 1,
          tile: { x: 2, y: 3 },
          status: 'construction',
          health: 35,
          owner: 'Северный двор',
          startedAt: 1000,
          completesAt: 1000 + 2 * 60 * 1000,
        },
      ],
      selectedBuildingId: 'dugout-test',
    })

    renderWithClient(<Inspector />)

    expect(screen.getByText('Мгновенно: 1 крист.')).toBeTruthy()
    expect(screen.getByLabelText('Завершить за 1 крист.')).toBeTruthy()
  })
})

function renderWithClient(ui: ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>)
}
