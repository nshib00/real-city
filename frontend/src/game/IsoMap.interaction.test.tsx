import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactElement } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { ProductionRecipeResponse } from '../shared/api/economy'
import { startProduction } from '../shared/api/economy'
import { chopForest, getChunks } from '../shared/api/world'
import type { WorldTile } from '../shared/contracts'
import { useAuthStore } from '../features/auth/useAuthStore'
import type { Player } from '../features/auth/types'
import { useGameStore } from './state/useGameStore'
import type { PlacedBuilding } from './state/useGameStore'
import { IsoMap } from './IsoMap'

const economyMocks = vi.hoisted(() => ({
  startProduction: vi.fn(),
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

vi.mock('./renderer/PixiStage', () => ({
  PixiStage: (props: {
    tiles?: { x: number; y: number }[]
    buildings?: { id: string; name: string }[]
    resources?: { id: string; resource: string }[]
    monsters?: { id: string; type: string }[]
    occupiedTiles?: Set<string>
    selectedBuildingId?: string | null
    selectedMonsterId?: string | null
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
      worldTiles: [],
      constructionNow: Date.parse('2026-09-29T10:00:00Z'),
      camera: { x: 0, y: 0, zoom: 1 },
      viewport: { center: { x: 0, y: 0 }, radius: 1 },
    })
  })

  it('starts lumber yard production when the workers badge is clicked', async () => {
    renderWithClient(<IsoMap />)

    fireEvent.click(await screen.findByText('3'))

    await waitFor(() => {
      expect(startProduction).toHaveBeenCalled()
      expect(vi.mocked(startProduction).mock.calls[0][0]).toEqual({
        building_id: 'lumber-yard-1',
        recipe_id: 'planks_from_wood',
      })
    })
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
          testBuilding({ id: 'warehouse-1', kind: 'warehouse', name: 'Склад', tile: { x: 1, y: 1 } }),
        ],
      })
    })

    renderWithClient(<IsoMap />)

    expect(pixiMocks.latestProps?.buildings?.map((building) => building.id)).toEqual(['coin-storage-1', 'warehouse-1'])
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
      next_level_xp: 100,
      settings: {
        notifications: { raid_alerts: true, production_ready: true, market_updates: true },
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
