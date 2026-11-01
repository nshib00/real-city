import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { ReactElement } from 'react'

import { useGameStore } from '../../game/state/useGameStore'
import { useAuthStore } from '../auth/useAuthStore'
import type { Player } from '../auth/types'
import { listPendingWeaponAttacks, useWeaponOnMonster, type MonsterLootResponse } from '../../shared/api/monsters'
import { deleteBuilding as deleteBuildingRequest, patchBuilding, placeBuilding, type BuildingResponse } from '../../shared/api/buildings'
import { Inspector } from './Inspector'
import { playCombatSound } from '../../audio/voiceManager'
import { TOWN_HALL_ASSET_REVISION } from '../../game/renderers/buildingAssetManifests'

vi.mock('../../audio/voiceManager', () => ({ playCombatSound: vi.fn() }))

vi.mock('../../shared/api/monsters', async () => ({
  ...await vi.importActual<typeof import('../../shared/api/monsters')>('../../shared/api/monsters'),
  useWeaponOnMonster: vi.fn(),
  listPendingWeaponAttacks: vi.fn(async () => ({ attacks: [] })),
}))

vi.mock('../../shared/api/buildings', async () => ({
  ...await vi.importActual<typeof import('../../shared/api/buildings')>('../../shared/api/buildings'),
  deleteBuilding: vi.fn(async () => ({ status: 'ok' })),
  patchBuilding: vi.fn(),
  placeBuilding: vi.fn(),
}))

vi.mock('../auth/api', async () => ({
  ...await vi.importActual<typeof import('../auth/api')>('../auth/api'),
  getPublicPlayer: vi.fn(async () => ({ id: 'player-2', display_name: 'Игрок Севера', level: 7 })),
}))

