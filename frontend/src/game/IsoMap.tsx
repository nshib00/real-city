import { useEffect, useMemo, useRef, useState } from 'react'
import type { MouseEvent, PointerEvent, ReactNode } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { QueryClient } from '@tanstack/react-query'
import { playUiSound } from '../audio/playUiSound'
import { playCombatSound } from '../audio/voiceManager'
import { startAmbience } from '../audio/ambience'
import { buildCatalog } from '../features/buildings/catalog'
import { validatePlacementPreview } from '../features/build-placement/placement'

import { flattenChunkTiles, useVisibleChunks } from '../features/world/useVisibleChunks'
import { MapEntryStatus } from '../features/world/MapEntryStatus'
import { InitialLoadingScreen } from '../features/loading/InitialLoadingScreen'
import { useOwnershipContext } from '../features/alliance/useOwnership'
import { occupiedTerritory } from './territory'
import { canChopForestTile } from '../features/world/forestActions'
import { CHUNK_SIZE, gridToScreen, nearestWrappedScreenCoord, roundGridCoord, screenToGrid, TILE_HEIGHT, TILE_WIDTH, tileToChunk, wrapGridCoord } from './coordinates/iso'
import { resolvePerformanceScenarioFromSearch, type PerformanceScenario } from './dev/performanceScenarios'
import { PixiStage } from './renderer/PixiStage'
import { AccessibleMapSelection } from './AccessibleMapSelection'
import { renderPerformanceSnapshot, type RenderPerformanceSnapshot } from './renderer/renderPerformanceMetrics'
import { filterVisibleIndexedMapObjects, filterVisibleMapObjects, indexMapObjects, occupiedTileKeys } from './renderer/visibleObjects'
import { useGameStore } from './state/useGameStore'
import type { PlacedBuilding } from './state/useGameStore'
import type { WorldTile } from '../shared/contracts'
import { chopForest, type ChunksResponse } from '../shared/api/world'
import { relocateBuilding, patchBuilding, toPlacedBuilding } from '../shared/api/buildings'
import { buildingSpriteAsset } from './renderers/buildingSpriteAssets'
import { claimMonsterLoot, listMonsterLoot, type MonsterLootResponse } from '../shared/api/monsters'
import { advanceField, harvestField, listProductionRecipes, patchProductionJob, startProduction } from '../shared/api/economy'
import type { InventoryItem, InventoryResponse, ProductionJobResponse, ProductionRecipeResponse } from '../shared/api/economy'
import { useAuthStore } from '../features/auth/useAuthStore'
import { PlayerBalloon } from '../features/player/PlayerBalloon'
import { listNearbyPlayers, updatePlayerPresence } from '../shared/api/playerPresence'
import { fieldCropSpec } from '../features/fields/fieldGrowth'
import { fieldHarvestSound, playConfirmedCoinChange, playConfirmedRareReward, productionMaterialVariant } from '../features/economy/economyAudio'
import { showToast } from '../features/notifications/toast'
import { ResourceIcon } from '../features/resources/ResourceIcon'
import { resourceCatalog } from '../../../shared/catalog/resources'
import { formatRemaining } from '../shared/time/formatRemaining'
import { updateProductionCache } from '../features/production/updateProductionCache'
import { useProductionJobs } from '../features/production/useProductionJobs'
import { mapObjectZIndex } from './renderer/depth'

const RECENT_CHOP_TILE_TTL_MS = 10_000

