import { fireEvent, render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { beforeEach, describe, expect, it } from 'vitest'
import type { ReactElement } from 'react'

import { useGameStore } from '../../game/state/useGameStore'
import { useAuthStore } from '../auth/useAuthStore'
import type { Player } from '../auth/types'
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
    useAuthStore.setState({ player: testPlayer('player-1'), isAuthenticated: true })
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
          owner: 'player-1',
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
          owner: 'player-1',
          startedAt: 1000,
          completesAt: null,
        },
      ],
      selectedBuildingId: 'dugout-test',
    })

    renderWithClient(<Inspector />)
    fireEvent.click(screen.getByLabelText('Улучшить'))

    expect(screen.getByRole('dialog', { name: 'Улучшение постройки' })).toBeTruthy()
    expect(screen.getByAltText('Модель: Землянка, уровень 2').getAttribute('src')).toBe('/assets/buildings/housing/dugout/dugout_l02_active.png')
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
          owner: 'player-1',
          startedAt: 1000,
          completesAt: null,
        },
      ],
      selectedBuildingId: 'town-hall-test',
    })

    renderWithClient(<Inspector />)
    fireEvent.click(screen.getByLabelText('Улучшить'))

    expect(screen.getByRole('dialog', { name: 'Улучшение постройки' })).toBeTruthy()
    expect(screen.getByAltText('Модель: Ратуша, уровень 2').getAttribute('src')).toBe('/assets/buildings/center/town_hall/town_hall_l02_active.png')
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
          owner: 'player-1',
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

  it('does not expose management actions for another player building', () => {
    useGameStore.setState({
      buildings: [
        {
          id: 'foreign-town-hall',
          kind: 'town_hall',
          name: 'Ратуша',
          level: 1,
          tile: { x: 2, y: 3 },
          status: 'active',
          health: 100,
          owner: 'player-2',
          startedAt: 1000,
          completesAt: null,
        },
      ],
      selectedBuildingId: 'foreign-town-hall',
    })

    renderWithClient(<Inspector />)

    expect(screen.getByText('Чужая постройка: управление недоступно')).toBeTruthy()
    expect(screen.queryByLabelText('Улучшить')).toBeNull()
    expect(screen.queryByLabelText('Удалить')).toBeNull()
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
