import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactElement } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { ProductionRecipeResponse } from '../shared/api/economy'
import { listProductionRecipes, startProduction } from '../shared/api/economy'
import { claimMonsterLoot, listMonsterLoot } from '../shared/api/monsters'
import { listNearbyPlayers } from '../shared/api/playerPresence'
import { chopForest, getChunks } from '../shared/api/world'
import { relocateBuilding } from '../shared/api/buildings'
import type { WorldTile } from '../shared/contracts'
import { useAuthStore } from '../features/auth/useAuthStore'
import { applyRealtimeEvent } from '../features/world/realtime'
import type { Player } from '../features/auth/types'
import { useGameStore } from './state/useGameStore'
import type { PlacedBuilding } from './state/useGameStore'
import { IsoMap } from './IsoMap'

const economyMocks = vi.hoisted(() => ({
  startProduction: vi.fn(),
}))

vi.mock('../shared/api/monsters', async () => {
  const actual = await vi.importActual<typeof import('../shared/api/monsters')>('../shared/api/monsters')
  return {
    ...actual,
    listMonsterLoot: vi.fn(async () => ({ loot: [] })),
    claimMonsterLoot: vi.fn(),
  }
})

vi.mock('../shared/api/playerPresence', () => ({
  listNearbyPlayers: vi.fn(async () => ({ players: [] })),
  updatePlayerPresence: vi.fn(async () => ({ status: 'ok' })),
}))

const pixiMocks = vi.hoisted(() => ({
  latestProps: undefined as {
    tiles?: { x: number; y: number }[]
    buildings?: { id: string; name: string }[]
    resources?: { id: string; resource: string }[]
    monsters?: { id: string; type: string }[]
    occupiedTiles?: Set<string>
    selectedBuildingId?: string | null
    selectedMonsterId?: string | null
    targetTileOnly?: boolean
  } | undefined,
}))

vi.mock('../shared/api/economy', async () => {
  const actual = await vi.importActual<typeof import('../shared/api/economy')>('../shared/api/economy')
  return {
    ...actual,
    listProductionRecipes: vi.fn(async () => ({ recipes: [lumberRecipe()] })),
    listProductionJobs: vi.fn(async () => ({ jobs: [] })),
    startProduction: economyMocks.startProduction,
  }
})

vi.mock('../shared/api/world', () => ({
  getChunks: vi.fn(),
  chopForest: vi.fn(),
}))

vi.mock('../shared/api/buildings', async () => {
  const actual = await vi.importActual<typeof import('../shared/api/buildings')>('../shared/api/buildings')
  return { ...actual, relocateBuilding: vi.fn() }
})

vi.mock('./renderer/PixiStage', () => ({
  PixiStage: (props: {
    tiles?: { x: number; y: number }[]
    buildings?: { id: string; name: string }[]
    resources?: { id: string; resource: string }[]
    monsters?: { id: string; type: string }[]
    occupiedTiles?: Set<string>
    selectedBuildingId?: string | null
    selectedMonsterId?: string | null
    targetTileOnly?: boolean
    onSelectTile: (tile: { x: number; y: number }) => void
    onSelectBuilding?: (building: { id: string; name: string }) => void
    onSelectMonster?: (monster: { id: string; type: string }) => void
  }) => {
    pixiMocks.latestProps = props
    return (
      <div data-testid="pixi-stage">
        <button type="button" data-testid="pixi-forest-a" onClick={() => props.onSelectTile({ x: 1, y: 1 })} />
        <button type="button" data-testid="pixi-forest-b" onClick={() => props.onSelectTile({ x: 2, y: 1 })} />
        <button type="button" data-testid="pixi-forest-negative" onClick={() => props.onSelectTile({ x: -1, y: 1 })} />
        {props.buildings?.map((building) => (
          <button
            key={building.id}
            type="button"
            data-testid={`pixi-building-${building.id}`}
            onClick={() => props.onSelectBuilding?.(building)}
          />
        ))}
        {props.resources?.map((resource) => (
          <button
            key={resource.id}
            type="button"
            data-testid={`pixi-resource-${resource.id}`}
            onClick={() => props.onSelectTile({ x: 2, y: 2 })}
          />
        ))}
        {props.monsters?.map((monster) => (
          <button
            key={monster.id}
            type="button"
            data-testid={`pixi-monster-${monster.id}`}
            onClick={() => props.onSelectMonster?.(monster)}
          />
        ))}
      </div>
    )
  },
}))

