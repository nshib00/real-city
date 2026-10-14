import { useEffect, useMemo, useRef, useState } from 'react'
import type { MouseEvent, PointerEvent, ReactNode } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { QueryClient } from '@tanstack/react-query'

import { flattenChunkTiles, useVisibleChunks } from '../features/world/useVisibleChunks'
import { canChopForestTile } from '../features/world/forestActions'
import { gridToScreen, nearestWrappedScreenCoord, roundGridCoord, screenToGrid, TILE_HEIGHT, TILE_WIDTH, tileToChunk, wrapGridCoord } from './coordinates/iso'
import { resolvePerformanceScenarioFromSearch, type PerformanceScenario } from './dev/performanceScenarios'
import { PixiStage } from './renderer/PixiStage'
import { renderPerformanceSnapshot, type RenderPerformanceSnapshot } from './renderer/renderPerformanceMetrics'
import { filterVisibleMapObjects, occupiedTileKeys } from './renderer/visibleObjects'
import { useGameStore } from './state/useGameStore'
import type { PlacedBuilding } from './state/useGameStore'
import type { WorldTile } from '../shared/contracts'
import { chopForest, type ChunksResponse } from '../shared/api/world'
import { toPlacedBuilding } from '../shared/api/buildings'
import { advanceField, harvestField, listProductionJobs, listProductionRecipes, patchProductionJob, startProduction } from '../shared/api/economy'
import type { InventoryItem, ProductionJobResponse, ProductionRecipeResponse } from '../shared/api/economy'
import { useAuthStore } from '../features/auth/useAuthStore'
import { fieldCropSpec } from '../features/fields/fieldGrowth'
import { ResourceIcon } from '../features/resources/ResourceIcon'
import { mapObjectZIndex } from './renderer/depth'

const RECENT_CHOP_TILE_TTL_MS = 10_000