describe('Inspector', () => {
  beforeEach(() => {
    vi.mocked(playCombatSound).mockClear()
    vi.mocked(deleteBuildingRequest).mockReset()
    vi.mocked(deleteBuildingRequest).mockResolvedValue({ status: 'ok' })
    vi.mocked(patchBuilding).mockReset()
    vi.mocked(placeBuilding).mockReset()
    vi.mocked(listPendingWeaponAttacks).mockResolvedValue({ attacks: [] })
    useGameStore.setState({
      selectedTile: { x: 2, y: 3 },
      selectedBuildingId: null,
      selectedMonsterId: null,
      hoveredTile: null,
      buildings: [],
      resourceNodes: [],
      monsters: [],
      deadMonsterIds: new Set(),
      worldTiles: [],
      tool: 'select',
    })
    useAuthStore.setState({ player: testPlayer('player-1'), isAuthenticated: true })
  })

  it('collapses with Escape, restores focus and preserves selection', () => {
    renderWithClient(<Inspector />)
    fireEvent.click(screen.getByRole('button', { name: 'Развернуть инспектор' }))
    expect(screen.getByRole('button', { name: 'Свернуть инспектор' }).getAttribute('aria-expanded')).toBe('true')
    fireEvent.keyDown(screen.getByLabelText('Инспектор'), { key: 'Escape' })
    expect(document.activeElement).toBe(screen.getByRole('button', { name: 'Развернуть инспектор' }))
    expect(useGameStore.getState().selectedTile).toEqual({ x: 2, y: 3 })
  })

  it('shows selected tile details and object/player tabs', () => {
    useGameStore.setState({
      worldTiles: [{ x: 2, y: 3, chunk_x: 0, chunk_y: 0, terrain: 'forest', elevation: 0, safe_zone: false, forest_density: 2 }],
    })
    renderWithClient(<Inspector />)

    expect(screen.getByText('Клетка A99')).toBeTruthy()
    expect(screen.getByRole('tab', { name: 'Клетка' })).toBeTruthy()
    expect(screen.getByText('A99')).toBeTruthy()
    expect(screen.getByText('2/3')).toBeTruthy()
    expect(screen.queryByLabelText('Срубить лес')).toBeNull()

    fireEvent.click(screen.getByRole('tab', { name: 'Объект' }))
    expect(screen.getByText('Постройка не выбрана')).toBeTruthy()

    fireEvent.click(screen.getByRole('tab', { name: 'Игрок' }))
    expect(screen.getByText('Игрок: Северный двор')).toBeTruthy()
  })

  it('сворачивает мобильный лист при переходе к размещению, сохраняя клетку', () => {
    renderWithClient(<Inspector />)
    fireEvent.click(screen.getByRole('button', { name: 'Развернуть инспектор' }))
    act(() => useGameStore.getState().setTool('build'))
    expect(screen.getByRole('button', { name: 'Развернуть инспектор' }).getAttribute('aria-expanded')).toBe('false')
    expect(useGameStore.getState().selectedTile).toEqual({ x: 2, y: 3 })
  })

  it('shows only the server terrain and waits for an unloaded tile', () => {
    renderWithClient(<Inspector />)
    expect(screen.getByText('Загрузка...')).toBeTruthy()
    expect(screen.queryByText('песчаная почва')).toBeNull()

    act(() => {
      useGameStore.setState({
        worldTiles: [{ x: 2, y: 3, chunk_x: 0, chunk_y: 0, terrain: 'grass', elevation: 0, safe_zone: false, forest_density: 0 }],
      })
    })
    expect(screen.getByText('луг')).toBeTruthy()
    expect(screen.queryByText('редколесье')).toBeNull()
  })

  it('starts restoring a free ruin from the tile inspector', async () => {
    useGameStore.setState({ worldTiles: [{ x: 2, y: 3, chunk_x: 0, chunk_y: 0, terrain: 'ruins', ruin_type: 'ruins_archive', elevation: 0, safe_zone: false, forest_density: 0 }] })
    vi.mocked(placeBuilding).mockResolvedValue({ building: {
      id: 'ruin-1', owner_id: 'player-1', type: 'ruins_archive', name: 'Архив чертежей', level: 1,
      state: 'building', health: 320, max_health: 320, tile_x: 2, tile_y: 3,
      started_at: '2026-10-24T12:00:00Z', completes_at: '2026-10-25T10:00:00Z',
    } })
    renderWithClient(<Inspector />)
    expect(screen.getByText(/22 ч/)).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Захватить и восстановить' }))
    await waitFor(() => expect(placeBuilding).toHaveBeenCalledWith({ type: 'ruins_archive', tile_x: 2, tile_y: 3 }))
    await waitFor(() => expect(useGameStore.getState().buildings.find((item) => item.id === 'ruin-1')?.owner).toBe('player-1'))
    expect(screen.getByText('Руина занята')).toBeTruthy()
  })

  it('puts dropped monster loot on the map immediately after a killing blow', async () => {
    const loot: MonsterLootResponse = {
      id: 'loot-1', monster_id: 'monster-1', tile_x: 2, tile_y: 3,
      items: [{ resource: 'wood', amount: 25 }], created_at: '2026-10-16T00:00:00Z',
    }
    vi.mocked(useWeaponOnMonster).mockResolvedValue({
      attack: { id: 'weapon-1', weapon: 'throwing_knives', due_at: '2026-10-16T00:00:00Z' },
      monster: {
        id: 'monster-1', type: 'roaming_melee', state: 'dead', tile_x: 2, tile_y: 3,
        target_id: '', target_type: '', health: 0, max_health: 180,
        damage: 18, aggro_radius: 5, updated_at: '2026-10-16T00:00:00Z',
      },
      loot,
    })
    useGameStore.setState({
      selectedMonsterId: 'monster-1',
      monsters: [{
        id: 'monster-1', type: 'roaming_melee', state: 'wandering', tile: { x: 2, y: 3 },
        targetId: '', targetType: '', health: 20, maxHealth: 180,
        damage: 18, aggroRadius: 5, updatedAt: 0,
      }],
    })
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false, staleTime: Infinity } } })
    queryClient.setQueryData(['monster-loot', 16, 16, 1], { loot: [] })
    queryClient.setQueryData(['monsters', 0, 0, 1], { monsters: [{ id: 'monster-1', state: 'wandering', health: 20 }] })
    render(<QueryClientProvider client={queryClient}><Inspector /></QueryClientProvider>)

    queryClient.setQueryData(['economy', 'inventory'], { inventory: { player_id: 'player-1', items: [{ resource: 'throwing_knives', amount: 1 }], coin_capacity: 2000, updated_at: '2026-10-16T00:00:00Z' } })
    fireEvent.click(screen.getByRole('button', { name: 'Выбрать оружие' }))
    const weaponButton = screen.getByRole('button', { name: 'Применить оружие' }) as HTMLButtonElement
    expect(weaponButton.disabled).toBe(false)
    fireEvent.click(weaponButton)

    await waitFor(() => expect(useWeaponOnMonster).toHaveBeenCalledWith('monster-1', 'throwing_knives'))

    await waitFor(() => expect(queryClient.getQueryData<{ loot: MonsterLootResponse[] }>(['monster-loot', 16, 16, 1])?.loot).toEqual([loot]))
    expect(playCombatSound).toHaveBeenCalledWith('combat.player.attack')
    expect(playCombatSound).toHaveBeenCalledWith('combat.player.hit')
    expect(queryClient.getQueryData<{ monsters: { id: string }[] }>(['monsters', 0, 0, 1])?.monsters).toEqual([])
    expect(useGameStore.getState().selectedMonsterId).toBeNull()
  })

  it('shows weapon icons and application times, then applies the selected weapon', async () => {
    vi.mocked(useWeaponOnMonster).mockResolvedValue({ attack: { id: 'attack-1', weapon: 'blackpowder_bomb', due_at: new Date(Date.now() + 40_000).toISOString() } })
    useGameStore.setState({
      selectedMonsterId: 'monster-1',
      monsters: [{ id: 'monster-1', type: 'roaming_melee', state: 'wandering', tile: { x: 2, y: 3 }, targetId: '', targetType: '', health: 360, maxHealth: 360, damage: 18, aggroRadius: 5, updatedAt: 0 }],
    })
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false, staleTime: Infinity } } })
    queryClient.setQueryData(['economy', 'inventory'], { inventory: { player_id: 'player-1', items: [{ resource: 'throwing_knives', amount: 2 }, { resource: 'blackpowder_bomb', amount: 1 }], coin_capacity: 2000, updated_at: new Date().toISOString() } })
    render(<QueryClientProvider client={queryClient}><Inspector /></QueryClientProvider>)

    fireEvent.click(screen.getByRole('button', { name: 'Выбрать оружие' }))
    const menu = screen.getByRole('dialog', { name: 'Оружие против монстра' })
    expect(menu.querySelector('img[src*="throwing_knives.webp"]')).toBeTruthy()
    expect(menu.querySelector('img[src*="blackpowder_bomb.webp"]')).toBeTruthy()
    expect(screen.getByText('мгновенно')).toBeTruthy()
    expect(screen.getByText('через 40 с')).toBeTruthy()
    fireEvent.click(screen.getByRole('radio', { name: /Пороховая бомба/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Применить оружие' }))
    await waitFor(() => expect(useWeaponOnMonster).toHaveBeenCalledWith('monster-1', 'blackpowder_bomb'))
  })

  it('shows a queued bomb after loading the inspector again', async () => {
    const dueAt = new Date(Date.now() + 40_000).toISOString()
    vi.mocked(listPendingWeaponAttacks).mockResolvedValue({ attacks: [{ id: 'attack-1', monster_id: 'monster-1', weapon: 'blackpowder_bomb', due_at: dueAt }] })
    useGameStore.setState({
      selectedMonsterId: 'monster-1',
      constructionNow: Date.now(),
      monsters: [{
        id: 'monster-1', type: 'roaming_melee', state: 'wandering', tile: { x: 2, y: 3 },
        targetId: '', targetType: '', health: 360, maxHealth: 360,
        damage: 18, aggroRadius: 5, updatedAt: 0,
      }],
    })
    renderWithClient(<Inspector />)
    fireEvent.click(screen.getByRole('tab', { name: 'Объект' }))
    await waitFor(() => expect(screen.getByText(/До срабатывания — Пороховая бомба:/)).toBeTruthy())
  })

  it('names the selected ruin variant', () => {
    useGameStore.setState({
      worldTiles: [{ x: 2, y: 3, chunk_x: 0, chunk_y: 0, terrain: 'ruins', ruin_type: 'ruins_archive', elevation: 0, safe_zone: false, forest_density: 0 }],
    })
    renderWithClient(<Inspector />)

    expect(screen.getByText('Архив чертежей')).toBeTruthy()
  })

  it('requires confirmation and removes a building from both map and query cache only after success', async () => {
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
          demolitionRefundCoins: 20,
          owner: 'player-1',
          startedAt: 1000,
          completesAt: null,
        },
      ],
      selectedBuildingId: 'town-hall-test',
    })

    let finishDelete: ((result: { status: string }) => void) | undefined
    vi.mocked(deleteBuildingRequest).mockImplementation(() => new Promise((resolve) => { finishDelete = resolve }))
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
    queryClient.setQueryData(['buildings'], { buildings: [{ id: 'town-hall-test' } as BuildingResponse] })
    render(<QueryClientProvider client={queryClient}><Inspector /></QueryClientProvider>)
    expect(screen.getByText('Ратуша, уровень 1')).toBeTruthy()

    fireEvent.click(screen.getByLabelText('Удалить'))
    expect(screen.getByRole('dialog', { name: 'Подтвердите снос' })).toBeTruthy()
    expect(screen.getByText(/Возврат: 20 монет/)).toBeTruthy()
    expect(useGameStore.getState().buildings).toHaveLength(1)
    fireEvent.click(screen.getByText('Отмена'))
    expect(deleteBuildingRequest).not.toHaveBeenCalled()

    fireEvent.click(screen.getByLabelText('Удалить'))
    fireEvent.click(screen.getByText('Удалить постройку'))
    await waitFor(() => expect(vi.mocked(deleteBuildingRequest).mock.calls[0]?.[0]).toBe('town-hall-test'))
    expect(useGameStore.getState().buildings).toHaveLength(1)
    expect(queryClient.getQueryData<{ buildings: BuildingResponse[] }>(['buildings'])?.buildings).toHaveLength(1)

    finishDelete?.({ status: 'ok' })
    await waitFor(() => expect(useGameStore.getState().buildings).toHaveLength(0))
    expect(queryClient.getQueryData<{ buildings: BuildingResponse[] }>(['buildings'])?.buildings).toHaveLength(0)
  })

  it('keeps the building and shows the server error when demolition fails', async () => {
    vi.mocked(deleteBuildingRequest).mockRejectedValue(new Error('Снос недоступен'))
    useGameStore.setState({
      buildings: [{
        id: 'dugout-test', kind: 'dugout', name: 'Землянка', level: 1,
        tile: { x: 2, y: 3 }, status: 'active', health: 35,
        owner: 'player-1', startedAt: 1000, completesAt: null,
      }],
      selectedBuildingId: 'dugout-test',
    })
    renderWithClient(<Inspector />)

    fireEvent.click(screen.getByLabelText('Удалить'))
    fireEvent.click(screen.getByText('Удалить постройку'))

    expect(await screen.findByRole('alert')).toHaveProperty('textContent', 'Снос недоступен')
    expect(useGameStore.getState().buildings).toHaveLength(1)
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

  it('closes the confirmation when its target disappears instead of acting on another object', () => {
    useGameStore.setState({ buildings: [{ id: 'gone-target', kind: 'dugout', name: 'Землянка', level: 1, tile: { x: 2, y: 3 }, status: 'active', health: 35, owner: 'player-1', startedAt: 1000, completesAt: null }], selectedBuildingId: 'gone-target' })
    renderWithClient(<Inspector />)
    fireEvent.click(screen.getByLabelText('Улучшить'))
    expect(screen.getByRole('dialog', { name: 'Улучшение постройки' })).toBeTruthy()
    act(() => useGameStore.setState({ buildings: [] }))
    expect(screen.queryByRole('dialog', { name: 'Улучшение постройки' })).toBeNull()
    expect(screen.getByText(/Выбранный объект больше не доступен/)).toBeTruthy()
    expect(patchBuilding).not.toHaveBeenCalled()
  })

  it('offers both exclusive branches after stone house level 6', async () => {
    useGameStore.setState({
      buildings: [{
        id: 'stone-6', kind: 'stone_house', name: 'Каменный дом', level: 6,
        tile: { x: 2, y: 3 }, status: 'active', health: 8700,
        owner: 'player-1', startedAt: 1000, completesAt: null,
      }],
      selectedBuildingId: 'stone-6',
    })
    renderWithClient(<Inspector />)
    fireEvent.click(screen.getByLabelText('Улучшить'))
    expect(screen.getByRole('dialog', { name: 'Выбор ветки улучшения' })).toBeTruthy()
    expect(screen.getByText('Многоквартирный дом')).toBeTruthy()
    expect(screen.getByText('Вилла')).toBeTruthy()
    expect(screen.getByAltText('Модель: Вилла, уровень 1').getAttribute('src')).toContain('villa_l01_active.png')
    fireEvent.click(screen.getByRole('button', { name: 'Улучшить до Вилла' }))
    await waitFor(() => expect(patchBuilding).toHaveBeenCalledWith('stone-6', 'upgrade', 'villa'))
  })

  it('lets the cannon owner enable its garrison', async () => {
    useGameStore.setState({
      selectedBuildingId: 'cannon-1',
      buildings: [{
        id: 'cannon-1', kind: 'defense_cannon', name: 'Пушка', level: 1,
        tile: { x: 2, y: 3 }, status: 'active', state: 'active', health: 260,
        maxHealth: 260, owner: 'player-1', startedAt: 1000, completesAt: null,
        cannonRange: 2, cannonDamage: 55, cannonAmmo: 'stone', cannonEnabled: false,
      }],
    })
    vi.mocked(patchBuilding).mockResolvedValue({ building: {
      id: 'cannon-1', owner_id: 'player-1', type: 'defense_cannon', name: 'Пушка', level: 1,
      state: 'active', health: 260, tile_x: 2, tile_y: 3,
      started_at: '2026-10-17T12:00:00Z', completes_at: null,
      cannon_enabled: true, cannon_range: 2, cannon_damage: 55, cannon_ammo: 'stone',
    } })
    renderWithClient(<Inspector />)
    fireEvent.click(screen.getByRole('tab', { name: 'Объект' }))
    expect(screen.getByText('Радиус: 2 кл. · Урон: 55')).toBeTruthy()
    fireEvent.click(screen.getByLabelText('Включить пушку'))
    await waitFor(() => expect(patchBuilding).toHaveBeenCalledWith('cannon-1', 'enable_cannon'))
    await waitFor(() => expect(screen.getByLabelText('Выключить пушку')).toBeTruthy())
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
    expect(screen.getByAltText('Модель: Ратуша, уровень 2').getAttribute('src')).toBe(`/assets/buildings/center/town_hall/town_hall_l02_active.png?v=${TOWN_HALL_ASSET_REVISION}`)
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

  it('shows the owner name and level without management actions', async () => {
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
    expect(await screen.findByText(/Игрок Севера/)).toBeTruthy()
    expect(screen.getByText(/Игрок Севера/).textContent).toContain('7')
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
      level_start_xp: 0,
      next_level_xp: 100,
      settings: {
        notifications: { attack_alerts: true, production_ready: true, market_updates: true },
        render_quality: 'medium',
      },
      updated_at: '2026-09-20T00:00:00Z',
    },
    created_at: '2026-09-20T00:00:00Z',
    updated_at: '2026-09-20T00:00:00Z',
  }
}