export function IsoMap() {
  const mapPowerSave = useGameStore((state) => state.uiPreferences.mapPowerSave)
  const ownership = useOwnershipContext()
  useEffect(() => startAmbience(), [])
  const selectedTile = useGameStore((state) => state.selectedTile)
  const hoveredTile = useGameStore((state) => state.hoveredTile)
  const placementPreviewKind = useGameStore((state) => state.placementPreviewKind)
  const relocatingBuildingId = useGameStore((state) => state.relocatingBuildingId)
  const setRelocatingBuildingId = useGameStore((state) => state.setRelocatingBuildingId)
  const tool = useGameStore((state) => state.tool)
  const camera = useGameStore((state) => state.camera)
  const viewport = useGameStore((state) => state.viewport)
  const buildings = useGameStore((state) => state.buildings)
  const resourceNodes = useGameStore((state) => state.resourceNodes)
  const monsters = useGameStore((state) => state.monsters)
  const monsterDamageEvents = useGameStore((state) => state.monsterDamageEvents)
  const removeMonsterDamage = useGameStore((state) => state.removeMonsterDamage)
  const buildingDamageEvents = useGameStore((state) => state.buildingDamageEvents)
  const removeBuildingDamage = useGameStore((state) => state.removeBuildingDamage)
  const constructionNow = useGameStore((state) => state.constructionNow)
  const selectedBuildingId = useGameStore((state) => state.selectedBuildingId)
  const selectedMonsterId = useGameStore((state) => state.selectedMonsterId)
  const selectTile = useGameStore((state) => state.selectTile)
  const setBuildMenuOpen = useGameStore((state) => state.setBuildMenuOpen)
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
  const dragDistance = useRef(0)
  const exploredTilesRef = useRef(new Set<string>())
  const pendingDragRef = useRef<{ screen: { x: number; y: number }; grid: { x: number; y: number } } | null>(null)
  const dragFrameRef = useRef<number | null>(null)
  const pendingChopTilesRef = useRef(new Set<string>())
  const optimisticChopTilesRef = useRef(new Map<string, WorldTile>())
  const optimisticChopResultTilesRef = useRef(new Map<string, WorldTile>())
  const recentChopTilesRef = useRef(new Map<string, { tile: WorldTile; expiresAt: number }>())
  const [stageSize, setStageSize] = useState({ width: 0, height: 0 })
  const [rendererReady, setRendererReady] = useState(false)
  const [rendererFailed, setRendererFailed] = useState(false)
  const activePointers = useRef(new Set<number>())
  const performanceScenario = useMemo(() => resolvePerformanceScenarioFromSearch(typeof window === 'undefined' ? '' : window.location.search), [])
  const viewportCenterRef = useRef(viewport.center)
  const renderCenter = useMemo(() => {
    if (stageSize.width <= 0 || stageSize.height <= 0) return viewport.center
    return screenToGrid({
      x: (stageSize.width * 0.02 - camera.x) / camera.zoom,
      y: (stageSize.height * 0.34 - camera.y) / camera.zoom,
    })
  }, [camera, stageSize, viewport.center])
  const centerChunk = useMemo(() => tileToChunk(wrapGridCoord(renderCenter)), [renderCenter])
  const visibleChunkRadius = useMemo(() => deriveVisibleChunkRadius(stageSize, camera.zoom), [camera.zoom, stageSize])
  const chunksQuery = useVisibleChunks(centerChunk, visibleChunkRadius)
  const tiles = useMemo(() => flattenChunkTiles(chunksQuery.data?.chunks), [chunksQuery.data?.chunks])
  const renderBuildings = performanceScenario?.buildings ?? buildings
  const renderResourceNodes = performanceScenario?.resources ?? resourceNodes
  const renderMonsters = performanceScenario?.monsters ?? monsters
  const territories = useMemo(() => occupiedTerritory(renderBuildings, ownership.viewerId, ownership.alliedIds), [renderBuildings, ownership.viewerId, ownership.alliedIds])
  const mapTiles = performanceScenario?.tiles ?? (worldTiles.length > 0 ? worldTiles : tiles)
  const mapTilesByKey = useMemo(() => new Map(mapTiles.map((tile) => [tileActionKey(tile), tile])), [mapTiles])
  const placementPreview = placementPreviewKind ? buildCatalog.find((item) => item.kind === placementPreviewKind) : undefined
  const previewTile = hoveredTile ?? selectedTile
  const placementValidity = placementPreview ? validatePlacementPreview({ kind: placementPreview.kind, tile: previewTile, footprint: placementPreview.footprint, buildings, worldTiles: mapTiles, monsters, ownerId: player?.id }) : null
  const missingCenterTile = mapTiles.length > 0 && !mapTilesByKey.has(tileActionKey(wrapGridCoord(roundGridCoord(renderCenter))))
  const realtimeStatus = useGameStore((state) => state.realtimeStatus)
  const relocatingBuilding = relocatingBuildingId ? buildings.find((item) => item.id === relocatingBuildingId) : null
  const relocationPreview = relocatingBuilding && hoveredTile ? validatePlacementPreview({
    kind: relocatingBuilding.kind,
    tile: hoveredTile,
    footprint: { width: relocatingBuilding.footprintW ?? 1, height: relocatingBuilding.footprintH ?? 1 },
    buildings,
    worldTiles: mapTiles,
    monsters,
    ignoreBuildingId: relocatingBuilding.id,
    skipTownHallCheck: true,
  }) : null
  useEffect(() => {
    if (!relocatingBuildingId) return
    const cancelOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setRelocatingBuildingId(null)
    }
    window.addEventListener('keydown', cancelOnEscape)
    return () => window.removeEventListener('keydown', cancelOnEscape)
  }, [relocatingBuildingId, setRelocatingBuildingId])
  useEffect(() => {
    if (relocatingBuildingId && !relocatingBuilding) setRelocatingBuildingId(null)
  }, [relocatingBuildingId, relocatingBuilding, setRelocatingBuildingId])
  const visibilityOptions = useMemo(
    () => ({ camera, viewportSize: stageSize }),
    [camera, stageSize],
  )
  const resourceVisibilityOptions = useMemo(() => ({ ...visibilityOptions, maxScreenExtent: 96 }), [visibilityOptions])
  const monsterVisibilityOptions = useMemo(() => ({ ...visibilityOptions, maxScreenExtent: 420 }), [visibilityOptions])
  const buildingSpatialIndex = useMemo(() => indexMapObjects(renderBuildings), [renderBuildings])
  const resourceSpatialIndex = useMemo(() => indexMapObjects(renderResourceNodes), [renderResourceNodes])
  const monsterSpatialIndex = useMemo(() => indexMapObjects(renderMonsters), [renderMonsters])
  const visibleBuildings = useMemo(() => filterVisibleIndexedMapObjects(buildingSpatialIndex, visibilityOptions), [buildingSpatialIndex, visibilityOptions])
  const buildingOccupiedTiles = useMemo(() => occupiedTileKeys(visibleBuildings), [visibleBuildings])
  const visibleResourceNodes = useMemo(() => filterVisibleIndexedMapObjects(resourceSpatialIndex, resourceVisibilityOptions), [resourceSpatialIndex, resourceVisibilityOptions])
  const visibleMonsters = useMemo(() => filterVisibleIndexedMapObjects(monsterSpatialIndex, monsterVisibilityOptions), [monsterSpatialIndex, monsterVisibilityOptions])
  const lootCenter = useMemo(() => wrapGridCoord({ x: centerChunk.x * CHUNK_SIZE + Math.floor(CHUNK_SIZE / 2), y: centerChunk.y * CHUNK_SIZE + Math.floor(CHUNK_SIZE / 2) }), [centerChunk])
  const lootQuery = useQuery({
    queryKey: ['monster-loot', lootCenter.x, lootCenter.y, visibleChunkRadius],
    queryFn: () => listMonsterLoot({ x: lootCenter.x, y: lootCenter.y, radius: Math.min(128, (visibleChunkRadius + 1) * CHUNK_SIZE) }),
    refetchInterval: realtimeStatus === 'connected' ? 30_000 : 8000,
    retry: false,
  })
  const visibleLoot = useMemo(() => filterVisibleMapObjects((lootQuery.data?.loot ?? []).map((drop) => ({ ...drop, tile: { x: drop.tile_x, y: drop.tile_y } })), resourceVisibilityOptions), [lootQuery.data, resourceVisibilityOptions])
  const presenceTile = useMemo(() => wrapGridCoord(roundGridCoord(viewport.center)), [viewport.center])
  const latestPresenceTileRef = useRef(presenceTile)
  const lastPresenceSentAtRef = useRef(0)
  latestPresenceTileRef.current = presenceTile
  const nearbyRadius = Math.min(80, (visibleChunkRadius + 2) * CHUNK_SIZE)
  const nearbyQuery = useQuery({
    queryKey: ['players', 'nearby', lootCenter.x, lootCenter.y, nearbyRadius],
    queryFn: () => listNearbyPlayers(lootCenter, nearbyRadius),
    enabled: Boolean(player),
    refetchInterval: realtimeStatus === 'connected' ? 30_000 : 5000,
    retry: false,
  })
  const visiblePlayers = useMemo(() => filterVisibleMapObjects((nearbyQuery.data?.players ?? []).map((other) => ({ ...other, tile: { x: other.tile_x, y: other.tile_y } })), resourceVisibilityOptions), [nearbyQuery.data, resourceVisibilityOptions])
  useEffect(() => {
    if (!player) return
    const delay = Math.max(0, 250 - (Date.now() - lastPresenceSentAtRef.current))
    const timeout = window.setTimeout(() => {
      if (document.hidden) return
      lastPresenceSentAtRef.current = Date.now()
      void updatePlayerPresence(latestPresenceTileRef.current).catch(() => undefined)
    }, delay)
    return () => window.clearTimeout(timeout)
  }, [player?.id, presenceTile.x, presenceTile.y])
  useEffect(() => {
    if (!player) return
    const interval = window.setInterval(() => {
      if (!document.hidden) void updatePlayerPresence(latestPresenceTileRef.current).catch(() => undefined)
    }, 5000)
    return () => {
      window.clearInterval(interval)
    }
  }, [player?.id])
  const claimLootMutation = useMutation({
    mutationFn: claimMonsterLoot,
    onSuccess: (result) => {
      playCombatSound('combat.loot.claimed')
      queryClient.setQueriesData<{ loot: MonsterLootResponse[] }>({ queryKey: ['monster-loot'] }, (current) => current ? { loot: current.loot.filter((drop) => drop.id !== result.loot.id) } : current)
      void queryClient.invalidateQueries({ queryKey: ['monster-loot'] })
      void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
    },
    onError: () => {
      void queryClient.invalidateQueries({ queryKey: ['monster-loot'] })
    },
  })
  const relocateMutation = useMutation({
    mutationFn: ({ id, tile, rotation }: { id: string; tile: { x: number; y: number }; rotation: number }) => relocateBuilding(id, tile, rotation),
    onSuccess: (result) => {
      addBuilding(toPlacedBuilding(result.building))
      setRelocatingBuildingId(null)
      void queryClient.invalidateQueries({ queryKey: ['buildings'] })
    },
    onError: (error) => showToast('warning', error instanceof Error ? error.message : 'Не удалось переместить постройку'),
  })
  const repairBuildingMutation = useMutation({
    mutationFn: (id: string) => patchBuilding(id, 'repair'),
    onSuccess: (result) => {
      if (result.building) addBuilding(toPlacedBuilding(result.building))
      void queryClient.invalidateQueries({ queryKey: ['buildings'] })
    },
    onError: (error) => showToast('warning', error instanceof Error ? error.message : 'Не удалось починить постройку'),
  })
  const recipesQuery = useQuery({ queryKey: ['production', 'recipes'], queryFn: listProductionRecipes, staleTime: 5 * 60_000, gcTime: 30 * 60_000 })
  const jobsQuery = useProductionJobs()
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
  const chopMutation = useMutation({
    mutationFn: chopForest,
    onSuccess: (result) => {
      playUiSound('economy.gather.wood')
      playCombatSound('world.forest.cut', 0.7)
      playConfirmedRareReward(queryClient.getQueryData<{ inventory: InventoryResponse }>(['economy', 'inventory'])?.inventory, result.inventory)
      playConfirmedCoinChange(queryClient.getQueryData<{ inventory: InventoryResponse }>(['economy', 'inventory'])?.inventory, result.inventory)
      rememberRecentChopTile(recentChopTilesRef.current, result.tile)
      updateWorldTile(result.tile)
      patchWorldTileInQueryCache(queryClient, result.tile)
      void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
    },
    onError: (_error, variables) => {
      showToast('warning', 'Не удалось вырубить лес')
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
      playUiSound(fieldHarvestSound(result.building.type))
      playConfirmedRareReward(queryClient.getQueryData<{ inventory: InventoryResponse }>(['economy', 'inventory'])?.inventory, result.inventory)
      playConfirmedCoinChange(queryClient.getQueryData<{ inventory: InventoryResponse }>(['economy', 'inventory'])?.inventory, result.inventory)
      addBuilding(toPlacedBuilding(result.building))
      void queryClient.invalidateQueries({ queryKey: ['buildings'] })
      void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
    },
  })
  const startProductionMutation = useMutation({
    mutationFn: startProduction,
    onSuccess: (result, variables) => {
      playUiSound('economy.production.started', productionMaterialVariant(buildings.find((building) => building.id === variables.building_id)?.kind))
      playConfirmedCoinChange(queryClient.getQueryData<{ inventory: InventoryResponse }>(['economy', 'inventory'])?.inventory, result.inventory)
      void updateProductionCache(queryClient, result)
    },
    onError: (error) => showToast('warning', error instanceof Error ? error.message : 'Не удалось запустить производство'),
  })
  const collectProductionMutation = useMutation({
    mutationFn: (id: string) => patchProductionJob(id, 'complete'),
    onSuccess: (result) => {
      playUiSound('economy.production.collected', productionMaterialVariant(buildings.find((building) => building.id === result.job.building_id)?.kind))
      playConfirmedRareReward(queryClient.getQueryData<{ inventory: InventoryResponse }>(['economy', 'inventory'])?.inventory, result.inventory)
      playConfirmedCoinChange(queryClient.getQueryData<{ inventory: InventoryResponse }>(['economy', 'inventory'])?.inventory, result.inventory)
      void updateProductionCache(queryClient, result)
      void queryClient.invalidateQueries({ queryKey: ['resources', 'nodes'] })
    },
    onError: (error) => showToast('warning', error instanceof Error ? error.message : 'Не удалось собрать продукцию'),
  })

  function handleSelectTile(tile: { x: number; y: number }) {
    if (relocatingBuilding) {
      if (relocateMutation.isPending) return
      const preview = validatePlacementPreview({
        kind: relocatingBuilding.kind,
        tile,
        footprint: { width: relocatingBuilding.footprintW ?? 1, height: relocatingBuilding.footprintH ?? 1 },
        buildings,
        worldTiles: mapTiles,
        monsters,
        ignoreBuildingId: relocatingBuilding.id,
        skipTownHallCheck: true,
      })
      if (!preview.valid) {
        showToast('warning', preview.reason ?? 'На эту клетку нельзя переместить постройку')
        return
      }
      relocateMutation.mutate({ id: relocatingBuilding.id, tile, rotation: relocatingBuilding.rotation ?? 0 })
      return
    }
    if (!selectedTile || selectedTile.x !== tile.x || selectedTile.y !== tile.y || selectedBuildingId || selectedMonsterId) playUiSound('ui.select.tile')
    if (placementPreviewKind) {
      selectTile(tile)
      return
    }
    const worldTile = mapTilesByKey.get(tileActionKey(tile))
    if (worldTile && (worldTile.terrain === 'forest' || worldTile.terrain === 'ruins') && !exploredTilesRef.current.has(tileActionKey(tile))) {
      exploredTilesRef.current.add(tileActionKey(tile))
      playCombatSound(worldTile.terrain === 'forest' ? 'world.forest.explore' : 'world.ruin.discovered', worldTile.terrain === 'forest' ? 0.35 : 0.45)
    }
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
    if (worldTile?.terrain === 'oil_well') {
      setBuildMenuOpen(true)
    }
  }

  function handleBuildingClick(building: PlacedBuilding) {
    if (tool === 'repair' && player && building.owner === player.id) {
      if (!repairBuildingMutation.isPending) repairBuildingMutation.mutate(building.id)
      return
    }
    if (selectedBuildingId !== building.id) playUiSound('ui.select.building')
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
    const recipe = findRecipeForBuilding(recipes, building)
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
    if (tiles.length === 0 || chunksQuery.isPlaceholderData) return
    const optimisticTiles = optimisticChopResultTilesRef.current
    const recentChopTiles = recentChopTilesRef.current
    setWorldTiles(mergeTransientWorldTiles(tiles, useGameStore.getState().worldTiles, optimisticTiles, recentChopTiles, centerChunk, visibleChunkRadius))
  }, [setWorldTiles, tiles, chunksQuery.isPlaceholderData, centerChunk.x, centerChunk.y, visibleChunkRadius])

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
      id="game-map"
      tabIndex={0}
      ref={mapStageRef}
      aria-label="Карта"
      aria-description="Стрелки — перемещение карты, плюс и минус — масштаб. F6 — следующая область интерфейса."
      onClickCapture={(event) => { if (event.detail !== 0 && dragDistance.current > 8) { event.preventDefault(); event.stopPropagation(); dragDistance.current = 0 } }}
      onKeyDown={(event) => {
        if (event.target !== event.currentTarget || event.ctrlKey || event.metaKey || event.altKey) return
        const delta = { ArrowLeft: { x: 64, y: 0 }, ArrowRight: { x: -64, y: 0 }, ArrowUp: { x: 0, y: 64 }, ArrowDown: { x: 0, y: -64 } }[event.key]
        if (delta) { event.preventDefault(); scheduleDragFrame(delta); flushDragFrame() }
        if (event.key === '+' || event.key === '=' || event.key === '-') { event.preventDefault(); setZoomAt({ zoom: camera.zoom + (event.key === '-' ? -0.1 : 0.1), viewportSize: stageSize }) }
      }}
      onPointerDown={(event) => {
        activePointers.current.add(event.pointerId)
        if (activePointers.current.size > 1) { dragStart.current = null; dragDistance.current = Number.POSITIVE_INFINITY; return }
        if (event.isPrimary === false || (event.pointerType === 'mouse' && event.button !== 0)) return
        dragDistance.current = 0
        dragStart.current = { x: event.clientX, y: event.clientY }
      }}
      onPointerMove={(event) => {
        if (activePointers.current.size > 1) return
        if (!dragStart.current || (event.pointerType !== 'touch' && event.buttons !== 1)) {
          return
        }
        const delta = { x: event.clientX - dragStart.current.x, y: event.clientY - dragStart.current.y }
        dragDistance.current += Math.hypot(delta.x, delta.y)
        scheduleDragFrame(delta)
        dragStart.current = { x: event.clientX, y: event.clientY }
      }}
      onPointerUp={(event) => {
        activePointers.current.delete(event.pointerId)
        flushDragFrame()
        dragStart.current = null
      }}
      onPointerCancel={(event) => {
        activePointers.current.delete(event.pointerId)
        dragDistance.current = Number.POSITIVE_INFINITY
        flushDragFrame()
        dragStart.current = null
      }}
      onPointerLeave={(event) => { activePointers.current.delete(event.pointerId); flushDragFrame(); dragStart.current = null }}
      onWheel={(event) => {
        if (event.ctrlKey || event.metaKey) return
        event.preventDefault()
        const rect = mapStageRef.current?.getBoundingClientRect()
        setZoomAt({
          zoom: camera.zoom + (event.deltaY > 0 ? -0.08 : 0.08),
          focalScreen: rect ? { x: event.clientX - rect.left, y: event.clientY - rect.top } : undefined,
          viewportSize: stageSize,
        })
      }}
    >
      <nav className="map-navigation" aria-label="Перемещение карты" onPointerDown={(event) => event.stopPropagation()} onWheel={(event) => event.stopPropagation()}>
        {([{ label: 'Карта влево', x: 64, y: 0, text: '←' }, { label: 'Карта вверх', x: 0, y: 64, text: '↑' }, { label: 'Карта вниз', x: 0, y: -64, text: '↓' }, { label: 'Карта вправо', x: -64, y: 0, text: '→' }]).map((direction) => <button key={direction.label} type="button" aria-label={direction.label} onClick={() => { scheduleDragFrame(direction); flushDragFrame() }}>{direction.text}</button>)}
        <button type="button" aria-label="Уменьшить карту" onClick={() => setZoomAt({ zoom: camera.zoom - 0.1, viewportSize: stageSize })}>−</button>
        <button type="button" aria-label="Увеличить карту" onClick={() => setZoomAt({ zoom: camera.zoom + 0.1, viewportSize: stageSize })}>+</button>
        <AccessibleMapSelection />
      </nav>
      {(chunksQuery.isPending || chunksQuery.isError || chunksQuery.isPlaceholderData || missingCenterTile || realtimeStatus !== 'connected') && !performanceScenario ? <div className="world-status" role="status" onPointerDown={(event) => event.stopPropagation()}>
        <strong>{realtimeStatus === 'offline' ? 'Нет связи с миром' : realtimeStatus !== 'connected' ? 'Подключаемся к миру…' : chunksQuery.isError ? 'Район не загрузился' : missingCenterTile && !chunksQuery.isFetching ? 'Данные района отсутствуют' : mapTiles.length ? 'Загружаем район…' : 'Загружаем мир…'}</strong>
        <span>{mapTiles.length ? 'Загруженная карта остаётся доступной. Данные могут устареть.' : 'Карта появится после получения данных сервера.'}</span>
        {chunksQuery.isError || missingCenterTile ? <button type="button" disabled={chunksQuery.isFetching} onClick={() => void chunksQuery.refetch()}>Повторить загрузку</button> : null}
      </div> : null}
      {placementValidity ? <div className="placement-status" role="status">{placementValidity.valid ? '✓ Место подходит предварительно. Подтвердите в меню строительства.' : `× ${placementValidity.reason}`} Сервер проверит размещение.</div> : null}
      <PixiStage key={mapPowerSave ? 'economy' : 'normal'} powerSave={mapPowerSave}
        onReady={() => { setRendererReady(true); setRendererFailed(false) }}
        onFailed={() => setRendererFailed(true)}
        territories={territories}
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
        viewerId={player?.id}
        onSelectTile={handleSelectTile}
        onHoverTile={hoverTile}
        onSelectBuilding={handleBuildingClick}
        onSelectMonster={(monster) => { if (selectedMonsterId !== monster.id) playUiSound('ui.select.monster'); selectMonster(monster.id) }}
        targetTileOnly={Boolean(relocatingBuilding)}
      />
      <div className="map-damage-layer" aria-hidden="true">
        {monsterDamageEvents.filter((event) => Date.now() - event.createdAt < 1500).map((event) => {
          const pos = damageScreenPosition(event.tile, camera, stageSize)
          return <span key={event.id} className="map-damage-number" style={{ left: pos.x, top: pos.y - 72 }} onAnimationEnd={() => removeMonsterDamage(event.id)}>-{event.damage}</span>
        })}
        {buildingDamageEvents.filter((event) => Date.now() - event.createdAt < 1500).map((event) => {
          const pos = damageScreenPosition(event.tile, camera, stageSize)
          return <span key={event.id} className="map-damage-number" style={{ left: pos.x, top: pos.y - 72 }} onAnimationEnd={() => removeBuildingDamage(event.id)}>-{event.damage}</span>
        })}
      </div>
      {relocatingBuilding ? <div className="map-relocation-hint" role="status">
        <span>Перемещение: {relocatingBuilding.name}. Выберите клетку на карте. Esc — отмена.</span>
        {relocationPreview && !relocationPreview.valid ? <span>{relocationPreview.reason}</span> : null}
        {relocateMutation.isPending ? <span>Перемещаем…</span> : null}
        <button type="button" onClick={() => setRelocatingBuildingId(null)} disabled={relocateMutation.isPending}>Отменить</button>
      </div> : null}
      <div
        className="map-origin"
        style={{
          transform: `translate(${camera.x}px, ${camera.y}px) scale(${camera.zoom})`,
        }}
      >
        {placementPreview?.previewImage && previewTile ? (() => {
          const pos = nearestWrappedScreenCoord(previewTile, gridToScreen(renderCenter))
          return <div className={`map-placement-preview${placementValidity?.valid === false ? ' map-placement-preview-invalid' : ''}`} style={{ transform: `translate(${pos.x}px, ${pos.y - 30}px)` }} aria-hidden="true">
            <img src={placementPreview.previewImage} alt="" draggable={false} />
            <svg className="placement-footprint" viewBox={`${-32 * placementPreview.footprint.height} -16 ${32 * (placementPreview.footprint.width + placementPreview.footprint.height)} ${16 * (placementPreview.footprint.width + placementPreview.footprint.height)}`} style={{ width: 32 * (placementPreview.footprint.width + placementPreview.footprint.height), height: 16 * (placementPreview.footprint.width + placementPreview.footprint.height) }}><polygon points={`0,-16 ${32 * placementPreview.footprint.width},${16 * (placementPreview.footprint.width - 1)} ${32 * (placementPreview.footprint.width - placementPreview.footprint.height)},${16 * (placementPreview.footprint.width + placementPreview.footprint.height - 1)} ${-32 * placementPreview.footprint.height},${16 * (placementPreview.footprint.height - 1)}`} /></svg>
          </div>
        })() : null}
        {relocatingBuilding && hoveredTile ? (() => {
          const pos = nearestWrappedScreenCoord(hoveredTile, gridToScreen(renderCenter))
          const asset = buildingSpriteAsset(relocatingBuilding)
          return asset ? <div className={`map-placement-preview${relocationPreview?.valid === false ? ' map-placement-preview-invalid' : ''}`} style={{ transform: `translate(${pos.x}px, ${pos.y - 30}px)` }} aria-hidden="true">
            <img src={asset} alt="" draggable={false} />
          </div> : null
        })() : null}
        {selectedBuildingId && (() => {
          const selected = buildings.find((item) => item.id === selectedBuildingId)
          if (!selected || !selected.rotation) return null
          const pos = nearestWrappedScreenCoord(selected.tile, gridToScreen(renderCenter))
          return <div className="map-building-direction" style={{ transform: `translate(${pos.x}px, ${pos.y}px)` }} aria-label={`Поворот ${(selected.rotation ?? 0) * 90} градусов`}>
            <span style={{ transform: `rotate(${(selected.rotation ?? 0) * 90}deg)` }}>▲</span>
          </div>
        })()}
        {visibleBuildings.filter((building) => building.owner === player?.id).map((building) => {
          const job = activeProductionByBuilding.get(building.id)
          const recipe = findRecipeForBuilding(recipes, building)
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
              viewportCenter={renderCenter}
              className="map-building-overlay-anchor"
              label={building.name}
              onSelect={() => handleBuildingClick(building)}
            >
              {building.status === 'construction' && building.completesAt ? <span className="construction-timer">{formatRemaining(building.completesAt - constructionNow)}</span> : null}
              {overlay ? <BuildingWorkBadge overlay={overlay} onActivate={() => handleBuildingClick(building)} /> : null}
            </MapObject>
          )
        })}
        {visibleLoot.map((drop) => (
          <MapObject
            key={drop.id}
            id={drop.id}
            x={drop.tile_x}
            y={drop.tile_y}
            viewportCenter={renderCenter}
            className="map-loot-anchor"
            label={`Собрать добычу: ${drop.items.map((item) => `${item.amount} ${resourceCatalog.find((resource) => resource.id === item.resource)?.name ?? item.resource}`).join(', ')}`}
            onSelect={() => { if (!claimLootMutation.isPending) claimLootMutation.mutate(drop.id) }}
          >
            <span className="map-loot-badge">
              {drop.items.map((item) => (
                <span key={item.resource}><ResourceIcon id={item.resource} label={resourceCatalog.find((resource) => resource.id === item.resource)?.name ?? item.resource} /> {item.amount}</span>
              ))}
            </span>
          </MapObject>
        ))}
        {visiblePlayers.map((other) => (
          <MapObject
            key={other.player_id}
            id={other.player_id}
            x={other.tile_x}
            y={other.tile_y}
            viewportCenter={renderCenter}
            className="map-player-anchor"
            label={`${other.name}, уровень ${other.level}`}
          >
            <PlayerBalloon player={other} />
          </MapObject>
        ))}
      </div>
      <MapEntryStatus query={chunksQuery} />
      <InitialLoadingScreen
        query={chunksQuery}
        tiles={tiles}
        buildings={visibleBuildings}
        allBuildings={renderBuildings}
        monsters={visibleMonsters}
        rendererReady={rendererReady}
        rendererFailed={rendererFailed}
        stageReady={stageSize.width > 0 && stageSize.height > 0}
        retryRenderer={() => { setRendererFailed(false); window.dispatchEvent(new Event('real-city:retry-renderer')) }}
      />
      <div className="map-debug" aria-live="polite">
        {performanceScenario ? <span>{performanceScenarioLabel(performanceScenario)}</span> : null}
        <MapFpsLabel />
        <span>chunk {centerChunk.x}:{centerChunk.y}</span>
        <span>zoom {camera.zoom.toFixed(2)}</span>
        <span>{chunksQuery.isFetching ? 'loading' : `${tiles.length} tiles`}</span>
      </div>
      {performanceScenario ? (
        <MapPerformanceHud
          scenario={performanceScenario}
        />
      ) : null}
    </section>
  )
}

