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
})

function renderWithClient(ui: ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>)
}