export function IsoMap() {
  const selectedTile = useGameStore((state) => state.selectedTile)
  const hoveredTile = useGameStore((state) => state.hoveredTile)
  const camera = useGameStore((state) => state.camera)
  const viewport = useGameStore((state) => state.viewport)
  const buildings = useGameStore((state) => state.buildings)
  const resourceNodes = useGameStore((state) => state.resourceNodes)
  const monsters = useGameStore((state) => state.monsters)
  const constructionNow = useGameStore((state) => state.constructionNow)
  const selectedBuildingId = useGameStore((state) => state.selectedBuildingId)
  const selectedMonsterId = useGameStore((state) => state.selectedMonsterId)
  const selectTile = useGameStore((state) => state.selectTile)
  const selectBuilding = useGameStore((state) => state.selectBuilding)
  const selectMonster = useGameStore((state) => state.selectMonster)
  const hoverTile = useGameStore((state) => state.hoverTile)
  const worldTiles = useGameStore((state) => state.worldTiles)
  const setWorldTiles = useGameStore((state) => state.setWorldTiles)
  const updateWorldTile = useGameStore((state) => state.updateWorldTile)
  const addBuilding = useGameStore((state) => state.addBuilding)
  const panCamera = useGameStore((state) => state.panCamera)
  const setZoomAt = useGameStore((state) => state.setZoomAt)
  const setViewportCenter = useGameStore((state) => state.setViewportCenter)
  const queryClient = useQueryClient()
  const player = useAuthStore((state) => state.player)
  const mapStageRef = useRef<HTMLElement | null>(null)
  const dragStart = useRef<{ x: number; y: number } | null>(null)
  const pendingDragRef = useRef<{ screen: { x: number; y: number }; grid: { x: number; y: number } } | null>(null)
  const dragFrameRef = useRef<number | null>(null)
  const pendingChopTilesRef = useRef(new Set<string>())
  const optimisticChopTilesRef = useRef(new Map<string, WorldTile>())
  const optimisticChopResultTilesRef = useRef(new Map<string, WorldTile>())
  const recentChopTilesRef = useRef(new Map<string, { tile: WorldTile; expiresAt: number }>())
  const [stageSize, setStageSize] = useState({ width: 0, height: 0 })
  const performanceSnapshot = useRenderPerformanceSnapshot()
  const performanceScenario = useMemo(() => resolvePerformanceScenarioFromSearch(typeof window === 'undefined' ? '' : window.location.search), [])
  const viewportCenterRef = useRef(viewport.center)
  const centerChunk = useMemo(() => tileToChunk(wrapGridCoord(viewport.center)), [viewport.center])
  const visibleChunkRadius = useMemo(() => deriveVisibleChunkRadius(stageSize, camera.zoom), [camera.zoom, stageSize])
  const chunksQuery = useVisibleChunks(centerChunk, visibleChunkRadius)
  const tiles = useMemo(() => flattenChunkTiles(chunksQuery.data?.chunks), [chunksQuery.data?.chunks])
  const renderBuildings = performanceScenario?.buildings ?? buildings
  const renderResourceNodes = performanceScenario?.resources ?? resourceNodes
  const renderMonsters = performanceScenario?.monsters ?? monsters
  const mapTiles = performanceScenario?.tiles ?? (worldTiles.length > 0 ? worldTiles : tiles)
  const mapTilesByKey = useMemo(() => new Map(mapTiles.map((tile) => [tileActionKey(tile), tile])), [mapTiles])
  const visibilityOptions = useMemo(
    () => ({ camera, viewportCenter: viewport.center, viewportSize: stageSize }),
    [camera, stageSize, viewport.center],
  )
  const visibleBuildings = useMemo(() => filterVisibleMapObjects(renderBuildings, visibilityOptions), [renderBuildings, visibilityOptions])
  const buildingOccupiedTiles = useMemo(() => occupiedTileKeys(visibleBuildings), [visibleBuildings])
  const visibleResourceNodes = useMemo(() => filterVisibleMapObjects(renderResourceNodes, visibilityOptions), [renderResourceNodes, visibilityOptions])
  const visibleMonsters = useMemo(() => filterVisibleMapObjects(renderMonsters, visibilityOptions), [renderMonsters, visibilityOptions])
  const recipesQuery = useQuery({ queryKey: ['production', 'recipes'], queryFn: listProductionRecipes, staleTime: 5 * 60_000, gcTime: 30 * 60_000 })
  const jobsQuery = useQuery({ queryKey: ['production', 'jobs'], queryFn: listProductionJobs, refetchInterval: 5000 })
  const recipes = recipesQuery.data?.recipes ?? []
  const productionJobs = jobsQuery.data?.jobs ?? []
  const activeProductionByBuilding = useMemo(() => {
    const result = new Map<string, ProductionJobResponse>()
    for (const job of productionJobs) {
      if (job.state === 'running' || job.state === 'ready') {
        result.set(job.building_id, job)
      }
    }
    return result
  }, [productionJobs])
  const recipeById = useMemo(() => new Map(recipes.map((recipe) => [recipe.id, recipe])), [recipes])
  const chopMutation = useMutation({
    mutationFn: chopForest,
    onSuccess: (result) => {
      rememberRecentChopTile(recentChopTilesRef.current, result.tile)
      updateWorldTile(result.tile)
      patchWorldTileInQueryCache(queryClient, result.tile)
      void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
    },
    onError: (_error, variables) => {
      const key = tileActionKey(variables)
      const previous = optimisticChopTilesRef.current.get(key)
      if (previous) {
        recentChopTilesRef.current.delete(key)
        updateWorldTile(previous)
        patchWorldTileInQueryCache(queryClient, previous)
      }
    },
    onSettled: (_data, _error, variables) => {
      const key = tileActionKey(variables)
      pendingChopTilesRef.current.delete(key)
      optimisticChopTilesRef.current.delete(key)
      optimisticChopResultTilesRef.current.delete(key)
    },
  })
  const advanceFieldMutation = useMutation({
    mutationFn: advanceField,
    onSuccess: (result) => {
      addBuilding(toPlacedBuilding(result.building))
      void queryClient.invalidateQueries({ queryKey: ['buildings'] })
      void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
    },
  })
  const harvestFieldMutation = useMutation({
    mutationFn: harvestField,
    onSuccess: (result) => {
      addBuilding(toPlacedBuilding(result.building))
      void queryClient.invalidateQueries({ queryKey: ['buildings'] })
      void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
    },
  })
  const startProductionMutation = useMutation({
    mutationFn: startProduction,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['production', 'jobs'] })
      void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
    },
  })
  const collectProductionMutation = useMutation({
    mutationFn: (id: string) => patchProductionJob(id, 'complete'),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['production', 'jobs'] })
      void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
    },
  })

  function handleSelectTile(tile: { x: number; y: number }) {
    const worldTile = mapTilesByKey.get(tileActionKey(tile))
    if (worldTile && canChopForestTile(worldTile)) {
      const key = tileActionKey(tile)
      selectTile(tile)
      if (pendingChopTilesRef.current.has(key)) {
        return
      }
      pendingChopTilesRef.current.add(key)
      const optimisticTile: WorldTile = {
        ...worldTile,
        forest_density: Math.max(0, worldTile.forest_density - 1),
        terrain: worldTile.forest_density <= 1 ? 'grass' as const : worldTile.terrain,
      }
      optimisticChopTilesRef.current.set(key, worldTile)
      optimisticChopResultTilesRef.current.set(key, optimisticTile)
      rememberRecentChopTile(recentChopTilesRef.current, optimisticTile)
      updateWorldTile(optimisticTile)
      patchWorldTileInQueryCache(queryClient, optimisticTile)
      chopMutation.mutate({ x: tile.x, y: tile.y })
      return
    }
    selectTile(tile)
  }

  function handleBuildingClick(building: PlacedBuilding) {
    const canManage = Boolean(player && building.owner === player.id && building.status === 'active')
    if (!canManage) {
      selectBuilding(building.id)
      return
    }
    const fieldSpec = fieldCropSpec(building.kind)
    if (fieldSpec) {
      const stage = building.fieldStage ?? building.growthStage ?? building.cropStage ?? 0
      const ready = isFieldStageReady(building, constructionNow)
      const maxStage = building.isSuperCrop || building.superCrop ? fieldSpec.superStages : fieldSpec.stages
      if (ready && stage >= maxStage && !harvestFieldMutation.isPending) {
        harvestFieldMutation.mutate(building.id)
        selectBuilding(building.id)
        return
      }
      if ((stage <= 0 || (ready && stage < maxStage)) && !advanceFieldMutation.isPending) {
        advanceFieldMutation.mutate(building.id)
        selectBuilding(building.id)
        return
      }
    }
    const job = activeProductionByBuilding.get(building.id)
    const recipe = job ? recipeById.get(job.recipe_id) : findRecipeForBuilding(recipes, building)
    if (job && recipe && isProductionReady(job, constructionNow) && !collectProductionMutation.isPending) {
      collectProductionMutation.mutate(job.id)
      selectBuilding(building.id)
      return
    }
    if (!job && recipe && !startProductionMutation.isPending) {
      startProductionMutation.mutate({ building_id: building.id, recipe_id: recipe.id })
      selectBuilding(building.id)
      return
    }
    selectBuilding(building.id)
  }

  function flushDragFrame() {
    if (dragFrameRef.current !== null) {
      cancelAnimationFrame(dragFrameRef.current)
      dragFrameRef.current = null
    }
    const pending = pendingDragRef.current
    pendingDragRef.current = null
    if (!pending) {
      return
    }

    viewportCenterRef.current = wrapGridCoord({
      x: viewportCenterRef.current.x + pending.grid.x,
      y: viewportCenterRef.current.y + pending.grid.y,
    })
    setViewportCenter(roundGridCoord(viewportCenterRef.current))
    panCamera(pending.screen)
  }

  function scheduleDragFrame(delta: { x: number; y: number }) {
    const gridDelta = screenToGrid({ x: -delta.x / camera.zoom, y: -delta.y / camera.zoom })
    pendingDragRef.current = pendingDragRef.current
      ? {
          screen: {
            x: pendingDragRef.current.screen.x + delta.x,
            y: pendingDragRef.current.screen.y + delta.y,
          },
          grid: {
            x: pendingDragRef.current.grid.x + gridDelta.x,
            y: pendingDragRef.current.grid.y + gridDelta.y,
          },
        }
      : { screen: delta, grid: gridDelta }

    if (dragFrameRef.current === null) {
      dragFrameRef.current = requestAnimationFrame(flushDragFrame)
    }
  }

  useEffect(() => {
    if (!dragStart.current) {
      viewportCenterRef.current = viewport.center
    }
  }, [viewport.center])

  useEffect(() => {
    return () => {
      if (dragFrameRef.current !== null) {
        cancelAnimationFrame(dragFrameRef.current)
      }
    }
  }, [])

  useEffect(() => {
    const optimisticTiles = optimisticChopResultTilesRef.current
    const recentChopTiles = recentChopTilesRef.current
    setWorldTiles(mergeTransientWorldTiles(tiles, useGameStore.getState().worldTiles, optimisticTiles, recentChopTiles))
  }, [setWorldTiles, tiles])

  useEffect(() => {
    if (viewport.radius !== visibleChunkRadius) {
      useGameStore.getState().setViewportRadius(visibleChunkRadius)
    }
  }, [viewport.radius, visibleChunkRadius])

  useEffect(() => {
    const element = mapStageRef.current
    if (!element || typeof ResizeObserver === 'undefined') {
      return
    }

    const observer = new ResizeObserver(([entry]) => {
      const width = entry.contentRect.width
      const height = entry.contentRect.height
      setStageSize((current) => (current.width === width && current.height === height ? current : { width, height }))
    })
    observer.observe(element)
    return () => observer.disconnect()
  }, [])

  return (
    <section
      className="map-stage"
      ref={mapStageRef}
      aria-label="Карта"
      onPointerDown={(event) => {
        dragStart.current = { x: event.clientX, y: event.clientY }
      }}
      onPointerMove={(event) => {
        if (!dragStart.current || event.buttons !== 1) {
          return
        }
        const delta = { x: event.clientX - dragStart.current.x, y: event.clientY - dragStart.current.y }
        scheduleDragFrame(delta)
        dragStart.current = { x: event.clientX, y: event.clientY }
      }}
      onPointerUp={() => {
        flushDragFrame()
        dragStart.current = null
      }}
      onPointerCancel={() => {
        flushDragFrame()
        dragStart.current = null
      }}
      onWheel={(event) => {
        event.preventDefault()
        const rect = mapStageRef.current?.getBoundingClientRect()
        setZoomAt({
          zoom: camera.zoom + (event.deltaY > 0 ? -0.08 : 0.08),
          focalScreen: rect ? { x: event.clientX - rect.left, y: event.clientY - rect.top } : undefined,
          viewportSize: stageSize,
        })
      }}
    >
      <PixiStage
        tiles={mapTiles}
        occupiedTiles={buildingOccupiedTiles}
        buildings={visibleBuildings}
        allBuildings={renderBuildings}
        resources={visibleResourceNodes}
        monsters={visibleMonsters}
        camera={camera}
        selectedTile={selectedTile}
        hoveredTile={hoveredTile}
        selectedBuildingId={selectedBuildingId}
        selectedMonsterId={selectedMonsterId}
        onSelectTile={handleSelectTile}
        onHoverTile={hoverTile}
        onSelectBuilding={handleBuildingClick}
        onSelectMonster={(monster) => selectMonster(monster.id)}
      />
      <div
        className="map-origin"
        style={{
          transform: `translate(${camera.x}px, ${camera.y}px) scale(${camera.zoom})`,
        }}
      >
        {visibleBuildings.map((building) => {
          const job = activeProductionByBuilding.get(building.id)
          const recipe = job ? recipeById.get(job.recipe_id) : findRecipeForBuilding(recipes, building)
          const overlay = building.status === 'construction'
            ? null
            : buildingOverlay(building, recipe, job, constructionNow)
          if (!overlay && !(building.status === 'construction' && building.completesAt)) {
            return null
          }
          return (
            <MapObject
              key={`${building.id}:overlay`}
              id={`${building.id}:overlay`}
              x={building.tile.x}
              y={building.tile.y}
              viewportCenter={viewport.center}
              className="map-building-overlay-anchor"
              label={building.name}
              onSelect={() => handleBuildingClick(building)}
            >
              {building.status === 'construction' && building.completesAt ? <span className="construction-timer">{formatRemaining(building.completesAt - constructionNow)}</span> : null}
              {overlay ? <BuildingWorkBadge overlay={overlay} onActivate={() => handleBuildingClick(building)} /> : null}
            </MapObject>
          )
        })}
      </div>
      <div className="map-debug" aria-live="polite">
        {performanceScenario ? <span>{performanceScenarioLabel(performanceScenario)}</span> : null}
        <span>fps {performanceSnapshot.fps.toFixed(1)}</span>
        <span>chunk {centerChunk.x}:{centerChunk.y}</span>
        <span>zoom {camera.zoom.toFixed(2)}</span>
        <span>{chunksQuery.isFetching ? 'loading' : `${tiles.length} tiles`}</span>
      </div>
      {performanceScenario ? (
        <MapPerformanceHud
          scenario={performanceScenario}
          visible={{ buildings: visibleBuildings.length, resources: visibleResourceNodes.length, monsters: visibleMonsters.length }}
        />
      ) : null}
    </section>
  )
}