function deriveVisibleChunkRadius(stageSize: { width: number; height: number }, zoom: number) {
  if (stageSize.width <= 0 || stageSize.height <= 0) {
    return 1
  }
  const gridReach = (stageSize.width / (2 * TILE_WIDTH) + stageSize.height / (2 * TILE_HEIGHT)) / zoom
  return Math.max(1, Math.min(3, Math.ceil((gridReach + 3) / CHUNK_SIZE)))
}

function MapFpsLabel() {
  const snapshot = useRenderPerformanceSnapshot()
  return <span>fps {snapshot.fps.toFixed(1)}</span>
}

function MapPerformanceHud({
  scenario,
}: {
  scenario: PerformanceScenario
}) {
  const snapshot = useRenderPerformanceSnapshot()

  return (
    <div className="map-performance-hud" aria-label="Performance HUD">
      <span>{scenario.name}</span>
      <span>fps {snapshot.fps.toFixed(1)}</span>
      <span>frame p50/p95 {snapshot.frameP50Ms.toFixed(1)}/{snapshot.frameP95Ms.toFixed(1)} ms</span>
      <span>visible tile/build/resource/monster {snapshot.visible.tiles}/{snapshot.visible.buildings}/{snapshot.visible.resources}/{snapshot.visible.monsters}</span>
      <span>Pixi children terrain/objects {snapshot.pixiChildren.terrain}/{snapshot.pixiChildren.objects}</span>
      <span>cache terrain/build/resource/overlay {snapshot.retainedCaches.terrain}/{snapshot.retainedCaches.buildings}/{snapshot.retainedCaches.resources}/{snapshot.retainedCaches.overlays}</span>
      <span>redraw #{snapshot.redraw.count} +{snapshot.redraw.created}/-{snapshot.redraw.destroyed}</span>
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

function damageScreenPosition(
  tile: { x: number; y: number },
  camera: { x: number; y: number; zoom: number },
  stage: { width: number; height: number },
) {
  const origin = { x: stage.width * 0.48 + camera.x, y: stage.height * 0.16 + camera.y }
  const target = { x: (stage.width / 2 - origin.x) / camera.zoom, y: (stage.height / 2 - origin.y) / camera.zoom }
  const pos = nearestWrappedScreenCoord(tile, target)
  return { x: origin.x + pos.x * camera.zoom, y: origin.y + pos.y * camera.zoom }
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
  centerChunk: { x: number; y: number },
  radius: number,
) {
  const now = Date.now()
  for (const [key, item] of recentChopTiles) {
    if (item.expiresAt <= now) {
      recentChopTiles.delete(key)
    }
  }
  const currentTilesByKey = new Map(currentTiles.map((tile) => [tileActionKey(tile), tile]))
  // Keep the overlap while the next chunk request is in flight. The renderer
  // clips off-screen tiles, and the extra ring is discarded as the camera moves.
  const merged = new Map(currentTiles.filter((tile) => {
    const chunk = tileToChunk(tile)
    return Math.abs(chunk.x - centerChunk.x) <= radius + 1 && Math.abs(chunk.y - centerChunk.y) <= radius + 1
  }).map((tile) => [tileActionKey(tile), tile]))
  for (const tile of tiles) {
    const key = tileActionKey(tile)
    const optimisticTile = optimisticTiles.get(key)
    if (optimisticTile) {
      merged.set(key, optimisticTile)
      continue
    }
    const recentChopTile = recentChopTiles.get(key)?.tile
    if (recentChopTile && shouldKeepRecentChopTile(tile, recentChopTile)) {
      merged.set(key, recentChopTile)
      continue
    }
    const currentTile = currentTilesByKey.get(key)
    if (currentTile && shouldKeepLocallyChoppedTile(tile, currentTile)) {
      merged.set(key, currentTile)
      continue
    }
    merged.set(key, tile)
  }
  return [...merged.values()]
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

type BuildingOverlay =
  | { type: 'timer'; text: string }
  | { type: 'ready'; label: string; rewards?: InventoryItem[] }
  | { type: 'workers'; workers: number; inputs?: InventoryItem[] }

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
        {overlay.inputs?.map((input) => (
          <span className="building-work-badge-input" key={input.resource}>
            <ResourceIcon id={input.resource} label={resourceCatalog.find((resource) => resource.id === input.resource)?.name ?? input.resource} />
            {input.amount}
          </span>
        ))}
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
    return { type: 'workers', workers: recipe.workers, inputs: recipe.input }
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
  return recipes.find((recipe) => recipe.building_type === building.kind && recipe.required_level === building.level)
    ?? recipes.find((recipe) => recipe.building_type === building.kind && recipe.required_level === 0)
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