describe('IsoMap production interactions', () => {
  beforeEach(() => {
    window.history.replaceState(null, '', '/')
    pixiMocks.latestProps = undefined
    vi.mocked(getChunks).mockReset()
    vi.mocked(getChunks).mockResolvedValue({ chunks: [] })
    vi.mocked(chopForest).mockReset()
    vi.mocked(relocateBuilding).mockReset()
    vi.mocked(listMonsterLoot).mockReset()
    vi.mocked(listMonsterLoot).mockResolvedValue({ loot: [] })
    vi.mocked(claimMonsterLoot).mockReset()
    vi.mocked(listNearbyPlayers).mockReset()
    vi.mocked(listNearbyPlayers).mockResolvedValue({ players: [] })
    economyMocks.startProduction.mockResolvedValue({
      job: {
        id: 'job-1',
        building_id: 'lumber-yard-1',
        recipe_id: 'planks_from_wood',
        state: 'running',
        started_at: '2026-09-29T10:00:00Z',
        completes_at: '2026-09-29T10:05:00Z',
      },
      inventory: {
        player_id: 'player-1',
        items: [],
        coin_capacity: 2000,
        updated_at: '2026-09-29T10:00:00Z',
      },
    })
    useAuthStore.setState({ player: testPlayer('player-1'), isAuthenticated: true })
    useGameStore.setState({
      selectedTile: null,
      selectedBuildingId: null,
      selectedMonsterId: null,
      hoveredTile: null,
      placementPreviewKind: null,
      relocatingBuildingId: null,
      buildings: [
        {
          id: 'lumber-yard-1',
          kind: 'lumber_yard',
          name: 'Лесопильный двор',
          level: 1,
          tile: { x: 0, y: 0 },
          status: 'active',
          health: 100,
          owner: 'player-1',
          startedAt: 0,
          completesAt: null,
        },
      ],
      resourceNodes: [],
      monsters: [],
      buildingDamageEvents: [],
      worldTiles: [],
      uiPreferences: { ...useGameStore.getState().uiPreferences, buildMenuOpen: false },
      constructionNow: Date.parse('2026-09-29T10:00:00Z'),
      camera: { x: 0, y: 0, zoom: 1 },
      viewport: { center: { x: 0, y: 0 }, radius: 1 },
    })
  })

  it('pans and zooms without dragging and keeps the selected object', () => {
    useGameStore.setState({ selectedBuildingId: 'lumber-yard-1' })
    renderWithClient(<IsoMap />)
    fireEvent.keyDown(screen.getByLabelText('Карта', { exact: true }), { key: 'ArrowRight' })
    expect(useGameStore.getState().camera.x).toBe(-64)
    fireEvent.click(screen.getByRole('button', { name: 'Карта влево' }))
    expect(useGameStore.getState().camera.x).toBe(0)
    fireEvent.click(screen.getByRole('button', { name: 'Увеличить карту' }))
    expect(useGameStore.getState().camera.zoom).toBeCloseTo(1.1)
    expect(useGameStore.getState().selectedBuildingId).toBe('lumber-yard-1')
  })

  it('suppresses an action click after a two-finger gesture', () => {
    renderWithClient(<IsoMap />)
    const tile = screen.getByTestId('pixi-forest-a')
    const stage = screen.getByLabelText('Карта', { exact: true })
    const pointer = (name: string, id: number, primary: boolean) => {
      const event = new Event(name, { bubbles: true })
      Object.assign(event, { pointerId: id, pointerType: 'touch', isPrimary: primary, clientX: 10, clientY: 10 })
      fireEvent(stage, event)
    }
    pointer('pointerdown', 1, true)
    pointer('pointerdown', 2, false)
    pointer('pointerup', 1, true)
    pointer('pointerup', 2, false)
    fireEvent.click(tile, { detail: 1 })
    expect(chopForest).not.toHaveBeenCalled()
    expect(relocateBuilding).not.toHaveBeenCalled()
    expect(useGameStore.getState().selectedTile).toBeNull()
  })

  it('moves a selected building to a free tile and rejects an occupied tile', async () => {
    vi.mocked(relocateBuilding).mockResolvedValue({ building: {
      id: 'lumber-yard-1', owner_id: 'player-1', type: 'lumber_yard', name: 'Лесопильный двор',
      level: 1, state: 'active', health: 100, tile_x: 2, tile_y: 1,
      rotation: 0, footprint_w: 1, footprint_h: 1,
      started_at: '2026-09-29T10:00:00Z', completes_at: null,
    } })
    useGameStore.setState((state) => ({
      buildings: [...state.buildings, {
        ...state.buildings[0], id: 'blocker', tile: { x: 1, y: 1 }, owner: 'player-2',
      }],
      selectedBuildingId: 'lumber-yard-1',
      relocatingBuildingId: 'lumber-yard-1',
    }))
    renderWithClient(<IsoMap />)

    expect(pixiMocks.latestProps?.targetTileOnly).toBe(true)
    fireEvent.click(screen.getByTestId('pixi-forest-a'))
    expect(relocateBuilding).not.toHaveBeenCalled()
    expect(useGameStore.getState().relocatingBuildingId).toBe('lumber-yard-1')

    fireEvent.click(screen.getByTestId('pixi-forest-b'))
    await waitFor(() => expect(relocateBuilding).toHaveBeenCalledWith('lumber-yard-1', { x: 2, y: 1 }, 0))
    await waitFor(() => expect(useGameStore.getState().buildings.find((item) => item.id === 'lumber-yard-1')?.tile).toEqual({ x: 2, y: 1 }))
    expect(useGameStore.getState().relocatingBuildingId).toBeNull()
  })

  it('cancels building relocation with Escape', () => {
    useGameStore.setState({ selectedBuildingId: 'lumber-yard-1', relocatingBuildingId: 'lumber-yard-1' })
    renderWithClient(<IsoMap />)

    fireEvent.keyDown(window, { key: 'Escape' })

    expect(useGameStore.getState().relocatingBuildingId).toBeNull()
    expect(pixiMocks.latestProps?.targetTileOnly).toBe(false)
  })

  it('rotates the relocation footprint before sending the move', async () => {
    vi.mocked(relocateBuilding).mockResolvedValue({ building: {
      id: 'lumber-yard-1', owner_id: 'player-1', type: 'lumber_yard', name: 'Лесопильный двор',
      level: 1, state: 'active', health: 100, tile_x: 2, tile_y: 1,
      rotation: 1, footprint_w: 1, footprint_h: 2,
      started_at: '2026-09-29T10:00:00Z', completes_at: null,
    } })
    useGameStore.setState((state) => ({
      buildings: [{ ...state.buildings[0], footprintW: 2, footprintH: 1 }],
      selectedBuildingId: 'lumber-yard-1', relocatingBuildingId: 'lumber-yard-1',
    }))
    renderWithClient(<IsoMap />)

    fireEvent.click(screen.getByRole('button', { name: 'Повернуть (R): 0°' }))
    fireEvent.click(screen.getByTestId('pixi-forest-b'))

    await waitFor(() => expect(relocateBuilding).toHaveBeenCalledWith('lumber-yard-1', { x: 2, y: 1 }, 1))
    await waitFor(() => expect(useGameStore.getState().buildings[0].footprintH).toBe(2))
  })

  it('renders a nearby player with their nickname and level', async () => {
    vi.mocked(listNearbyPlayers).mockResolvedValue({
      players: [{ player_id: 'player-2', name: 'Аэрон', level: 4, tile_x: 1, tile_y: 1 }],
    })

    renderWithClient(<IsoMap />)

    expect(await screen.findByText('Аэрон')).toBeTruthy()
    expect(screen.getByTitle('Уровень 4').textContent).toContain('4')
  })

  it('moves a nearby balloon when another player changes tile', async () => {
    vi.mocked(listNearbyPlayers).mockResolvedValue({
      players: [{ player_id: 'player-2', name: 'Аэрон', level: 4, tile_x: 1, tile_y: 1 }],
    })
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    renderWithClient(<IsoMap />, queryClient)
    const balloon = await screen.findByRole('button', { name: 'Аэрон, уровень 4' })
    const before = balloon.style.transform
    const state = useGameStore.getState()

    act(() => applyRealtimeEvent({
      type: 'presence.moved', event_id: 'move-1', seq: 1, sent_at: '2026-10-25T00:00:00Z', payload_version: 1,
      payload: { player: { player_id: 'player-2', name: 'Аэрон', level: 4, tile_x: 2, tile_y: 1 } },
    }, {
      queryClient, updateWorldTile: state.updateWorldTile, addBuilding: state.addBuilding,
      deleteBuilding: state.deleteBuilding, upsertResourceNode: state.upsertResourceNode, upsertMonster: state.upsertMonster,
    }))

    await waitFor(() => expect(balloon.style.transform).not.toBe(before))
    expect(listNearbyPlayers).toHaveBeenCalledTimes(1)
  })

  it('starts lumber yard production when the workers badge is clicked', async () => {
    renderWithClient(<IsoMap />)

    const workersBadge = (await screen.findByText('3')).closest('.building-work-badge-workers')
    expect(workersBadge?.querySelector('.resource-icon-population')).toBeTruthy()
    expect(workersBadge?.querySelector('.building-work-badge-input')?.textContent).toBe('10')
    expect(workersBadge?.querySelector('.resource-icon-wood')?.getAttribute('aria-label')).toBe('Древесина')
    fireEvent.click(workersBadge!)

    await waitFor(() => {
      expect(startProduction).toHaveBeenCalled()
      expect(vi.mocked(startProduction).mock.calls[0][0]).toEqual({
        building_id: 'lumber-yard-1',
        recipe_id: 'planks_from_wood',
      })
    })
  })

  it('shows the upgraded sawmill inputs instead of the level-one recipe', async () => {
    vi.mocked(listProductionRecipes).mockResolvedValueOnce({
      recipes: [
        lumberRecipe(),
        {
          ...lumberRecipe(),
          required_level: 4,
          duration_sec: 1395,
          workers: 4,
          input: [{ resource: 'wood', amount: 24 }, { resource: 'fuel', amount: 5 }],
          output: [{ resource: 'planks', amount: 11 }],
          rare_output: [{ resource: 'premium_planks', amount: 1, chance: 0.01 }],
        },
      ],
    })
    useGameStore.setState({ buildings: [{ ...useGameStore.getState().buildings[0], level: 4 }] })

    renderWithClient(<IsoMap />)

    const workersBadge = (await screen.findByText('4')).closest('.building-work-badge-workers')
    expect(workersBadge?.querySelector('.resource-icon-fuel')).toBeTruthy()
    expect(workersBadge?.textContent).toContain('24')
    expect(workersBadge?.textContent).toContain('5')
  })

  it('shows public monster loot and lets the player claim it', async () => {
    const loot = { id: 'loot-1', monster_id: 'monster-1', tile_x: 1, tile_y: 1, items: [{ resource: 'wood', amount: 25 }], created_at: '2026-09-29T10:00:00Z' }
    vi.mocked(listMonsterLoot).mockResolvedValueOnce({ loot: [loot] })
    vi.mocked(claimMonsterLoot).mockResolvedValue({ loot, inventory: { player_id: 'player-1', items: loot.items, coin_capacity: 2000, updated_at: '2026-09-29T10:00:00Z' } })

    renderWithClient(<IsoMap />)

    fireEvent.click(await screen.findByRole('button', { name: 'Собрать добычу: 25 Древесина' }))
    await waitFor(() => expect(vi.mocked(claimMonsterLoot).mock.calls[0]?.[0]).toBe('loot-1'))
    await waitFor(() => expect(screen.queryByRole('button', { name: 'Собрать добычу: 25 Древесина' })).toBeNull())
  })

  it('shows a newly dropped reward without waiting for the next loot poll', async () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    renderWithClient(<IsoMap />, queryClient)
    await waitFor(() => expect(queryClient.getQueryData<{ loot: unknown[] }>(['monster-loot', 16, 16, 1])).toEqual({ loot: [] }))

    act(() => {
      queryClient.setQueriesData<{ loot: { id: string; monster_id: string; tile_x: number; tile_y: number; items: { resource: string; amount: number }[]; created_at: string }[] }>(
        { queryKey: ['monster-loot'] },
        (current) => current ? { loot: [...current.loot, { id: 'new-loot', monster_id: 'monster-1', tile_x: 1, tile_y: 1, items: [{ resource: 'wood', amount: 25 }], created_at: '2026-09-29T10:00:00Z' }] } : current,
      )
    })

    expect(await screen.findByRole('button', { name: 'Собрать добычу: 25 Древесина' })).toBeTruthy()
  })

  it('opens a foreign building without starting production', async () => {
    vi.mocked(startProduction).mockClear()
    act(() => {
      useGameStore.setState({
        buildings: [{ ...useGameStore.getState().buildings[0], id: 'foreign-yard', owner: 'player-2' }],
      })
    })

    renderWithClient(<IsoMap />)
    fireEvent.click(screen.getByTestId('pixi-building-foreign-yard'))

    await waitFor(() => expect(useGameStore.getState().selectedBuildingId).toBe('foreign-yard'))
    expect(startProduction).not.toHaveBeenCalled()
  })

  it('opens construction when an unbuilt oil well tile is clicked', async () => {
    vi.mocked(getChunks).mockResolvedValue({ chunks: [testChunk([
      { x: 2, y: 1, chunk_x: 0, chunk_y: 0, terrain: 'oil_well', elevation: 0, safe_zone: false, forest_density: 0 },
    ])] })
    renderWithClient(<IsoMap />)
    await waitFor(() => expect(pixiMocks.latestProps?.tiles).toHaveLength(1))

    fireEvent.click(screen.getByTestId('pixi-forest-b'))

    expect(useGameStore.getState().selectedTile).toEqual({ x: 2, y: 1 })
    expect(useGameStore.getState().uiPreferences.buildMenuOpen).toBe(true)
    expect(chopForest).not.toHaveBeenCalled()
  })

  it('keeps the current map visible while the next district is loading', async () => {
    const firstTile: WorldTile = { x: 1, y: 1, chunk_x: 0, chunk_y: 0, terrain: 'grass', elevation: 0, safe_zone: false, forest_density: 0 }
    const nextTile: WorldTile = { x: 33, y: 1, chunk_x: 1, chunk_y: 0, terrain: 'forest', elevation: 0, safe_zone: false, forest_density: 2 }
    let resolveNext!: (response: { chunks: ReturnType<typeof testChunk>[] }) => void
    vi.mocked(getChunks)
      .mockResolvedValueOnce({ chunks: [testChunk([firstTile])] })
      .mockImplementationOnce(() => new Promise((resolve) => { resolveNext = resolve }))

    const exampleBuilding = useGameStore.getState().buildings[0]
    useGameStore.setState({ buildings: [
      { ...exampleBuilding, id: 'left-building', tile: { x: 31, y: 1 } },
      { ...exampleBuilding, id: 'right-building', tile: { x: 33, y: 1 } },
    ] })
    renderWithClient(<IsoMap />)
    await waitFor(() => expect(pixiMocks.latestProps?.tiles).toEqual([firstTile]))

    act(() => useGameStore.getState().setViewportCenter({ x: 32, y: 0 }))
    await waitFor(() => expect(getChunks).toHaveBeenCalledTimes(2))
    expect(pixiMocks.latestProps?.tiles).toEqual([firstTile])

    await act(async () => resolveNext({ chunks: [testChunk([nextTile])] }))
    await waitFor(() => expect(pixiMocks.latestProps?.tiles).toEqual([firstTile, nextTile]))
    expect(useGameStore.getState().worldTiles).toEqual([firstTile, nextTile])
    expect(pixiMocks.latestProps?.buildings?.map((building) => building.id)).toEqual(['left-building', 'right-building'])

    const distantTile: WorldTile = { ...firstTile, x: 129, chunk_x: 4 }
    vi.mocked(getChunks).mockResolvedValue({ chunks: [testChunk([distantTile])] })
    act(() => useGameStore.getState().setViewportCenter({ x: 128, y: 0 }))
    await waitFor(() => expect(pixiMocks.latestProps?.tiles).toEqual([distantTile]))
  })

  it('moves a placement preview without chopping a forest tile', async () => {
    vi.mocked(getChunks).mockResolvedValue({ chunks: [testChunk([
      { x: 2, y: 1, chunk_x: 0, chunk_y: 0, terrain: 'forest', elevation: 0, safe_zone: false, forest_density: 2 },
    ])] })
    useGameStore.setState({ selectedTile: { x: 1, y: 1 }, placementPreviewKind: 'town_hall' })
    renderWithClient(<IsoMap />)
    await waitFor(() => expect(pixiMocks.latestProps?.tiles).toHaveLength(1))

    expect(document.querySelector('.map-placement-preview img')).toBeTruthy()
    fireEvent.click(screen.getByTestId('pixi-forest-b'))

    expect(useGameStore.getState().selectedTile).toEqual({ x: 2, y: 1 })
    expect(chopForest).not.toHaveBeenCalled()
    expect(useGameStore.getState().placementPreviewKind).toBe('town_hall')
  })

  it('passes visible buildings to the Pixi object layer and keeps overlay controls in DOM', async () => {
    renderWithClient(<IsoMap />)

    expect(await screen.findByText('3')).toBeTruthy()
    expect(screen.getByText('fps 0.0')).toBeTruthy()
    expect(pixiMocks.latestProps?.buildings?.map((building) => building.id)).toEqual(['lumber-yard-1'])
    expect(screen.getByLabelText('Лесопильный двор').className).toContain('map-building-overlay-anchor')
  })

  it('passes unsupported building kinds to Pixi procedural fallback instead of DOM', async () => {
    act(() => {
      useGameStore.setState({
        buildings: [
          testBuilding({ id: 'coin-storage-1', kind: 'coin_storage', name: 'Монетный склад', tile: { x: 0, y: 1 } }),
          testBuilding({ id: 'mint-1', kind: 'mint', name: 'Монетный двор', tile: { x: 1, y: 1 } }),
        ],
      })
    })

    renderWithClient(<IsoMap />)

    expect(pixiMocks.latestProps?.buildings?.map((building) => building.id)).toEqual(['coin-storage-1', 'mint-1'])
    expect(pixiMocks.latestProps?.occupiedTiles?.has('0:1')).toBe(true)
    expect(pixiMocks.latestProps?.occupiedTiles?.has('1:1')).toBe(true)
    expect(screen.queryByLabelText('Склад')).toBeNull()
  })

  it('starts lumber yard production when a Pixi building hit area is clicked', async () => {
    renderWithClient(<IsoMap />)

    await screen.findByText('3')
    fireEvent.click(screen.getByTestId('pixi-building-lumber-yard-1'))

    await waitFor(() => {
      expect(startProduction).toHaveBeenCalled()
      expect(vi.mocked(startProduction).mock.calls[0][0]).toEqual({
        building_id: 'lumber-yard-1',
        recipe_id: 'planks_from_wood',
      })
    })
  })

  it('starts chopping each clicked forest tile even while another chop is pending', async () => {
    vi.mocked(getChunks).mockResolvedValue({ chunks: [testChunk([
      { x: 1, y: 1, chunk_x: 0, chunk_y: 0, terrain: 'forest', elevation: 0, safe_zone: false, forest_density: 3 },
      { x: 2, y: 1, chunk_x: 0, chunk_y: 0, terrain: 'forest', elevation: 0, safe_zone: false, forest_density: 3 },
    ])] })
    vi.mocked(chopForest).mockReturnValue(new Promise(() => undefined))
    renderWithClient(<IsoMap />)
    await waitFor(() => expect(pixiMocks.latestProps?.tiles).toHaveLength(2))

    fireEvent.click(screen.getByTestId('pixi-forest-a'))
    expect(useGameStore.getState().worldTiles.find((tile) => tile.x === 1 && tile.y === 1)?.forest_density).toBe(2)
    fireEvent.click(screen.getByTestId('pixi-forest-b'))
    fireEvent.click(screen.getByTestId('pixi-forest-a'))

    await waitFor(() => expect(chopForest).toHaveBeenCalledTimes(2))
    expect(vi.mocked(chopForest).mock.calls.map(([tile]) => tile)).toEqual(expect.arrayContaining([{ x: 1, y: 1 }, { x: 2, y: 1 }]))
  })

  it('does not restore a recently chopped tile from stale chunk data when chopping the next tile', async () => {
    const firstTile: WorldTile = { x: 1, y: 1, chunk_x: 0, chunk_y: 0, terrain: 'forest', elevation: 0, safe_zone: false, forest_density: 3 }
    const secondTile: WorldTile = { x: 2, y: 1, chunk_x: 0, chunk_y: 0, terrain: 'forest', elevation: 0, safe_zone: false, forest_density: 3 }
    const staleChunks = { chunks: [testChunk([firstTile, secondTile])] }
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
    vi.mocked(getChunks).mockResolvedValue(staleChunks)
    vi.mocked(chopForest).mockImplementation(async (tile) => ({
      tile: {
        ...(tile.x === firstTile.x ? firstTile : secondTile),
        forest_density: 2,
      },
      inventory: { player_id: 'player-1', items: [], coin_capacity: 2000, updated_at: '2026-09-29T10:00:00Z' },
    }))
    renderWithClient(<IsoMap />, queryClient)
    await waitFor(() => expect(pixiMocks.latestProps?.tiles).toHaveLength(2))

    fireEvent.click(screen.getByTestId('pixi-forest-a'))
    await waitFor(() => {
      expect(useGameStore.getState().worldTiles.find((tile) => tile.x === 1 && tile.y === 1)?.forest_density).toBe(2)
    })

    act(() => {
      queryClient.setQueryData(['world', 'chunks', 0, 0, 1], staleChunks)
    })
    fireEvent.click(screen.getByTestId('pixi-forest-b'))

    await waitFor(() => expect(chopForest).toHaveBeenCalledTimes(2))
    expect(useGameStore.getState().worldTiles.find((tile) => tile.x === 1 && tile.y === 1)?.forest_density).toBe(2)
    expect(useGameStore.getState().worldTiles.find((tile) => tile.x === 2 && tile.y === 1)?.forest_density).toBe(2)
  })

  it('does not restore a fully cleared forest tile from stale chunk data after the recent chop window', async () => {
    const nowSpy = vi.spyOn(Date, 'now').mockReturnValue(10_000)
    const firstTile: WorldTile = { x: 1, y: 1, chunk_x: 0, chunk_y: 0, terrain: 'forest', elevation: 0, safe_zone: false, forest_density: 3 }
    const secondTile: WorldTile = { x: 2, y: 1, chunk_x: 0, chunk_y: 0, terrain: 'forest', elevation: 0, safe_zone: false, forest_density: 3 }
    const staleChunks = { chunks: [testChunk([firstTile, secondTile])] }
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
    let firstDensity = firstTile.forest_density
    vi.mocked(getChunks).mockResolvedValue(staleChunks)
    vi.mocked(chopForest).mockImplementation(async (tile) => {
      const source = tile.x === firstTile.x ? firstTile : secondTile
      if (tile.x === firstTile.x) {
        firstDensity -= 1
        return {
          tile: { ...firstTile, terrain: firstDensity <= 0 ? 'grass' : 'forest', forest_density: Math.max(0, firstDensity) },
          inventory: { player_id: 'player-1', items: [], coin_capacity: 2000, updated_at: '2026-09-29T10:00:00Z' },
        }
      }
      return {
        tile: { ...source, forest_density: 2 },
        inventory: { player_id: 'player-1', items: [], coin_capacity: 2000, updated_at: '2026-09-29T10:00:00Z' },
      }
    })
    renderWithClient(<IsoMap />, queryClient)
    await waitFor(() => expect(pixiMocks.latestProps?.tiles).toHaveLength(2))

    fireEvent.click(screen.getByTestId('pixi-forest-a'))
    await waitFor(() => expect(useGameStore.getState().worldTiles.find((tile) => tile.x === 1 && tile.y === 1)?.forest_density).toBe(2))
    fireEvent.click(screen.getByTestId('pixi-forest-a'))
    await waitFor(() => expect(useGameStore.getState().worldTiles.find((tile) => tile.x === 1 && tile.y === 1)?.forest_density).toBe(1))
    fireEvent.click(screen.getByTestId('pixi-forest-a'))
    await waitFor(() => {
      const tile = useGameStore.getState().worldTiles.find((item) => item.x === 1 && item.y === 1)
      expect(tile?.terrain).toBe('grass')
      expect(tile?.forest_density).toBe(0)
    })

    nowSpy.mockReturnValue(21_000)
    act(() => {
      queryClient.setQueryData(['world', 'chunks', 0, 0, 1], staleChunks)
    })
    fireEvent.click(screen.getByTestId('pixi-forest-b'))

    await waitFor(() => expect(chopForest).toHaveBeenCalledTimes(4))
    const first = useGameStore.getState().worldTiles.find((tile) => tile.x === 1 && tile.y === 1)
    const second = useGameStore.getState().worldTiles.find((tile) => tile.x === 2 && tile.y === 1)
    expect(first?.terrain).toBe('grass')
    expect(first?.forest_density).toBe(0)
    expect(second?.forest_density).toBe(2)
    nowSpy.mockRestore()
  })

  it('chops the raw rendered tile coordinate without wrapping it to another cell', async () => {
    vi.mocked(getChunks).mockResolvedValue({ chunks: [testChunk([
      { x: -1, y: 1, chunk_x: -1, chunk_y: 0, terrain: 'forest', elevation: 0, safe_zone: false, forest_density: 3 },
      { x: 159, y: 1, chunk_x: 4, chunk_y: 0, terrain: 'forest', elevation: 0, safe_zone: false, forest_density: 3 },
    ])] })
    vi.mocked(chopForest).mockReturnValue(new Promise(() => undefined))
    renderWithClient(<IsoMap />)
    await waitFor(() => expect(pixiMocks.latestProps?.tiles).toHaveLength(2))

    fireEvent.click(screen.getByTestId('pixi-forest-negative'))

    await waitFor(() => expect(vi.mocked(chopForest).mock.calls.map(([tile]) => tile)).toContainEqual({ x: -1, y: 1 }))
    expect(useGameStore.getState().selectedTile).toEqual({ x: -1, y: 1 })
    expect(useGameStore.getState().worldTiles.find((tile) => tile.x === -1 && tile.y === 1)?.forest_density).toBe(2)
    expect(useGameStore.getState().worldTiles.find((tile) => tile.x === 159 && tile.y === 1)?.forest_density).toBe(3)
  })

  it('passes visible monsters to Pixi and selects them through the object layer', async () => {
    act(() => {
      useGameStore.setState({
        monsters: [
          {
            id: 'monster-1',
            type: 'resource_guardian',
            state: 'aggro',
            tile: { x: 0, y: 0 },
            targetId: '',
            targetType: '',
            health: 35,
            maxHealth: 140,
            damage: 12,
            aggroRadius: 4,
            updatedAt: Date.now(),
          },
        ],
      })
    })

    renderWithClient(<IsoMap />)

    expect(pixiMocks.latestProps?.monsters?.map((monster) => monster.id)).toEqual(['monster-1'])
    fireEvent.click(screen.getByTestId('pixi-monster-monster-1'))

    await waitFor(() => {
      expect(useGameStore.getState().selectedMonsterId).toBe('monster-1')
      expect(pixiMocks.latestProps?.selectedMonsterId).toBe('monster-1')
    })
  })

  it('shows the lost HP above a building after a monster hit', () => {
    renderWithClient(<IsoMap />)

    act(() => {
      useGameStore.getState().recordBuildingDamage({
        id: 'building-hit-1', buildingId: 'lumber-yard-1', tile: { x: 0, y: 0 },
        damage: 23, createdAt: Date.now(),
      })
    })

    const damage = screen.getByText('-23')
    expect(damage.classList.contains('map-damage-number')).toBe(true)
    expect(damage.parentElement?.classList.contains('map-damage-layer')).toBe(true)
    expect(damage.style.left).toBeTruthy()
    expect(damage.style.top).toBeTruthy()
  })

  it('shows the lost HP above a monster after a hit', () => {
    renderWithClient(<IsoMap />)

    act(() => {
      useGameStore.getState().recordMonsterDamage({
        id: 'monster-hit-1', monsterId: 'monster-1', tile: { x: 0, y: 0 },
        damage: 12, createdAt: Date.now(),
      })
    })

    const damage = screen.getByText('-12')
    expect(damage.classList.contains('map-damage-number')).toBe(true)
    expect(damage.parentElement?.classList.contains('map-damage-layer')).toBe(true)
  })

  it('passes visible resource nodes to Pixi instead of rendering DOM resource markers', async () => {
    act(() => {
      useGameStore.setState({
        resourceNodes: [
          {
            id: 'wood-node-1',
            type: 'forest_cache',
            resource: 'wood',
            amount: 40,
            maxAmount: 100,
            state: 'claimed',
            ownerId: 'player-1',
            tile: { x: 0, y: 0 },
            respawnAt: null,
          },
        ],
      })
    })

    renderWithClient(<IsoMap />)

    expect(pixiMocks.latestProps?.resources?.map((resource) => resource.id)).toEqual(['wood-node-1'])
    expect(screen.queryByLabelText('Древесина: 40/100')).toBeNull()
    fireEvent.click(screen.getByTestId('pixi-resource-wood-node-1'))

    await waitFor(() => {
      expect(useGameStore.getState().selectedTile).toEqual({ x: 2, y: 2 })
    })
  })

  it('enables the dev performance scenario from query parameters', async () => {
    window.history.replaceState(null, '', '/?perf=mixed&perfBuildings=24&perfMonsters=8&perfResources=6&perfTileRadius=2')

    renderWithClient(<IsoMap />)

    await waitFor(() => {
      expect(pixiMocks.latestProps?.buildings).toHaveLength(24)
      expect(pixiMocks.latestProps?.monsters).toHaveLength(8)
      expect(pixiMocks.latestProps?.resources).toHaveLength(6)
    })
    expect(screen.getByLabelText('Performance HUD').textContent).toContain('mixed')
    expect(screen.getByText('perf mixed: 24b/6r/8m')).toBeTruthy()
  })
})