function deriveVisibleChunkRadius(stageSize: { width: number; height: number }, zoom: number) {
  if (stageSize.width <= 0 || stageSize.height <= 0) {
    return 1
  }
  const visibleTilesX = stageSize.width / Math.max(1, TILE_WIDTH * zoom)
  const visibleTilesY = stageSize.height / Math.max(1, TILE_HEIGHT * zoom)
  const chunkSpan = Math.max(visibleTilesX, visibleTilesY) / 10
  return Math.max(1, Math.min(3, Math.ceil(chunkSpan / 2) + 1))
}

function MapPerformanceHud({
  scenario,
  visible,
}: {
  scenario: PerformanceScenario
  visible: { buildings: number; resources: number; monsters: number }
}) {
  const snapshot = useRenderPerformanceSnapshot()

  return (
    <div className="map-performance-hud" aria-label="Performance HUD">
      <span>{scenario.name}</span>
      <span>fps {snapshot.fps.toFixed(1)}</span>
      <span>obj {visible.buildings}/{visible.resources}/{visible.monsters}</span>
      <span>heap {snapshot.usedHeapMb === null ? 'n/a' : `${snapshot.usedHeapMb} MB`}</span>
      <span>gl {snapshot.activePixiContexts}+{snapshot.activeThreePreviews}</span>
    </div>
  )
}

