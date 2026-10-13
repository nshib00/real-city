import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactElement } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { ProductionRecipeResponse } from '../shared/api/economy'
import { startProduction } from '../shared/api/economy'
import { chopForest } from '../shared/api/world'
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
  getChunks: vi.fn(async () => ({ chunks: [] })),
  chopForest: vi.fn(),
}))

vi.mock('./renderer/PixiStage', () => ({
  PixiStage: (props: {
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
    vi.mocked(chopForest).mockReturnValue(new Promise(() => undefined))
    renderWithClient(<IsoMap />)
    act(() => {
      useGameStore.setState({
        worldTiles: [
          { x: 1, y: 1, chunk_x: 0, chunk_y: 0, terrain: 'forest', elevation: 0, safe_zone: false, forest_density: 3 },
          { x: 2, y: 1, chunk_x: 0, chunk_y: 0, terrain: 'forest', elevation: 0, safe_zone: false, forest_density: 3 },
        ],
      })
    })

    fireEvent.click(screen.getByTestId('pixi-forest-a'))
    expect(useGameStore.getState().worldTiles.find((tile) => tile.x === 1 && tile.y === 1)?.forest_density).toBe(2)
    fireEvent.click(screen.getByTestId('pixi-forest-b'))
    fireEvent.click(screen.getByTestId('pixi-forest-a'))

    await waitFor(() => expect(chopForest).toHaveBeenCalledTimes(2))
    expect(vi.mocked(chopForest).mock.calls.map(([tile]) => tile)).toEqual(expect.arrayContaining([{ x: 1, y: 1 }, { x: 2, y: 1 }]))
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

function renderWithClient(ui: ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
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