function renderWithClient(ui: ReactElement, queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })) {
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>)
}

function lumberRecipe(): ProductionRecipeResponse {
  return {
    id: 'planks_from_wood',
    name: 'Доски',
    building_type: 'lumber_yard',
    required_level: 1,
    duration_sec: 300,
    workers: 3,
    input: [{ resource: 'wood', amount: 10 }],
    output: [{ resource: 'planks', amount: 4 }],
    rare_output: [],
  }
}

function testBuilding(overrides: Partial<PlacedBuilding>): PlacedBuilding {
  return {
    ...baseBuilding(),
    ...overrides,
  }
}

function baseBuilding(): PlacedBuilding {
  return {
    id: 'building-1',
    kind: 'lumber_yard',
    name: 'Постройка',
    level: 1,
    tile: { x: 0, y: 0 },
    status: 'active' as const,
    health: 100,
    maxHealth: 100,
    owner: 'player-1',
    startedAt: 0,
    completesAt: null,
  }
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
      updated_at: '2026-09-29T10:00:00Z',
    },
    created_at: '2026-09-29T10:00:00Z',
    updated_at: '2026-09-29T10:00:00Z',
  }
}

function testChunk(tiles: WorldTile[]) {
  return {
    map_id: 'dev-world',
    chunk_x: tiles[0]?.chunk_x ?? 0,
    chunk_y: tiles[0]?.chunk_y ?? 0,
    version: 1,
    tiles,
  }
}