function useRenderPerformanceSnapshot() {
  const [snapshot, setSnapshot] = useState<RenderPerformanceSnapshot>(() => renderPerformanceSnapshot())

  useEffect(() => {
    const interval = window.setInterval(() => setSnapshot(renderPerformanceSnapshot()), 1000)
    return () => window.clearInterval(interval)
  }, [])

  return snapshot
}

function performanceScenarioLabel(scenario: PerformanceScenario) {
  return `perf ${scenario.name}: ${scenario.buildings.length}b/${scenario.resources.length}r/${scenario.monsters.length}m`
}

function patchWorldTileInQueryCache(queryClient: QueryClient, tile: WorldTile) {
  queryClient.setQueriesData<ChunksResponse>({ queryKey: ['world', 'chunks'] }, (current) => patchTileInChunks(current, tile))
}

function patchTileInChunks(current: ChunksResponse | undefined, tile: WorldTile) {
  if (!current) {
    return current
  }
  let changed = false
  const chunks = current.chunks.map((chunk) => {
    let chunkChanged = false
    const tiles = chunk.tiles.map((item) => {
      if (item.x !== tile.x || item.y !== tile.y) {
        return item
      }
      chunkChanged = true
      changed = true
      return { ...item, ...tile }
    })
    return chunkChanged ? { ...chunk, tiles } : chunk
  })
  return changed ? { ...current, chunks } : current
}

