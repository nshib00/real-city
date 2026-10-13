import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { ReactElement } from 'react'

import { useGameStore } from '../../game/state/useGameStore'
import { useAuthStore } from '../auth/useAuthStore'
import type { Player } from '../auth/types'
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
      uiPreferences: { compactPanels: false, resourceRegistryOpen: false, alliancePanelOpen: false, buildMenuOpen: true, isChatCollapsed: false, areNotificationsCollapsed: false },
    })
    useAuthStore.setState({ player: testPlayer('p1'), isAuthenticated: true })
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
          owner: 'p1',
          startedAt: 1000,
          completesAt: null,
        },
      ],
    })
    renderWithClient(<BuildMenu />, {
      inventory: {
        player_id: 'p1',
        items: [
          { resource: 'population', amount: 0 },
          { resource: 'coins', amount: 50 },
          { resource: 'wood', amount: 3 },
        ],
        coin_capacity: 2000,
        updated_at: '2026-10-10T00:00:00Z',
      },
    })

    expect(screen.getByLabelText('Построить Землянка').hasAttribute('disabled')).toBe(false)
    fireEvent.click(screen.getByLabelText('Построить Землянка'))

    await waitFor(() =>
      expect(useGameStore.getState().buildings.some((building) => building.kind === 'dugout' && building.level === 1 && building.status === 'construction')).toBe(true),
    )
  })

  it('does not treat another player town hall as the current player town hall', () => {
    useGameStore.setState({
      selectedTile: { x: 4, y: 1 },
      buildings: [
        {
          id: 'foreign-town-hall',
          kind: 'town_hall',
          name: 'Ратуша',
          level: 1,
          tile: { x: 0, y: 0 },
          status: 'active',
          health: 100,
          owner: 'p2',
          startedAt: 1000,
          completesAt: null,
        },
      ],
    })

    renderWithClient(<BuildMenu />)

    expect(screen.getByLabelText('Построить Землянка').hasAttribute('disabled')).toBe(true)
    expect(screen.getByLabelText('Построить Ратуша').hasAttribute('disabled')).toBe(false)
  })

  it('shows only directly buildable planned buildings', () => {
    renderWithClient(<BuildMenu />)

    for (const name of [
      'Ратуша',
      'Землянка',
      'Грядка ветролиста',
      'Хранилище монет',
      'Каменотесы',
      'Лесопильный двор',
      'Нефтеперерабатывающий завод',
      'Кирпичная печь',
      'Стекольная мастерская',
      'Кузница',
      'Ткацкий двор',
      'Красильня',
      'Механическая мастерская',
      'Оптическая мастерская',
      'Монетный двор',
      'Грунтовая дорога',
      'Обычная дорога',
      'Мостовая',
      'Деревянная стена',
      'Каменная стена',
      'Бетонная стена',
      'Современная стена',
      'Сторожевая башня',
      'Рынок',
      'Союзный дом',
    ]) {
      expect(screen.getByLabelText(`Построить ${name}`)).toBeTruthy()
    }

    for (const name of [
      'Мастерская',
      'Склад материалов',
      'Деревянный дом',
      'Каменный дом',
      'Многоквартирный дом',
      'Жилой небоскреб',
      'Вилла',
      'Дворец',
    ]) {
      expect(screen.queryByLabelText(`Построить ${name}`)).toBeNull()
    }
  })

  it('shows generated ground road preview and documented cost', () => {
    renderWithClient(<BuildMenu />)

    const roadCard = screen.getByLabelText('Построить Грунтовая дорога').closest('.build-card')
    expect(roadCard?.querySelector('img')?.getAttribute('src')).toBe('/assets/buildings/roads/ground_road/ground_road_straight_ew_active.png')
    expect(roadCard?.textContent).toContain('150')
    expect(roadCard?.textContent).toContain('3')
  })

  it('sorts all buildings by coin cost', () => {
    const { container } = renderWithClient(<BuildMenu />)

    const names = buildCardNames(container)
    expect(names.slice(0, 5)).toEqual(['Ратуша', 'Землянка', 'Каменотесы', 'Грунтовая дорога', 'Кирпичная печь'])
  })

  it('sorts each category by coin cost independently', () => {
    const { container } = renderWithClient(<BuildMenu />)

    fireEvent.click(screen.getByRole('tab', { name: 'Грядки' }))

    const names = buildCardNames(container)
    expect(names.slice(0, 6)).toEqual(['Грядка ветролиста', 'Семенной огород', 'Льняное поле', 'Тростниковая грядка', 'Грибница', 'Травяная грядка'])
  })

  it('shows all road and wall variants plus coin storage previews', () => {
    renderWithClient(<BuildMenu />)

    const coinStorageCard = screen.getByLabelText('Построить Хранилище монет').closest('.build-card')
    expect(coinStorageCard?.querySelector('img')?.getAttribute('src')).toContain('/assets/buildings/storage/coin_storage/coin_storage_l01_active.png')
    expect(coinStorageCard?.textContent).toContain('1500')

    expect(screen.getByLabelText('Построить Обычная дорога').closest('.build-card')?.querySelector('img')?.getAttribute('src')).toBe(
      '/assets/buildings/roads/common_road/common_road_straight_ew_active.png',
    )
    expect(screen.getByLabelText('Построить Мостовая').closest('.build-card')?.querySelector('img')?.getAttribute('src')).toBe(
      '/assets/buildings/roads/paved_road/paved_road_straight_ew_active.png',
    )
    expect(screen.getByLabelText('Построить Каменная стена').closest('.build-card')?.querySelector('img')?.getAttribute('src')).toBe(
      '/assets/buildings/roads/stone_wall/stone_wall_straight_ew_active.png',
    )
    expect(screen.getByLabelText('Построить Бетонная стена').closest('.build-card')?.querySelector('img')?.getAttribute('src')).toBe(
      '/assets/buildings/roads/reinforced_wall/reinforced_wall_straight_ew_active.png',
    )
  })
})

function buildCardNames(container: HTMLElement) {
  return Array.from(container.querySelectorAll('.build-card strong')).map((item) => item.textContent ?? '')
}

function renderWithClient(ui: ReactElement, inventoryData?: unknown) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  if (inventoryData) {
    queryClient.setQueryData(['economy', 'inventory'], inventoryData)
  }
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