function mergeTransientWorldTiles(
  tiles: WorldTile[],
  currentTiles: WorldTile[],
  optimisticTiles: ReadonlyMap<string, WorldTile>,
  recentChopTiles: Map<string, { tile: WorldTile; expiresAt: number }>,
) {
  const now = Date.now()
  for (const [key, item] of recentChopTiles) {
    if (item.expiresAt <= now) {
      recentChopTiles.delete(key)
    }
  }
  const currentTilesByKey = new Map(currentTiles.map((tile) => [tileActionKey(tile), tile]))
  return tiles.map((tile) => {
    const key = tileActionKey(tile)
    const optimisticTile = optimisticTiles.get(key)
    if (optimisticTile) {
      return optimisticTile
    }
    const recentChopTile = recentChopTiles.get(key)?.tile
    if (recentChopTile && shouldKeepRecentChopTile(tile, recentChopTile)) {
      return recentChopTile
    }
    const currentTile = currentTilesByKey.get(key)
    if (currentTile && shouldKeepLocallyChoppedTile(tile, currentTile)) {
      return currentTile
    }
    return tile
  })
}

function rememberRecentChopTile(chopTiles: Map<string, { tile: WorldTile; expiresAt: number }>, tile: WorldTile) {
  chopTiles.set(tileActionKey(tile), { tile, expiresAt: Date.now() + RECENT_CHOP_TILE_TTL_MS })
}

function shouldKeepRecentChopTile(incoming: WorldTile, recent: WorldTile) {
  return shouldKeepLocallyChoppedTile(incoming, recent)
}

function shouldKeepLocallyChoppedTile(incoming: WorldTile, local: WorldTile) {
  if (incoming.terrain === 'forest' && local.terrain !== 'forest') {
    return true
  }
  return incoming.terrain === 'forest' && local.terrain === 'forest' && incoming.forest_density > local.forest_density
}

function MapObject({
  id,
  x,
  y,
  className,
  label,
  onSelect,
  children,
  viewportCenter,
}: {
  id: string
  x: number
  y: number
  className: string
  label?: string
  onSelect?: () => void
  children?: ReactNode
  viewportCenter: { x: number; y: number }
}) {
  const pos = nearestWrappedScreenCoord({ x, y }, gridToScreen(viewportCenter))
  return (
    <button
      className={className}
      key={id}
      type="button"
      title={label}
      aria-label={label ?? id}
      style={{ transform: `translate(${pos.x}px, ${pos.y - 30}px)`, zIndex: mapObjectZIndex(pos.y) }}
      onClick={(event) => {
        event.stopPropagation()
        onSelect?.()
      }}
    >
      {children}
    </button>
  )
}

function formatRemaining(ms: number) {
  const totalSeconds = Math.max(0, Math.ceil(ms / 1000))
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}

type BuildingOverlay =
  | { type: 'timer'; text: string }
  | { type: 'ready'; label: string; rewards?: InventoryItem[] }
  | { type: 'workers'; workers: number }

function BuildingWorkBadge({ overlay, onActivate }: { overlay: BuildingOverlay; onActivate?: () => void }) {
  const handleActivate = (event: MouseEvent<HTMLSpanElement>) => {
    event.stopPropagation()
    onActivate?.()
  }
  const stopMapDrag = (event: PointerEvent<HTMLSpanElement>) => {
    event.stopPropagation()
  }

  if (overlay.type === 'timer') {
    return (
      <span className="building-work-badge building-work-badge-timer" onClick={handleActivate} onPointerDown={stopMapDrag}>
        {overlay.text}
      </span>
    )
  }
  if (overlay.type === 'workers') {
    return (
      <span className="building-work-badge building-work-badge-workers" onClick={handleActivate} onPointerDown={stopMapDrag}>
        <ResourceIcon id="population" label="Жители" />
        {overlay.workers}
      </span>
    )
  }
  return (
    <span className="building-work-badge building-work-badge-ready" onClick={handleActivate} onPointerDown={stopMapDrag}>
      {overlay.rewards?.length ? overlay.rewards.map((reward) => (
        <span key={`${reward.resource}:${reward.amount}`}>
          <ResourceIcon id={reward.resource} label={reward.resource} />
          {reward.amount}
        </span>
      )) : overlay.label}
    </span>
  )
}

function buildingOverlay(building: PlacedBuilding, recipe: ProductionRecipeResponse | undefined, job: ProductionJobResponse | undefined, now: number): BuildingOverlay | null {
  const fieldSpec = fieldCropSpec(building.kind)
  if (fieldSpec) {
    const stage = building.fieldStage ?? building.growthStage ?? building.cropStage ?? 0
    const ready = isFieldStageReady(building, now)
    const maxStage = building.isSuperCrop || building.superCrop ? fieldSpec.superStages : fieldSpec.stages
    if (stage > 0 && !ready && building.fieldStageReadyAt) {
      return { type: 'timer', text: formatRemaining(building.fieldStageReadyAt - now) }
    }
    if (stage >= maxStage && ready) {
      return { type: 'ready', label: 'Урожай', rewards: fieldRewards(building) }
    }
    if (stage > 0 && ready) {
      return { type: 'ready', label: `Фаза ${stage}/${maxStage}` }
    }
    return { type: 'workers', workers: fieldWorkers(building) }
  }
  if (job && recipe) {
    if (isProductionReady(job, now)) {
      return { type: 'ready', label: 'Готово', rewards: recipe.output }
    }
    return { type: 'timer', text: formatRemaining(Date.parse(job.completes_at) - now) }
  }
  if (recipe) {
    return { type: 'workers', workers: recipe.workers }
  }
  return null
}

function isFieldStageReady(building: PlacedBuilding, now: number) {
  if (building.fieldStageReadyAt) {
    return building.fieldStageReadyAt <= now
  }
  return Boolean(building.fieldStageReady)
}

function isProductionReady(job: ProductionJobResponse, now: number) {
  return job.state === 'ready' || (job.state === 'running' && Date.parse(job.completes_at) <= now)
}

function tileActionKey(tile: { x: number; y: number }) {
  return `${tile.x}:${tile.y}`
}

function findRecipeForBuilding(recipes: ProductionRecipeResponse[], building: PlacedBuilding) {
  return recipes.find((recipe) => recipe.building_type === building.kind && (!recipe.workers || building.level >= 1))
}

function fieldWorkers(building: PlacedBuilding) {
  const spec = fieldCropSpec(building.kind)
  if (!spec) {
    return 0
  }
  return spec.workersByLevel[Math.max(0, Math.min(spec.workersByLevel.length - 1, building.level - 1))] ?? 1
}

function fieldRewards(building: PlacedBuilding): InventoryItem[] {
  const spec = fieldCropSpec(building.kind)
  if (!spec) {
    return []
  }
  const rewards = spec.rewardsByLevel[Math.max(0, Math.min(spec.rewardsByLevel.length - 1, building.level - 1))]
  if (building.isSuperCrop || building.superCrop) {
    return [{ resource: 'coins', amount: rewards.superCoins ?? rewards.coins }, ...(rewards.superRewards ?? rewards.rewards)]
  }
  return [{ resource: 'coins', amount: rewards.coins }, ...rewards.rewards]
}
